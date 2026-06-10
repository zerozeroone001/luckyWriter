from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from config import settings
from models import Base


# 创建异步引擎
engine = create_async_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=settings.DEBUG,
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_database():
    """初始化数据库：创建所有表并修复历史表结构。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _allow_nullable_ai_channel_model_name(conn)
        await _ensure_ai_generation_logs_model_id(conn)
        await _ensure_ai_generation_logs_request_fields(conn)
        await _ensure_novels_style_prompt(conn)


async def _ensure_ai_generation_logs_model_id(conn):
    """为旧版 AI 生成日志表补齐 model_id 字段。"""
    result = await conn.execute(text("PRAGMA table_info(ai_generation_logs)"))
    columns = result.fetchall()
    has_model_id = any(column[1] == "model_id" for column in columns)

    if has_model_id:
        return

    await conn.execute(text("ALTER TABLE ai_generation_logs ADD COLUMN model_id INTEGER"))


async def _ensure_ai_generation_logs_request_fields(conn):
    """为旧版 AI 生成日志表补齐请求信息字段。"""
    result = await conn.execute(text("PRAGMA table_info(ai_generation_logs)"))
    columns = result.fetchall()
    column_names = {column[1] for column in columns}
    fields = {
        "api_endpoint": "VARCHAR(200)",
        "channel_name": "VARCHAR(100)",
        "channel_provider": "VARCHAR(50)",
        "model_name": "VARCHAR(100)",
        "model_identifier": "VARCHAR(100)",
        "request_params": "TEXT",
    }

    for field_name, field_type in fields.items():
        if field_name not in column_names:
            await conn.execute(text(f"ALTER TABLE ai_generation_logs ADD COLUMN {field_name} {field_type}"))


async def _ensure_novels_style_prompt(conn):
    """为 novels 表补齐 style_prompt 字段。"""
    result = await conn.execute(text("PRAGMA table_info(novels)"))
    columns = result.fetchall()
    has_style_prompt = any(column[1] == "style_prompt" for column in columns)

    if not has_style_prompt:
        await conn.execute(text("ALTER TABLE novels ADD COLUMN style_prompt TEXT"))


async def _allow_nullable_ai_channel_model_name(conn):
    """将旧版 ai_channels.model_name 的非空约束迁移为可空。"""
    result = await conn.execute(text("PRAGMA table_info(ai_channels)"))
    columns = result.fetchall()
    model_name_column = next((column for column in columns if column[1] == "model_name"), None)

    if model_name_column is None or not model_name_column[3]:
        return

    column_definitions = []
    column_names = []

    for _, name, column_type, notnull, default_value, primary_key in columns:
        quoted_name = _quote_sqlite_identifier(name)
        normalized_type = column_type or "TEXT"
        column_names.append(quoted_name)

        if primary_key:
            definition = f"{quoted_name} {normalized_type} PRIMARY KEY"
            if name == "id" and normalized_type.upper() == "INTEGER":
                definition += " AUTOINCREMENT"
        else:
            definition = f"{quoted_name} {normalized_type}"
            if name != "model_name" and notnull:
                definition += " NOT NULL"
            if default_value is not None:
                definition += f" DEFAULT {default_value}"

        column_definitions.append(definition)

    joined_columns = ", ".join(column_names)
    await conn.execute(text("PRAGMA foreign_keys=OFF"))
    await conn.execute(text(f"CREATE TABLE ai_channels_new ({', '.join(column_definitions)})"))
    await conn.execute(text(f"INSERT INTO ai_channels_new ({joined_columns}) SELECT {joined_columns} FROM ai_channels"))
    await conn.execute(text("DROP TABLE ai_channels"))
    await conn.execute(text("ALTER TABLE ai_channels_new RENAME TO ai_channels"))
    await conn.execute(text("PRAGMA foreign_keys=ON"))


def _quote_sqlite_identifier(identifier: str) -> str:
    """安全引用 SQLite 标识符。"""
    return f'"{identifier.replace(chr(34), chr(34) * 2)}"'


async def get_db() -> AsyncSession:
    """获取数据库会话（依赖注入）"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

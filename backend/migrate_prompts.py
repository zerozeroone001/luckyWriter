"""迁移 system_presets 表结构"""
from sqlalchemy import create_engine, text
from config import settings

sync_engine = create_engine(settings.database_url.replace('+aiosqlite', ''))

with sync_engine.connect() as conn:
    # 创建新表
    conn.execute(text("""
    CREATE TABLE system_presets_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        prompt_type VARCHAR(50) DEFAULT 'default',
        prompt_role VARCHAR(100) NOT NULL,
        system_prompt TEXT NOT NULL,
        use_case VARCHAR(100),
        is_default BOOLEAN DEFAULT 0,
        created_at DATETIME,
        updated_at DATETIME
    )
    """))

    # 迁移旧数据（如果存在）
    result = conn.execute(text("SELECT COUNT(*) FROM system_presets"))
    count = result.scalar()

    if count > 0:
        conn.execute(text("""
        INSERT INTO system_presets_new (id, name, prompt_type, prompt_role, system_prompt, use_case, is_default, created_at, updated_at)
        SELECT id, preset_name, 'default', COALESCE(description, '默认角色'), system_prompt, use_case, is_default, created_at, updated_at
        FROM system_presets
        """))

    # 删除旧表
    conn.execute(text("DROP TABLE system_presets"))

    # 重命名新表
    conn.execute(text("ALTER TABLE system_presets_new RENAME TO system_presets"))

    conn.commit()
    print("表结构迁移完成")

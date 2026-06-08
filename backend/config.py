from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """应用配置"""

    # 应用基本配置
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    DEBUG: bool = True

    # 项目根目录
    BASE_DIR: Path = Path(__file__).parent.parent

    # 数据库配置
    DATABASE_PATH: str = "data/writer.db"

    # AI 渠道配置
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    # 备份配置
    BACKUP_RETENTION_DAYS: int = 30
    AUTO_BACKUP_INTERVAL_HOURS: int = 24

    # 内容过滤关键词（政治、暴力、色情等）
    FILTER_KEYWORDS: list = [
        "敏感词1", "敏感词2"  # 根据需要配置
    ]

    @property
    def database_url(self) -> str:
        """数据库连接URL"""
        db_path = self.BASE_DIR / self.DATABASE_PATH
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{db_path}"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

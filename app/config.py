from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # API配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True

    # 数据库配置
    DB_PATH: str = "market_data.db"

    # API密钥
    CG_API_KEY: str = os.getenv("CG_API_KEY", "")
    CMC_API_KEY: str = os.getenv("CMC_API_KEY", "")
    COOKIE: str = os.getenv("COOKIE", "")

    # 调试模式
    DEBUG: bool = False

    # 数据刷新配置
    FORCE_REFRESH_DATA: bool = False

    # 定时任务配置
    COIN_LIST_REFRESH_INTERVAL_MINUTES: int = 1440
    EXCHANGE_DATA_REFRESH_INTERVAL_MINUTES: int = 120
    TOKEN_HOLDERS_REFRESH_INTERVAL_MINUTES: int = 1440
    MARKET_DATA_REFRESH_INTERVAL_MINUTES: int = 120

    class Config:
        env_file = ".env"

# 创建全局配置实例
settings = Settings()

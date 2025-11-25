from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # API配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = False

    # Coingecko API配置
    CG_API_KEY: Optional[str] = None
    CMC_API_KEY: Optional[str] = None
    # Cookie相关配置
    COOKIE: Optional[str] = None

    # 调度器配置
    SCHEDULER_INTERVAL: int = 300  # 5分钟更新一次

    # 日志配置
    LOG_LEVEL: str = "INFO"

    # 启动项
    FORCE_REFRESH_DATA: bool = True

    class Config:
        # 检查是否在Docker环境中运行
        if not os.getenv("DOCKER_ENV"):
            env_file = ".env"
        env_file_encoding = "utf-8"


# 创建全局配置实例
settings = Settings()

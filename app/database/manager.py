from sqlmodel import create_engine, Session
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_url: str = None):
        if db_url is None:
            db_url = f"sqlite:///{settings.DB_PATH}"

        self.engine = create_engine(db_url, echo=settings.DEBUG)

    def init_db(self):
        """初始化数据库表结构"""
        try:
            # 使用 SQLModel 的方式创建所有表
            from app.database.models import SQLModel
            SQLModel.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")

    def get_session(self) -> Session:
        """获取数据库会话"""
        return Session(self.engine)

    def close_session(self, session):
        """关闭数据库会话"""
        session.close()

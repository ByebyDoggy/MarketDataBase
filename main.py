from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from app.database.processor import DataProcessor
from app.database.models import Coin
from app.database.manager import DatabaseManager
from app.config import settings
import logging
import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.database.query import CoinRepository
from app.sevice import CoinService
# 添加GraphQL相关导入
import strawberry
from strawberry.fastapi import GraphQLRouter
from app.graphql import Query as GraphQLQuery

# 初始化组件
db_manager = DatabaseManager()
app_service: CoinService = None

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_session():
    """依赖注入：获取数据库会话"""
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db_manager.close_session(db)

def get_coin_service(db: Session = Depends(get_db_session)):
    """依赖注入：获取币种服务"""
    repository = CoinRepository(db)
    processor = DataProcessor(db)
    return CoinService(repository, processor)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global app_service

    # 初始化数据库
    db_manager.init_db()

    # 获取数据库会话和服务
    db = db_manager.get_session()
    repository = CoinRepository(db)
    processor = DataProcessor(db)
    app_service = CoinService(repository, processor)

    # 初始化数据
    force_refresh = settings.FORCE_REFRESH_DATA
    if force_refresh:
        await app_service.refresh_data()
    db_manager.close_session(db)

    # schedule 定时任务
    scheduler = AsyncIOScheduler()
    scheduler.add_job(app_service.processor.initialize_coins_data, IntervalTrigger(minutes=settings.COIN_LIST_REFRESH_INTERVAL_MINUTES))
    scheduler.add_job(app_service.processor.update_exchange_data, IntervalTrigger(minutes=settings.EXCHANGE_DATA_REFRESH_INTERVAL_MINUTES))
    scheduler.add_job(app_service.processor.update_market_data, IntervalTrigger(minutes=settings.MARKET_DATA_REFRESH_INTERVAL_MINUTES))
    scheduler.add_job(app_service.processor.update_top_project_token_holders, IntervalTrigger(minutes=settings.TOKEN_HOLDERS_REFRESH_INTERVAL_MINUTES))
    scheduler.start()

    logger.info("Application started")
    yield
    logger.info("Application stopped")

# 创建GraphQL schema
schema = strawberry.Schema(query=GraphQLQuery)

app = FastAPI(
    title="Coingecko Data API",
    description="基于Coingecko SDK的加密货币数据服务",
    version="2.0.0",
    lifespan=lifespan
)

# 添加GraphQL路由
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ... existing code ...

# 删除原有的HTTP查询端点，只保留根路径和健康检查端点
@app.get("/")
async def root():
    return {
        "message": "Coingecko Data API",
        "status": "running",
        "version": "2.0.0",
        "graphql_endpoint": "/graphql"
    }

@app.get("/health")
async def health_check(service: CoinService = Depends(get_coin_service)):
    """健康检查"""
    db = next(get_db_session())
    coin_count = db.query(Coin).count()
    return {
        "status": "healthy",
        "coin_count": coin_count
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.API_HOST, port=settings.API_PORT, reload=settings.API_RELOAD)

# main.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.data_processor import DataProcessor
from app.models import CoinInfo, SearchRequest
import logging
import uvicorn
from typing import List
from app.config import settings
from app.scheduler import DataScheduler

# 初始化数据调度器
data_scheduler: DataScheduler = DataScheduler()
# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global data_scheduler
    await data_scheduler.initialize_data(force_refresh=settings.FORCE_REFRESH_DATA)
    processor:DataProcessor = data_scheduler.processor
    await processor.fetch_token_top_holders(token_id='swell-network',use_sync=True)
    data_scheduler.start_scheduler()
    logger.info("Application started")
    yield
    data_scheduler.stop_scheduler()
    logger.info("Application stopped")


app = FastAPI(
    title="Coingecko Data API",
    description="基于Coingecko SDK的加密货币数据服务",
    version="1.0.0",
    lifespan=lifespan
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "Coingecko Data API",
        "status": "running",
        "initialized": data_scheduler.is_initialized if data_scheduler else False
    }

@app.get("/coin/by_contract/{contract_address}")
async def get_coin_by_contract(contract_address: str) -> List[CoinInfo]:
    """
    根据链上合约地址获取币种信息
    支持多个链（返回所有匹配）
    """
    global data_scheduler
    if not data_scheduler or not data_scheduler.is_initialized:
        raise HTTPException(status_code=503, detail="Service initializing")

    normalized_addr = contract_address.lower()
    matches = []

    for coin in data_scheduler.processor.coin_data.values():
        for info in coin.on_chain_info:
            if info.contract_address.lower() == normalized_addr:
                matches.append(coin)
                break

    if not matches:
        raise HTTPException(status_code=404, detail="No coin found for this contract address")

    return matches

@app.get("/coin/{coin_id}")
async def get_coin_by_id(coin_id: str) -> CoinInfo:
    """根据coin_id获取币种信息"""
    global data_scheduler
    if not data_scheduler or not data_scheduler.is_initialized:
        raise HTTPException(status_code=503, detail="Service initializing")

    coin_info = data_scheduler.processor.get_coin_by_id(coin_id)
    if not coin_info:
        raise HTTPException(status_code=404, detail="Coin not found")

    return coin_info


@app.post("/search")
async def search_coin(request: SearchRequest) -> list[CoinInfo]:
    """搜索币种信息"""
    global data_scheduler
    if not data_scheduler or not data_scheduler.is_initialized:
        raise HTTPException(status_code=503, detail="Service initializing")

    if not request.search_term.strip():
        raise HTTPException(status_code=400, detail="Search term cannot be empty")

    results = data_scheduler.processor.search_coins(request.search_term)
    return results


@app.get("/search")
async def search_coin_get(search_term: str = Query(..., description="搜索词")) -> list[CoinInfo]:
    """搜索币种信息 (GET版本)"""
    global data_scheduler
    if not data_scheduler or not data_scheduler.is_initialized:
        raise HTTPException(status_code=503, detail="Service initializing")

    if not search_term.strip():
        raise HTTPException(status_code=400, detail="Search term cannot be empty")

    results = data_scheduler.processor.search_coins(search_term)
    return results


@app.get("/coins")
async def get_all_coins(limit: int = Query(100, ge=1, le=1000)) -> list[CoinInfo]:
    """获取所有币种信息（分页）"""
    global data_scheduler
    if not data_scheduler or not data_scheduler.is_initialized:
        raise HTTPException(status_code=503, detail="Service initializing")

    coin_ids = data_scheduler.processor.get_all_coin_ids()[:limit]
    coins = []
    for coin_id in coin_ids:
        coin_info = data_scheduler.processor.get_coin_by_id(coin_id)
        if coin_info:
            coins.append(coin_info)

    return coins

# 新增：根据holder address查询持有代币信息的端点
@app.get("/holder/{holder_address}/tokens")
async def get_tokens_by_holder(holder_address: str) -> list[CoinInfo]:
    """
    根据holder address查询持有的代币信息
    """
    global data_scheduler
    if not data_scheduler or not data_scheduler.is_initialized:
        raise HTTPException(status_code=503, detail="Service initializing")

    # 验证holder_address格式（简单验证）
    if not holder_address or len(holder_address) < 10:
        raise HTTPException(status_code=400, detail="Invalid holder address")

    # 调用processor中的方法获取holder持有的代币信息
    # 注意：这里假设data_scheduler.processor有get_tokens_by_holder方法
    try:
        tokens = data_scheduler.processor.get_coins_by_holder(holder_address)
        if not tokens:
            raise HTTPException(status_code=404, detail="No tokens found for this holder")
        return tokens
    except AttributeError:
        raise HTTPException(status_code=501, detail="This feature is not implemented yet")
    except Exception as e:
        logger.error(f"Error fetching tokens for holder {holder_address}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check():
    """健康检查"""
    global data_scheduler
    status = "healthy" if data_scheduler and data_scheduler.is_initialized else "initializing"
    coin_count = len(data_scheduler.processor.coin_data) if data_scheduler else 0

    return {
        "status": status,
        "initialized": data_scheduler.is_initialized if data_scheduler else False,
        "coin_count": coin_count,
        "search_index_size": len(data_scheduler.processor.search_index) if data_scheduler else 0
    }

# 添加一个新的端点用于手动触发数据保存
@app.post("/admin/save-data")
async def save_data():
    """手动保存数据到数据库"""
    global data_scheduler
    if not data_scheduler or not data_scheduler.is_initialized:
        raise HTTPException(status_code=503, detail="Service initializing")

    try:
        data_scheduler.processor.save_to_db()
        return {"message": "Data saved successfully"}
    except Exception as e:
        logger.error(f"Error saving data: {e}")
        raise HTTPException(status_code=500, detail="Failed to save data")



if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.API_HOST, port=settings.API_PORT, reload=settings.API_RELOAD)

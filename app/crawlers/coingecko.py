from app.crawlers.core import BaseCrawler
from coingecko_sdk import AsyncCoingecko
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class CoingeckoCrawler(BaseCrawler):
    def __init__(self):
        self.cg = AsyncCoingecko(demo_api_key=settings.CG_API_KEY, environment='demo')

    async def fetch_coins_list(self):
        """获取币种列表"""
        try:
            response = await self.cg.coins.list.get(include_platform=True)
            return response
        except Exception as e:
            logger.error(f"Error fetching coins list: {e}")
            return []

    async def fetch_markets_data(self, vs_currency: str = "usd", page: int = 1):
        """获取市场数据"""
        try:
            response = await self.cg.coins.markets.get(vs_currency=vs_currency, page=page)
            return response
        except Exception as e:
            logger.error(f"Error fetching markets data: {e}")
            return []

    async def fetch_exchange_tickers(self, exchange_id: str):
        """获取交易所交易对"""
        try:
            response = await self.cg.exchanges.tickers.get(id=exchange_id)
            return response.tickers
        except Exception as e:
            logger.error(f"Error fetching exchange tickers for {exchange_id}: {e}")
            return []

    async def fetch_derivatives_tickers(self, exchange_id: str):
        """获取衍生品交易所交易对"""
        try:
            response = await self.cg.derivatives.exchanges.get_id(
                id=exchange_id,
                include_tickers='unexpired'
            )
            return response.tickers
        except Exception as e:
            logger.error(f"Error fetching derivatives tickers for {exchange_id}: {e}")
            return []

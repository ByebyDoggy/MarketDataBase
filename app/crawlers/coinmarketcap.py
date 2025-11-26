from app.crawlers.core import BaseCrawler
from coinmarketcapapi import CoinMarketCapAPI
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class CoinMarketCapCrawler(BaseCrawler):
    def __init__(self):
        self.cmc = CoinMarketCapAPI(api_key=settings.CMC_API_KEY)

    def fetch_listings_latest(self, limit: int = 2000):
        """获取最新上市列表"""
        try:
            response = self.cmc.cryptocurrency_listings_latest(limit=limit)
            return response.data
        except Exception as e:
            logger.error(f"Error fetching CMC listings: {e}")
            return []

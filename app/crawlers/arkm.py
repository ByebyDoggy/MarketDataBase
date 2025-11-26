from app.crawlers.core import BaseCrawler
from arkm import AsyncArkmClient, SyncArkmClient
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class ArkmCrawler(BaseCrawler):
    def __init__(self):
        self.arkm_async_client = AsyncArkmClient(cookie=settings.COOKIE)
        self.arkm_sync_client = SyncArkmClient(cookie=settings.COOKIE)

    async def fetch_token_holders(self, token_id: str, use_sync: bool = False):
        """获取代币持有者"""
        path = f"/token/holders/{token_id}?groupByEntity=true"
        try:
            if use_sync:
                response = self.arkm_sync_client.get(path=path)
            else:
                response = await self.arkm_async_client.get(path=path)
            return response
        except Exception as e:
            logger.error(f"Error fetching token holders for {token_id}: {e}")
            return {}

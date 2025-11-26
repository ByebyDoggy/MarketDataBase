import asyncio

from app.database.processor import DataProcessor
from app.database.models import Coin
from typing import List, Optional

from app.database.query import CoinRepository


class CoinService:
    def __init__(self, coin_repository: CoinRepository, data_processor: DataProcessor):
        self.repository = coin_repository
        self.processor = data_processor

    def get_coin_by_id(self, coin_id: str) -> Optional[Coin]:
        """根据ID获取币种"""
        return self.repository.get_coin_by_id(coin_id)

    def get_coins_by_contract_address(self, contract_address: str) -> List[Coin]:
        """根据合约地址获取币种"""
        return self.repository.get_coins_by_contract_address(contract_address)

    def get_coins_by_exchange(self, exchange_id: str) -> List[Coin]:
        """根据交易所获取币种"""
        return self.repository.get_coins_by_exchange(exchange_id)

    def search_coins(self, search_term: str) -> List[Coin]:
        """搜索币种"""
        return self.repository.search_coins(search_term)

    def get_all_coins(self, limit: int = 100) -> List[Coin]:
        """获取所有币种"""
        return self.repository.get_all_coins(limit)

    def get_tokens_by_holder(self, holder_address: str) -> List[Coin]:
        """根据持有者地址获取代币"""
        return self.repository.get_tokens_by_holder(holder_address)

    async def refresh_data(self):
        """刷新数据"""
        await self.processor.initialize_coins_data()
        await self.processor.update_market_data()
        await self.processor.update_exchange_data()
        asyncio.create_task(self.processor.update_top_project_token_holders())

# scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.data_processor import DataProcessor
import logging

logger = logging.getLogger(__name__)


class DataScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.processor = DataProcessor()
        self.is_initialized = False

    async def initialize_data(self, force_refresh: bool = True):
        """初始化数据"""
        try:
            await self.processor.initialize_data(force_refresh)
            coin_ids = self.processor.get_all_coin_ids()
            logger.info(f"Initialized data for {len(coin_ids)} coins")
            await self.processor.update_top_exchanges_infos()
            logger.info(f"Updated top exchanges infos for {len(coin_ids)} coins")
            await self.processor.update_markets_data()
            logger.info(f"Updated markets data for {len(coin_ids)} coins")
            self.is_initialized = True
            logger.info(f"Data initialization completed for {len(coin_ids)} coins")
        except Exception as e:
            logger.error(f"Error initializing data: {e}")

    async def update_flow(self):
        if not self.is_initialized:
            return
        try:
            await self.processor.initialize_data()
            await self.processor.update_top_exchanges_infos()
            await self.processor.update_markets_data()
        except Exception as e:
            logger.error(f"Error updating top coins: {e}")

    def start_scheduler(self):
        """启动定时任务"""
        # 每30分钟更新一次前30个币种的数据
        self.scheduler.add_job(
            self.update_flow,
            trigger=IntervalTrigger(minutes=60*24),
            id='update_top_coins'
        )

        # 每1小时写入一次数据库
        self.scheduler.add_job(
            self.save_data,
            trigger=IntervalTrigger(hours=1),
            id='save_data_to_db'
        )

        self.scheduler.add_job(
            self.update_exchange_tokens_holders,
            trigger=IntervalTrigger(hours=24),
            id='update_exchange_tokens_holders'
        )

        self.scheduler.start()
        logger.info("Data scheduler started")

    def stop_scheduler(self):
        """停止定时任务"""
        self.scheduler.shutdown()
        logger.info("Data scheduler stopped")

    def save_data(self):
        """手动保存数据到数据库"""
        if not self.is_initialized:
            return
        try:
            self.processor.save_to_db()
            logger.info("Data saved successfully")
        except Exception as e:
            logger.error(f"Error saving data: {e}")

    async def update_exchange_tokens_holders(self):
        """更新交易所代币持有者"""
        if not self.is_initialized:
            return
        try:
            for coin_id,coin_info in self.processor.coin_data.items():
                spots = coin_info.exchange_spots
                perps = coin_info.exchange_contracts
                if spots or perps:
                    await self.processor.fetch_token_top_holders(coin_id,use_sync=True)
            logger.info("Exchange tokens holders updated successfully")
        except Exception as e:
            logger.error(f"Error updating Binance tokens holders: {e}")

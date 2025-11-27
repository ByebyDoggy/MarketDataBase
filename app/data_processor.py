import asyncio
import sqlite3
from collections import defaultdict
from typing import List, Dict, Optional, Set

from arkm import AsyncArkmClient, SyncArkmClient
from app.models import ExchangeSpot, ExchangeContract, OnChainInfo, SupplyInfo, CoinInfo, AddressHolder, ArkmLabel
from coingecko_sdk import AsyncCoingecko
import logging
from app.const import TOP_SWAP_EXCHANGES, TOP_SPOT_EXCHANGES, ORIGIN_TOKEN_WRAPPED_TOKEN_MAP
from app.config import settings
from coinmarketcapapi import CoinMarketCapAPI

logger = logging.getLogger(__name__)


class DataProcessor:
    def __init__(self, db_path: str = "market_data.db"):
        self.coin_data: Dict[str, CoinInfo] = {}
        self.search_index: Dict[str, Set[str]] = defaultdict(set)  # 确保有这一行
        self.search_index: Dict[str, List[str]] = {}  # search_term -> [coin_ids]
        self.holder_to_coins: Dict[str, Set[str]] = {}  # address -> set of coin_ids
        self.cg = AsyncCoingecko(demo_api_key=settings.CG_API_KEY, environment='demo')
        self.cmc = CoinMarketCapAPI(api_key=settings.CMC_API_KEY)
        self.arkm_async_client = AsyncArkmClient(cookie=settings.COOKIE)
        self.arkm_sync_client = SyncArkmClient(cookie=settings.COOKIE)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建存储币种信息的表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coins (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def save_to_db(self):
        """将内存中的数据保存到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for coin_id, coin_info in self.coin_data.items():
            # 将CoinInfo对象序列化为JSON字符串
            coin_data = coin_info.model_dump_json()
            cursor.execute(
                "INSERT OR REPLACE INTO coins (id, data) VALUES (?, ?)",
                (coin_id, coin_data)
            )

        conn.commit()
        conn.close()
        logging.info(f"Saved {len(self.coin_data)} coins to database")

    def load_from_db(self) -> bool:
        """从数据库加载数据到内存"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT id, data FROM coins")
            rows = cursor.fetchall()

            self.coin_data.clear()
            for row in rows:
                coin_id, coin_data = row
                # 反序列化JSON字符串为CoinInfo对象
                coin_info = CoinInfo.model_validate_json(coin_data)
                self.coin_data[coin_id] = coin_info

            conn.close()
            self._build_search_index()
            logging.info(f"Loaded {len(self.coin_data)} coins from database")
            return True
        except Exception as e:
            logging.error(f"Failed to load data from database: {e}")
            return False

    async def initialize_data(self, force_refresh: bool = True):
        """初始化数据"""
        if not force_refresh:
            # 尝试从数据库加载数据
            if self.load_from_db() and len(self.coin_data) > 0:
                logging.info("Data loaded from database")
                return

        try:
            # 初始化链上合约全币种信息
            coins_list_response = await self.cg.coins.list.get(include_platform=True)
            for info in coins_list_response:
                coin_id = info.id
                symbol = info.symbol.upper()
                name = info.name
                # 初始化币种信息
                if coin_id not in self.coin_data:
                    self.coin_data[coin_id] = CoinInfo(
                        coin_id=coin_id,
                        symbol=symbol,
                        name=name,
                        exchange_spots=set(),
                        exchange_contracts=set(),
                        on_chain_info={OnChainInfo(chain_name=chain_name, contract_address=address)
                                       for chain_name, address in info.platforms.items() if address},
                        supply_info=SupplyInfo()
                    )
                # 更新搜索索引
                self._update_search_index(coin_id, symbol, name)
            logger.info("Initializing coin data...")
            self.save_to_db()
        except Exception as e:
            logger.error(f"Error initializing data: {e}")

    async def update_markets_data(self):
        response = self.cmc.cryptocurrency_listings_latest(limit=2000)
        datas = response.data
        for data in datas:
            coin_id = data.get('slug')
            cmc_symbol = data.get('symbol')
            cmc_name = data.get('name')
            # 查找全部CoinInfo ,若symbol与cmc_symbol且name与cmc_name匹配，无需coin_id一致
            for info in self.coin_data.values():
                if info.symbol == cmc_symbol and info.name == cmc_name:
                    coin_id = info.coin_id
                    break
            circulating_supply = data.get('circulating_supply')
            total_supply = data.get('total_supply')
            market_cap = data.get('quote', {}).get('USD', {}).get('market_cap')
            if coin_id in self.coin_data:
                self.coin_data[coin_id].supply_info = SupplyInfo(
                    total_supply=total_supply,
                    circulating_supply=circulating_supply,
                    cached_price=data.get('quote', {}).get('USD', {}).get('price'),
                    market_cap=market_cap
                )
            if coin_id in ORIGIN_TOKEN_WRAPPED_TOKEN_MAP:
                for wrapped_token in ORIGIN_TOKEN_WRAPPED_TOKEN_MAP[coin_id]:
                    if wrapped_token in self.coin_data:
                        self.coin_data[wrapped_token].supply_info = self.coin_data[coin_id].supply_info
        logger.info(f"Initialized {len(self.coin_data)} coins")

    async def update_top_exchanges_infos(self):
        """更新币种详细信息"""
        try:
            # 顶级现货交易所数据更新
            for spot_exchange_id in TOP_SPOT_EXCHANGES:
                tickers_response = await self.cg.exchanges.tickers.get(id=spot_exchange_id)
                tickers = tickers_response.tickers
                for ticker in tickers:
                    if hasattr(ticker, 'base') and hasattr(ticker, 'target'):
                        base = ticker.base.upper()
                        target = ticker.target.upper()
                        coin_id = ticker.coin_id
                        if target in ['USDT', 'USDC']:
                            if coin_id in self.coin_data:
                                self.coin_data[coin_id].exchange_spots.add(ExchangeSpot(
                                    exchange_name=spot_exchange_id,
                                    spot_name=f"{base}/{target}"
                                ))
                                self._update_search_index(coin_id, base)
                                self._update_search_index(coin_id, f"{base}/{target}")
            await asyncio.sleep(0.5)
            # 顶级合约交易所数据更新
            for swap_exchange_id in TOP_SWAP_EXCHANGES:
                tickers_response = await self.cg.derivatives.exchanges.get_id(id=swap_exchange_id,
                                                                              include_tickers='unexpired')
                tickers = tickers_response.tickers
                for ticker in tickers:
                    if hasattr(ticker, 'base') and hasattr(ticker, 'target'):
                        base = ticker.base.upper()
                        target = ticker.target.upper()
                        if target in ['USDT', 'USDC']:
                            if ticker.coin_id in self.coin_data:
                                self.coin_data[ticker.coin_id].exchange_contracts.add(ExchangeContract(
                                    exchange_name=swap_exchange_id,
                                    contract_name=f"{base}/{target}"
                                ))
                            else:
                                if not ticker.coin_id:
                                    continue
                                self.coin_data[ticker.coin_id] = CoinInfo(
                                    coin_id=ticker.coin_id,
                                    symbol=ticker.base.upper(),
                                    name=ticker.base,
                                    exchange_contracts={ExchangeContract(
                                        exchange_name=swap_exchange_id,
                                        contract_name=f"{base}/{target}"
                                   )},
                                    exchange_spots=set(),
                                    on_chain_info=set(),
                                    supply_info=SupplyInfo()
                                )
                            self._update_search_index(ticker.coin_id, base)
                            self._update_search_index(ticker.coin_id, f"{base}/{target}")
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Error updating details for : {e}")
            import traceback
            traceback.print_exc()

    def _update_search_index(self, coin_id: str, *search_terms: str) -> None:
        """更新搜索索引"""
        for term in search_terms:
            if term:
                term_lower = str(term).lower().strip()
                if term_lower not in self.search_index:
                    self.search_index[term_lower] = []
                if coin_id not in self.search_index[term_lower]:
                    self.search_index[term_lower].append(coin_id)

    def search_coins(self, search_term: str) -> List[CoinInfo]:
        """搜索币种信息"""
        search_term_lower = search_term.lower().strip()
        coin_ids = self.search_index.get(search_term_lower, [])

        results = []
        for coin_id in coin_ids:
            if coin_id in self.coin_data:
                results.append(self.coin_data[coin_id])

        return results

    def get_coin_by_id(self, coin_id: str) -> Optional[CoinInfo]:
        """根据coin_id获取币种信息"""
        return self.coin_data.get(coin_id)

    def get_all_coin_ids(self) -> List[str]:
        """获取所有coin_id"""
        return list(self.coin_data.keys())

    async def fetch_token_top_holders(self, token_id: str, use_sync: bool = False):
        """获取代币顶部持有者"""
        path = f"/token/holders/{token_id}?groupByEntity=true"
        try:
            if use_sync:
                response = self.arkm_sync_client.get(path=path)
            else:
                response = await self.arkm_async_client.get(path=path)
        except Exception:
            return []
        try:
            if response:
                json_response = response
                addressTopHolders = json_response.get('addressTopHolders', [])
                for chain, holders in addressTopHolders.items():
                    if not holders:
                        continue
                    for holder in holders:
                        address_info = holder.get('address', {})
                        if address_info:
                            label_info = address_info.get('arkhamLabel', {})
                            address = address_info.get('address', '')
                            holder_obj = AddressHolder(
                                address=address,
                                label=ArkmLabel(
                                    name=label_info.get('name', ''),
                                    address=label_info.get('address', ''),
                                    chain_type=chain
                                ),
                                balance=holder.get('balance'),
                                usd_value=holder.get('usd')
                            )
                            # 将holder添加进币的信息里
                            self.coin_data[token_id].holders.add(holder_obj)
                            # 同步更新反向索引：该地址持有哪些币
                            if address not in self.holder_to_coins:
                                self.holder_to_coins[address] = set()
                            self.holder_to_coins[address].add(token_id)
            return []
        except Exception as e:
            logger.error(f"Error fetching token top holders for {token_id}: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_coins_by_holder(self, holder_address: str) -> List[CoinInfo]:
        """根据地址获取其所持有的所有代币信息"""
        coin_ids = self.holder_to_coins.get(holder_address, set())
        result = []
        for cid in coin_ids:
            if cid in self.coin_data:
                result.append(self.coin_data[cid])
        return result

    def _build_search_index(self):
        """构建搜索索引"""
        self.search_index.clear()
        for coin_id, coin_info in self.coin_data.items():
            self._update_search_index(coin_id, coin_info.symbol, coin_info.name)
        logger.info(f"Built search index with {len(self.search_index)} entries")

    def get_coins_by_exchange(self, exchange_id: str) -> List[CoinInfo]:
        """根据交易所ID获取币种信息"""
        result = []
        for coin_id, coin_info in self.coin_data.items():
            exchange_names = {spot.exchange_name for spot in coin_info.exchange_spots} | {contract.exchange_name for contract in coin_info.exchange_contracts}
            if exchange_id in exchange_names:
                result.append(coin_info)
        return result

from sqlalchemy.orm import Session
from app.database.models import Coin, SupplyInfo, OnChainInfo, ExchangeSpot, ExchangeContract, Holder, CoinHolding, \
    ARKMEntity, Label
from app.crawlers.coingecko import CoingeckoCrawler
from app.crawlers.coinmarketcap import CoinMarketCapCrawler
from app.crawlers.arkm import ArkmCrawler
from app.const import TOP_SPOT_EXCHANGES, TOP_SWAP_EXCHANGES, UPDATE_HOLDERS_EXCHANGES, ORIGIN_TOKEN_WRAPPED_TOKEN_MAP
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.cg_crawler = CoingeckoCrawler()
        self.cmc_crawler = CoinMarketCapCrawler()
        self.arkm_crawler = ArkmCrawler()

    async def initialize_coins_data(self):
        """初始化币种数据"""
        # 获取币种列表并保存到数据库
        coins_list = await self.cg_crawler.fetch_coins_list()
        for item in coins_list:
            # 检查币种是否已存在
            existing_coin = self.db.query(Coin).filter(Coin.id == item.id).first()
            if not existing_coin:
                coin = Coin(
                    id=item.id,
                    symbol=item.symbol.upper(),
                    name=item.name
                )
                self.db.add(coin)

                # 保存链上信息
                for chain_name, contract_address in item.platforms.items():
                    if contract_address:
                        on_chain_info = OnChainInfo(
                            coin_id=item.id,
                            chain_name=chain_name,
                            contract_address=contract_address
                        )
                        self.db.add(on_chain_info)

        self.db.commit()
        logger.info(f"Initialized {len(coins_list)} coins")

    async def update_market_data(self):
        """更新市场数据"""
        # 获取CMC数据
        cmc_data = self.cmc_crawler.fetch_listings_latest()

        for item in cmc_data:
            coin_id = item.get('slug')
            cmc_symbol = item.get('symbol')
            cmc_name = item.get('name')
            # 查找匹配的币种
            coin = self.db.query(Coin).filter(
                Coin.symbol == cmc_symbol.upper(),
                Coin.name == cmc_name
            ).first()
            if coin:
                print(f"Found coin: {coin.id} - {coin.symbol} - {coin.name}")
                # 更新供应信息
                supply_info = self.db.query(SupplyInfo).filter(
                    SupplyInfo.coin_id == coin.id
                ).first()

                if not supply_info:
                    supply_info = SupplyInfo(coin_id=coin.id)
                    self.db.add(supply_info)

                supply_info.total_supply = item.get('total_supply')
                supply_info.circulating_supply = item.get('circulating_supply')
                supply_info.market_cap = item.get('quote', {}).get('USD', {}).get('market_cap')
                supply_info.cached_price = item.get('quote', {}).get('USD', {}).get('price')

                # 处理包装代币供应信息
                if coin_id in ORIGIN_TOKEN_WRAPPED_TOKEN_MAP:
                    for wrapped_token_id in ORIGIN_TOKEN_WRAPPED_TOKEN_MAP[coin_id]:
                        wrapped_coin = self.db.query(Coin).filter(Coin.id == wrapped_token_id).first()
                        if wrapped_coin:
                            # 为包装代币单独创建 SupplyInfo 或复用已有 SupplyInfo 并复制数据
                            wrapped_supply_info = self.db.query(SupplyInfo).filter(
                                SupplyInfo.coin_id == wrapped_coin.id
                            ).first()

                            if not wrapped_supply_info:
                                wrapped_supply_info = SupplyInfo(coin_id=wrapped_coin.id)
                                self.db.add(wrapped_supply_info)

                            # 将原始代币的数据拷贝到包装代币
                            wrapped_supply_info.total_supply = supply_info.total_supply
                            wrapped_supply_info.circulating_supply = supply_info.circulating_supply
                            wrapped_supply_info.market_cap = supply_info.market_cap
                            wrapped_supply_info.cached_price = supply_info.cached_price
        self.db.commit()
        logger.info("Market data updated")

    async def update_exchange_data(self):
        """更新交易所数据"""
        # 更新现货交易所
        for exchange_id in TOP_SPOT_EXCHANGES:
            tickers = await self.cg_crawler.fetch_exchange_tickers(exchange_id)
            for ticker in tickers:
                if hasattr(ticker, 'base') and hasattr(ticker, 'target'):
                    base = ticker.base.upper()
                    target = ticker.target.upper()
                    coin_id = ticker.coin_id

                    if target in ['USDT', 'USDC']:
                        # 查找币种
                        coin = self.db.query(Coin).filter(Coin.id == coin_id).first()
                        if coin:
                            # 检查是否已存在该交易对
                            existing_spot = self.db.query(ExchangeSpot).filter(
                                ExchangeSpot.coin_id == coin_id,
                                ExchangeSpot.exchange_name == exchange_id,
                                ExchangeSpot.spot_name == f"{base}/{target}"
                            ).first()

                            if not existing_spot:
                                spot = ExchangeSpot(
                                    coin_id=coin_id,
                                    exchange_name=exchange_id,
                                    spot_name=f"{base}/{target}"
                                )
                                self.db.add(spot)

        # 更新合约交易所
        for exchange_id in TOP_SWAP_EXCHANGES:
            tickers = await self.cg_crawler.fetch_derivatives_tickers(exchange_id)
            for ticker in tickers:
                if hasattr(ticker, 'base') and hasattr(ticker, 'target'):
                    base = ticker.base.upper()
                    target = ticker.target.upper()
                    coin_id = ticker.coin_id

                    if target in ['USDT', 'USDC']:
                        # 查找币种
                        coin = self.db.query(Coin).filter(Coin.id == coin_id).first()
                        if coin:
                            # 检查是否已存在该交易对
                            existing_contract = self.db.query(ExchangeContract).filter(
                                ExchangeContract.coin_id == coin_id,
                                ExchangeContract.exchange_name == exchange_id,
                                ExchangeContract.contract_name == f"{base}/{target}"
                            ).first()

                            if not existing_contract:
                                contract = ExchangeContract(
                                    coin_id=coin_id,
                                    exchange_name=exchange_id,
                                    contract_name=f"{base}/{target}"
                                )
                                self.db.add(contract)

        self.db.commit()
        logger.info("Exchange data updated")

    async def update_top_project_token_holders(self):
        """更新顶级项目代币持有者"""
        # 获取顶级项目代币列表,查询代币的具有现货交易所/合约交易所在TOP_SPOT_EXCHANGES或TOP_SWAP_EXCHANGES中的任意一个
        # 查询代币的具有现货交易所/合约交易所在UPDATE_HOLDERS_EXCHANGES中的任意一个

        # 查询在TOP_SPOT_EXCHANGES或TOP_SWAP_EXCHANGES中的代币
        spot_coins = self.db.query(ExchangeSpot.coin_id).filter(
            ExchangeSpot.exchange_name.in_(UPDATE_HOLDERS_EXCHANGES)
        ).distinct().all()

        contract_coins = self.db.query(ExchangeContract.coin_id).filter(
            ExchangeContract.exchange_name.in_(UPDATE_HOLDERS_EXCHANGES)
        ).distinct().all()

        # 合并去重币种ID列表
        coin_ids = set()
        for coin in spot_coins:
            coin_ids.add(coin.coin_id)
        for coin in contract_coins:
            coin_ids.add(coin.coin_id)

        # 为每个符合条件的代币获取持有者数据
        for coin_id in coin_ids:
            try:
                await self.fetch_token_holders(coin_id, use_sync=True)
            except Exception as e:
                logger.error(f"Failed to update holders for coin {coin_id}: {str(e)}")
                continue

        logger.info(f"Updated token holders for {len(coin_ids)} top project tokens")

    async def update_most_popular_wrapped_token_holders(self):
        """更新热门包装代币持有者"""
        pass


    async def fetch_token_holders(self, token_id: str, use_sync: bool = False):
        """获取代币持有者数据"""
        response = await self.arkm_crawler.fetch_token_holders(token_id, use_sync)
        if not response:
            return

        address_top_holders = response.get('addressTopHolders', {})
        for chain, holders in address_top_holders.items():
            if not holders:
                continue

            for holder_data in holders:
                address_info = holder_data.get('address', {})
                if address_info:
                    address = address_info.get('address', '')
                    label_info = address_info.get('arkhamLabel', {})
                    entity_info = address_info.get('arkhamEntity', {})

                    # 查找或创建持有者
                    holder = self.db.query(Holder).filter(Holder.address == address).first()
                    if not holder:
                        holder = Holder(
                            address=address,
                            entity=ARKMEntity(
                                name=entity_info.get('name', ''),
                                type=entity_info.get('type', '')
                            ),
                            label=Label(
                                name=label_info.get('name', ''),
                                chain_type=chain
                            ),
                            chain_type=chain
                        )
                        self.db.add(holder)
                        self.db.flush()  # 获取holder.id

                    # 更新持有信息
                    holding = self.db.query(CoinHolding).filter(
                        CoinHolding.coin_id == token_id,
                        CoinHolding.holder_id == holder.id
                    ).first()

                    if not holding:
                        holding = CoinHolding(
                            coin_id=token_id,
                            holder_id=holder.id,
                            balance=holder_data.get('balance'),
                            usd_value=holder_data.get('usd')
                        )
                        self.db.add(holding)

        self.db.commit()
        logger.info(f"Holders data updated for token {token_id}")

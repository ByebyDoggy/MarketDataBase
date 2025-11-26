import strawberry
from typing import List, Optional
from app.database.manager import DatabaseManager
from app.database.query import CoinRepository
from app.database.processor import DataProcessor
from app.sevice import CoinService
from app.graphql.models import (
    CoinInfoGraphQL, SupplyInfoGraphQL, OnChainInfoGraphQL,
    ExchangeSpotGraphQL, ExchangeContractGraphQL, CoinHoldingGraphQL, HolderGraphQL
)

db_manager = DatabaseManager()

# 创建GraphQL模型的辅助函数
def convert_coin_to_graphql(coin_db):
    """将数据库Coin模型转换为GraphQL模型"""
    # 基本信息转换
    coin_dict = {
        "id": coin_db.id,
        "symbol": coin_db.symbol,
        "name": coin_db.name,
        # 这些字段应该来自SupplyInfo或其他相关表
        "current_price": None,
        "market_cap": None,
        "market_cap_rank": None,
        "total_volume": None,
        "high_24h": None,
        "low_24h": None,
        "price_change_24h": None,
        "price_change_percentage_24h": None,
        "market_cap_change_24h": None,
        "market_cap_change_percentage_24h": None,
        "circulating_supply": None,
        "total_supply": None,
        "max_supply": None,
        "ath": None,
        "ath_change_percentage": None,
        "ath_date": None,
        "atl": None,
        "atl_change_percentage": None,
        "atl_date": None,
        "last_updated": coin_db.updated_at.isoformat() if coin_db.updated_at else None,
    }

    # 添加关联数据
    if coin_db.supply_info:
        supply_info = coin_db.supply_info
        coin_dict["supply_info"] = SupplyInfoGraphQL(
            id=supply_info.id,
            coin_id=supply_info.coin_id,
            total_supply=supply_info.total_supply,
            circulating_supply=supply_info.circulating_supply,
            cached_price=supply_info.cached_price,
            market_cap=supply_info.market_cap,
            updated_at=supply_info.updated_at.isoformat() if supply_info.updated_at else ""
        )
        # 将supply_info中的价格信息同步到coin顶层
        coin_dict["current_price"] = supply_info.cached_price
        coin_dict["market_cap"] = supply_info.market_cap
        coin_dict["circulating_supply"] = supply_info.circulating_supply
        coin_dict["total_supply"] = supply_info.total_supply

    # 处理OnChainInfo列表
    coin_dict["on_chain_infos"] = []
    if coin_db.on_chain_infos:
        for oci in coin_db.on_chain_infos:
            coin_dict["on_chain_infos"].append(OnChainInfoGraphQL(
                id=oci.id,
                coin_id=oci.coin_id,
                chain_name=oci.chain_name,
                contract_address=oci.contract_address,
                updated_at=oci.updated_at.isoformat() if oci.updated_at else ""
            ))

    # 处理ExchangeSpot列表
    coin_dict["exchange_spots"] = []
    if coin_db.exchange_spots:
        for es in coin_db.exchange_spots:
            coin_dict["exchange_spots"].append(ExchangeSpotGraphQL(
                id=es.id,
                coin_id=es.coin_id,
                exchange_name=es.exchange_name,
                spot_name=es.spot_name,
                updated_at=es.updated_at.isoformat() if es.updated_at else ""
            ))

    # 处理ExchangeContract列表
    coin_dict["exchange_contracts"] = []
    if coin_db.exchange_contracts:
        for ec in coin_db.exchange_contracts:
            coin_dict["exchange_contracts"].append(ExchangeContractGraphQL(
                id=ec.id,
                coin_id=ec.coin_id,
                exchange_name=ec.exchange_name,
                contract_name=ec.contract_name,
                updated_at=ec.updated_at.isoformat() if ec.updated_at else ""
            ))

    # 处理Holdings列表
    coin_dict["holdings"] = []
    if coin_db.holdings:
        for holding in coin_db.holdings:
            holder_graphql = None
            if holding.holder:
                holder = holding.holder
                holder_graphql = HolderGraphQL(
                    id=holder.id,
                    address=holder.address,
                    label_name=holder.label_name,
                    label_address=holder.label_address,
                    chain_type=holder.chain_type,
                    updated_at=holder.updated_at.isoformat() if holder.updated_at else ""
                )

            coin_dict["holdings"].append(CoinHoldingGraphQL(
                id=holding.id,
                coin_id=holding.coin_id,
                holder_id=holding.holder_id,
                balance=holding.balance,
                usd_value=holding.usd_value,
                updated_at=holding.updated_at.isoformat() if holding.updated_at else "",
                holder=holder_graphql
            ))

    return CoinInfoGraphQL(**coin_dict)

@strawberry.type
class Query:
    @strawberry.field
    def coin_by_id(self, coin_id: str) -> Optional[CoinInfoGraphQL]:
        """根据coin_id获取币种信息"""
        db = db_manager.get_session()
        try:
            repository = CoinRepository(db)
            processor = DataProcessor(db)
            service = CoinService(repository, processor)
            coin = service.get_coin_by_id(coin_id)
            if not coin:
                return None
            return convert_coin_to_graphql(coin)
        finally:
            db_manager.close_session(db)

    @strawberry.field
    def coins(
        self,
        symbol: Optional[str] = None,
        name: Optional[str] = None,
        contract_address: Optional[str] = None,
        limit: Optional[int] = 50,
        offset: Optional[int] = 0
    ) -> List[CoinInfoGraphQL]:
        """根据多种条件获取币种信息列表"""
        db = db_manager.get_session()
        try:
            repository = CoinRepository(db)
            processor = DataProcessor(db)
            service = CoinService(repository, processor)

            # 使用repository进行复杂查询
            coins = repository.get_coins_with_filters(
                symbol=symbol,
                name=name,
                contract_address=contract_address,
                limit=limit,
                offset=offset
            )

            return [convert_coin_to_graphql(coin) for coin in coins]
        finally:
            db_manager.close_session(db)

    @strawberry.field
    def coins_by_exchange_type(self, exchange_type: str) -> List[CoinInfoGraphQL]:
        """根据交易所类型获取币种信息"""
        db = db_manager.get_session()
        try:
            repository = CoinRepository(db)
            processor = DataProcessor(db)
            service = CoinService(repository, processor)
            coins = service.get_coins_by_exchange(exchange_type)
            return [convert_coin_to_graphql(coin) for coin in coins]
        finally:
            db_manager.close_session(db)

    @strawberry.field
    def coins_by_contract_address(self, contract_address: str) -> List[CoinInfoGraphQL]:
        """根据合约地址获取币种信息"""
        db = db_manager.get_session()
        try:
            repository = CoinRepository(db)
            processor = DataProcessor(db)
            service = CoinService(repository, processor)
            coins = service.get_coins_by_contract_address(contract_address)
            return [convert_coin_to_graphql(coin) for coin in coins]
        finally:
            db_manager.close_session(db)

    @strawberry.field
    def coins_by_holder_address(self, holder_address: str) -> List[CoinInfoGraphQL]:
        """根据持有者地址获取币种信息"""
        db = db_manager.get_session()
        try:
            repository = CoinRepository(db)
            processor = DataProcessor(db)
            service = CoinService(repository, processor)
            coins = service.get_tokens_by_holder(holder_address)
            return [convert_coin_to_graphql(coin) for coin in coins]
        finally:
            db_manager.close_session(db)

    @strawberry.field
    def search_coins(self, search_term: str) -> List[CoinInfoGraphQL]:
        """搜索币种信息"""
        db = db_manager.get_session()
        try:
            repository = CoinRepository(db)
            processor = DataProcessor(db)
            service = CoinService(repository, processor)
            coins = service.search_coins(search_term)
            return [convert_coin_to_graphql(coin) for coin in coins]
        finally:
            db_manager.close_session(db)

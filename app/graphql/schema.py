import strawberry
from typing import List, Optional
from app.database.manager import DatabaseManager
from app.database.query import CoinRepository
from app.database.processor import DataProcessor
from app.sevice import CoinService
from app.graphql.models import (
    CoinGraphQL, SupplyInfoGraphQL, OnChainInfoGraphQL,
    ExchangeSpotGraphQL, ExchangeContractGraphQL, CoinHoldingGraphQL, HolderGraphQL, ARKMEntityGraphQL, LabelGraphQL
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
        "circulating_supply": None,
        "total_supply": None,
        "created_at": coin_db.created_at.isoformat() if coin_db.created_at else None,
        "updated_at": coin_db.updated_at.isoformat() if coin_db.updated_at else None,
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
                holder_entity_graphql = ARKMEntityGraphQL(
                    id=holder.entity.id,
                    name=holder.entity.name,
                    type=holder.entity.type,
                ) if holder.entity else None
                holder_label_graphql = ARKMEntityGraphQL(
                    id=holder.label.id,
                    name=holder.label.name,
                    type=holder.label.chain_type,
                ) if holder.label else None

                holder_graphql = HolderGraphQL(
                    id=holder.id,
                    address=holder.address,
                    chain_type=holder.chain_type,
                    entity=holder_entity_graphql,
                    label=holder_label_graphql,
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

    return CoinGraphQL(**coin_dict)


def convert_exchange_spot_to_graphql(es) -> ExchangeSpotGraphQL:
    """将数据库模型转换为GraphQL类型"""
    return ExchangeSpotGraphQL(
        id=es.id,
        coin_id=es.coin_id,
        exchange_name=es.exchange_name,
        spot_name=es.spot_name,
        updated_at=es.updated_at.isoformat() if es.updated_at else "",
        coin=convert_coin_to_graphql(es.coin) if es.coin else None
    )


def convert_exchange_contract_to_graphql(ec) -> ExchangeContractGraphQL:
    """将数据库模型转换为GraphQL类型"""
    return ExchangeContractGraphQL(
        id=ec.id,
        coin_id=ec.coin_id,
        exchange_name=ec.exchange_name,
        contract_name=ec.contract_name,
        updated_at=ec.updated_at.isoformat() if ec.updated_at else "",
        coin=convert_coin_to_graphql(ec.coin) if ec.coin else None
    )


def convert_coin_holding_to_graphql(holding) -> CoinHoldingGraphQL:
    """将数据库模型转换为GraphQL类型"""
    return CoinHoldingGraphQL(
        id=holding.id,
        coin_id=holding.coin_id,
        holder_id=holding.holder_id,
        balance=holding.balance,
        usd_value=holding.usd_value,
        updated_at=holding.updated_at.isoformat() if holding.updated_at else "",
        holder=convert_holder_to_graphql(holding.holder) if holding.holder else None
    )

def convert_coin_holding_to_graphql_without_holders(holding) -> CoinHoldingGraphQL:
    """将数据库模型转换为GraphQL类型"""
    return CoinHoldingGraphQL(
        id=holding.id,
        coin_id=holding.coin_id,
        holder_id=holding.holder_id,
        balance=holding.balance,
        usd_value=holding.usd_value,
        updated_at=holding.updated_at.isoformat() if holding.updated_at else "",
        holder=None
    )

def convert_holder_to_graphql(holder) -> HolderGraphQL:
    """将数据库模型转换为GraphQL类型"""
    return HolderGraphQL(
        id=holder.id,
        address=holder.address,
        chain_type=holder.chain_type,
        updated_at=holder.updated_at.isoformat() if holder.updated_at else "",
        entity=convert_arkm_entity_to_graphql(holder.entity) if holder.entity else None,
        label=convert_label_to_graphql(holder.label) if holder.label else None,
        coins=[convert_coin_holding_to_graphql_without_holders(holding) for holding in holder.coin_holdings]
    )


def convert_arkm_entity_to_graphql(entity) -> ARKMEntityGraphQL:
    """将数据库模型转换为GraphQL类型"""
    return ARKMEntityGraphQL(
        id=entity.id,
        name=entity.name,
        type=entity.type,
    )


def convert_label_to_graphql(label) -> LabelGraphQL:
    """将数据库模型转换为GraphQL类型"""
    return LabelGraphQL(
        id=label.id,
        name=label.name,
        chain_type=label.chain_type,
    )


@strawberry.type
class Query:
    @strawberry.field
    def coins(
            self,
            coin_id: Optional[str] = None,
            symbol: Optional[str] = None,
            name: Optional[str] = None,
            contract_address: Optional[str] = None,
            limit: Optional[int] = 50,
            offset: Optional[int] = 0
    ) -> List[CoinGraphQL]:
        """根据多种条件获取币种信息列表"""
        db = db_manager.get_session()
        try:
            repository = CoinRepository(db)
            processor = DataProcessor(db)
            service = CoinService(repository, processor)

            # 使用repository进行复杂查询
            coins = repository.get_coins_with_filters(
                coin_id=coin_id,
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
    def spot_exchanges(
            self,
            exchange_id: str,
            coin_id: Optional[str] = None,
            limit: Optional[int] = 50,
            offset: Optional[int] = 0
    ) -> List[ExchangeSpotGraphQL]:
        """根据币种ID获取现货交易所信息列表"""
        db = db_manager.get_session()
        try:
            repository = CoinRepository(db)
            processor = DataProcessor(db)
            service = CoinService(repository, processor)

            # 使用repository进行复杂查询
            exchange_spots = repository.get_exchange_spots_with_filters(
                coin_id=coin_id,
                exchange_id=exchange_id,
                limit=limit,
                offset=offset
            )

            return [convert_exchange_spot_to_graphql(es) for es in exchange_spots]
        finally:
            db_manager.close_session(db)

    @strawberry.field
    def contract_exchanges(
            self,
            exchange_id: str,
            coin_id: Optional[str] = None,
            limit: Optional[int] = 50,
            offset: Optional[int] = 0
    ) -> List[ExchangeContractGraphQL]:
        """根据币种ID获取合约交易所信息列表"""
        db = db_manager.get_session()
        try:
            repository = CoinRepository(db)
            processor = DataProcessor(db)
            service = CoinService(repository, processor)

            # 使用repository进行复杂查询
            exchange_contracts = repository.get_exchange_contracts_with_filters(
                coin_id=coin_id,
                exchange_id=exchange_id,
                limit=limit,
                offset=offset
            )

            return [convert_exchange_contract_to_graphql(ec) for ec in exchange_contracts]
        finally:
            db_manager.close_session(db)

    @strawberry.field
    def holders(
            self,
            chain_type: Optional[str] = None,
            coin_id: Optional[str] = None,
            limit: Optional[int] = 50,
            offset: Optional[int] = 0
    ) -> List[CoinHoldingGraphQL]:
        """根据币种ID获取持仓信息列表"""
        db = db_manager.get_session()
        try:
            repository = CoinRepository(db)
            processor = DataProcessor(db)
            service = CoinService(repository, processor)

            # 使用repository进行复杂查询
            holdings = repository.get_coin_holding_with_filters(
                chain_type=chain_type,
                coin_id=coin_id,
                limit=limit,
                offset=offset
            )

            return [convert_coin_holding_to_graphql(holding) for holding in holdings]
        finally:
            db_manager.close_session(db)

    @strawberry.field
    def holder_detail(self,
                      holder_address: str,
                      chain_type: Optional[str] = None,
                      ) -> Optional[HolderGraphQL]:
        """根据地址获取持仓信息"""
        db = db_manager.get_session()
        try:
            repository = CoinRepository(db)
            processor = DataProcessor(db)
            service = CoinService(repository, processor)

            # 使用repository进行复杂查询
            holder = repository.get_holder_with_filters(
                holder_address=holder_address,
                chain_type=chain_type,
            )
            return convert_holder_to_graphql(holder) if holder else None
        finally:
            db_manager.close_session(db)

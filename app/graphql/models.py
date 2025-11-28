import strawberry
from typing import Optional, List
import datetime

# ---------------------------
# SupplyInfo
# ---------------------------
@strawberry.type
class SupplyInfoGraphQL:
    id: int
    coin_id: str
    total_supply: Optional[float]
    circulating_supply: Optional[float]
    cached_price: Optional[float]
    market_cap: Optional[float]
    updated_at: datetime.datetime

# ---------------------------
# OnChainInfo
# ---------------------------
@strawberry.type
class OnChainInfoGraphQL:
    id: int
    coin_id: str
    chain_name: str
    contract_address: str
    updated_at: datetime.datetime

# ---------------------------
# ExchangeSpot
# ---------------------------
@strawberry.type
class ExchangeSpotGraphQL:
    id: int
    coin_id: str
    exchange_name: str
    spot_name: str
    updated_at: datetime.datetime
    # 关联数据
    coin: Optional['CoinGraphQL'] = None

# ---------------------------
# ExchangeContract
# ---------------------------
@strawberry.type
class ExchangeContractGraphQL:
    id: int
    coin_id: str
    exchange_name: str
    contract_name: str
    updated_at: datetime.datetime
    # 关联数据
    coin: Optional['CoinGraphQL'] = None

# ---------------------------
# Label
# ---------------------------
@strawberry.type
class LabelGraphQL:
    id: int
    name: str
    chain_type: Optional[str]

# ---------------------------
# ARKMEntity
# ---------------------------
@strawberry.type
class ARKMEntityGraphQL:
    id: int
    name: str
    type: Optional[str]

# ---------------------------
# Holder
# ---------------------------
@strawberry.type
class HolderGraphQL:
    id: int
    address: str
    chain_type: Optional[str]
    updated_at: datetime.datetime

    # 关联数据
    entity: Optional[ARKMEntityGraphQL] = None
    label: Optional[LabelGraphQL] = None
    coins: List['CoinHoldingGraphQL'] = strawberry.field(default_factory=list)

# ---------------------------
# CoinHolding
# ---------------------------
@strawberry.type
class CoinHoldingGraphQL:
    id: int
    coin_id: str
    holder_id: int
    balance: Optional[float]
    usd_value: Optional[float]
    updated_at: datetime.datetime

    # 关联数据
    holder: Optional[HolderGraphQL] = None

# ---------------------------
# Coin
# ---------------------------
@strawberry.type
class CoinGraphQL:
    id: str
    symbol: str
    name: str
    current_price: Optional[float] = None
    market_cap: Optional[float] = None
    circulating_supply: Optional[float] = None
    total_supply: Optional[float] = None
    created_at: datetime.datetime = datetime.datetime.now()
    updated_at: datetime.datetime = datetime.datetime.now()

    # 关联数据
    supply_info: Optional[SupplyInfoGraphQL] = None
    on_chain_infos: List[OnChainInfoGraphQL] = strawberry.field(default_factory=list)
    exchange_spots: List[ExchangeSpotGraphQL] = strawberry.field(default_factory=list)
    exchange_contracts: List[ExchangeContractGraphQL] = strawberry.field(default_factory=list)
    holdings: List[CoinHoldingGraphQL] = strawberry.field(default_factory=list)

@strawberry.type
class CoinPriceGraphQL:
    coin_id: str
    price: Optional[float]
    updated_at: datetime.datetime

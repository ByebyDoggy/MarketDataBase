import strawberry
from typing import Optional, List

@strawberry.type
class SupplyInfoGraphQL:
    id: int
    coin_id: str
    total_supply: Optional[float]
    circulating_supply: Optional[float]
    cached_price: Optional[float]
    market_cap: Optional[float]
    updated_at: str

@strawberry.type
class OnChainInfoGraphQL:
    id: int
    coin_id: str
    chain_name: str
    contract_address: str
    updated_at: str

@strawberry.type
class ExchangeSpotGraphQL:
    id: int
    coin_id: str
    exchange_name: str
    spot_name: str
    updated_at: str

@strawberry.type
class ExchangeContractGraphQL:
    id: int
    coin_id: str
    exchange_name: str
    contract_name: str
    updated_at: str

@strawberry.type
class HolderGraphQL:
    id: int
    address: str
    label_name: Optional[str]
    label_address: Optional[str]
    chain_type: Optional[str]
    updated_at: str

@strawberry.type
class CoinHoldingGraphQL:
    id: int
    coin_id: str
    holder_id: int
    balance: Optional[float]
    usd_value: Optional[float]
    updated_at: str
    holder: Optional[HolderGraphQL]

@strawberry.type
class CoinInfoGraphQL:
    id: str
    symbol: str
    name: str
    current_price: Optional[float]
    market_cap: Optional[float]
    market_cap_rank: Optional[int]
    total_volume: Optional[float]
    high_24h: Optional[float]
    low_24h: Optional[float]
    price_change_24h: Optional[float]
    price_change_percentage_24h: Optional[float]
    market_cap_change_24h: Optional[float]
    market_cap_change_percentage_24h: Optional[float]
    circulating_supply: Optional[float]
    total_supply: Optional[float]
    max_supply: Optional[float]
    ath: Optional[float]
    ath_change_percentage: Optional[float]
    ath_date: Optional[str]
    atl: Optional[float]
    atl_change_percentage: Optional[float]
    atl_date: Optional[str]
    last_updated: Optional[str]

    # 关联数据
    supply_info: Optional[SupplyInfoGraphQL] = None
    on_chain_infos: List[OnChainInfoGraphQL] = strawberry.field(default_factory=list)
    exchange_spots: List[ExchangeSpotGraphQL] = strawberry.field(default_factory=list)
    exchange_contracts: List[ExchangeContractGraphQL] = strawberry.field(default_factory=list)
    holdings: List[CoinHoldingGraphQL] = strawberry.field(default_factory=list)

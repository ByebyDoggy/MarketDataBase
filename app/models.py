# models.py
from typing import List, Optional, Dict, Any, Set
from pydantic import BaseModel


class ExchangeSpot(BaseModel):
    exchange_name: str
    spot_name: str

    def __hash__(self):
        return hash((self.exchange_name, self.spot_name))


class ExchangeContract(BaseModel):
    exchange_name: str
    contract_name: str

    def __hash__(self):
        return hash((self.exchange_name, self.contract_name))


class OnChainInfo(BaseModel):
    chain_name: str
    contract_address: str
    def __hash__(self):
        return hash((self.chain_name, self.contract_address))


class SupplyInfo(BaseModel):
    total_supply: Optional[float] = None
    circulating_supply: Optional[float] = None
    cached_price: Optional[float] = None
    market_cap: Optional[float] = None


class CoinInfo(BaseModel):
    coin_id: str
    symbol: str
    name: str
    exchange_spots: Set[ExchangeSpot]
    exchange_contracts: Set[ExchangeContract]
    on_chain_info: Set[OnChainInfo]
    supply_info: Optional[SupplyInfo]
    holders: Set['AddressHolder'] = set()


class SearchRequest(BaseModel):
    search_term: str


class ArkmLabel(BaseModel):
    name: str
    address: str
    chain_type: str


class AddressHolder(BaseModel):
    address: str
    label: ArkmLabel
    balance: Optional[float] = None
    usd_value: Optional[float] = None

    def __hash__(self):
        return hash((self.address, self.label.name))

from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
import datetime

# 币种信息表
class Coin(SQLModel, table=True):
    __tablename__ = 'coins'

    id: str = Field(primary_key=True)
    symbol: str = Field(nullable=False)
    name: str = Field(nullable=False)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    # 关系定义
    supply_info: Optional["SupplyInfo"] = Relationship(back_populates="coin", sa_relationship_kwargs={"uselist": False})
    on_chain_infos: List["OnChainInfo"] = Relationship(back_populates="coin")
    exchange_spots: List["ExchangeSpot"] = Relationship(back_populates="coin")
    exchange_contracts: List["ExchangeContract"] = Relationship(back_populates="coin")
    holdings: List["CoinHolding"] = Relationship(back_populates="coin")

# 供应信息表
class SupplyInfo(SQLModel, table=True):
    __tablename__ = 'supply_info'

    id: Optional[int] = Field(default=None, primary_key=True)
    coin_id: str = Field(foreign_key="coins.id", nullable=False)
    total_supply: Optional[float] = Field(default=None)
    circulating_supply: Optional[float] = Field(default=None)
    cached_price: Optional[float] = Field(default=None)
    market_cap: Optional[float] = Field(default=None)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    coin: Coin = Relationship(back_populates="supply_info")

# 链上信息表
class OnChainInfo(SQLModel, table=True):
    __tablename__ = 'on_chain_info'

    id: Optional[int] = Field(default=None, primary_key=True)
    coin_id: str = Field(foreign_key="coins.id", nullable=False)
    chain_name: str = Field(nullable=False)
    contract_address: str = Field(nullable=False)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    coin: Coin = Relationship(back_populates="on_chain_infos")

# 现货交易所信息表
class ExchangeSpot(SQLModel, table=True):
    __tablename__ = 'exchange_spots'

    id: Optional[int] = Field(default=None, primary_key=True)
    coin_id: str = Field(foreign_key="coins.id", nullable=False)
    exchange_name: str = Field(nullable=False)
    spot_name: str = Field(nullable=False)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    coin: Coin = Relationship(back_populates="exchange_spots")

# 合约交易所信息表
class ExchangeContract(SQLModel, table=True):
    __tablename__ = 'exchange_contracts'

    id: Optional[int] = Field(default=None, primary_key=True)
    coin_id: str = Field(foreign_key="coins.id", nullable=False)
    exchange_name: str = Field(nullable=False)
    contract_name: str = Field(nullable=False)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    coin: Coin = Relationship(back_populates="exchange_contracts")

# 持有者信息表
class Holder(SQLModel, table=True):
    __tablename__ = 'holders'

    id: Optional[int] = Field(default=None, primary_key=True)
    address: str = Field(unique=True, nullable=False)
    label_name: Optional[str] = Field(default=None)
    label_address: Optional[str] = Field(default=None)
    chain_type: Optional[str] = Field(default=None)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    # 多对多关系
    coin_holdings: List["CoinHolding"] = Relationship(back_populates="holder")

# 币种持有信息表（多对多关系）
class CoinHolding(SQLModel, table=True):
    __tablename__ = 'coin_holdings'

    id: Optional[int] = Field(default=None, primary_key=True)
    coin_id: str = Field(foreign_key="coins.id", nullable=False)
    holder_id: int = Field(foreign_key="holders.id", nullable=False)
    balance: Optional[float] = Field(default=None)
    usd_value: Optional[float] = Field(default=None)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    coin: Coin = Relationship(back_populates="holdings")
    holder: Holder = Relationship(back_populates="coin_holdings")

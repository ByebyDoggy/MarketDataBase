from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from sqlalchemy import Column, String, UniqueConstraint, Index
import datetime


# ---------------------------
# 币种表
# ---------------------------
class Coin(SQLModel, table=True):
    __tablename__ = "coins"
    __table_args__ = (
        Index("idx_symbol", "symbol"),
        Index("idx_name", "name"),
        # 可选：fulltext 搜索
        # Index("ft_symbol_name", "symbol", "name", mysql_prefix="FULLTEXT"),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
    )

    id: str = Field(primary_key=True)
    symbol: str = Field(nullable=False)
    name: str = Field(nullable=False)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    supply_info: Optional["SupplyInfo"] = Relationship(back_populates="coin", sa_relationship_kwargs={"uselist": False})
    on_chain_infos: List["OnChainInfo"] = Relationship(back_populates="coin")
    exchange_spots: List["ExchangeSpot"] = Relationship(back_populates="coin")
    exchange_contracts: List["ExchangeContract"] = Relationship(back_populates="coin")
    holdings: List["CoinHolding"] = Relationship(back_populates="coin")


# ---------------------------
# 供应信息表
# ---------------------------
class SupplyInfo(SQLModel, table=True):
    __tablename__ = "supply_info"
    __table_args__ = (
        UniqueConstraint("coin_id"),  # 每个币只能一条
        Index("idx_supply_coin", "coin_id"),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    coin_id: str = Field(foreign_key="coins.id", nullable=False)
    total_supply: Optional[float] = None
    circulating_supply: Optional[float] = None
    cached_price: Optional[float] = None
    market_cap: Optional[float] = None
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    coin: Coin = Relationship(back_populates="supply_info")


# ---------------------------
# 链上信息表
# ---------------------------
class OnChainInfo(SQLModel, table=True):
    __tablename__ = "on_chain_info"
    __table_args__ = (
        Index("idx_chain_coin", "coin_id", "chain_name"),
        UniqueConstraint("chain_name", "contract_address"),  # 避免重复合约记录
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    coin_id: str = Field(foreign_key="coins.id", nullable=False)
    chain_name: str = Field(nullable=False)
    contract_address: str = Field(nullable=False)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    coin: Coin = Relationship(back_populates="on_chain_infos")


# ---------------------------
# 现货交易所表
# ---------------------------
class ExchangeSpot(SQLModel, table=True):
    __tablename__ = "exchange_spots"
    __table_args__ = (
        Index("idx_spot_coin_exchange", "coin_id", "exchange_name"),
        UniqueConstraint("exchange_name", "spot_name"),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    coin_id: str = Field(foreign_key="coins.id", nullable=False)
    exchange_name: str = Field(nullable=False)
    spot_name: str = Field(nullable=False)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    coin: Coin = Relationship(back_populates="exchange_spots")


# ---------------------------
# 合约交易所表
# ---------------------------
class ExchangeContract(SQLModel, table=True):
    __tablename__ = "exchange_contracts"
    __table_args__ = (
        Index("idx_contract_coin_exchange", "coin_id", "exchange_name"),
        UniqueConstraint("exchange_name", "contract_name"),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    coin_id: str = Field(foreign_key="coins.id", nullable=False)
    exchange_name: str = Field(nullable=False)
    contract_name: str = Field(nullable=False)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    coin: Coin = Relationship(back_populates="exchange_contracts")


# ---------------------------
# 持有者表
# ---------------------------
class Holder(SQLModel, table=True):
    __tablename__ = "holders"
    __table_args__ = (
        Index("idx_holder_label_chain", "label_name", "chain_type"),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    # address 优化（默认 TEXT → varchar(64）更适合链上地址，性能更好）
    address: str = Field(
        sa_column=Column(String(64), unique=True, index=True, nullable=False)
    )

    label_name: Optional[str] = Field(default=None, index=True)
    label_address: Optional[str] = None
    chain_type: Optional[str] = Field(default=None)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    coin_holdings: List["CoinHolding"] = Relationship(back_populates="holder")


# ---------------------------
# 多对多：币种持有表
# ---------------------------
class CoinHolding(SQLModel, table=True):
    __tablename__ = "coin_holdings"
    __table_args__ = (
        UniqueConstraint("coin_id", "holder_id"),  # 一个人对一个币只有一条记录
        Index("idx_coin_holding", "coin_id", "holder_id"),  # 查询超级快
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    coin_id: str = Field(foreign_key="coins.id", nullable=False)
    holder_id: int = Field(foreign_key="holders.id", nullable=False)
    balance: Optional[float] = None
    usd_value: Optional[float] = None
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    coin: Coin = Relationship(back_populates="holdings")
    holder: Holder = Relationship(back_populates="coin_holdings")

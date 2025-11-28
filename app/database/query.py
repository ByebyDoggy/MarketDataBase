from app.database.models import (
    Coin, SupplyInfo, OnChainInfo,
    ExchangeSpot, ExchangeContract,
    Holder, CoinHolding
)
from typing import List, Optional
from sqlmodel import select, Session
from sqlalchemy.orm import selectinload


class CoinRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    # ------------------------------------------
    # 通用的完全优化查询基底（所有查询用它）
    # ------------------------------------------
    def _base_query(self):
        return (
            select(Coin)
            .options(
                selectinload(Coin.supply_info),
                selectinload(Coin.on_chain_infos),
                selectinload(Coin.exchange_spots),
                selectinload(Coin.exchange_contracts),
                selectinload(Coin.holdings).selectinload(CoinHolding.holder).selectinload(Holder.label)
            )
        )

    # ------------------------------------------
    def get_coins_with_filters(
        self,
        coin_id: Optional[str] = None,
        symbol: Optional[str] = None,
        name: Optional[str] = None,
        contract_address: Optional[str] = None,
        limit: int = 50, offset: int = 0
    ):
        query = self._base_query()

        if coin_id:
            query = query.where(Coin.id == coin_id)

        if symbol:
            query = query.where(Coin.symbol.ilike(f"%{symbol}%"))

        if name:
            query = query.where(Coin.name.ilike(f"%{name}%"))

        if contract_address:
            query = (
                query.join(OnChainInfo)
                .where(OnChainInfo.contract_address == contract_address)
            )

        query = query.offset(offset).limit(limit)

        return self.db.exec(query).all()

    def get_exchange_spots_with_filters(
        self,
        coin_id: Optional[str] = None,
        exchange_id: Optional[str] = None,
        limit: int = 50, offset: int = 0
    ):
        query = (
            select(ExchangeSpot)
            .options(
                selectinload(ExchangeSpot.coin)
            )
        )

        if coin_id:
            query = query.where(ExchangeSpot.coin_id == coin_id)

        if exchange_id:
            query = query.where(ExchangeSpot.exchange_name == exchange_id)

        query = query.offset(offset).limit(limit)

        return self.db.exec(query).all()

    def get_exchange_contracts_with_filters(
        self,
        coin_id: Optional[str] = None,
        exchange_id: Optional[str] = None,
        limit: int = 50, offset: int = 0
    ):
        query = (
            select(ExchangeContract)
            .options(
                selectinload(ExchangeContract.coin)
            )
        )

        if coin_id:
            query = query.where(ExchangeContract.coin_id == coin_id)

        if exchange_id:
            query = query.where(ExchangeContract.exchange_name == exchange_id)

        query = query.offset(offset).limit(limit)

        return self.db.exec(query).all()

    def get_coin_holding_with_filters(
        self,
        chain_type: Optional[str] = None,
        coin_id: Optional[str] = None,
        limit: int = 50, offset: int = 0
    ):

        query = (
            select(CoinHolding)
            .join(CoinHolding.holder)  # join Holder 表
            .options(
                selectinload(CoinHolding.coin),  # 预加载 coin
                selectinload(CoinHolding.holder)  # 预加载 holder
            )
        )

        if chain_type:
            query = query.where(Holder.chain_type == chain_type)

        if coin_id:
            query = query.where(CoinHolding.coin_id == coin_id)

        query = query.offset(offset).limit(limit)

        return self.db.exec(query).all()

    def get_holder_with_filters(
        self,
        holder_address: str,
        chain_type: Optional[str] = None,
    ):
        query = (
            select(Holder)
            .options(
                selectinload(Holder.coin_holdings).selectinload(CoinHolding.coin)
            )
        )

        if chain_type:
            query = query.where(Holder.chain_type == chain_type)

        query = query.where(Holder.address == holder_address)

        return self.db.exec(query).first()


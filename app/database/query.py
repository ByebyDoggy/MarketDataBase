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
                selectinload(Coin.holdings).selectinload(CoinHolding.holder)
            )
        )

    # ------------------------------------------
    def get_coin_by_id(self, coin_id: str) -> Optional[Coin]:
        query = self._base_query().where(Coin.id == coin_id)
        return self.db.exec(query).first()

    # ------------------------------------------
    def get_coins_by_contract_address(self, contract_address: str) -> List[Coin]:
        query = (
            self._base_query()
            .join(OnChainInfo, OnChainInfo.coin_id == Coin.id)
            .where(OnChainInfo.contract_address.ilike(f"%{contract_address}%"))
        )
        return self.db.exec(query).all()

    # ------------------------------------------
    def get_coins_by_exchange(self, exchange_name: str) -> List[Coin]:

        # 现货
        q1 = (
            self._base_query()
            .join(ExchangeSpot, ExchangeSpot.coin_id == Coin.id)
            .where(ExchangeSpot.exchange_name == exchange_name)
        )
        spot = self.db.exec(q1).all()

        # 合约
        q2 = (
            self._base_query()
            .join(ExchangeContract, ExchangeContract.coin_id == Coin.id)
            .where(ExchangeContract.exchange_name == exchange_name)
        )
        contract = self.db.exec(q2).all()

        # 去重
        coin_map = {c.id: c for c in (spot + contract)}
        return list(coin_map.values())

    # ------------------------------------------
    def search_coins(self, search_term: str) -> List[Coin]:
        query = (
            self._base_query()
            .where(
                Coin.symbol.ilike(f"%{search_term}%")
                | Coin.name.ilike(f"%{search_term}%")
            )
        )
        return self.db.exec(query).all()

    # ------------------------------------------
    def get_all_coins(self, limit: int = 100) -> List[Coin]:
        query = self._base_query().limit(limit)
        return self.db.exec(query).all()

    # ------------------------------------------
    def get_tokens_by_holder(self, holder_address: str) -> List[Coin]:
        query = (
            self._base_query()
            .join(CoinHolding, CoinHolding.coin_id == Coin.id)
            .join(Holder, Holder.id == CoinHolding.holder_id)
            .where(Holder.address == holder_address)
        )
        return self.db.exec(query).all()

    # ------------------------------------------
    def get_coins_with_filters(
        self, symbol=None, name=None, contract_address=None,
        limit=50, offset=0
    ):
        query = self._base_query()

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

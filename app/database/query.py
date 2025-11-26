from app.database.models import Coin, SupplyInfo, OnChainInfo, ExchangeSpot, ExchangeContract, Holder, CoinHolding
from typing import List, Optional
from sqlmodel import select, Session
from sqlalchemy.orm import selectinload
class CoinRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def get_coin_by_id(self, coin_id: str) -> Optional[Coin]:
        """根据ID获取币种"""
        return self.db.query(Coin).filter(Coin.id == coin_id).first()

    def get_coins_by_contract_address(self, contract_address: str) -> List[Coin]:
        """根据合约地址获取币种"""
        return self.db.query(Coin)\
            .join(OnChainInfo)\
            .filter(OnChainInfo.contract_address.ilike(contract_address))\
            .all()

    def get_coins_by_exchange(self, exchange_name: str) -> List[Coin]:
        """根据交易所获取币种"""
        # 查询现货交易所
        spot_coins = self.db.query(Coin)\
            .join(ExchangeSpot)\
            .filter(ExchangeSpot.exchange_name == exchange_name)\
            .all()

        # 查询合约交易所
        contract_coins = self.db.query(Coin)\
            .join(ExchangeContract)\
            .filter(ExchangeContract.exchange_name == exchange_name)\
            .all()

        # 合并结果并去重
        coin_dict = {coin.id: coin for coin in spot_coins + contract_coins}
        return list(coin_dict.values())

    def search_coins(self, search_term: str) -> List[Coin]:
        """搜索币种"""
        return self.db.query(Coin)\
            .filter(
                Coin.symbol.ilike(f"%{search_term}%") |
                Coin.name.ilike(f"%{search_term}%")
            )\
            .all()

    def get_all_coins(self, limit: int = 100) -> List[Coin]:
        """获取所有币种"""
        return self.db.query(Coin).limit(limit).all()

    def get_tokens_by_holder(self, holder_address: str) -> List[Coin]:
        """根据持有者地址获取代币"""
        return self.db.query(Coin)\
            .join(CoinHolding)\
            .join(Holder)\
            .filter(Holder.address == holder_address)\
            .all()

    # 在CoinRepository类中添加以下方法
    def get_coins_with_filters(self, symbol=None, name=None, contract_address=None, limit=50, offset=0):
        """
        根据多种条件获取币种信息列表
        """
        query = select(Coin).options(
            selectinload(Coin.supply_info),
            selectinload(Coin.on_chain_infos),
            selectinload(Coin.exchange_spots),
            selectinload(Coin.exchange_contracts),
            selectinload(Coin.holdings).selectinload(CoinHolding.holder)
        )

        if symbol:
            query = query.where(Coin.symbol.ilike(f"%{symbol}%"))
        if name:
            query = query.where(Coin.name.ilike(f"%{name}%"))
        if contract_address:
            query = query.join(OnChainInfo).where(OnChainInfo.contract_address == contract_address)

        query = query.offset(offset).limit(limit)
        result = self.db.exec(query)
        return result.all()


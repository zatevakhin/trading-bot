from abc import ABC, abstractmethod

from exchange_api.customtypes import TimeInForceStatus


class ExchangeApiAdapterBase(ABC):
    def __init__(self, exchange_api) -> None:
        self.exchange_api = exchange_api

    @abstractmethod
    def returnTicker(self, pair: 'CurrencyPair') -> str:
        raise NotImplementedError

    @abstractmethod
    def returnChartData(self, pair: 'CurrencyPair', interval: 'CandleTimeInterval', start: int, end: int) -> dict:
        raise NotImplementedError

    @abstractmethod
    def buy(self, pair: 'CurrencyPair', price: int, amount: int, timeInForce: TimeInForceStatus) -> dict:
        raise NotImplementedError

    @abstractmethod
    def sell(self, pair: 'CurrencyPair', price: int, amount: int, timeInForce: TimeInForceStatus) -> dict:
        raise NotImplementedError

    @abstractmethod
    def cancel(self, pair: 'CurrencyPair', orderId: int) -> dict:
        raise NotImplementedError

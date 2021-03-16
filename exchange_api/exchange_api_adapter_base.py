from abc import ABC, abstractmethod

import requests

from exchange_api.customtypes import TimeInForceStatus


class ExchangeApiAdapterBase(ABC):
    def __init__(self, exchange_api) -> None:
        self.exchange_api = exchange_api

    @abstractmethod
    def returnTicker(self, pair: 'CurrencyPair') -> str:
        raise NotImplementedError

    @abstractmethod
    def returnChartData(self, pair: 'CurrencyPair', interval: int, start: int, end: int) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def buy(self, pair: 'CurrencyPair', price: int, amount: int, timeInForce: TimeInForceStatus) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def sell(self, pair: 'CurrencyPair', price: int, amount: int) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def cancel(self, pair: 'CurrencyPair', orderId: int) -> list[str]:
        raise NotImplementedError

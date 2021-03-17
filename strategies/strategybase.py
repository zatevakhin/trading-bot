from abc import ABC, abstractmethod


class StrategyBase(ABC):
    __strategy__ = None

    @abstractmethod
    def preload(self, candles: list['Candle']):
        raise NotImplementedError

    @abstractmethod
    def on_tick(self, candle: 'Candle'):
        raise NotImplementedError

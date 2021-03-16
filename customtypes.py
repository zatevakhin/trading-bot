from enum import Enum, auto

from candle import Candle


class CurrencyPair:
    def __init__(self, buy, sell):
        self.buy = buy
        self.sell = sell

    def __repr__(self):
        return f"{self.buy}<->{self.sell}"


class TradeStatus(Enum):
    CREATED = auto()
    OPEN = auto()
    CLOSED = auto()


class Exchange(Enum):
    BINANCE = auto()
    POLONIEX = auto()


class TradingMode(Enum):
    BACKTEST = auto()
    LIVE_TEST = auto()
    LIVE = auto()


class CandleTimeInterval(Enum):
    I_1M = auto()
    I_3M = auto()
    I_5M = auto()
    I_15M = auto()
    I_30M = auto()
    I_1H = auto()
    I_2H = auto()
    I_4H = auto()
    I_6H = auto()
    I_8H = auto()
    I_12H = auto()
    I_1D = auto()


CANDLE_TIME_INTERVALS_POLONIEX = (
    CandleTimeInterval.I_5M,
    CandleTimeInterval.I_15M,
    CandleTimeInterval.I_30M,
    CandleTimeInterval.I_2H,
    CandleTimeInterval.I_4H,
    CandleTimeInterval.I_1D,
)

CANDLE_TIME_INTERVALS_BINANCE = (
    CandleTimeInterval.I_1M,
    CandleTimeInterval.I_3M,
    CandleTimeInterval.I_5M,
    CandleTimeInterval.I_15M,
    CandleTimeInterval.I_30M,
    CandleTimeInterval.I_1H,
    CandleTimeInterval.I_2H,
    CandleTimeInterval.I_4H,
    CandleTimeInterval.I_6H,
    CandleTimeInterval.I_8H,
    CandleTimeInterval.I_12H,
    CandleTimeInterval.I_1D,
)


class IStrategy(object):
    __strategy__ = None

    def preload(self, candles: list[Candle]):
        raise NotImplementedError

    def on_tick(self, candle: Candle):
        raise NotImplementedError

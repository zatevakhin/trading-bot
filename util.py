
from customtypes import CandleTimeInterval, Exchange
from customtypes import CANDLE_TIME_INTERVALS_BINANCE
from customtypes import CANDLE_TIME_INTERVALS_POLONIEX

MAP_CUSTOM_TYPE_TO_POLONIEX = {
    CandleTimeInterval.I_5M:  "300",
    CandleTimeInterval.I_15M: "900",
    CandleTimeInterval.I_30M: "1800",
    CandleTimeInterval.I_2H:  "7200",
    CandleTimeInterval.I_4H:  "14400",
    CandleTimeInterval.I_1D:  "86400"
}

MAP_CUSTOM_TYPE_TO_BINANCE = {
    CandleTimeInterval.I_1M:  "1m",
    CandleTimeInterval.I_3M:  "3m",
    CandleTimeInterval.I_5M:  "5m",
    CandleTimeInterval.I_15M: "15m",
    CandleTimeInterval.I_30M: "30m",
    CandleTimeInterval.I_1H:  "1h",
    CandleTimeInterval.I_2H:  "2h",
    CandleTimeInterval.I_4H:  "4h",
    CandleTimeInterval.I_6H:  "6h",
    CandleTimeInterval.I_8H:  "8h",
    CandleTimeInterval.I_12H: "12h",
    CandleTimeInterval.I_1D:  "1d",
}

EXCHANGES_INTERVALS_MAP = {
    Exchange.POLONIEX: MAP_CUSTOM_TYPE_TO_POLONIEX,
    Exchange.BINANCE: MAP_CUSTOM_TYPE_TO_BINANCE
}

def map_interval_for_exchange(exchange: Exchange, interval: CandleTimeInterval) -> str:
    return EXCHANGES_INTERVALS_MAP[exchange][interval]

def map_arg_to_custom(interval: str) -> CandleTimeInterval:
    return {
        "1m":  CandleTimeInterval.I_1M,
        "3m":  CandleTimeInterval.I_3M,
        "5m":  CandleTimeInterval.I_5M,
        "15m": CandleTimeInterval.I_15M,
        "30m": CandleTimeInterval.I_30M,
        "1h":  CandleTimeInterval.I_1H,
        "2h":  CandleTimeInterval.I_2H,
        "4h":  CandleTimeInterval.I_4H,
        "6h":  CandleTimeInterval.I_6H,
        "8h":  CandleTimeInterval.I_8H,
        "12h": CandleTimeInterval.I_12H,
        "1d":  CandleTimeInterval.I_1D,
    }.get(interval, None)

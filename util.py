import time

import userconfig
from customtypes import CandleTimeInterval, Exchange, TradingMode

MAP_CUSTOM_TYPE_TO_POLONIEX = {
    CandleTimeInterval.I_5M: "300",
    CandleTimeInterval.I_15M: "900",
    CandleTimeInterval.I_30M: "1800",
    CandleTimeInterval.I_2H: "7200",
    CandleTimeInterval.I_4H: "14400",
    CandleTimeInterval.I_1D: "86400"
}

MAP_CUSTOM_TYPE_TO_BINANCE = {
    CandleTimeInterval.I_1M: "1m",
    CandleTimeInterval.I_3M: "3m",
    CandleTimeInterval.I_5M: "5m",
    CandleTimeInterval.I_15M: "15m",
    CandleTimeInterval.I_30M: "30m",
    CandleTimeInterval.I_1H: "1h",
    CandleTimeInterval.I_2H: "2h",
    CandleTimeInterval.I_4H: "4h",
    CandleTimeInterval.I_6H: "6h",
    CandleTimeInterval.I_8H: "8h",
    CandleTimeInterval.I_12H: "12h",
    CandleTimeInterval.I_1D: "1d",
}

EXCHANGES_INTERVALS_MAP = {Exchange.POLONIEX: MAP_CUSTOM_TYPE_TO_POLONIEX, Exchange.BINANCE: MAP_CUSTOM_TYPE_TO_BINANCE}


def map_interval_for_exchange(exchange: Exchange, interval: CandleTimeInterval) -> str:
    return EXCHANGES_INTERVALS_MAP[exchange][interval]


def interval_mapper(interval: str) -> CandleTimeInterval:
    return {
        "1m": CandleTimeInterval.I_1M,
        "3m": CandleTimeInterval.I_3M,
        "5m": CandleTimeInterval.I_5M,
        "15m": CandleTimeInterval.I_15M,
        "30m": CandleTimeInterval.I_30M,
        "1h": CandleTimeInterval.I_1H,
        "2h": CandleTimeInterval.I_2H,
        "4h": CandleTimeInterval.I_4H,
        "6h": CandleTimeInterval.I_6H,
        "8h": CandleTimeInterval.I_8H,
        "12h": CandleTimeInterval.I_12H,
        "1d": CandleTimeInterval.I_1D,
    }.get(interval, None)


def interval_mapper_to_seconds(interval: str) -> int:
    one_minute = 60
    one_hour = one_minute * 60
    return {
        CandleTimeInterval.I_1M: one_minute,
        CandleTimeInterval.I_3M: one_minute * 3,
        CandleTimeInterval.I_5M: one_minute * 5,
        CandleTimeInterval.I_15M: one_minute * 15,
        CandleTimeInterval.I_30M: one_minute * 30,
        CandleTimeInterval.I_1H: one_hour,
        CandleTimeInterval.I_2H: one_hour * 2,
        CandleTimeInterval.I_4H: one_hour * 4,
        CandleTimeInterval.I_6H: one_hour * 6,
        CandleTimeInterval.I_8H: one_hour * 8,
        CandleTimeInterval.I_12H: one_hour * 12,
        CandleTimeInterval.I_1D: one_hour * 24,
    }.get(interval, None)


def mode_mapper(mode: str) -> TradingMode:
    return {
        "backtest": TradingMode.BACKTEST,
        "live-test": TradingMode.LIVE_TEST,
        "live": TradingMode.LIVE,
    }.get(mode)


def get_exchange_api(exchange: str):
    if exchange in ["poloniex"]:
        from exchange_api.poloniex_adapter import PoloniexAdapter
        return PoloniexAdapter(userconfig.POLONIEX_API_KEY, userconfig.POLONIEX_SECRET)
    elif exchange in ["binance"]:
        from exchange_api.binance_adapter import BinanceAdapter
        return BinanceAdapter(userconfig.BINANCE_API_KEY, userconfig.BINANCE_SECRET)

    return None


def almost_equal(a, b, e):
    return abs(a - b) < e


def end_time(t):
    end_t = 0
    if t in ['now']:
        end_t = int(time.time())
    else:
        end_t = int(t)

    return end_t

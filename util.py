import importlib
import itertools
import operator
import os
import time

import numpy as np

import userconfig
from customtypes import CandleTimeInterval, Exchange, IStrategy, TradingMode
from exchange_api.binance_adapter import BinanceAdapter
from exchange_api.poloniex_adapter import PoloniexAdapter

MIN_TREND_LINE_LENGTH = 3

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
        return PoloniexAdapter(userconfig.POLONIEX_API_KEY, userconfig.POLONIEX_SECRET)
    elif exchange in ["binance"]:
        return BinanceAdapter(userconfig.BINANCE_API_KEY, userconfig.BINANCE_SECRET)

    return None


IGNORED_strategy = ["__pycache__", "__init__"]


class StrategiesManager(object):
    def __init__(self, directory):
        self.directory = directory

    def get_strategy(self, name):
        return self.get_strategies(IStrategy).get(name, None)

    def get_strategies(self, addon_type) -> dict:
        return StrategiesManager.__find_strategy(self.directory, addon_type)

    @staticmethod
    def __get_strategy_list_from(path: str):
        strategy = map(lambda x: os.path.splitext(x)[0], os.listdir(path))
        strategy = filter(lambda x: x not in IGNORED_strategy, strategy)
        strategy = map(lambda x: os.path.join(path, x), strategy)
        strategy = map(lambda x: x.replace("/", '.'), strategy)
        return list(strategy)

    @staticmethod
    def __find_strategy(path: str, addon_type):
        strategy = StrategiesManager.__get_strategy_list_from(path)
        founded_strategy = {}

        for addon in strategy:
            importlib.import_module(addon)

        for addon in addon_type.__subclasses__():
            if addon.__module__ not in strategy:
                continue

            founded_strategy[addon.__strategy__] = addon

        return founded_strategy


def frame_trend(df, n, indicator, callback):
    elements = list(df.iloc[-n:][indicator])
    previous = elements.pop(0)

    comparations = []
    for current in elements:
        comparations.append(callback(previous, current))
        previous = current

    return comparations.count(True) > comparations.count(False)


def get_aprox_trend_line(df, n, indicator):
    # n - passed candles

    x = list(range(1, n + 1))
    y = list(df.iloc[-n:][indicator])
    z = np.polyfit(x, y, 1)

    return np.poly1d(z)(x)


def is_uptrend(df, aprox, indicator):
    close_indicator = "Close"
    low_indicator = "Low"

    second_low, first_low = list(df.iloc[-2:][low_indicator])
    second_candle_close, first_candle_close = list(df.iloc[-2:][close_indicator])
    second_trend_candle, first_trend_candle = list(aprox[-2:])

    second_closed_upper_that_trend = second_candle_close >= second_trend_candle
    second_low_upper_that_trend = second_low >= second_trend_candle
    first_low_upper_that_trend = first_low >= first_trend_candle
    first_closed_upper_that_trend = first_candle_close >= first_trend_candle

    states = [
        second_closed_upper_that_trend,
        second_low_upper_that_trend,
        first_low_upper_that_trend,
        first_closed_upper_that_trend,
    ]

    states_combinations = itertools.combinations(states, 2)
    combinations = list(map(lambda x: x[0] == x[1] and x[0] == True, states_combinations))

    return combinations.count(True) >= 1 and operator.le(aprox[0], aprox[-1])


def is_downtrend(df, aprox, indicator):
    close_indicator = "Close"
    high_indicator = "High"

    second_high, first_high = list(df.iloc[-2:][high_indicator])
    second_candle_close, first_candle_close = list(df.iloc[-2:][close_indicator])
    second_trend_candle, first_trend_candle = list(aprox[-2:])

    states = [
        second_high <= second_trend_candle,
        second_candle_close <= second_trend_candle,
        first_high <= first_trend_candle,
        first_candle_close <= first_trend_candle,
    ]

    states_combinations = itertools.combinations(states, 2)
    combinations = list(map(lambda x: x[0] == x[1] and x[0] == True, states_combinations))

    return combinations.count(True) >= 1 and operator.ge(aprox[0], aprox[-1])

    # return is_trend(operator.lt, df, aprox, indicator)


def is_trend(op, df, aprox, indicator):
    close_indicator = "Close"

    second_candle_close, first_candle_close = list(df.iloc[-2:][close_indicator])
    second_candle, first_candle = list(df.iloc[-2:][indicator])
    second_trend_candle, first_trend_candle = list(aprox[-2:])

    print(op(second_candle, second_trend_candle), op, second_candle, second_trend_candle)
    print(op(first_candle, first_trend_candle), op, first_candle, first_trend_candle)

    return op(first_candle, first_trend_candle) and op(second_candle, second_trend_candle) and op(
        second_candle_close, second_candle) and op(second_candle_close, second_candle)


def almost_equal(a, b, e):
    return abs(a - b) < e


def end_time(t):
    end_t = 0
    if t in ['now']:
        end_t = int(time.time())
    else:
        end_t = int(t)

    return end_t


def trend_line_detection(df, n, indicator, min_n=3) -> int:
    poly = get_aprox_trend_line(df, n, indicator)

    (prev_iteration_trend, curr_iteration_trend) = poly[-2:]
    (prev_iteration, curr_iteration) = list(df.iloc[-2:][indicator])

    return [min_n, n + 1][prev_iteration_trend > prev_iteration and curr_iteration_trend > curr_iteration]

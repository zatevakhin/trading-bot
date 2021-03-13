
from customtypes import CandleTimeInterval, Exchange, IStrategy

import userconfig
from poloniex import Poloniex
from binance import Binance

import importlib
import os



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



def get_exchange_api(exchange: str):

    if exchange in ["poloniex"]:
         return Poloniex(userconfig.POLONIEX_API_KEY, userconfig.POLONIEX_SECRET)

    elif exchange in ["binance"]:
        return Binance(userconfig.BINANCE_API_KEY, userconfig.BINANCE_SECRET)

    return None


IGNORED_strategy = [
    "__pycache__",
    "__init__"
]

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

    return comparations.count(True) > comparations.count(False)

def almost_equal(a, b, e):
    return abs(a - b) < e

import importlib
import os

from strategies.strategybase import StrategyBase

IGNORED_FILES = ['__pycache__', '__init__', 'strategybase']


class StrategyManager(object):
    def __init__(self, directory):
        self.directory = directory

    def get_strategy(self, name):
        return self.get_strategies(StrategyBase).get(name, None)

    def get_strategies(self, addon_type) -> dict:
        return StrategyManager.__find_strategy(self.directory, addon_type)

    @staticmethod
    def __get_strategy_list_from(path: str):
        strategy = map(lambda x: os.path.splitext(x)[0], os.listdir(path))
        strategy = filter(lambda x: x not in IGNORED_FILES, strategy)
        strategy = map(lambda x: os.path.join(path, x), strategy)
        strategy = map(lambda x: x.replace("/", '.'), strategy)
        return list(strategy)

    @staticmethod
    def __find_strategy(path: str, addon_type):
        strategy = StrategyManager.__get_strategy_list_from(path)
        founded_strategy = {}

        for addon in strategy:
            importlib.import_module(addon)

        for addon in addon_type.__subclasses__():
            if addon.__module__ not in strategy:
                continue

            founded_strategy[addon.__strategy__] = addon

        return founded_strategy

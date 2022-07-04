import math

import talib as ta
from chart import Chart

from strategies.strategybase import StrategyBase


def is_pinbar_red(candle):
    is_red = candle.p_open > candle.p_close

    body = abs(candle.p_open - candle.p_close)

    low = abs(candle.p_close - candle.p_low)
    high = abs(candle.p_open - candle.p_high)

    return is_red and low > body and high < low and high < body


# (candle.p_open + (body * 2)) < candle.p_high


class Strategy(StrategyBase):
    __strategy__ = 'rp'

    def __init__(self, args, chart: 'Chart', exchange, mode, budget):
        super().__init__(args, chart, exchange, mode, budget)

    def tick(self) -> dict:
        candle = self.get_current_candle()

        if is_pinbar_red(candle):
            return {"lows": [{"x": candle.t_open, "y": candle.p_low, "c": candle.p_low}]}
        return {}

    def rt_tick(self, candle: 'Candle') -> dict:
        return {}

import math

import talib as ta
from basetypes.trend_direction import TrendDirection
from chart import Chart
from utils.trand_indicators import *

from strategies.strategybase import StrategyBase

MAIN_PERIOD = 50
SIGNAL_PERIOD = 7

MIN_TREND_LINE_LENGTH = 3


class Strategy(StrategyBase):
    __strategy__ = 'scalper.1.0'

    def __init__(self, chart: 'Chart', exchange, mode, budget):
        super().__init__(chart, exchange, mode, budget)

        self.num_candles_downtrend = MIN_TREND_LINE_LENGTH
        self.num_candles_uptrend = MIN_TREND_LINE_LENGTH
        self.previous_trend = TrendDirection.FLAT

    def tick(self) -> dict:
        candle = self.get_current_candle()

        #--------------------------
        # TREND DIRECTION
        #--------------------------
        aprox_uptrend = get_trend_aproximation(self.indicators.low_array, self.num_candles_uptrend)
        aprox_downtrend = get_trend_aproximation(self.indicators.high_array, self.num_candles_downtrend)

        is_uptrend = stupid_check_uptrend(self.indicators, aprox_uptrend)
        is_downtrend = stupid_check_downtrend(self.indicators, aprox_downtrend)

        trend_direction = TrendDirection.FLAT

        if is_uptrend == is_downtrend:
            self.num_candles_uptrend = MIN_TREND_LINE_LENGTH
            self.num_candles_downtrend = MIN_TREND_LINE_LENGTH

        current_n_uptrend = [MIN_TREND_LINE_LENGTH, self.num_candles_uptrend + 1][is_uptrend]
        current_n_downtrend = [MIN_TREND_LINE_LENGTH, self.num_candles_downtrend + 1][is_downtrend]

        if is_uptrend and current_n_uptrend > self.num_candles_uptrend:
            trend_direction = TrendDirection.UPTREND

        if is_downtrend and current_n_downtrend > self.num_candles_downtrend:
            trend_direction = TrendDirection.DOWNTREND

        #--------------------------
        # TREND DIRECTION END
        #--------------------------

        close = self.indicators.close_array

        sma = ta.SMA(ta.SMA(close, math.ceil(MAIN_PERIOD / 2)), math.floor(MAIN_PERIOD / 2) + 1)
        signal_line = ta.SMA(close, SIGNAL_PERIOD)

        scalping_line = signal_line - sma

        if trend_direction in [TrendDirection.UPTREND, TrendDirection.FLAT]:
            if self.previous_trend in [TrendDirection.DOWNTREND]:
                if (scalping_line < 0)[-1]:
                    if scalping_line[-1] > scalping_line[-2]:
                        self.open_trade(stop_loss_percent=1.0)

        if (scalping_line > 0)[-1]:
            self.close_trade()

        #--------------------------
        self.num_candles_uptrend = current_n_uptrend
        self.num_candles_downtrend = current_n_downtrend
        self.previous_trend = trend_direction

        return {"scalping-line": scalping_line, "uptrend": aprox_uptrend, "downtrend": aprox_downtrend}

from basetypes.trend_direction import TrendDirection
from chart import Chart
from utils.trand_indicators import *

from strategies.strategybase import StrategyBase

MIN_UPTREND_LINE_LENGTH = 2
MIN_DONWTREND_LINE_LENGTH = 3


class Strategy(StrategyBase):
    __strategy__ = 'default'

    def __init__(self, chart: 'Chart', exchange, mode, budget):
        super().__init__(chart, exchange, mode, budget)

        self.num_candles_downtrend = MIN_DONWTREND_LINE_LENGTH
        self.num_candles_uptrend = MIN_UPTREND_LINE_LENGTH
        self.previous_trend = TrendDirection.FLAT

    def tick(self) -> dict:
        current_rsi = self.indicators.rsi_array[-1]

        aprox_uptrend = get_trend_aproximation(self.indicators.low_array, self.num_candles_uptrend)
        aprox_downtrend = get_trend_aproximation(self.indicators.high_array, self.num_candles_downtrend)

        is_uptrend = stupid_check_uptrend(self.indicators, aprox_uptrend)
        is_downtrend = stupid_check_downtrend(self.indicators, aprox_downtrend)

        trend_direction = TrendDirection.FLAT

        if is_uptrend == is_downtrend:
            self.num_candles_uptrend = MIN_UPTREND_LINE_LENGTH
            self.num_candles_downtrend = MIN_DONWTREND_LINE_LENGTH

        current_n_uptrend = [MIN_UPTREND_LINE_LENGTH, self.num_candles_uptrend + 1][is_uptrend]
        current_n_downtrend = [MIN_DONWTREND_LINE_LENGTH, self.num_candles_downtrend + 1][is_downtrend]

        if is_uptrend and current_n_uptrend > self.num_candles_uptrend:
            trend_direction = TrendDirection.UPTREND

        if is_downtrend and current_n_downtrend > self.num_candles_downtrend:
            trend_direction = TrendDirection.DOWNTREND

        if trend_direction in [TrendDirection.UPTREND, TrendDirection.FLAT]:
            if self.previous_trend in [TrendDirection.DOWNTREND]:
                if current_rsi <= 50:
                    self.open_trade(stop_loss_percent=1.0)

        #--------------------------

        if trend_direction in [TrendDirection.DOWNTREND, TrendDirection.FLAT]:
            if self.previous_trend in [TrendDirection.UPTREND]:
                self.close_trade()

        #--------------------------
        self.num_candles_uptrend = current_n_uptrend
        self.num_candles_downtrend = current_n_downtrend
        self.previous_trend = trend_direction

        return {"uptrend": aprox_uptrend, "downtrend": aprox_downtrend}

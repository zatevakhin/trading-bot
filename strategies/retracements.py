from chart import Chart
from loguru import logger

from strategies.strategybase import StrategyBase


class Strategy(StrategyBase):
    __strategy__ = 'retracements'

    def __init__(self, args, chart: 'Chart', exchange, mode, budget):
        super().__init__(args, chart, exchange, mode, budget)

    def tick(self) -> dict:
        candle = self.get_current_candle()

        logger.info(candle)

        low = list(reversed(list(self.indicators.low_array)))
        high = list(reversed(list(self.indicators.high_array)))
        opn = list(reversed(list(self.indicators.open_array)))
        close = list(reversed(list(self.indicators.close_array)))

        # retracementEnded = open < close and high[1] < high and high[2] > high[1] and high[3] > high[2]
        # endOfBullRun = open > close and low[1] > low and low[2] < low[1] and low[3] < low[2]
        # and (opn[2] > close[1] and opn[3] > close[2])

        retracementEnded = opn[0] < close[0] and high[1] < high[0] and high[2] > high[1] and high[3] > high[2] and (opn[2] > close[1]
                                                                                                                    and opn[3] > close[2])
        endOfBullRun = opn[0] > close[0] and low[1] > low[0] and low[2] < low[1] and low[3] < low[2]

        #--------------------------
        if retracementEnded:
            self.open_trade(stop_loss_percent=1.0)

        #--------------------------

        if endOfBullRun:
            self.close_trade()

        if self.position:
            self.position.set_prop_limit(candle, 1.0)

        return {}

    def rt_tick(self, candle: 'Candle') -> dict:

        return {}

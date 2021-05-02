import talib as ta
from chart import Chart

from strategies.strategybase import StrategyBase


class Strategy(StrategyBase):
    __strategy__ = 'macd'

    def __init__(self, args, chart: 'Chart', exchange, mode, budget):
        super().__init__(args, chart, exchange, mode, budget)

    def tick(self) -> dict:
        candle = self.get_current_candle()

        close2 = self.indicators.close_array

        macd_o, signal_o, hist_o = ta.MACD(close2, fastperiod=12, slowperiod=26, signalperiod=9)
        # hist = list(reversed(hist_o))
        macd = list(reversed(macd_o))
        signal = list(reversed(signal_o))

        if macd[0] > signal[0]:
            self.open_trade(stop_loss_percent=1.0)

        if macd[0] < signal[0]:
            self.close_trade()

        return {"macd": macd_o, "signal": signal_o, "hist": hist_o}

    def rt_tick(self, candle: 'Candle') -> dict:

        return {}

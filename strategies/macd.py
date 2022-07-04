import talib as ta
from chart import Chart
from loguru import logger

from strategies.strategybase import StrategyBase


class Strategy(StrategyBase):
    __strategy__ = 'macd'

    def __init__(self, args, chart: 'Chart', exchange, mode, budget):
        super().__init__(args, chart, exchange, mode, budget)
        self.fast = int(args.get("fast", 12))
        self.slow = int(args.get("slow", 26))
        self.signal = int(args.get("sig", 9))
        self.rsi_threshold = int(args.get("th-rsi", 50))

        logger.opt(colors=True).info(
            f"MACD: fastperiod: <red>{self.fast}</red>, slowperiod: <red>{self.slow}</red>, signalperiod: <red>{self.signal}</red>")

        logger.opt(colors=True).info(f"MACD: RSI Threshold: <red>{self.rsi_threshold}</red>")

    def tick(self) -> dict:
        candle = self.get_current_candle()
        rsi_array = list(reversed(self.indicators.rsi_array))

        close = self.indicators.close_array
        macd_o, signal_o, hist_o = ta.MACD(close, fastperiod=self.fast, slowperiod=self.slow, signalperiod=self.signal)

        macd = list(reversed(macd_o))
        signal = list(reversed(signal_o))

        ema50 = list(reversed(list(self.indicators.ema50)))
        ema200 = list(reversed(list(self.indicators.ema200)))

        if ema200[0] >= ema50[0]:
            if macd[0] > signal[0] and macd[1] <= signal[1]:
                if rsi_array[0] <= self.rsi_threshold:
                    self.open_trade(stop_loss_percent=0.0)

        if macd[0] < signal[0] and macd[1] >= signal[1]:
            self.close_trade()

        return {"macd": macd_o, "signal": signal_o, "hist": hist_o}

    def rt_tick(self, candle: 'Candle') -> dict:
        return {}

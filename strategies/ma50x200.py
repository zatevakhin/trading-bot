from enum import Enum, auto

import talib as ta
from chart import Chart
from loguru import logger

from strategies.strategybase import StrategyBase


class State(Enum):
    HIGH = auto()
    MID = auto()
    LOW = auto()


class Strategy(StrategyBase):
    __strategy__ = '50x200'

    def __init__(self, args, chart: 'Chart', exchange, mode, budget):
        super().__init__(args, chart, exchange, mode, budget)
        self.mPatterns = []
        self.is_trade_open = False
        self.is_hold = False
        self.is_change = False

        self.state_list = []

    def tick(self) -> dict:
        candle = self.get_current_candle()

        ema200 = list(reversed(list(self.indicators.ema200)))
        ema50 = list(reversed(list(self.indicators.ema50)))
        ema25 = list(reversed(list(self.indicators.ema25)))
        ema12 = list(reversed(list(self.indicators.ema12)))
        ema6 = list(reversed(list(self.indicators.ema6)))
        close = list(reversed(list(self.indicators.close_array)))
        high = list(reversed(list(self.indicators.high_array)))

        if close[:5] > ema200[:5] and close[:5] > ema50[:5] and close[:5] > ema25[:5] and close[:5] > ema12[:5]:
            self.state_list.append(State.HIGH)
            self.mPatterns.append({"pos": (candle.t_open, candle.p_low), "size": 25, "symbol": "arrow_down", "color": "#0000FF"})

        elif close[:5] < ema200[:5] and close[:5] < ema50[:5] and close[:5] < ema25[:5] and close[:5] < ema12[:5]:
            self.mPatterns.append({"pos": (candle.t_open, candle.p_high), "size": 25, "symbol": "arrow_up", "color": "#FF0000"})
            self.state_list.append(State.LOW)

        else:
            self.state_list.append(State.MID)
            self.mPatterns.append({"pos": (candle.t_open, candle.p_high), "size": 15, "symbol": "x", "color": "#FF0000"})

        if self.state_list and len(self.state_list) >= 3:
            if self.state_list[-2] == State.HIGH and self.state_list[-1] == State.MID:
                pass

            elif self.state_list[-3] == State.HIGH and self.state_list[-2] == State.HIGH and self.state_list[-1] == State.MID:
                pass

        return {"scatter": self.mPatterns}

    def rt_tick(self, candle: 'Candle') -> dict:
        return {}

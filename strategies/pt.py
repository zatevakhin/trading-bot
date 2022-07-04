import math

import talib as ta
from chart import Chart

from strategies.strategybase import StrategyBase


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def find_v_shape_new(candles, n):

    v_shapes = []

    for chunk in chunks(candles, n):
        if len(chunk) < 5:
            continue

        is_v_shape = all([
            chunk[0].p_close > chunk[1].p_close,
            chunk[1].p_close >= chunk[2].p_close,
            chunk[2].p_close <= chunk[3].p_close,
            chunk[3].p_close < chunk[4].p_close,
        ])

        v_low = chunk[2]

        if is_v_shape:
            v_shapes.append({"x": v_low.t_open, "y": v_low.p_low, "c": v_low})

    return v_shapes


def find_v_max(candles, n):

    v_shapes = []

    for chunk in chunks(candles, n):
        if len(chunk) < 5:
            continue

        is_v_shape = all([
            chunk[0].p_close < chunk[1].p_close,
            chunk[1].p_close <= chunk[2].p_close,
            chunk[2].p_close >= chunk[3].p_close,
            chunk[3].p_close > chunk[4].p_close,
        ])

        v_low = chunk[2]

        if is_v_shape:
            v_shapes.append({"x": v_low.t_open, "y": v_low.p_high, "c": v_low})

    return v_shapes


class Strategy(StrategyBase):
    __strategy__ = 'pt'

    def __init__(self, args, chart: 'Chart', exchange, mode, budget):
        super().__init__(args, chart, exchange, mode, budget)
        self.mPatterns = []

    def tick(self) -> dict:
        candle = self.get_current_candle()

        lst_candles = self.chart.get_candles()[-5:]

        o = self.indicators.open_array
        c = self.indicators.close_array
        l = self.indicators.low_array
        h = self.indicators.high_array

        # if ta.CDL2CROWS(o, h, l, c)[-1]:
        #     self.mPatterns.append({"pos": (candle.t_open, candle.p_low), "size": 20, "symbol": "o"})

        # if ta.CDL3BLACKCROWS(o, h, l, c)[-1]:
        #     self.mPatterns.append({"pos": (candle.t_open, candle.p_low), "size": 20, "symbol": "arrow_down", 'color': "#FF0000"})

        # if ta.CDL3INSIDE(o, h, l, c)[-1]:
        #     self.mPatterns.append({"pos": (candle.t_open, candle.p_low), "size": 20, "symbol": "arrow_right"})

        # if (integer := ta.CDL3LINESTRIKE(o, h, l, c))[-1]:
        #     self.mPatterns.append({"pos": (candle.t_open, candle.p_low), "size": 10, "symbol": 'o'})

        # if (integer := ta.CDL3OUTSIDE(o, h, l, c))[-1]:
        #     self.mPatterns.append({"pos": (candle.t_open, candle.p_low), "size": 20, "symbol": 'arrow_left'})

        # if (integer := ta.CDLDOJI(o, h, l, c))[-1] != 0:
        #     self.mPatterns.append({"pos": (candle.t_open, candle.p_high), "size": 10, "symbol": "+"})

        if (integer := ta.CDLDOJI(o, h, l, c))[-1] != 0:
            self.mPatterns.append({"pos": (candle.t_open, candle.p_low), "size": 10, "symbol": "+", "color": "#0000FF"})

        if (integer := ta.CDLMORNINGSTAR(o, h, l, c))[-1] != 0:
            self.mPatterns.append({"pos": (candle.t_open, candle.p_low), "size": 10, "symbol": "star", "color": "#0000FF"})

        if (integer := ta.CDLEVENINGSTAR(o, h, l, c))[-1] != 0:
            self.mPatterns.append({"pos": (candle.t_open, candle.p_low), "size": 10, "symbol": "star", "color": "#FF0000"})

        if (integer := ta.CDLMORNINGDOJISTAR(o, h, l, c))[-1] != 0:
            self.mPatterns.append({"pos": (candle.t_open, candle.p_high), "size": 10, "symbol": "x", "color": "#0000FF"})

        if (integer := ta.CDLEVENINGDOJISTAR(o, h, l, c))[-1] != 0:
            self.mPatterns.append({"pos": (candle.t_open, candle.p_high), "size": 10, "symbol": "x", "color": "#FF0000"})

        if (integer := ta.CDLTASUKIGAP(o, h, l, c))[-1] != 0:
            print("CDLTASUKIGAP", integer[-1])
            self.mPatterns.append({"pos": (candle.t_open, candle.p_high), "size": 40, "symbol": "arrow_right", "color": "#FF0000"})

        if (integer := ta.CDLMATCHINGLOW(o, h, l, c))[-1] != 0:
            print("CDLMATCHINGLOW", integer[-1])
            self.mPatterns.append({"pos": (candle.t_open, candle.p_high), "size": 10, "symbol": "s", "color": "#FF0000"})

        if (integer := ta.CDLABANDONEDBABY(o, h, l, c))[-1] != 0:
            self.mPatterns.append({"pos": (candle.t_open, candle.p_high), "size": 20, "symbol": "crosshair", "color": "#FF0000"})

        # if (integer := ta.CDL3STARSINSOUTH(o, h, l, c))[-1] != 0:
        #     self.mPatterns.append({"pos": (candle.t_open, candle.p_low), "size": 10, "symbol": "star", "color": "#FF00FF"})

        # if (integer := ta.CDLABANDONEDBABY(o, h, l, c))[-1] != 0:
        #     self.mPatterns.append({"pos": (candle.t_open, candle.p_low), "size": 10, "symbol": "p", "color": "#FF0000"})

        # if (integer := ta.CDLBREAKAWAY(o, h, l, c))[-1] != 0:
        #     self.mPatterns.append({"pos": (candle.t_open, candle.p_high), "size": 50, "symbol": "arrow_up", "color": "#FF0000"})

        # if (integer := ta.CDLDARKCLOUDCOVER(o, h, l, c))[-1] != 0:
        #     self.mPatterns.append({"pos": (candle.t_open, candle.p_high), "size": 40, "symbol": "arrow_up", "color": "#0000FF"})

        # if (integer := ta.CDLPIERCING(o, h, l, c))[-1] != 0:
        #     self.mPatterns.append({"pos": (candle.t_open, candle.p_high), "size": 40, "symbol": "arrow_down", "color": "#FF0000"})

        # if (integer := ta.CDLINVERTEDHAMMER(o, h, l, c))[-1] != 0:
        #     self.mPatterns.append({"pos": (candle.t_open, candle.p_high), "size": 40, "symbol": "arrow_up", "color": "#0000FF"})

        # if (integer := ta.CDLPIERCING(o, h, l, c))[-1] != 0:
        #     self.mPatterns.append({"pos": (candle.t_open, candle.p_high), "size": 10, "symbol": "o", "color": "#FF00FF"})

        # if (integer := ta.CDLADVANCEBLOCK(o, h, l, c))[-1] != 0:
        #     self.mPatterns.append({"pos": (candle.t_open, candle.p_low), "size": 10, "symbol": "p", "color": "#00FF00"})

        # if (integer := ta.CDLBELTHOLD(o, h, l, c))[-1] != 0:
        #     self.mPatterns.append({"pos": (candle.t_open, candle.p_low), "size": 10, "symbol": "p", "color": "#0000FF"})

        # if (integer := ta.CDLMORNINGDOJISTAR(o, h, l, c))[-1] != 0:
        #     self.mPatterns.append({"pos": (candle.t_open, candle.p_low), "size": 10, "symbol": "h"})

        # if (integer := ta.CDL3WHITESOLDIERS(o, h, l, c))[-1] != 0:
        #     self.mPatterns.append({"pos": (candle.t_open, candle.p_low), "size": 20, "symbol": "arrow_up", 'color': "#FFFFFF"})

        # if (integer := ta.CDLENGULFING(o, h, l, c))[-1] > 0:
        #     self.mPatterns.append({"pos": (candle.t_open, candle.p_low), "size": 10, "symbol": 't2'})

        # if (integer := ta.CDLENGULFING(o, h, l, c))[-1] < 0:
        #     self.mPatterns.append({"pos": (candle.t_open, candle.p_low), "size": 10, "symbol": 't3'})

        return {"scatter": self.mPatterns}
        # lows highs

    def rt_tick(self, candle: 'Candle') -> dict:
        return {}

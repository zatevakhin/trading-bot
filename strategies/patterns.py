import math
from enum import unique
from functools import reduce

import talib as ta
from chart import Chart
from numpy.lib.function_base import append

from strategies.strategybase import StrategyBase


def is_pinbar_bear(candle):
    body = abs(candle.p_open - candle.p_close)
    return (candle.p_open + (body * 2)) < candle.p_high


def is_pinbar_bull(candle):
    body = abs(candle.p_open - candle.p_close)
    return (candle.p_open - (body * 2)) > candle.p_low


def bull_pinbar_with_confirmation(candle, p_candle):
    pinbar = is_pinbar_bull(p_candle)
    return pinbar and candle.p_close > p_candle.p_close


def bear_pinbar_with_confirmation(candle, p_candle):
    pinbar = is_pinbar_bear(p_candle)
    return pinbar and candle.p_close < p_candle.p_close


def is_engulfing_bull(candle, candle_p):
    is_green = candle.p_open > candle.p_close

    p_max = max(candle.p_open, candle.p_close)
    p_min = min(candle.p_open, candle.p_close)

    pp_max = max(candle_p.p_open, candle_p.p_close)
    pp_min = min(candle_p.p_open, candle_p.p_close)

    return is_green and p_max >= pp_max and p_min <= pp_min


def is_engulfing_bear(candle, candle_p):
    is_red = candle_p.p_open < candle_p.p_close

    p_max = max(candle.p_open, candle.p_close)
    p_min = min(candle.p_open, candle.p_close)

    pp_max = max(candle_p.p_open, candle_p.p_close)
    pp_min = min(candle_p.p_open, candle_p.p_close)

    return is_red and pp_max >= p_max and pp_min <= p_min


def find_resistance(candles):
    high_candle = None

    for candle in candles:
        if not high_candle or candle.p_high > high_candle.p_high:
            high_candle = candle

    high_body = max(high_candle.p_open, high_candle.p_close)

    return {"x-start": high_candle.t_open, "x-end": candles[-1].t_open, "y": high_body, "type": "R"}


def closest(lst, k):
    return lst[min(range(len(lst)), key=lambda i: abs(lst[i] - k))]


# def find_clusters(candles, percent):

#     for candle in candles:
#         x = (abs(candle.p_open - candle.p_close) / 100) * percent

#         for c2 in candles:
#             if abs(x - abs(candle.p_open - candle.p_close)) > abs(c2.p_open - c2.p_close):

#     {"x": c.t_open, "low": c.p_low, "c": c}
#     return lows


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


def find_v_shape(candles, n):
    mins = []
    maxs = []

    for chunk in chunks(candles, n):
        c_max = max(chunk, key=lambda x: x.p_high)
        c_min = min(chunk, key=lambda x: x.p_low)

        mins.append({"x": c_min.t_open, "low": c_min.p_low})
        maxs.append({"x": c_max.t_open, "high": c_max.p_high})

    return mins, maxs


def find_mins(candles, chunk_sz):
    mins = []

    for chunk in chunks(candles, chunk_sz):
        c_min = min(chunk, key=lambda x: x.p_low)

        mins.append({"x": c_min.t_open, "low": c_min.p_low, "c": c_min})

    return mins


def find_maxs(candles, chunk_sz):
    maxs = []

    for chunk in chunks(candles, chunk_sz):
        c_max = max(chunk, key=lambda x: x.p_high)

        maxs.append({"x": c_max.t_open, "y": c_max.p_high, "c": c_max})

    return maxs


def add_to_group(group, item, err):
    match = False

    for j in group:
        if match:
            break

        if abs(j["y"] - item["y"]) < (item["y"] * err):
            match = True

    if match:
        return group + [item]


def add_to_groups(groups, item, err):
    if not groups:
        groups.append([item])
    else:
        added = False
        for gi, group in enumerate(groups):
            ret = add_to_group(group, item, err)

            if ret:
                added = True
                groups[gi] = ret

        if not added:
            groups.append([item])


def find_support(candles, err):
    mins = find_mins(candles, 12)

    min_candles = list(map(lambda m: m.get("c"), mins))

    supports = []
    for c in min_candles:
        for c2 in min_candles:
            if c2.t_open != c.t_open and abs(c.average - c2.average) < (c.average * err):
                supports.append({"x": c.t_open, "y": c.average})

    check_timestamp = []
    filtered = []
    for i in sorted(supports, key=lambda x: x["y"]):
        if i["x"] not in check_timestamp:
            check_timestamp.append(i["x"])
            filtered.append(i)

    groups = []

    for i in filtered:
        add_to_groups(groups, i, err)

    supports = []
    for group in groups:
        m = sum(map(lambda x: x["y"], group)) / len(group)

        t = sorted(group, key=lambda x: x["x"])

        support = {"x-start": t[-1]["x"], "x-end": candles[-1].t_open, "y": m}
        supports.append(support)

    return supports


def find_resist(candles, err):
    maxs = find_maxs(candles, 12)

    min_candles = list(map(lambda m: m.get("c"), maxs))

    supports = []
    for c in min_candles:
        for c2 in min_candles:
            if c2.t_open != c.t_open and abs(c.average - c2.average) < (c.average * err):
                supports.append({"x": c.t_open, "y": c.average})

    check_timestamp = []
    filtered = []
    for i in sorted(supports, key=lambda x: x["y"]):
        if i["x"] not in check_timestamp:
            check_timestamp.append(i["x"])
            filtered.append(i)

    groups = []

    for i in filtered:
        add_to_groups(groups, i, err)

    supports = []
    for group in groups:
        m = sum(map(lambda x: x["y"], group)) / len(group)

        t = sorted(group, key=lambda x: x["x"])

        support = {"x-start": t[-1]["x"], "x-end": candles[-1].t_open, "y": m}
        supports.append(support)

    return supports


class Strategy(StrategyBase):
    __strategy__ = 'patterns'

    def __init__(self, args, chart: 'Chart', exchange, mode, budget):
        super().__init__(args, chart, exchange, mode, budget)

    def tick(self) -> dict:

        v_shapes = find_v_shape_new(self.chart.get_candles(), 5)

        # v_shape = self.chart.get_candles()[-5:]

        # is_v_shape = all([
        #     v_shape[0].p_low > v_shape[1].p_low,
        #     v_shape[1].p_low >= v_shape[2].p_low,
        #     v_shape[2].p_low <= v_shape[3].p_low,
        #     v_shape[3].p_low < v_shape[4].p_low,
        # ])

        # v_low = v_shape[2]

        # v_shape = []

        # if is_v_shape:
        #     v_shape.append({"x": v_low.t_open, "y": v_low.p_high, "c": v_low})

        # ema6 = list(self.indicators.ema6_array)

        # bear = is_engulfing_bear(candle, candle_p)
        # bull = is_engulfing_bull(candle, candle_p)

        # bear = bear_pinbar_with_confirmation(candle, candle_p)
        # bear = is_pinbar_bear(candle)
        # bull = bull_pinbar_with_confirmation(candle, candle_p)

        # if bull and not bear:
        #     self.open_trade(stop_loss_percent=5.0)

        # if not bull and bear:
        #     self.close_trade()

        # supports_and_resists = []

        # supports_and_resists.append(find_resistance(self.chart.get_candles()[-50:]))
        # supports_and_resists.append(find_resistance(self.chart.get_candles()[-100:]))
        # supports_and_resists.append(find_resistance(self.chart.get_candles()[-200:]))

        # supports_and_resists.append(find_support(self.chart.get_candles()[-50:]))
        # supports_and_resists.append(find_support(self.chart.get_candles()[-100:]))
        # supports_and_resists.append(find_support(self.chart.get_candles()[-200:]))

        # lows = find_lows(list(reversed(self.chart.get_candles()[-300:])))

        # supports_and_resists.append(find_supports_2(lows, self.get_current_candle()))
        # highs = find_v_shape(self.chart.get_candles(), 12)

        # err = 0.05
        # lows = find_mins(self.chart.get_candles(), 12)

        # supports = find_support(self.chart.get_candles(), err)
        # resists = find_resist(self.chart.get_candles(), err)

        return {"lows": v_shapes}  #{"supports": [], "resists": [], "lows": [], "highs": []}
        return {}  #{"supports": [], "resists": [], "lows": [], "highs": []}

    def rt_tick(self, candle: 'Candle') -> dict:
        return {}

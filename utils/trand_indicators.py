import itertools
import operator

import numpy as np

MIN_TREND_LINE_LENGTH = 3


def get_trend_aproximation(df, n, indicator):
    # n - passed candles

    x = list(range(1, n + 1))
    y = list(df.iloc[-n:][indicator])
    z = np.polyfit(x, y, 1)

    return np.poly1d(z)(x)


def check_uptrend(df, aprox, aggresive=False):
    open_indicator = "Open"
    close_indicator = "Close"
    low_indicator = "Low"

    second_open, first_open = list(df.iloc[-2:][open_indicator])
    second_low, first_low = list(df.iloc[-2:][low_indicator])
    second_candle_close, first_candle_close = list(df.iloc[-2:][close_indicator])
    second_trend_candle, first_trend_candle = list(aprox[-2:])

    first_low_upper_that_trend = first_low >= first_trend_candle
    first_closed_upper_that_trend = first_candle_close >= first_trend_candle
    second_closed_upper_that_trend = second_candle_close >= second_trend_candle
    second_low_upper_that_trend = second_low >= second_trend_candle

    first_candle_up = first_candle_close > first_open
    second_candle_up = second_candle_close > second_open

    states = [
        first_low_upper_that_trend,
        first_closed_upper_that_trend,
    ]

    if not aggresive:
        states.append(second_closed_upper_that_trend)
        states.append(second_low_upper_that_trend)

    states = itertools.combinations(states, 2)
    combinations = list(map(lambda i: (lambda x, y: x and x == y)(*i), states))

    return combinations.count(True) >= 1 and operator.le(aprox[0], aprox[-1])


def check_downtrend(df, aprox, aggresive=False):
    open_indicator = "Open"
    close_indicator = "Close"
    high_indicator = "High"

    second_open, first_open = list(df.iloc[-2:][open_indicator])
    second_high, first_high = list(df.iloc[-2:][high_indicator])
    second_candle_close, first_candle_close = list(df.iloc[-2:][close_indicator])
    second_trend_candle, first_trend_candle = list(aprox[-2:])

    first_candle_down = not first_candle_close > first_open
    second_candle_down = not second_candle_close > second_open

    states = [
        first_high <= first_trend_candle,
        first_candle_close <= first_trend_candle,
    ]

    if not aggresive:
        states.append(second_high <= second_trend_candle)
        states.append(second_candle_close <= second_trend_candle)

    states = itertools.combinations(states, 2)
    combinations = list(map(lambda i: (lambda x, y: x and x == y)(*i), states))

    return combinations.count(True) >= 1 and operator.ge(aprox[0], aprox[-1])


def stupid_check_uptrend(df, aprox, aggresive=False):
    open_indicator = "Open"
    close_indicator = "Close"

    second_open, first_open = list(df.iloc[-2:][open_indicator])
    second_candle_close, first_candle_close = list(df.iloc[-2:][close_indicator])

    first_candle_up = first_candle_close > first_open
    second_candle_up = second_candle_close > second_open

    if not aggresive:
        first_candle_up = second_candle_up and first_candle_up

    return first_candle_up and operator.le(aprox[0], aprox[-1])


def stupid_check_downtrend(df, aprox, aggresive=False):
    open_indicator = "Open"
    close_indicator = "Close"

    second_open, first_open = list(df.iloc[-2:][open_indicator])
    second_candle_close, first_candle_close = list(df.iloc[-2:][close_indicator])

    first_candle_down = not first_candle_close > first_open
    second_candle_down = not second_candle_close > second_open

    if not aggresive:
        first_candle_down = first_candle_down and second_candle_down

    return first_candle_down and operator.ge(aprox[0], aprox[-1])


def check_frame_trend(df, n, indicator, callback):
    elements = list(df.iloc[-n:][indicator])
    previous = elements.pop(0)

    comparations = []
    for current in elements:
        comparations.append(callback(previous, current))
        previous = current

    return comparations.count(True) > comparations.count(False)

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
    close_indicator = "Close"
    low_indicator = "Low"

    second_low, first_low = list(df.iloc[-2:][low_indicator])
    second_candle_close, first_candle_close = list(df.iloc[-2:][close_indicator])
    second_trend_candle, first_trend_candle = list(aprox[-2:])

    first_low_upper_that_trend = first_low >= first_trend_candle
    first_closed_upper_that_trend = first_candle_close >= first_trend_candle

    states = [
        first_low_upper_that_trend,
        first_closed_upper_that_trend,
    ]

    if not aggresive:
        second_closed_upper_that_trend = second_candle_close >= second_trend_candle
        second_low_upper_that_trend = second_low >= second_trend_candle

        states.append(second_closed_upper_that_trend)
        states.append(second_low_upper_that_trend)

    states = itertools.combinations(states, 2)
    combinations = list(map(lambda i: (lambda x, y: x and x == y)(*i), states))

    return combinations.count(True) >= 1 and operator.le(aprox[0], aprox[-1])


def check_downtrend(df, aprox, aggresive=False):
    close_indicator = "Close"
    high_indicator = "High"

    second_high, first_high = list(df.iloc[-2:][high_indicator])
    second_candle_close, first_candle_close = list(df.iloc[-2:][close_indicator])
    second_trend_candle, first_trend_candle = list(aprox[-2:])

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


def check_frame_trend(df, n, indicator, callback):
    elements = list(df.iloc[-n:][indicator])
    previous = elements.pop(0)

    comparations = []
    for current in elements:
        comparations.append(callback(previous, current))
        previous = current

    return comparations.count(True) > comparations.count(False)

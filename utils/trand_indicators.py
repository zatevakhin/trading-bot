import operator

import numpy as np


def get_trend_aproximation(indicator_list, n):
    # n - passed candles

    x = list(range(1, n + 1))
    y = list(indicator_list[-n:])
    z = np.polyfit(x, y, 1)

    return np.poly1d(z)(x)


def stupid_check_uptrend(indicators, aprox, strict=True):
    open_price_list = indicators.open_array
    close_price_list = indicators.close_array

    if not operator.le(aprox[0], aprox[-1]):
        return False

    second_open, first_open = list(open_price_list[-2:])
    second_candle_close, first_candle_close = list(close_price_list[-2:])

    first_candle_up = first_candle_close > first_open
    second_candle_up = second_candle_close > second_open

    if strict:
        return second_candle_up and first_candle_up

    return second_candle_up or first_candle_up


def stupid_check_downtrend(indicators, aprox, strict=True):
    open_price_list = indicators.open_array
    close_price_list = indicators.close_array

    if not operator.ge(aprox[0], aprox[-1]):
        return False

    prev_open, curr_open = list(open_price_list[-2:])
    prev_candle_close, curr_candle_close = list(close_price_list[-2:])

    curr_candle_down = not curr_candle_close > curr_open
    prev_candle_down = not prev_candle_close > prev_open

    if strict:
        return curr_candle_down and prev_candle_down

    return curr_candle_down or prev_candle_down

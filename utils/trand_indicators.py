import operator

import numpy as np


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

    if not operator.le(aprox[0], aprox[-1]):
        return False

    second_open, first_open = list(df.iloc[-2:][open_indicator])
    second_low, first_low = list(df.iloc[-2:][low_indicator])
    second_candle_close, first_candle_close = list(df.iloc[-2:][close_indicator])
    second_trend_candle, first_trend_candle = list(aprox[-2:])

    first_candle_green = first_candle_close > first_open
    second_candle_green = second_candle_close > second_open

    first_trend_up = first_candle_green
    second_trend_up = second_candle_green

    first_up = first_open >= second_open
    second_up = second_candle_close <= first_candle_close

    first_trend_up = first_trend_up or first_up
    second_trend_up = second_trend_up or second_up

    first_low_continues_trend = first_low > first_trend_candle
    # first_open_continues_trend = first_open > first_trend_candle
    # first_close_continues_trend = first_candle_close > first_trend_candle

    second_low_continues_trend = second_low > second_trend_candle
    # second_open_continues_trend = second_open > second_trend_candle
    # second_close_continues_trend = second_candle_close > second_trend_candle

    first_trend_up = first_trend_up or first_low_continues_trend
    second_trend_up = second_trend_up or second_low_continues_trend

    if aggresive:
        return first_trend_up or second_trend_up

    return first_trend_up and second_trend_up


def check_downtrend(df, aprox, aggresive=False):
    open_indicator = "Open"
    close_indicator = "Close"
    high_indicator = "High"

    if not operator.ge(aprox[0], aprox[-1]):
        return False

    second_open, first_open = list(df.iloc[-2:][open_indicator])
    second_high, first_high = list(df.iloc[-2:][high_indicator])
    second_candle_close, first_candle_close = list(df.iloc[-2:][close_indicator])
    second_trend_candle, first_trend_candle = list(aprox[-2:])

    first_candle_red = not first_candle_close < first_open
    second_candle_red = not second_candle_close < second_open

    first_down = first_open <= second_open
    second_down = second_candle_close >= first_candle_close

    first_trend_down = first_candle_red
    second_trend_down = second_candle_red

    first_trend_down = first_trend_down or first_down
    second_trend_down = second_trend_down or second_down

    first_high_continues_trend = first_trend_candle > first_high
    # first_open_continues_trend = first_open > first_trend_candle
    # first_close_continues_trend = first_candle_close > first_trend_candle

    second_high_continues_trend = second_trend_candle > second_high
    # second_open_continues_trend = second_open > second_trend_candle
    # second_close_continues_trend = second_candle_close > second_trend_candle

    first_trend_down = first_trend_down or first_high_continues_trend
    second_trend_down = second_trend_down or second_high_continues_trend

    if aggresive:
        return first_trend_down or second_trend_down

    return first_trend_down and second_trend_down


def stupid_check_uptrend(df, aprox, strict=True):
    open_indicator = "Open"
    close_indicator = "Close"

    if not operator.le(aprox[0], aprox[-1]):
        return False

    second_open, first_open = list(df.iloc[-2:][open_indicator])
    second_candle_close, first_candle_close = list(df.iloc[-2:][close_indicator])

    first_candle_up = first_candle_close > first_open
    second_candle_up = second_candle_close > second_open

    if strict:
        return second_candle_up and first_candle_up

    return second_candle_up or first_candle_up


def stupid_check_downtrend(df, aprox, strict=True):
    open_indicator = "Open"
    close_indicator = "Close"

    if not operator.ge(aprox[0], aprox[-1]):
        return False

    prev_open, curr_open = list(df.iloc[-2:][open_indicator])
    prev_candle_close, curr_candle_close = list(df.iloc[-2:][close_indicator])

    curr_candle_down = not curr_candle_close > curr_open
    prev_candle_down = not prev_candle_close > prev_open

    if strict:
        return curr_candle_down and prev_candle_down

    return curr_candle_down or prev_candle_down

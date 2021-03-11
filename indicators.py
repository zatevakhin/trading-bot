import numpy as np

def MovingAverage(dataPoints, period):
    if len(dataPoints) > 1:
        return sum(dataPoints[-period:]) / float(len(dataPoints[-period:]))

def Momentum(dataPoints, period=14):
    if len(dataPoints) > (period - 1):
        return dataPoints[-1] * 100 / dataPoints[-period]

def EMA(prices, period):
    x = np.asarray(prices)
    weights = None
    weights = np.exp(np.linspace(-1., 0., period))
    weights /= weights.sum()

    a = np.convolve(x, weights, mode='full')[:len(x)]
    a[:period] = a[period]
    return a

def MACD(prices, nslow=26, nfast=12):
    emaslow = EMA(prices, nslow)
    emafast = EMA(prices, nfast)
    return emaslow, emafast, emafast - emaslow

def RSI(prices, period=14):
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum()/period
    down = -seed[seed < 0].sum()/period
    rs = up/down
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100./(1. + rs)

    for i in range(period, len(prices)):
        delta = deltas[i - 1]  # cause the diff is 1 shorter
        if delta > 0:
                upval = delta
                downval = 0.
        else:
                upval = 0.
                downval = -delta

        up = (up*(period - 1) + upval)/period
        down = (down*(period - 1) + downval)/period
        rs = up/down
        rsi[i] = 100. - 100./(1. + rs)

    if len(prices) > period:
            return rsi[-1]
    else:
            return 50 # output a neutral amount until enough prices in list to calculate RSI

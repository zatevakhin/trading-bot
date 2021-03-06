import numpy as np
import talib as ta


class Indicators:
    def __init__(self):
        self.open = np.array([])
        self.close = np.array([])
        self.high = np.array([])
        self.low = np.array([])
        self.volume = np.array([])
        self.datetime = np.array([])
        self.psar = np.array([])
        self.ema200 = np.array([])
        self.ema50 = np.array([])
        self.ema25 = np.array([])
        self.ema12 = np.array([])
        self.ema6 = np.array([])
        self.rsi = np.array([])
        self.adx = np.array([])
        self.di_plus = np.array([])
        self.di_minus = np.array([])

    @property
    def datetime_array(self) -> np.array:
        return self.datetime

    @datetime_array.setter
    def datetime_array(self, candles: list['Candle']):
        self.datetime = list(map(lambda x: x.t_open, candles))

    @property
    def close_array(self) -> np.array:
        return self.close

    @close_array.setter
    def close_array(self, candles: list['Candle']):
        self.close = np.array(list(map(lambda x: x.p_close, candles)))

    @property
    def open_array(self) -> np.array:
        return self.open

    @open_array.setter
    def open_array(self, candles: list['Candle']):
        self.open = np.array(list(map(lambda x: x.p_open, candles)))

    @property
    def high_array(self) -> np.array:
        return self.high

    @high_array.setter
    def high_array(self, candles: list['Candle']):
        self.high = np.array(list(map(lambda x: x.p_high, candles)))

    @property
    def low_array(self) -> np.array:
        return self.low

    @low_array.setter
    def low_array(self, candles: list['Candle']):
        self.low = np.array(list(map(lambda x: x.p_low, candles)))

    @property
    def volume_array(self) -> np.array:
        return self.volume

    @volume_array.setter
    def volume_array(self, candles: list['Candle']):
        self.volume = np.array(list(map(lambda x: x.volume, candles)))

    @property
    def ema200_array(self) -> np.array:
        if not self.close.size:
            raise ValueError("Set first close prices array!")

        if self.ema200.size != self.close.size:
            self.ema200 = ta.EMA(self.close, timeperiod=200)

        return self.ema200

    @property
    def psar_array(self) -> np.array:
        if not self.high.size:
            raise ValueError("Set first high prices array!")

        if not self.low.size:
            raise ValueError("Set first low prices array!")

        if self.psar.size != self.close.size:
            self.psar = ta.SAR(self.high, self.low, acceleration=0.02, maximum=0.2)

        return self.psar

    @property
    def ema50_array(self) -> np.array:
        if not self.close.size:
            raise ValueError("Set first close prices array!")

        if self.ema50.size != self.close.size:
            self.ema50 = ta.EMA(self.close, timeperiod=50)

        return self.ema50

    @property
    def ema25_array(self) -> np.array:
        if not self.close.size:
            raise ValueError("Set first close prices array!")

        if self.ema25.size != self.close.size:
            self.ema25 = ta.EMA(self.close, timeperiod=25)

        return self.ema25

    @property
    def ema12_array(self) -> np.array:
        if not self.close.size:
            raise ValueError("Set first close prices array!")

        if self.ema12.size != self.close.size:
            self.ema12 = ta.EMA(self.close, timeperiod=12)

        return self.ema12

    @property
    def ema6_array(self) -> np.array:
        if not self.close.size:
            raise ValueError("Set first close prices array!")

        if self.ema6.size != self.close.size:
            self.ema6 = ta.EMA(self.close, timeperiod=6)

        return self.ema6

    @property
    def rsi_array(self) -> np.array:
        if not self.close.size:
            raise ValueError("Set first close prices array!")

        if self.rsi.size != self.close.size:
            self.rsi = ta.RSI(self.close, timeperiod=14)

        return self.rsi

    @property
    def adx_array(self) -> np.array:
        if not self.high.size:
            raise ValueError("Set first high prices array!")

        if not self.low.size:
            raise ValueError("Set first low prices array!")

        if not self.close.size:
            raise ValueError("Set first close prices array!")

        if self.adx.size != self.close.size:
            self.adx = ta.ADX(self.high, self.low, self.close, timeperiod=14)

        return self.adx

    @property
    def di_plus_array(self) -> np.array:
        if not self.high.size:
            raise ValueError("Set first high prices array!")

        if not self.low.size:
            raise ValueError("Set first low prices array!")

        if not self.close.size:
            raise ValueError("Set first close prices array!")

        if self.di_plus.size != self.close.size:
            self.di_plus = ta.PLUS_DI(self.high, self.low, self.close, timeperiod=14)

        return self.di_plus

    @property
    def di_minus_array(self) -> np.array:
        if not self.high.size:
            raise ValueError("Set first high prices array!")

        if not self.low.size:
            raise ValueError("Set first low prices array!")

        if not self.close.size:
            raise ValueError("Set first close prices array!")

        if self.di_minus.size != self.close.size:
            self.di_minus = ta.MINUS_DI(self.high, self.low, self.close, timeperiod=14)

        return self.di_minus

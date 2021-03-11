import requests
import urllib
import time
import hmac, hashlib
import random
from candle import Candle

BINANCE_API_ENDPOINTS = [
    "https://api.binance.com",
    "https://api1.binance.com",
    "https://api2.binance.com",
    "https://api3.binance.com"
]

def interval_adapter(interval):
    return ({
        '300' : '5m'
    }).get(str(interval))

def get_api_endpoint():
    return random.choice(BINANCE_API_ENDPOINTS)

class Binance:
    def __init__(self, api_key, secret):
        self.api_key = str(api_key)
        self.secret = str(secret)


    def api_query(self, endpoint: str, api: str, data: dict = {}):
        ret = requests.get(f"{endpoint}{api}", params=data)
        return ret.json()

    def returnTicker(self, pair):
        params = {"symbol": pair.fmt_binance()}
        return self.api_query(get_api_endpoint(), "/api/v3/ticker/price", params).get("price", None)

    def returnChartData(self, pair: str, interval, start=None, end=None, limit=1000):
        interval = interval_adapter(interval)

        params = {"symbol": pair.fmt_binance(), "interval": interval, "startTime": start * 1000, "endTime": end * 1000, "limit": limit}
        params = {k: v for k, v in params.items() if v is not None}
        binance_candles = self.api_query(get_api_endpoint(), "/api/v3/klines", params)

        candles = []
        for binance_candle in binance_candles:
            (o_time, o, h, l, c, v, c_time, *x) = binance_candle
            candles.append(Candle(timestamp=c_time / 1000, opn=float(o), close=float(c), high=float(h), low=float(l)))

        return candles

    def buy(self, currencyPair, rate, amount, immediate=False):
        # Places a limit buy order in a given market. Required POST parameters are "currencyPair", "rate", and "amount".
        # If successful, the method will return the order number.

        # https://docs.poloniex.com/#buy
        params = {"currencyPair": currencyPair, "rate": rate, "amount": amount}
        if immediate:
            params.update({"immediateOrCancel": int(immediate)})

        return self.api_query(get_api_endpoint(), "buy", params)

    def sell(self, currencyPair, rate, amount):
        # Places a sell order in a given market. Required POST parameters are "currencyPair", "rate", and "amount".
        # If successful, the method will return the order number.

        # https://docs.poloniex.com/#sell
        params = {"currencyPair": currencyPair, "rate": rate, "amount": amount}
        return self.api_query(get_api_endpoint(), "sell", params)

    def cancel(self, currencyPair, orderNumber):
        # Cancels an order you have placed in a given market. Requires exactly one of "orderNumber" or "clientOrderId" POST parameters.
        # If successful, the method will return a success of 1.

        # https://docs.poloniex.com/#cancelorder
        params = {"currencyPair": currencyPair, "orderNumber": orderNumber}
        return self.api_query(get_api_endpoint(), "cancelOrder", params)


import hashlib
import hmac
import time
import urllib

import requests
from loguru import logger

from candle import Candle

POLONIEX_PUBLIC_API = "https://poloniex.com/public"
POLONIEX_PRIVATE_API = "https://poloniex.com/tradingApi"


def createTimeStamp(datestr, fmt="%Y-%m-%d %H:%M:%S"):
    return time.mktime(time.strptime(datestr, fmt))


class ApiQueryError(Exception):
    pass


class Poloniex:
    def __init__(self, api_key, secret):
        self.api_key = str(api_key)
        self.secret = str(secret)

    def api_query(self, api: str, command: str, data: dict = {}):
        ret: requests.Response = None

        if api == POLONIEX_PUBLIC_API:
            params = {"command": command, **data}
            ret = requests.get(f"{api}", params=params)

        elif api == POLONIEX_PRIVATE_API:
            post_data = {"command": command, "nonce": int(time.time() * 1000), **data}
            post_data_quote = urllib.parse.urlencode(post_data)

            sign = hmac.new(str.encode(self.secret, "utf-8"), str.encode(post_data_quote, "utf-8"),
                            hashlib.sha512).hexdigest()

            headers = {"Sign": sign, "Key": self.api_key}

            ret = requests.post(f"{api}", data=post_data, headers=headers)
        else:
            assert (True, "Wat?")

        data = ret.json()

        if 'error' in data:
            raise ApiQueryError(data)

        return data

    def returnTicker(self, pair):
        # https://docs.poloniex.com/#returnticker

        data = self.api_query(POLONIEX_PUBLIC_API, "returnTicker")
        return data.get(pair.fmt_poloniex(), {}).get("last")

    def return24hVolume(self):
        # https://docs.poloniex.com/#return24hvolume
        return self.api_query(POLONIEX_PUBLIC_API, "return24hVolume")

    def returnChartData(self, pair, period, start, end):
        params = {"currencyPair": pair.fmt_poloniex(), "period": period, "start": start, "end": end}
        poloniex_candles = self.api_query(POLONIEX_PUBLIC_API, "returnChartData", params)

        candles = []
        for item in poloniex_candles:
            (t, h, l, o, c) = (item["date"], item["high"], item["low"], item["open"], item["close"])
            candles.append(Candle(timestamp=t, opn=float(o), close=float(c), high=float(h), low=float(l)))

        return candles

    def returnOrderBook(self, pair):
        # https://docs.poloniex.com/#returnorderbook
        params = {"currencyPair": pair.fmt_poloniex()}
        return self.api_query(POLONIEX_PUBLIC_API, "returnOrderBook", params)

    def returnMarketTradeHistory(self, pair):
        # https://docs.poloniex.com/#returntradehistory-public
        params = {"currencyPair": pair.fmt_poloniex()}
        return self.api_query(POLONIEX_PUBLIC_API, "returnTradeHistory", params)

    def returnBalances(self):
        # Returns all of your balances available for trade after having deducted all open orders.
        # { '1CR': '0.00000000', ABY: '0.00000000', ...}

        # https://docs.poloniex.com/#returnbalances
        return self.api_query(POLONIEX_PRIVATE_API, "returnBalances")

    def returnOpenOrders(self, pair):
        # Returns your open orders for a given market, specified by the "currencyPair" POST parameter, e.g. "BTC_ETH".
        #  Set "currencyPair" to "all" to return open orders for all markets.

        # https://docs.poloniex.com/#returnopenorders
        params = {"currencyPair": pair.fmt_poloniex()}
        return self.api_query(POLONIEX_PRIVATE_API, "returnOpenOrders", params)

    def returnTradeHistory(self, pair):
        # Returns your trade history for a given market, specified by the "currencyPair" POST parameter.
        # You may specify "all" as the currencyPair to receive your trade history for all markets.

        # https://docs.poloniex.com/#returntradehistory-private
        params = {"currencyPair": pair.fmt_poloniex()}
        return self.api_query(POLONIEX_PRIVATE_API, "returnTradeHistory", params)

    def buy(self, pair, rate, amount, fill_or_kill=True):
        # Places a limit buy order in a given market. Required POST parameters are "currencyPair", "rate", and "amount".
        # If successful, the method will return the order number.

        # https://docs.poloniex.com/#buy
        params = {"currencyPair": pair.fmt_poloniex(), "rate": rate, "amount": amount}
        if fill_or_kill:
            params.update({"fillOrKill": int(fill_or_kill)})

        return self.api_query(POLONIEX_PRIVATE_API, "buy", params)

    def sell(self, pair, rate, amount):
        # Places a sell order in a given market. Required POST parameters are "currencyPair", "rate", and "amount".
        # If successful, the method will return the order number.

        # https://docs.poloniex.com/#sell
        params = {"currencyPair": pair.fmt_poloniex(), "rate": rate, "amount": amount}
        return self.api_query(POLONIEX_PRIVATE_API, "sell", params)

    def cancel(self, pair, orderNumber):
        # Cancels an order you have placed in a given market. Requires exactly one of "orderNumber" or "clientOrderId" POST parameters.
        # If successful, the method will return a success of 1.

        # https://docs.poloniex.com/#cancelorder
        params = {"currencyPair": pair.fmt_poloniex(), "orderNumber": orderNumber}
        return self.api_query(POLONIEX_PRIVATE_API, "cancelOrder", params)

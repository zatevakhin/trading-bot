import requests
import urllib
import time
import hmac, hashlib

POLONIEX_PUBLIC_API = "https://poloniex.com/public"
POLONIEX_PRIVATE_API = "https://poloniex.com/tradingApi"


def createTimeStamp(datestr, fmt="%Y-%m-%d %H:%M:%S"):
    return time.mktime(time.strptime(datestr, fmt))


class Poloniex:
    def __init__(self, api_key, secret):
        self.api_key = str(api_key)
        self.secret = str(secret)

    def post_process(self, before):
        after = before

        # Add timestamps if there isnt one but is a datetime
        if "return" in after:
            if isinstance(after["return"], list):
                for x in range(0, len(after["return"])):
                    if isinstance(after["return"][x], dict):
                        if "datetime" in after["return"][x] and "timestamp" not in after["return"][x]:
                            after["return"][x]["timestamp"] = float(
                                createTimeStamp(after["return"][x]["datetime"])
                            )

        return after

    def api_query(self, api: str, command: str, data: dict = {}):
        ret: requests.Response = None

        if api == POLONIEX_PUBLIC_API:
            params={"command": command, **data}
            ret = requests.get(f"{api}", params=params)

        elif api == POLONIEX_PRIVATE_API:
            post_data={"command": command, "nonce": int(time.time() * 1000), **data}
            post_data_quote = urllib.parse.urlencode(post_data)

            sign = hmac.new(
                str.encode(self.secret, "utf-8"),
                str.encode(post_data_quote, "utf-8"),
                hashlib.sha512
            ).hexdigest()

            headers = {"Sign": sign, "Key": self.api_key}

            ret = requests.post(f"{api}", data=post_data, headers=headers)
            print(ret.content)
            # post_process
        else:
            assert(True, "Wat?")

        return ret.json()

    def returnTicker(self):
        # https://docs.poloniex.com/#returnticker
        return self.api_query(POLONIEX_PUBLIC_API, "returnTicker")

    def return24hVolume(self):
        # https://docs.poloniex.com/#return24hvolume
        return self.api_query(POLONIEX_PUBLIC_API, "return24hVolume")

    def returnChartData(self, currencyPair, period, start, end):
        params = {"currencyPair": currencyPair, "period": period, "start": start, "end": end}
        return self.api_query(POLONIEX_PUBLIC_API, "returnChartData", params)

    def returnOrderBook(self, currencyPair):
        # https://docs.poloniex.com/#returnorderbook
        params = {"currencyPair": currencyPair}
        return self.api_query(POLONIEX_PUBLIC_API, "returnOrderBook", params)

    def returnMarketTradeHistory(self, currencyPair):
        # https://docs.poloniex.com/#returntradehistory-public
        params = {"currencyPair": currencyPair}
        return self.api_query(POLONIEX_PUBLIC_API, "returnTradeHistory", params)

    def returnBalances(self):
        # Returns all of your balances available for trade after having deducted all open orders.
        # { '1CR': '0.00000000', ABY: '0.00000000', ...}

        # https://docs.poloniex.com/#returnbalances
        return self.api_query(POLONIEX_PRIVATE_API, "returnBalances")

    def returnOpenOrders(self, currencyPair):
        # Returns your open orders for a given market, specified by the "currencyPair" POST parameter, e.g. "BTC_ETH".
        #  Set "currencyPair" to "all" to return open orders for all markets.

        # https://docs.poloniex.com/#returnopenorders
        params = {"currencyPair": currencyPair}
        return self.api_query(POLONIEX_PRIVATE_API, "returnOpenOrders", params)

    def returnTradeHistory(self, currencyPair):
        # Returns your trade history for a given market, specified by the "currencyPair" POST parameter.
        # You may specify "all" as the currencyPair to receive your trade history for all markets.

        # https://docs.poloniex.com/#returntradehistory-private
        params = {"currencyPair": currencyPair}
        return self.api_query(POLONIEX_PRIVATE_API, "returnTradeHistory", params)

    def buy(self, currencyPair, rate, amount, immediate=False):
        # Places a limit buy order in a given market. Required POST parameters are "currencyPair", "rate", and "amount".
        # If successful, the method will return the order number.

        # https://docs.poloniex.com/#buy
        params = {"currencyPair": currencyPair, "rate": rate, "amount": amount}
        if immediate:
            params.update({"immediateOrCancel": int(immediate)})

        return self.api_query(POLONIEX_PRIVATE_API, "buy", params)

    def sell(self, currencyPair, rate, amount):
        # Places a sell order in a given market. Required POST parameters are "currencyPair", "rate", and "amount".
        # If successful, the method will return the order number.

        # https://docs.poloniex.com/#sell
        params = {"currencyPair": currencyPair, "rate": rate, "amount": amount}
        return self.api_query(POLONIEX_PRIVATE_API, "sell", params)

    def cancel(self, currencyPair, orderNumber):
        # Cancels an order you have placed in a given market. Requires exactly one of "orderNumber" or "clientOrderId" POST parameters.
        # If successful, the method will return a success of 1.

        # https://docs.poloniex.com/#cancelorder
        params = {"currencyPair": currencyPair, "orderNumber": orderNumber}
        return self.api_query(POLONIEX_PRIVATE_API, "cancelOrder", params)


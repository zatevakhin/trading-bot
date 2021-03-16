import hashlib
import hmac
import random
import time
from enum import Enum, auto
from urllib.parse import urlencode, urljoin

import requests

import util
from candle import Candle


class BinanceException(Exception):
    def __init__(self, status_code, data):

        self.status_code = status_code
        if data:
            self.code = data['code']
            self.msg = data['msg']
        else:
            self.code = None
            self.msg = None
        message = f"{status_code} [{self.code}] {self.msg}"

        super().__init__(message)


BINANCE_API_ENDPOINTS = [
    "https://api.binance.com", "https://api1.binance.com", "https://api2.binance.com", "https://api3.binance.com"
]


class TimeInForceStatus(Enum):
    GTC = 'GTC'  # Good Til Canceled An order will be on the book unless the order is canceled.
    IOC = 'IOC'  # Immediate Or Cancel An order will try to fill the order as much as it can before the order expires.
    FOK = 'FOK'  # Fill or Kill An order will expire if the full order cannot be filled upon execution.


class CRUDType(Enum):
    GET = auto()
    POST = auto()
    DELETE = auto()


def interval_adapter(interval):
    return util.MAP_CUSTOM_TYPE_TO_BINANCE.get(interval)


def get_api_endpoint():
    return random.choice(BINANCE_API_ENDPOINTS)


class Binance:
    def __init__(self, api_key, secret):
        self.api_key = str(api_key)
        self.secret = str(secret)

        self.exchange_info = self.api_query(get_api_endpoint(), "/api/v3/exchangeInfo")

    def get_symbol_info(self, pair):
        for symbol in self.exchange_info["symbols"]:
            if symbol["symbol"] == pair.fmt_binance():
                return symbol

    def api_query(self, endpoint: str, api: str, data: dict = {}):
        ret = requests.get(f"{endpoint}{api}", params=data)
        return ret.json()

    def api_query_private(self, crudType: CRUDType, command: str, data: dict = {}):
        headers = {'X-MBX-APIKEY': self.api_key}

        data['timestamp'] = int(time.time() * 1000)
        data['recvWindow'] = 5000
        query_string = urlencode(data)
        data['signature'] = hmac.new(self.secret.encode('utf-8'), query_string.encode('utf-8'),
                                     hashlib.sha256).hexdigest()
        url = urljoin(get_api_endpoint(), command)

        if crudType is crudType.POST:
            resp = requests.post(url, headers=headers, params=data)
        elif crudType is crudType.DELETE:
            resp = requests.delete(url, headers=headers, params=data)
        else:
            raise ValueError('WTF type')

        if resp.status_code == 200:
            data = resp.json()
            # print(json.dumps(data, indent=2))
        else:
            raise BinanceException(status_code=resp.status_code, data=resp.json())

        return resp.json()

    def returnTicker(self, pair):
        params = {"symbol": pair.fmt_binance()}
        return self.api_query(get_api_endpoint(), "/api/v3/ticker/price", params).get("price", None)

    def returnChartData(self, pair: str, interval, start=None, end=None, limit=1000):
        interval = interval_adapter(interval)

        params = {
            "symbol": pair.fmt_binance(),
            "interval": interval,
            "startTime": start * 1000,
            "endTime": end * 1000,
            "limit": limit
        }
        params = {k: v for k, v in params.items() if v is not None}
        binance_candles = self.api_query(get_api_endpoint(), "/api/v3/klines", params)

        candles = []
        for binance_candle in binance_candles:
            (o_time, o, h, l, c, v, c_time, *x) = binance_candle
            candles.append(
                Candle(interval=interval,
                       timestamp=c_time / 1000,
                       opn=float(o),
                       close=float(c),
                       high=float(h),
                       low=float(l)))

        return candles

    def buy(self, pair, price, quantity, timeInForceStatus=TimeInForceStatus.FOK):
        params = {
            'symbol': pair.fmt_binance(),
            'side': 'BUY',
            'type': 'LIMIT',
            'timeInForce': timeInForceStatus.value,
            'quantity': quantity,
            'price': price,
        }
        print(params)
        return self.api_query_private(CRUDType.POST, '/api/v3/order', params)

    def sell(self, pair, price, quantity, timeInForceStatus=TimeInForceStatus.GTC):
        params = {
            'symbol': pair.fmt_binance(),
            'side': 'SELL',
            'type': 'LIMIT',
            'timeInForce': timeInForceStatus.value,
            'quantity': quantity,
            'price': price,
        }

        return self.api_query_private(CRUDType.POST, '/api/v3/order', params)

    def cancel(self, pair, orderId):
        PATH = '/api/v3/order'
        params = {'symbol': pair.fmt_binance(), 'orderId': orderId}

        return self.api_query_private(CRUDType.DELETE, '/api/v3/order', params)


# import userconfig
# from customtypes import CurrencyPair

# if __name__ == "__main__":
#     api = Binance(userconfig.BINANCE_API_KEY, userconfig.BINANCE_SECRET)
#     pair = CurrencyPair('RVN', 'USDT')

# print(api.buy(pair, 0.239693, 62.579963))

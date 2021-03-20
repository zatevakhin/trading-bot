import hashlib
import hmac
import random
import time
from urllib.parse import urlencode, urljoin

import requests
from candle import Candle

from exchange_api.customtypes import BinanceFilterError, BinanceQueryError
from exchange_api.utils import binance_filters
from exchange_api.utils.order_convert import convert_binance_to_internal

BINANCE_API_ENDPOINTS = [
    "https://api.binance.com", "https://api1.binance.com", "https://api2.binance.com", "https://api3.binance.com"
]


def get_api_endpoint():
    return random.choice(BINANCE_API_ENDPOINTS)


class Binance:
    def __init__(self, api_key: str, secret: str) -> None:
        self.api_key = str(api_key)
        self.secret = str(secret)
        self.exchange_info = self.exchangeInfo()

    def _api_query(self, endpoint: str, api: str, data: dict = {}) -> dict:
        ret = requests.get(f"{endpoint}{api}", params=data)
        return ret.json()

    def _api_query_private(self, operation: callable, command: str, data: dict = {}) -> dict:
        headers = {'X-MBX-APIKEY': self.api_key}

        data['timestamp'] = int(time.time() * 1000)
        data['recvWindow'] = 5000
        query_string = urlencode(data)
        data['signature'] = hmac.new(self.secret.encode('utf-8'), query_string.encode('utf-8'),
                                     hashlib.sha256).hexdigest()
        url = urljoin(get_api_endpoint(), command)

        resp = operation(url, headers=headers, params=data)

        if resp.status_code != 200:
            raise BinanceQueryError(status_code=resp.status_code, data=resp.json())

        return resp.json()

    def returnTicker(self, symbol: str) -> dict:
        params = {"symbol": symbol}
        return self._api_query(get_api_endpoint(), "/api/v3/ticker/price", params).get("price", None)

    def returnKlines(self,
                     symbol: str,
                     interval: str,
                     startTime: int = None,
                     endTime: int = None,
                     limit: int = 1000) -> list['Candle']:

        received_klines = []
        start_from = startTime

        while start_from < endTime:
            params = {
                "symbol": symbol,
                "interval": interval,
                "startTime": start_from,
                "endTime": endTime,
                "limit": limit
            }

            params = {k: v for k, v in params.items() if v is not None}
            klines = self._api_query(get_api_endpoint(), "/api/v3/klines", params)

            received_klines = [*received_klines, *klines]
            close_time = int(received_klines[len(received_klines) - 1][6])  # 6 - close time
            start_from = close_time

        candles = []
        for kline in received_klines:
            (o_time, o, h, l, c, v, c_time, *x) = kline
            candles.append(
                Candle(interval, timestamp=o_time / 1000, opn=float(o), close=float(c), high=float(h), low=float(l)))

        return candles

    def createBuyOrder(self, symbol: str, price: int, quantity: float, timeInForce: str) -> 'Order':
        passed_price_filter, price = binance_filters.get_price_filter(symbol, self.exchange_info, price)
        if not passed_price_filter:
            raise BinanceFilterError(symbol, price, "Price")

        passed_quantity_filter, quantity = binance_filters.get_quantity_filter(symbol, self.exchange_info, quantity)
        if not passed_quantity_filter:
            raise BinanceFilterError(symbol, quantity, "Quantity")

        params = {
            'symbol': symbol,
            'side': 'BUY',
            'type': 'LIMIT',
            'timeInForce': timeInForce,
            'quantity': quantity,
            'price': price
        }

        order = self._api_query_private(requests.post, '/api/v3/order', params)
        return convert_binance_to_internal(order)

    def createBuyMarketOrder(self, symbol: str, quantity: float) -> 'Order':
        passed_quantity_filter, quantity = binance_filters.get_quantity_filter(symbol, self.exchange_info, quantity)
        if not passed_quantity_filter:
            raise BinanceFilterError(symbol, quantity, "Quantity")

        params = {'symbol': symbol, 'side': 'BUY', 'type': 'MARKET', 'quantity': quantity}

        order = self._api_query_private(requests.post, '/api/v3/order', params)
        return convert_binance_to_internal(order)

    def createSellOrder(self, symbol: str, price: int, quantity: float, timeInForce: str) -> 'Order':
        passed_price_filter, price = binance_filters.get_price_filter(symbol, self.exchange_info, price)
        if not passed_price_filter:
            raise BinanceFilterError(symbol, price, "Price")

        passed_quantity_filter, quantity = binance_filters.get_quantity_filter(symbol, self.exchange_info, quantity)
        if not passed_quantity_filter:
            raise BinanceFilterError(symbol, quantity, "Quantity")

        params = {
            'symbol': symbol,
            'side': 'SELL',
            'type': 'LIMIT',
            'timeInForce': timeInForce,
            'quantity': quantity,
            'price': price
        }

        order = self._api_query_private(requests.post, '/api/v3/order', params)
        return convert_binance_to_internal(order)

    def createSellMarketOrder(self, symbol: str, quantity: float) -> 'Order':
        passed_quantity_filter, quantity = binance_filters.get_quantity_filter(symbol, self.exchange_info, quantity)
        if not passed_quantity_filter:
            raise BinanceFilterError(symbol, quantity, "Quantity")

        params = {'symbol': symbol, 'side': 'SELL', 'type': 'MARKET', 'quantity': quantity}

        order = self._api_query_private(requests.post, '/api/v3/order', params)
        return convert_binance_to_internal(order)

    def cancel(self, symbol: str, orderId: int) -> dict:
        params = {'symbol': symbol, 'orderId': orderId}

        return self._api_query_private(requests.delete, '/api/v3/order', params)

    def exchangeInfo(self) -> dict:
        return self._api_query(get_api_endpoint(), "/api/v3/exchangeInfo")

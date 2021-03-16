import util

from exchange_api.binance import Binance
from exchange_api.customtypes import TimeInForceStatus
from exchange_api.exchange_api_adapter_base import ExchangeApiAdapterBase

MAP_CUSTOM_TIME_IN_FORCE_BINANCE = {
    TimeInForceStatus.GOOD_TIL_CANCELED: "GTC",
    TimeInForceStatus.IMMEDIAGE_OR_CANCEL: "IOC",
    TimeInForceStatus.FILL_OR_KILL: "FOK"
}


def _interval_adapter(interval: 'CandleTimeInterval') -> str:
    return util.MAP_CUSTOM_TYPE_TO_BINANCE.get(interval)


def _pair_adapter(pair: 'CurrencyPair') -> str:
    return f"{pair.buy}{pair.sell}"


def _time_in_force_adapter(time_in_force: TimeInForceStatus) -> str:
    if time_in_force in MAP_CUSTOM_TIME_IN_FORCE_BINANCE:
        return MAP_CUSTOM_TIME_IN_FORCE_POLONIEX[time_in_force]

    return MAP_CUSTOM_TIME_IN_FORCE_POLONIEX[TimeInForceStatus.GOOD_TIL_CANCELED]


class BinanceAdapter(ExchangeApiAdapterBase):
    def __init__(self, api_key: str, secret: str) -> None:
        exchange_api = Binance(api_key, secret)
        super().__init__(exchange_api)

    def returnTicker(self, pair: 'CurrencyPair') -> str:
        pair = _pair_adapter(pair)
        return self.exchange_api.returnTicker(pair)

    def returnChartData(self, pair: 'CurrencyPair', interval: 'CandleTimeInterval', start: int,
                        end: int) -> list['Candle']:
        pair = _pair_adapter(pair)
        interval = _interval_adapter(interval)
        if interval is None:
            raise ValueError("Wrong interval")

        startTime = start * 1000,
        endTime = end * 1000,

        return self.exchange_api.returnKlines(pair, interval, startTime, endTime)

    def buy(self, pair: 'CurrencyPair', price: int, amount: int, timeInForce: TimeInForceStatus) -> list[str]:
        pair = _pair_adapter(pair)
        timeInForce = _time_in_force_adapter(timeInForce)
        return self.exchange_api.createBuyOrder(pair, price, amount, timeInForce)

    def sell(self, pair: 'CurrencyPair', price: int, amount: int) -> list[str]:
        pair = _pair_adapter(pair)
        return self.exchange_api.createSellOrder(pair, price, amount)

    def cancel(self, pair: 'CurrencyPair', orderId: int) -> list[str]:
        pair = _pair_adapter(pair)
        return self.exchange_api.createCancelOrder(pair, orderId)

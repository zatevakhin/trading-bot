import util

from exchange_api.customtypes import TimeInForceStatus
from exchange_api.exchange_api_adapter_base import ExchangeApiAdapterBase
from exchange_api.poloniex import Poloniex

MAP_CUSTOM_TIME_IN_FORCE_POLONIEX = {
    TimeInForceStatus.IMMEDIAGE_OR_CANCEL: "immediateOrCancel",
    TimeInForceStatus.FILL_OR_KILL: "fillOrKill"
}


def _interval_adapter(interval: 'CandleTimeInterval') -> str:
    return util.MAP_CUSTOM_TYPE_TO_POLONIEX.get(interval)


def _pair_adapter(pair: 'CurrencyPair') -> str:
    return f"{pair.sell}_{pair.buy}"


def _time_in_force_adapter(time_in_force: TimeInForceStatus) -> dict[str, bool]:
    mods = {}
    if time_in_force in MAP_CUSTOM_TIME_IN_FORCE_POLONIEX:
        key = MAP_CUSTOM_TIME_IN_FORCE_POLONIEX[time_in_force]
        mods[key] = True

    return mods


class PoloniexAdapter(ExchangeApiAdapterBase):
    def __init__(self, api_key: str, secret: str) -> None:
        exchange_api = Poloniex(api_key, secret)
        super().__init__(exchange_api)

    def returnTicker(self, pair: 'CurrencyPair') -> str:
        pair = _pair_adapter(pair)
        return self.exchange_api.returnTicker(pair)

    def returnChartData(self, pair: 'CurrencyPair', interval: 'CandleTimeInterval', start: int,
                        end: int) -> list['Candle']:
        pair = _pair_adapter(pair)
        interval = _interval_adapter(interval)
        return self.exchange_api.returnChartData(pair, interval, start, end)

    def buy(self, pair: 'CurrencyPair', price: int, amount: int, timeInForce: TimeInForceStatus) -> list[str]:
        pair = _pair_adapter(pair)
        timeInForce = _time_in_force_adapter(pair)
        return self.exchange_api.buy(pair, price, amount, timeInForce)

    def sell(self, pair: 'CurrencyPair', price: int, amount: int) -> list[str]:
        pair = _pair_adapter(pair)
        return self.exchange_api.sell(pair, price, amount)

    def cancel(self, pair: 'CurrencyPair', orderId: int) -> list[str]:
        pair = _pair_adapter(pair)
        return self.exchange_api.cancel(pair, orderId)

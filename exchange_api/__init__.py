import userconfig

from exchange_api.binance_adapter import BinanceAdapter
from exchange_api.poloniex_adapter import PoloniexAdapter


def get_exchange_api(exchange: str):
    if exchange in ["poloniex"]:
        return PoloniexAdapter(userconfig.POLONIEX_API_KEY, userconfig.POLONIEX_SECRET)
    elif exchange in ["binance"]:
        return BinanceAdapter(userconfig.BINANCE_API_KEY, userconfig.BINANCE_SECRET)

    return None

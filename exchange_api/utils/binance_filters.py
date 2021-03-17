import math


def get_symbol_info(pair: str, exchange_info: dict) -> str:
    for symbol in exchange_info["symbols"]:
        if symbol["symbol"] == pair:
            return symbol


def get_base_assert_precision(pair: str, exchange_info: dict) -> dict:
    info = get_symbol_info(pair, exchange_info)
    base_asset_precision = info.get('baseAssetPrecision')
    return base_asset_precision


def get_filter(pair: str, exchange_info: dict, filter_type: str) -> dict:
    info = get_symbol_info(pair, exchange_info)
    for fltr in info.get('filters', []):
        if fltr['filterType'] == filter_type:
            return fltr
    return None


def get_price_filter(pair: str,
                     exchange_info: dict,
                     price: float,
                     should_round_price: bool = True) -> tuple[bool, float]:
    fltr = get_filter(pair, exchange_info, 'PRICE_FILTER')
    base_asset_precision = get_base_assert_precision(pair, exchange_info)

    min_price = round(float(fltr["minPrice"]), base_asset_precision)
    max_price = round(float(fltr["maxPrice"]), base_asset_precision)
    tick_size = round(float(fltr["tickSize"]), base_asset_precision)

    if should_round_price and (tick_size != 0):
        price = round(price - price % tick_size, base_asset_precision)

    min_price_filter = (price >= min_price) if (min_price != 0) else True
    max_price_filter = (price <= max_price) if (max_price != 0) else True
    tick_size_filter = math.isclose((price - min_price) % tick_size, 0, abs_tol=tick_size) if (tick_size != 0) else True

    passed_price_filter = min_price_filter and max_price_filter and tick_size_filter
    return passed_price_filter, price


def get_quantity_filter(pair: str,
                        exchange_info: dict,
                        quantity: float,
                        should_round_quantity: bool = True) -> tuple[bool, float]:
    fltr = get_filter(pair, exchange_info, 'LOT_SIZE')
    base_asset_precision = get_base_assert_precision(pair, exchange_info)

    min_qty = round(float(fltr["minQty"]), base_asset_precision)
    max_qty = round(float(fltr["maxQty"]), base_asset_precision)
    step_size = round(float(fltr["stepSize"]), base_asset_precision)

    if should_round_quantity:
        quantity = round(quantity - quantity % step_size, base_asset_precision)

    min_qty_filter = (quantity >= min_qty)
    max_qty_filter = (quantity <= max_qty)
    step_size_filter = math.isclose((quantity - min_qty) % step_size, 0, abs_tol=step_size)

    passed_quantity_filter = min_qty_filter and max_qty_filter and step_size_filter
    return passed_quantity_filter, quantity

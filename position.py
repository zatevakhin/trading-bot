from termcolor import colored

from basetypes.order import Order, OrderStatus
from candle import Candle
from customtypes import TradeStatus, TradingMode
from exchange_api.customtypes import BinanceQueryError, TimeInForceStatus
from exchange_api.exchange_api_adapter_base import ExchangeApiAdapterBase


class Position(object):
    def __init__(self, pair, budget, mode, exchange, stop_loss_percent):
        self.pair = pair
        self.budget = budget
        self.mode: TradingMode = mode
        self.exchange: ExchangeApiAdapterBase = exchange
        self.status = TradeStatus.CREATED
        self.entry_price = 0
        self.exit_price = 0
        self.open_candle = None
        self.close_candle = None
        self.stop_loss_percent = stop_loss_percent
        self.stop_loss = 0

        self.prop_limit = 0
        self.prop_limit_price = 0

        self.exchange_order: 'Order' = None

        assert (stop_loss_percent <= 100.0 or stop_loss_percent >= 0.0), "Incorrect stop loss limit!"

    def set_prop_limit(self, candle, percent):
        new_prop_limit = (candle.low / 100) * percent

        if new_prop_limit > self.prop_limit:
            print(">>> Prop limit updated: {:0.8f} -> {:0.8f}".format(self.prop_limit, new_prop_limit))
            self.prop_limit = new_prop_limit
            self.prop_limit_price = candle.average

    def open(self, candle: Candle):
        self.open_candle = candle
        self.entry_price = candle.average

        if self.stop_loss_percent:
            self.stop_loss = (self.entry_price / 100) * self.stop_loss_percent

        self.status = TradeStatus.OPEN

        if self.mode in [TradingMode.LIVE]:
            amount = (self.budget / self.entry_price)

            try:
                order = self.exchange.buy(self.pair, self.entry_price, amount, TimeInForceStatus.FILL_OR_KILL)

                if not order.is_status(OrderStatus.FILLED):
                    order = self.exchange.buyMarketPrice(self.pair, amount)

            except BinanceQueryError as e:
                print("buy", e)
                return

            if not order.is_status(OrderStatus.FILLED):
                return

            print(order)

            self.exchange_order = order
            self.entry_price = order.price

        print("Trade", colored("opened", 'green'))

        return True

    def close(self, candle):
        if self.mode in [TradingMode.LIVE]:
            quantity = self.exchange_order.quantity

            try:
                order = self.exchange.sell(self.pair, float(candle.average), quantity, TimeInForceStatus.FILL_OR_KILL)

                if not order.is_status(OrderStatus.FILLED):
                    order = self.exchange.sellMarketPrice(self.pair, quantity)

            except BinanceQueryError as e:
                print("sell", e)
                return

            if not order.is_status(OrderStatus.FILLED):
                return

            print(order)

            self.exit_price = order.price
        else:
            self.exit_price = float(candle.average)

        print("Trade", colored("closed", 'red'))

        self.close_candle = candle
        self.status = TradeStatus.CLOSED

    def tick(self, candle):
        if self.prop_limit:
            if (self.prop_limit_price - self.prop_limit) >= float(candle.average):
                print(colored(">>>", 'green', attrs=["bold"]), "Prop limit")
                self.close(candle)

        if self.stop_loss:
            if (self.entry_price - self.stop_loss) >= float(candle.average):
                print(colored("STOP LOSS", 'red', attrs=["bold"]))
                self.close(candle)

    def profit(self, candle):
        diff = float(candle.average) - self.entry_price
        return (diff * 100) / float(candle.average)

    def showTrade(self):
        entry_price_fmt = colored("{:0.8f}".format(self.entry_price), "grey", attrs=["bold"])
        exit_price_fmt = colored("{:0.8f}".format(self.exit_price), "white", attrs=["bold"])

        tradeStatus = "Entry Price: {}, Status: {} Exit Price: {}".format(entry_price_fmt, self.status.name,
                                                                          exit_price_fmt)

        pp = 0
        if self.status == TradeStatus.CLOSED:
            tradeStatus = tradeStatus + " Profit: "

            color = ['red', 'green'][self.exit_price > self.entry_price]
            diff = self.exit_price - self.entry_price
            profitPercent = (diff * 100) / self.exit_price
            fmt = "{: 3.2f}%".format(profitPercent)

            tradeStatus = f"{tradeStatus} {colored(fmt, color)}"

            print(tradeStatus)

            pp = profitPercent

        return pp

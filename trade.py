from termcolor import colored

from candle import Candle
from customtypes import TradeStatus, TradingMode
from exchange_api.customtypes import ApiQueryError
from exchange_api.exchange_api_adapter_base import ExchangeApiAdapterBase


class Trade(object):
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

        self.bought_amount = None

        assert (stop_loss_percent <= 100.0 or stop_loss_percent >= 0.0), "Incorrect stop loss limit!"

    def open(self, candle: Candle):
        self.open_candle = candle
        self.entry_price = candle.average

        if self.stop_loss_percent:
            self.stop_loss = (self.entry_price / 100) * self.stop_loss_percent

        self.status = TradeStatus.OPEN

        if self.mode in [TradingMode.LIVE]:
            amount = (self.budget / self.entry_price)

            try:
                trade = self.exchange.buy(self.pair, self.entry_price, amount)
            except ApiQueryError:
                return

            print("exchange.buy", trade)

            resulting_trades = trade.get('resultingTrades', [])

            bought_list = map(lambda t: float(t['takerAdjustment']), resulting_trades)
            self.bought_amount = sum(bought_list)

        print("Trade", colored("opened", 'green'))

        return True

    def close(self, candle):
        self.close_candle = candle

        self.status = TradeStatus.CLOSED
        self.exit_price = float(candle.average)
        print("Trade", colored("closed", 'red'))

        if self.mode in [TradingMode.LIVE]:
            print("exchange.sell", self.exchange.sell(self.pair, self.exit_price, self.bought_amount))

    def tick(self, candle):
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

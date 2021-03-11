from customtypes import TradeStatus
from termcolor import colored
from poloniex import Poloniex


class Trade(object):
    def __init__(self, service, currentPrice, stopLossPercent=0, candle=None):
        self.service: Poloniex = service
        self.status = TradeStatus.OPEN
        self.entryPrice = currentPrice
        self.exitPrice = 0.0
        self.open_candle = candle
        self.close_candle = None
        self.stopLoss = 0

        print("Trade", colored("opened", 'green'))

        assert (stopLossPercent <= 100.0 or stopLossPercent >= 0.0), "Incorrect stop loss limit!"

        if stopLossPercent:
            self.stopLoss = (currentPrice / 100) * stopLossPercent

    def close(self, currentPrice, candle=None):
        self.close_candle = candle

        self.status = TradeStatus.CLOSED
        self.exitPrice = float(currentPrice)
        print("Trade", colored("closed", 'red'))

    def tick(self, currentPrice):
        if self.stopLoss:
            if (self.entryPrice - self.stopLoss) >= currentPrice:
                print(colored("STOP LOSS", 'red', attrs=["bold"]))
                self.close(currentPrice)


    def showTrade(self):
        entry_price_fmt = colored("{:0.8f}".format(self.entryPrice), "grey", attrs=["bold"])
        exit_price_fmt = colored("{:0.8f}".format(self.exitPrice), "white", attrs=["bold"])

        tradeStatus = "Entry Price: {}, Status: {} Exit Price: {}".format(
           entry_price_fmt, self.status.name, exit_price_fmt
        )

        pp = 0
        if self.status == TradeStatus.CLOSED:
            tradeStatus = tradeStatus + " Profit: "

            color = ['red', 'green'][self.exitPrice > self.entryPrice]
            diff = self.exitPrice - self.entryPrice
            profitPercent = (diff * 100) / self.exitPrice
            fmt = "{: 3.2f}%".format(profitPercent)

            tradeStatus = f"{tradeStatus} {colored(fmt, color)}"

            print(tradeStatus)

            pp = profitPercent

        return pp

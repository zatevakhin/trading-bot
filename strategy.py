import indicators
from trade import Trade, TradeStatus


from termcolor import colored


class Strategy(object):
    def __init__(self, service):
        self.service = service
        self.prices = []
        self.trades = []
        self.currentPrice = 0
        self.currentClose = 0
        self.numSimulTrades = 1

    def tick(self, candlestick):
        self.currentPrice = float(candlestick.average)
        self.prices.append(self.currentPrice)

        mv_avg = indicators.MovingAverage(self.prices, 15)
        if not mv_avg:
            return

        price_fmt = colored("{:0.8f}".format(candlestick.average), 'cyan')
        mv_avg_fmt = colored("{:0.8f}".format(mv_avg), 'cyan')

        print(f"Price: {price_fmt}\tMoving Average: {mv_avg_fmt}")

        self.evaluatePositions()
        self.updateOpenTrades()
        self.showPositions()

    def evaluatePositions(self):
        openTrades = []
        for trade in self.trades:
            if trade.status == TradeStatus.OPEN:
                openTrades.append(trade)

        if len(openTrades) < self.numSimulTrades:
            if self.currentPrice < indicators.MovingAverage(self.prices, 15):
                self.trades.append(Trade(self.service, self.currentPrice, stopLossPercent=5.0))

        for trade in openTrades:
            if self.currentPrice > indicators.MovingAverage(self.prices, 15):
                trade.close(self.currentPrice)

    def updateOpenTrades(self):
        for trade in self.trades:
            if trade.status == TradeStatus.OPEN:
                trade.tick(self.currentPrice)

    def showPositions(self):
        for trade in self.trades:
            trade.showTrade()

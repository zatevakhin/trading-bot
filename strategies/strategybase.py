from abc import ABC, abstractmethod

from basetypes.indicators import Indicators
from customtypes import TradeStatus
from termcolor import colored
from trade import Trade, TradeStatus

MAX_SIMULTANEOUS_TRADES = 1


class StrategyBase(ABC):
    __strategy__ = None

    def __init__(self, chart, exchange, mode, budget):
        self.chart = chart
        self.exchange = exchange
        self.pair = self.chart.pair
        self.mode = mode
        self.budget = budget
        self.indicators = Indicators()

        self.trades = []

    def get_indicators(self):
        return self.indicators

    def on_preload(self, candles: list['Candle'], num_candles_to_preload: int):
        self.chart.reset(candles[:num_candles_to_preload])

        candles = self.chart.get_candles()

        self.indicators.datetime_array = candles
        self.indicators.open_array = candles
        self.indicators.close_array = candles
        self.indicators.high_array = candles
        self.indicators.low_array = candles

    def on_tick(self, candle: 'Candle') -> dict:
        self.chart.add(candle)

        candles = self.chart.get_candles()

        self.indicators.datetime_array = candles
        self.indicators.open_array = candles
        self.indicators.close_array = candles
        self.indicators.high_array = candles
        self.indicators.low_array = candles

        ret: dict = self.tick()

        self.update_open_trades()

        return ret

    @abstractmethod
    def tick(self) -> dict:
        raise NotImplementedError

    def get_current_candle(self) -> 'Candle':
        return self.chart.get_last_candle()

    def open_trade(self, candle: 'Candle', stop_loss_percent=0) -> bool:
        trade = Trade(self.pair, self.budget, self.mode, self.exchange, stop_loss_percent)

        is_trade_been_open = False

        num_open_trades = len(self.get_trades(open_only=True))

        if num_open_trades < MAX_SIMULTANEOUS_TRADES:
            if trade.open(candle):
                self.trades.append(trade)

                is_trade_been_open = True

        return is_trade_been_open

    def close_trade(self, candle: 'Candle'):
        open_trades = self.get_trades(open_only=True)

        for trade in open_trades:
            if abs(trade.profit(candle)) >= 0.1:
                trade.close(candle)

    def get_trades(self, open_only=False) -> list['Trade']:
        if open_only:
            return list(filter(lambda x: x.status == TradeStatus.OPEN, self.trades))

        return self.trades

    def update_open_trades(self):
        open_trades = self.get_trades(open_only=True)

        for trade in open_trades:
            trade.tick(self.get_current_candle())

    def show_positions(self):
        trades = self.get_trades()

        trades_profit_percent = []

        for trade in trades:
            trades_profit_percent.append(trade.showTrade())

        trades_profit_percent = list(filter(bool, trades_profit_percent))

        if trades_profit_percent:
            profit = sum(trades_profit_percent)
            pf = colored("{: 3.2f}%".format(profit), 'white', attrs=["bold"])

            print(f"Summary profit {pf}")

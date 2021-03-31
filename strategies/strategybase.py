from abc import ABC, abstractmethod

from basetypes.indicators import Indicators
from position import Position
from termcolor import colored


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
        self.position = None

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

        self.update_open_position()

        return ret

    @abstractmethod
    def tick(self) -> dict:
        raise NotImplementedError

    def get_current_candle(self) -> 'Candle':
        return self.chart.get_last_candle()

    def open_trade(self, stop_loss_percent=0) -> bool:
        if self.position:
            return False

        candle = self.get_current_candle()

        pos = Position(self.pair, self.budget, self.mode, self.exchange, stop_loss_percent)

        if pos.open(candle):
            self.position = pos

            return True

        return False

    def close_trade(self):
        if self.position:
            candle = self.get_current_candle()

            self.position.close(candle)
            self.trades.append(self.position)
            self.position = None

    def get_closed_positions(self) -> list['Position']:
        return self.trades

    def get_open_position(self) -> 'Position':
        return self.position

    def update_open_position(self):
        if self.position:
            self.position.tick(self.get_current_candle())

            if self.position.close_candle:
                self.trades.append(self.position)
                self.position = None

    def show_positions(self):
        trades_profit_percent = []

        closed_positions = self.get_closed_positions()
        for trade in closed_positions:
            trades_profit_percent.append(trade.showTrade())

        trades_profit_percent = list(filter(bool, trades_profit_percent))

        if trades_profit_percent:
            profit = sum(trades_profit_percent)
            pf = colored("{: 3.2f}%".format(profit), 'white', attrs=["bold"])
            sf = colored("{}".format(len(closed_positions)), 'yellow')

            print(f"Closed positions: {sf}, Summary profit: {pf}")

import argparse
import time

from termcolor import colored

import util
from chart import Chart
from customtypes import CurrencyPair, TradingMode
from exchange_api import get_exchange_api
from utils.strategy_manager import StrategyManager
from workers.backtest_ticker import BacktestTicker
from workers.live_ticker import LiveTicker
from workers.websocket_live_ticker import WebsocketLiveTicker


class Application:
    def __init__(self, args):

        # Configure Trader
        self.configure_trader(args)

    def configure_trader(self, args):
        self.pair = CurrencyPair(*args.pair.split(","))
        self.exchange = get_exchange_api(args.exchange)
        self.strategies_mgr = StrategyManager("strategies/")

        self.tick = int(args.tick)
        self.backtest_tick = float(args.tick_b)
        self.period = util.interval_mapper(args.period)
        self.preload = int(args.preload)
        self.websocket = args.websocket

        self.mode = util.mode_mapper(args.mode)

        self.start_time = int(args.t_start or 0)
        self.start_end = util.end_time(args.t_end or 0)

        self.chart = Chart(self.exchange, self.pair, None)

        strategy = self.strategies_mgr.get_strategy(args.strategy)

        budget = float(args.budget or 0)

        if not budget and self.mode in [TradingMode.LIVE]:
            raise ValueError("Budget should be more that '0' for live trading.")

        strategy_args = util.parse_strategy_args(args.strategy_args)
        self.strategy = strategy(strategy_args, self.chart, self.exchange, self.mode, budget)

        self.strategy_ticker_thread = None

    def main(self):
        interval = util.interval_mapper_to_seconds(self.period)
        start = int(time.time()) - (interval * self.preload)
        end = int(time.time())

        if self.mode in [TradingMode.BACKTEST]:
            start = self.start_time - (interval * self.preload)
            end = self.start_end

        candles, last_candle = self.exchange.returnChartData(self.pair, self.period, start, end)
        self.strategy.on_preload(candles, self.preload)

        candles = candles[self.preload:]

        if self.mode in [TradingMode.LIVE, TradingMode.LIVE_TEST]:
            if self.websocket:
                self.strategy_ticker_thread = WebsocketLiveTicker(self, last_candle)
            else:
                self.strategy_ticker_thread = LiveTicker(self, last_candle)
        else:
            self.strategy_ticker_thread = BacktestTicker(self, candles)

        self.strategy_ticker_thread.start()

        loop = True
        while loop:
            for _ in range(self.tick):
                try:
                    time.sleep(1)

                    i = input(colored(">>> ", 'yellow'))

                    if i in ["t", "T"]:
                        self.strategy.show_positions()
                    elif i in ["q", "Q"]:
                        raise KeyboardInterrupt
                    elif i in ["o", "O"]:
                        self.strategy.open_trade(stop_loss_percent=1)
                    elif i in ["c", "C"]:
                        self.strategy.close_trade()
                    else:
                        print("Unhandled input: ", i)

                except KeyboardInterrupt:
                    loop = False
                    break

        self.strategy_ticker_thread.stop()
        self.strategy_ticker_thread.join()

        print(colored(">>>", 'red'), "Exit.")

    def chart_tick(self, candle):
        _ = self.strategy.on_tick(candle)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument('--preload', '-l', default=300, help=f"Num old candles to preload.")

    p.add_argument('--mode', '-m', default='live', help=f"Trading modes (backtest, live_test, live)")
    p.add_argument('--t-start', '-S', default=None, help=f"Timespan start (used for backtesting).")
    p.add_argument('--t-end', '-E', default=None, help=f"Timespan end (used for backtesting).")

    p.add_argument('--pair', '-c', default='BTC,USDT', help=f"Currency pair. ex. BTC,USDT.")
    p.add_argument('--tick', '-t', default=30, help=f"Candle update timespan.")
    p.add_argument('--tick-b', default=0.5, help=f"Candle update time for backtesting.")
    p.add_argument('--budget',
                   '-b',
                   default=None,
                   help=f"Budget used to by crypto in currency which second param in pair.")

    p.add_argument('--period', '-p', default='5m', help=f"Timespan width for candle.")
    p.add_argument('--period-help', '-P', action='store_true', help=f"Show period help.")
    p.add_argument('--websocket', '-w', action='store_true', help=f"Use websocket to update candle.")

    p.add_argument('--exchange', '-e', default=None, help=f"Exchange used for trading.")
    p.add_argument('--strategy', '-s', default='default', help=f"Trading strategy.")
    p.add_argument('--strategy-args', '-a', default=None, help=f"Trading strategy arguments. ex. 'a=1;b=2'")

    p.add_argument('--list-exchanges', default=None, help=f"Show available exchanges.")
    p.add_argument('--list-strategies', default=None, help=f"Show available strategies.")

    w = Application(p.parse_args())
    w.main()

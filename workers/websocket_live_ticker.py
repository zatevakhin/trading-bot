import json
import time

import util
from basetypes.exchange import Exchange
from candle import Candle
from websocket import WebSocketApp

from .baseworker import Worker, WorkerStatus

BINANCE_WEBSOCKET = 'wss://stream.binance.com:9443/ws/'


class WebsocketLiveTicker(Worker):
    def __init__(self, app):
        Worker.__init__(self, name="websocket-live-ticker")
        self.app = app
        self.period = app.period
        self.pair = app.pair
        self.chart = app.chart
        self.tick = app.tick
        self.wsapp: 'WebSocketApp' = None
        self.candle: 'Candle' = None

    def stop(self):
        self.wsapp.close()

    def run(self):
        buy = str(self.pair.buy).lower()
        sell = str(self.pair.sell).lower()

        stream = f"{BINANCE_WEBSOCKET}{buy}{sell}@ticker"

        def on_message_cb(wsapp, data):
            self.on_message(json.loads(data))

        def on_open(wsapp, message):
            print(message)

        def on_error(wsapp, message):
            print(message)

        self.wsapp = WebSocketApp(stream, on_message=on_message_cb, on_open=on_open, on_error=on_error)
        self.wsapp.run_forever()

    def on_message(self, data):
        if not self.candle:
            # prev_candle = self.chart.get_candles()[-1]
            # self.candle = Candle(interval=self.period, timestamp=prev_candle.timetamp)
            self.candle = Candle(interval=self.period)

        last_price = float(data.get("c"))
        self.candle.tick(last_price)

        if self.candle.is_closed():
            self.app.chart_tick(self.candle)
            self.candle = Candle(interval=self.period,
                                 opn=self.candle.current,
                                 high=self.candle.current,
                                 low=self.candle.current)

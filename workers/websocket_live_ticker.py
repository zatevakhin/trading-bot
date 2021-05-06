import json

import util
from candle import Candle
from loguru import logger
from websocket import WebSocketApp

from .baseworker import Worker

BINANCE_WEBSOCKET = 'wss://stream.binance.com:9443/ws/'


class WebsocketLiveTicker(Worker):
    def __init__(self, app, last_candle=None):
        Worker.__init__(self, name="websocket-live-ticker")
        self.app = app
        self.period = app.period
        self.pair = app.pair
        self.chart = app.chart
        self.tick = app.tick
        self.wsapp: 'WebSocketApp' = None
        self.candle: 'Candle' = last_candle
        self.reconnect = True

    def stop(self):
        self.reconnect = False
        self.wsapp.close()

    def run(self):
        p = util.MAP_CUSTOM_TYPE_TO_BINANCE.get(self.period)
        logger.info(f"Started: WebsocketLiveTicker (p: {p})")
        buy = str(self.pair.buy).lower()
        sell = str(self.pair.sell).lower()

        stream = f"{BINANCE_WEBSOCKET}{buy}{sell}@ticker"
        stream = f"{BINANCE_WEBSOCKET}{buy}{sell}@kline_{p}"

        def on_message(wsapp, data):
            self.on_message(json.loads(data))

        def on_open(wsapp, message):
            logger.info(message)

        def on_close(wsapp, message):
            logger.info(message)

        def on_error(wsapp, message):
            logger.error(message)

        is_restart = False
        while self.reconnect:
            self.wsapp = WebSocketApp(stream, on_message=on_message, on_open=on_open, on_error=on_error, on_close=on_close)
            logger.success(f"WebSocket app {is_restart and 're-' or ''}starting.")
            self.wsapp.run_forever()
            logger.warning("WebSocket app stopped.")

            is_restart = True

        logger.info("Completly Stopped: WebsocketLiveTicker")

    def on_message(self, data):
        kline = data.get("k")
        t_open = int(int(kline.get("t")) / 1000)
        t_close = int(int(kline.get("T")) / 1000)

        if not self.candle:
            self.candle = Candle(self.period, t_open, t_close)

        if self.candle and not self.candle.t_close:
            self.candle.t_close = t_close

        p_open = float(kline.get("o"))
        p_close = float(kline.get("c"))
        p_high = float(kline.get("h"))
        p_low = float(kline.get("l"))
        volume = float(kline.get("v"))
        is_closed = float(kline.get("x"))

        self.candle.tick(p_open, p_close, p_high, p_low, volume, is_closed)
        self.app.strategy.on_rt_tick(self.candle)

        if self.candle.is_closed():
            self.app.chart_tick(self.candle)
            self.candle = None

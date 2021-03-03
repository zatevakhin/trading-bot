from poloniex import Poloniex
from chart import Chart, getChartData
from strategy import Strategy
from candlestick import Candlestick
from database import Database
import time
import sys

import sql_query as sql


class Cache:
    def __init__(self, db):
        self.db: Database = db

    def select(self, pair, period, start, end) -> list[Candlestick]:
        with self.db.connect() as connection:
            cur = connection.cursor()
            return cur.execute(sql.SQL_SELECT_DATAFRAMES, [pair, period, start, end]).fetchall()

    def insert(self, pair, candle):
        with self.db.connect() as connection:
            cur = connection.cursor()
            cur.execute(sql.SQL_INSER_CURRENCY_PAIR, [pair])

            pair_id = cur.execute(sql.SQL_SELECT_PAIR_ID, [pair]).fetchone().get("id")

            cur.execute(sql.SQL_INSER_DATAFRAME, [
                pair_id, candle.period, candle.timestamp, candle.high, candle.low, candle.open, candle.close
            ])


class Application:
    def __init__(self):
        self.service = Poloniex(None, None)
        self.db = Database("poloniex.db")
        self.cache = Cache(self.db)
        self.pair = "USDT_DOGE"

    def run(self):
        # 300, 900, 1800, 7200, 14400, and 86400
        period = 300

        chart = Chart(self.service, self.pair)
        strategy = Strategy(self.service)

        start = int(time.time()) - (60 * 60 * 24 * 7)
        end = int(time.time())

        chart.reset(getChartData(self.service, self.pair, period, start, end, self.cache))

        for candlestick in chart.getPoints():
            strategy.tick(candlestick)


def main(argv):
    app = Application()
    app.run()

if __name__ == "__main__":
    main(sys.argv[1:])


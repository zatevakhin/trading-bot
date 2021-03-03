

SQL_INSER_DATAFRAME = """
insert or ignore into dataframe (pair_id, period, timestamp, high, low, open, close) values (?, ?, ?, ?, ?, ?, ?)
"""
SQL_INSER_CURRENCY_PAIR = """
insert or ignore into currency_pair (pair) values (?)
"""

SQL_SELECT_PAIR_ID = """select * from currency_pair where pair = ? limit 1;"""

SQL_SELECT_DATAFRAMES = """
select currency_pair.pair, dataframe.period, dataframe.timestamp, dataframe.high, dataframe.low, dataframe.open, dataframe.close from dataframe
    join currency_pair on dataframe.pair_id = currency_pair.id
where
    currency_pair.pair = ? and
    dataframe.period = ? and
    dataframe.timestamp between ? and ?
order by dataframe.timestamp
"""

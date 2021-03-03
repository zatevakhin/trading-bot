# -*- coding: utf-8 -*-

import sqlite3


CREATE_CURRENCY_PAIR_TABLE = """
CREATE TABLE IF NOT EXISTS `currency_pair` (
    `id`    INTEGER     PRIMARY KEY NOT NULL,
    `pair`  VARCHAR(10) UNIQUE      NOT NULL
);"""

CREATE_DATAFRAME_TABLE = """
CREATE TABLE IF NOT EXISTS `dataframe` (
    `id`              INTEGER PRIMARY KEY NOT NULL,
    `pair_id`         INTEGER             NOT NULL,

    `period`          INTEGER             NOT NULL,
    `timestamp`       TIMESTAMP UNIQUE    NOT NULL,

    `high`            REAL                NOT NULL,
    `low`             REAL                NOT NULL,
    `open`            REAL                NOT NULL,
    `close`           REAL                NOT NULL,

    FOREIGN KEY (pair_id) REFERENCES currency_pair(id)
);"""

class Database(object):

    def __init__(self, name):
        self.name = name

        with self.connect() as connection:
            c = connection.cursor()
            c.execute(CREATE_CURRENCY_PAIR_TABLE)
            c.execute(CREATE_DATAFRAME_TABLE)


    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.name)
        connection.row_factory = Database.dict_factory

        connection.text_factory = str

        connection.execute("PRAGMA foreign_keys = ON;")
        connection.execute("PRAGMA encoding = 'UTF-8';")

        return connection

    @staticmethod
    def dict_factory(cursor, row):
        return {col[0]: row[idx] for (idx, col) in enumerate(cursor.description)}

from __future__ import annotations
import sqlite3
import pickle
import atexit
from datetime import datetime


class Connection:
    _instance: Connection = None

    def __init__(self, database_file: str = ":memory:"):
        self._conn = sqlite3.connect(
            database_file, detect_types=sqlite3.PARSE_DECLTYPES
        )
        self._conn.row_factory = Connection._dict_factory
        self._conn.execute("PRAGMA foreign_keys = ON")
        atexit.register(lambda: self._conn.close())
        sqlite3.register_adapter(datetime, lambda date: date.isoformat())
        sqlite3.register_converter(
            "datetime",
            lambda date_bytes: datetime.fromisoformat(date_bytes.decode("utf8")),
        )

    def execute(self, query: str, args: tuple = tuple()):
        with self._conn:
            return self._conn.execute(query, args)

    @staticmethod
    def _dict_factory(cursor: sqlite3.Cursor, row: tuple):
        fields = [column[0] for column in cursor.description]
        return {key: value for key, value in zip(fields, row)}

    @staticmethod
    def register_complex_type(sql_type_name: str, python_type: type):
        sqlite3.register_adapter(python_type, lambda item: pickle.dumps(item))
        sqlite3.register_converter(sql_type_name, lambda bytes: pickle.loads(bytes))

    @property
    def connection(self):
        return self._conn

    @classmethod
    @property
    def instance(cls):
        if cls._instance is None:
            cls._instance = Connection(
                "test.db"
            )  # TODO: fetch db from a settings module or something
        return cls._instance

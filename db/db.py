import pathlib

from playhouse.sqlite_ext import SqliteDatabase

from .module import CategoryModule, NovelModule

pathlib.Path("data").mkdir(parents=True, exist_ok=True)

DATABASE = SqliteDatabase(
    "data/data.db",
    pragmas={
        "journal_mode": "wal",
        "cache_size": -1 * 64000,  # 64MB
        "foreign_keys": 1,
        "ignore_check_constraints": 0,
        "synchronous": 0,
    },
)


class DataBase:
    NovelModule: NovelModule
    CategoryModule: CategoryModule

    def __init__(self) -> None:
        self.database = DATABASE

        self.connect()
        self.database.create_tables([NovelModule, CategoryModule], safe=True)

    def connect(self):
        self.database.connect()
        return self

    def close(self):
        self.database.close()

# flake8: noqa: F401

from .db import DATABASE
from .module import CategoryModule, CategoryType, NovelModule, NovelType



class DataBase:
    NovelModule = NovelModule
    CategoryModule = CategoryModule

    def __init__(self) -> None:
        self.database = DATABASE

        self.connect()
        self.database.create_tables([self.NovelModule, self.CategoryModule], safe=True)
        self.close()

    def connect(self):
        self.database.connect()
        return self

    def close(self):
        self.database.close()
        return self

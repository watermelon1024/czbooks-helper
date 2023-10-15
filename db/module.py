from typing import TypedDict

from playhouse.sqlite_ext import (
    Model,
    IntegerField,
    CharField,
    TextField,
    JSONField,
    ForeignKeyField,
)

from .db import DATABASE


class BaseModel(Model):
    class Meta:
        database = DATABASE


class CategoryModule(BaseModel):
    """category data module"""

    name = CharField(null=False)
    url = CharField(null=False)


class CategoryType(TypedDict):
    """category data model type"""

    name: str
    url: str


class NovelModule(BaseModel):
    """novel data model"""

    novel_id = CharField(null=False, unique=True, index=True)
    titel = CharField(null=False)
    description = TextField(null=False)
    thumbnail = JSONField(null=True)
    author = CharField(null=False)
    state = CharField(null=False)
    last_update = CharField(null=False)
    views = IntegerField(null=False, default=0)
    category = ForeignKeyField(CategoryModule, backref="NovelModule")
    hashtags = TextField(null=False)
    chapter_list = TextField(null=False)
    word_count = IntegerField(null=True)


class NovelType(TypedDict):
    """novel data model type"""

    novel_id: str
    titel: str
    description: str
    thumbnail: dict | None
    author: str
    state: str
    last_update: str
    views: int
    category: CategoryType
    hashtags: str
    chapter_list: str
    word_count: int | None

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
    hashtags_str = TextField(null=False)


class NovelType(TypedDict):
    """novel data model type"""

    novel_id: str
    titel: str
    description: str
    thumbnail: dict
    author: str
    state: str
    last_update: str
    views: int
    category: CategoryModule
    hashtags_str: str

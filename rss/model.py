from datetime import datetime
from typing import NamedTuple


class Category(NamedTuple):
    domain: str  # str or URL
    name: str


class Enclosure(NamedTuple):
    url: str
    mime_type: str
    length: int


class FeedItem(NamedTuple):
    title: str
    description: str
    link: str

    author: str | None
    comments: str | None  # actually comments URL
    guid: tuple[str, bool] | None  # actually an unique URL
    source: tuple[str, str] | None  # second item is an URL
    pub_date: datetime | None
    enclosure: Enclosure | None
    categories: list[Category] | None  # second str is an URL, sort of

    errors: list[str]  # list of errors parsing the item


class Cloud(NamedTuple):
    registerProcedure: str
    protocol: str
    domain: str
    path: int
    port: int


class FeedChannel(NamedTuple):
    title: str
    link: str
    description: str
    items: dict[str, FeedItem]

    language: str | None
    copyright: str | None
    managingEditor: str | None
    webMaster: str | None
    generator: str | None
    docs: str | None
    ttl: int | None
    skipHours: int | None
    skipDays: int | None
    cloud: Cloud | None
    pubDate: datetime | None
    lastBuildDate: datetime | None
    categories: list[Category] | None  # second str is an URL, sort of
    image: None  # TODO
    textinput: None  # TODO

    # PICS rating. Not sure what goes into or if has attrs since not even the
    # w3cshools has an entriy about
    rating: str | None

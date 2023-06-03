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
    categories: set[Category] | None  # second str is an URL, sort of

    errors: list[str]  # list of errors parsing the item


class Cloud(NamedTuple):
    register_procedure: str
    protocol: str
    domain: str
    path: int
    port: int


class TextInput(NamedTuple):
    description: str
    name: str
    link: str
    title: str


class Image(NamedTuple):
    link: str
    title: str
    url: str
    description: str | None
    width: int
    height: int


class FeedChannel(NamedTuple):
    title: str
    link: str
    description: str
    items: dict[str, FeedItem]

    language: str | None
    copyright: str | None
    managing_editor: str | None
    webmaster: str | None
    generator: str | None
    docs: str | None
    ttl: int | None
    skip_hours: int | None
    skip_days: int | None
    cloud: Cloud | None
    pub_date: datetime | None
    last_build_date: datetime | None
    categories: set[Category] | None  # second str is an URL, sort of
    image: Image | None
    text_input: TextInput | None

    # PICS rating. Not sure what goes into or if has attrs since not even the
    # w3cshools has an entry about
    rating: str | None

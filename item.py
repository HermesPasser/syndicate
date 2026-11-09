from __future__ import annotations

from aggregator.connection import Connection
from aggregator.dao.rss.item import ItemDao
from aggregator.dao.rss.item_category import ItemCategoryDao
from rss.model import FeedItem


# TODO: figureout a better name
class Item:

    def __init__(
        self, item: FeedItem, read: bool, state: ItemMetadataDao | None = None
    ) -> None:
        self.item = item
        self._read = read
        self._state = state

    @property
    def read(self):
        return self._read

    def mark(self, mark: bool):
        self._read = mark
        if self._state:
            self._state.mark(self)


# TODO: cascade delete/update
class ItemMetadataDao:
    def __init__(self, connection=Connection.instance):
        self.connection = connection
        self.item_category = ItemCategoryDao(connection)

    def migrate(self):
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS item_metadata (
                id INTEGER AUTO INCREMENT, -- we're not using the foreign as pk here in case we change that in the future
                link TEXT NOT NULL UNIQUE,
                read INTEGER NOT NULL DEFAULT FALSE,
                FOREIGN KEY (link) REFERENCES "item" (link)
            );""")

        self.connection.execute("""
            -- Not sure if we should keep it after finishing developing
            CREATE TRIGGER IF NOT EXISTS automatically_mark_unread
                AFTER INSERT ON item
            BEGIN
                INSERT INTO item_metadata (link) VALUES (new.link);
            END;""")
        self.item_category.migrate()

    def list(self, channel: str, only_unread=False):
        filter = "AND read = FALSE" if only_unread else ""
        cursor = self.connection.execute(
            f"SELECT * FROM item LEFT JOIN item_metadata ON item_metadata.link = item.link WHERE channel_title = ? {filter};",
            (channel,),
        )

        return (self._build(item) for item in cursor)

    def _build(self, item: dict):
        # Keys from the table metadata to be remove before passing to item table model
        keys = ("id", "read")

        return Item(
            ItemDao.build(
                {key: val for key, val in item.items() if key not in keys},
                self.item_category.select_many(item["link"]),
            ),
            item["read"],
            self,
        )

    def mark(self, item: Item):
        self.connection.execute(
            "UPDATE item_metadata SET read = ? WHERE link = ?;",
            (item.read, item.item.link),
        )
        self.connection.connection.commit()

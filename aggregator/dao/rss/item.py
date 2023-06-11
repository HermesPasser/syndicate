from rss.model import FeedItem, FeedChannel, Enclosure
from aggregator.dao.rss.item_category import ItemCategoryDao
from aggregator.connection import Connection


class ItemDao():
   def __init__(self, connection=Connection.instance):
        self.connection = connection
        self.item_category = ItemCategoryDao()

   def migrate(self):
        Connection.register_complex_type("enclosure", Enclosure)
        Connection.register_complex_type("tuple", tuple)

        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS item(
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                link TEXT NOT NULL PRIMARY KEY,

                author TEXT,
                comments TEXT,
                guid tuple,
                source TEXT,
                pub_date datetime,
                enclosure enclosure,

                channel_title TEXT NOT NULL,
                FOREIGN KEY(channel_title) REFERENCES channel(title)
        );"""
        )
        self.item_category.migrate()

   def insert(self, item: FeedItem, channel_title: str):
        as_dict = item._asdict()
        as_dict['channel_title'] = channel_title
        del as_dict["categories"]
        del as_dict["errors"]

        values = as_dict.values()
        rows = ",".join(as_dict.keys())
        placeholders = ",".join(["?"] * len(values))

        self.connection.execute(
            f"INSERT OR IGNORE INTO item({rows}) VALUES ({placeholders});",
            tuple(values),
        )

        self.item_category.insert_many(item)

   def insert_many(self, channel: FeedChannel):
      for item in channel.items.values():
        self.insert(item, channel.title)

   def _build(self, item: dict, categories):
        del item['channel_title']
        return FeedItem(**item, errors=[], categories=set(categories))

   def select_many(self, channel: FeedChannel | str):
        title = channel
        if isinstance(channel, FeedChannel):
            title = channel.title

        cursor = self.connection.execute("SELECT * FROM item WHERE channel_title = ?;", (title, ))
        return (
            self._build(item, self.item_category.select_many(item["link"]))
            for item in cursor
        )

   def delete(self, item: FeedItem):
        self.item_category.delete_many(item)
        self.connection.execute(
            "DELETE FROM item WHERE title = ?;",
            (item.title,),
        )

   def delete_many(self, items: list[FeedItem]):
        for item in items:
            self.delete(item)
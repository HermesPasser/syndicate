from rss.model import Cloud, FeedChannel, TextInput, Image
from aggregator.dao.rss.channel_category import ChannelCategoryDao
from aggregator.dao.rss.item import ItemDao
from aggregator.connection import Connection


class ChannelDao:
    def __init__(self, connection=Connection.instance):
        self.connection = connection
        self.channel_category = ChannelCategoryDao()
        self.item = ItemDao()

    def migrate(self):
        Connection.register_complex_type("textinput", TextInput)
        Connection.register_complex_type("image", Image)
        Connection.register_complex_type("cloud", Cloud)

        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS channel(
                title TEXT NOT NULL PRIMARY KEY,
                link TEXT NOT NULL,
                description TEXT NOT NULL,

                language TEXT,
                copyright TEXT,
                managing_editor TEXT,
                webmaster TEXT,
                generator TEXT,
                docs TEXT,
                rating TEXT,

                ttl INTEGER,
                skip_hours INTEGER,
                skip_days INTEGER,
                cloud cloud,
                pub_date datetime,
                last_build_date datetime,
                image image,
                text_input textinput
        );"""
        )

        self.item.migrate()
        self.channel_category.migrate()

    def insert(self, channel: FeedChannel):
        as_dict = channel._asdict()
        del as_dict["items"]
        del as_dict["categories"]

        values = as_dict.values()
        rows = ",".join(as_dict.keys())
        placeholders = ",".join(["?"] * len(values))

        self.connection.execute(
            f"INSERT OR IGNORE INTO channel({rows}) VALUES ({placeholders})",
            tuple(values),
        )

        self.item.insert_many(channel)
        self.channel_category.insert_many(channel)

    def _build(self, item: dict, categories: list, feed_items: list):
        # TODO: guid may be null
        dict_items = { item.guid[0]: item for item in feed_items}
        return FeedChannel(**item, items=dict_items, categories=set(categories))

    def select_all(self):
        cursor = self.connection.execute("SELECT * FROM channel;")
        return (
            self._build(
                item,
                self.channel_category.select_many(item["title"]),
                self.item.select_many(item["title"])
            )
            for item in cursor
        )

    def delete(self, channel: FeedChannel):
        self.channel_category.delete_many(channel)
        # NOTE: FeedChannel.items is not used since we may not
        #       want to have it populated with all the existing items
        #       that are in the db.
        self.item.delete_many(self.item.select_many(channel))
        self.connection.execute(
            "DELETE FROM channel WHERE title = ?;",
            (channel.title,),
        )

    def delete_many(self, channels: list[FeedChannel]):
        for channel in channels:
            self.delete(channel)

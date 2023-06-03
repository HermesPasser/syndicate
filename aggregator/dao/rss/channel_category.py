from typing import Generator
from rss.model import FeedChannel, Category
from aggregator.dao.rss.category import CategoryDao
from aggregator.connection import Connection


class ChannelCategoryDao:
    def __init__(self, connection=Connection.instance):
        self.connection = connection
        self.category = CategoryDao()

    def migrate(self):
        self.category.migrate()
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS channel_category(
                channel_title TEXT NOT NULL,
                category feedcategory NOT NULL,
                PRIMARY KEY(channel_title, category),
                FOREIGN KEY(channel_title) REFERENCES channel(title),
                FOREIGN KEY(category) REFERENCES category(category)
        );"""
        )

    def insert_many(self, channel: FeedChannel):
        self.category.insert_many(channel.categories)
        for category in channel.categories:
            self.connection.execute(
                """
                INSERT OR IGNORE INTO channel_category (channel_title, category)
                    VALUES(?, ?);
            """,
                (channel.title, category),
            )

    def select_many(
        self, channel: FeedChannel | str
    ) -> Generator[Category, None, None]:
        title = channel
        if isinstance(title, FeedChannel):
            title = channel.title

        cursor = self.connection.execute(
            """
            SELECT channel_category.category FROM channel_category
                LEFT JOIN channel
                    ON channel.title = channel_category.channel_title
                WHERE channel_category.channel_title = ?
        """,
            (title,),
        )
        return (list(item.values())[0] for item in cursor)

    def delete_many(self, channel: FeedChannel):
        self.connection.execute(
            """
            DELETE FROM channel_category WHERE channel_title = ?;
        """,
            (channel.title,),
        )
        self.category.delete_many(channel.categories)

from typing import Generator
from rss.model import FeedItem, Category
from aggregator.dao.rss.category import CategoryDao
from aggregator.connection import Connection


class ItemCategoryDao:
    def __init__(self, connection=Connection.instance):
        self.connection = connection
        self.category = CategoryDao()

    def migrate(self):
        self.category.migrate()
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS item_category(
                item_id TEXT NOT NULL,
                category feedcategory NOT NULL,
                PRIMARY KEY(item_id, category),
                FOREIGN KEY(item_id) REFERENCES item(link),
                FOREIGN KEY(category) REFERENCES category(category)
        );"""
        )

    def insert_many(self, item: FeedItem):
        self.category.insert_many(item.categories)
        for category in item.categories:
            self.connection.execute(
                """
                INSERT OR IGNORE INTO item_category (item_id, category)
                    VALUES(?, ?);
            """,
                (item.link, category),
            )

    def select_many(self, item: FeedItem | str) -> Generator[Category, None, None]:
        item_id = item
        if isinstance(item, FeedItem):
            item_id = item.link

        cursor = self.connection.execute(
            """
            SELECT item_category.category FROM item_category
                LEFT JOIN item
                    ON item.link = item_category.item_id
                WHERE item_category.item_id = ?
        """, (item_id,),
        )
        return (list(item.values())[0] for item in cursor)


    def delete_many(self, item: FeedItem):
        self.connection.execute(
            "DELETE FROM item_category WHERE item_id = ?;",
            (item.link,),
        )
        self.category.delete_many(item.categories)

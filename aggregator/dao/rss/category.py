from aggregator.connection import Connection
from rss.model import Category


class CategoryDao:
    def __init__(self, connection=Connection.instance):
        self.connection = connection

    def migrate(self):
        Connection.register_complex_type("feedcategory", Category)
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS category(
                category feedcategory PRIMARY KEY
        );"""
        )

    def insert_many(self, categories: Category):
        if len(categories) > 0:
            placeholders = ",".join(["(?)"] * len(categories))
            self.connection.execute(
                f"INSERT OR IGNORE INTO category (category) VALUES {placeholders};",
                tuple(categories),
            )

    def delete_many(self, categories: Category):
        for category in categories:
            self.connection.execute(
                """
                DELETE FROM category 
                    WHERE 
                        category = ?
                    AND 
                        NOT EXISTS (SELECT 1 FROM channel_category 
                                        WHERE channel_category.category = category.category
                );
            """,
                (category,),
            )

from aggregator.connection import Connection
from aggregator.dao.rss.category import CategoryDao
from aggregator.dao.rss.channel import ChannelDao
from aggregator.dao.rss.channel_category import ChannelCategoryDao
from aggregator.dao.rss.item import ItemDao
from aggregator.dao.rss.item_category import ItemCategoryDao


def migrate(connection: Connection):
    for dao_type in [
        ChannelDao,
        CategoryDao,
        ChannelCategoryDao,
        ItemCategoryDao,
        ItemDao,
    ]:
        dao_type(connection).migrate()

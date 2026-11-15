from collections.abc import Callable
import datetime
from pathlib import Path
import sqlite3
import uuid
import dateutil
import requests

from aggregator.connection import Connection
from aggregator.dao.rss.channel import ChannelDao
from aggregator.dao.rss.item import ItemDao
from item import Item, ItemMetadataDao
from rss.model import FeedItem
from rss.parser import RssParser


def uuid_from_url(url):
    return str(uuid.uuid3(uuid.NAMESPACE_URL, url))


class FeedError(Exception):
    pass


DB_FOLDER = Path.home().joinpath("syndicate")
DB_FILE = DB_FOLDER.joinpath("syndicate.db")
DB_FOLDER.mkdir(exist_ok=True)


# TODO: mover channel_metadata para fora
# FIXME: folder need to be created
class ChannelList:
    def __init__(self, db_file_name=DB_FILE):
        self.db_file = db_file_name
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()
        # TODO: feed so it may not break the new models until
        #       everything is fixed. Those tables will change
        #       and the duplicated stuff will be removed
        self.channel_table_name = "channel_metadata"
        self._callback = None

        self.item = ItemDao(Connection(str(DB_FILE)))
        self.item_metadata = ItemMetadataDao(Connection(str(DB_FILE)))
        self.channel = ChannelDao(Connection(str(DB_FILE)))

    # TODO: get rid of it
    def channel_link(self, channel_name: str):
        self.cursor.execute(
            f"SELECT feed_link from {self.channel_table_name} WHERE name = ?;",
            (channel_name,),
        )
        result = self.cursor.fetchone()
        return result[0] if result else None

    @property
    def channel_links(self):
        self.cursor.execute(f"SELECT feed_link from {self.channel_table_name}")
        rows = self.cursor.fetchall()
        rows = [row[0] for row in rows]
        return rows

    @property
    def channel_id_and_title(self):
        self.cursor.execute(f"SELECT id, name from {self.channel_table_name}")
        rows = self.cursor.fetchall()
        rows = [(row[0], row[1]) for row in rows]
        return rows

    # TODO: get rid of this id in favor of title of use id in all places
    def get_feed(self, channel_id: str):
        title = self.cursor.execute(
            f"SELECT name from {self.channel_table_name} WHERE id = ?", (channel_id,)
        ).fetchone()[0]
        return list(self.item_metadata.list(title))

    def open(self):
        self._create_db()

    def _create_db(self):
        # TODO: add a display_name since can be edited (the old name columns still needs to be here since will be a PK)
        self.cursor.execute(f"""
			CREATE TABLE IF NOT EXISTS {self.channel_table_name} (
				id 		    VARCHAR(36) NOT NULL PRIMARY KEY,
				name	    VARCHAR(30) NOT NULL,
				feed_link  	VARCHAR(120)
			);
		""")

        self.conn.commit()

    def subscribe(self, callback: Callable[[FeedItem], None]):
        self._callback = callback

    def notify(self, item: FeedItem):
        if self._callback:
            self._callback(item)

    def close(self):
        self.cursor.close()
        self.conn.commit()
        self.conn.close()

    def channel_exists(self, id):
        self.cursor.execute(
            f"SELECT name FROM {self.channel_table_name} WHERE id=?", (id,)
        )
        exists = len(self.cursor.fetchall()) == 1
        return exists

    def add_channel(self, name: str, url: str):
        ch_id = uuid_from_url(url)
        if self.channel_exists(ch_id):
            raise FeedError(f'"{name}" channel (of id: {ch_id}) already exists')

        self.cursor.execute(
            f"INSERT INTO {self.channel_table_name} (id, name, feed_link) VALUES (?,?,?)",
            (ch_id, name, url),
        )

        self.conn.commit()
        return ch_id

    def add_feed_item(self, title, content, link, item_id, date, channel_id):
        # TODO: this is only here yet because i need to figure out what to do with the
        #       tests that rely on it
        ...

    def mark_feed_item_as(self, item: Item, is_read: bool):
        item.mark(is_read)


# FIXME: it seems it doesnt add a second channel to the feed
# i think it does not anymore, check it out


def mili_to_date(float):
    return datetime.datetime.fromtimestamp(float)


def str_date_to_mili(str_date: str) -> int:
    """Construct a POSIX timestamp from a date string."""
    try:
        return int(dateutil.parser.parse((str_date)).timestamp())
    except ValueError as ex:
        print("str_date_to_mili:", str_date, ex)
        return 0


def fetch_rss(url):
    # TODO: error handling when is not 200
    response = requests.get(url, timeout=2)
    response.raise_for_status()
    return response.text


def parse_rss(
    feed: ChannelList, xml_content: str, url: str, channel_name: str = "", notify=False
):
    """Factory that parse the xml contents and upload all to the database"""

    channel = RssParser(xml_content).parse()

    # Upload the old models
    ch_id = uuid_from_url(url)
    channel_name = channel_name or channel.title
    if not feed.channel_exists(ch_id):
        ch_id = feed.add_channel(
            channel_name, url
        )  # feed's url, not the embeded link inside of it

    # TODO: wip  Upload the new models, so we can merge the old way of read/unread and the
    #            new models that have all that sweet extra information
    dao = ChannelDao(Connection(str(DB_FILE)))
    dao.insert(channel)

    if notify:
        for item in channel.items.values():
            feed.notify(item)


def get_new_items_from_channel(url: str, after_date: datetime.datetime):
    # TODO: save those new items in db

    # TODO: add filtering to RssParser.parse()
    #       so we dont have to parse stuff we already parsed
    channel = RssParser(fetch_rss(url)).parse()
    return [
        c
        for c in channel.items.values()
        if c.pub_date is None or c.pub_date >= after_date
    ]

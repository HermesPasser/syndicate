import datetime
import urllib.request as req
from pathlib import Path
import sqlite3
import certifi
import copy
import json
import uuid
import re
import dateutil
import requests

from rss.parser import RssParser

def uuid_from_url(url):
    return str(uuid.uuid3(uuid.NAMESPACE_URL, url))


class FeedError(Exception):
    pass


"""
	channels.json format:
{
	<uuid()>: { title: '', url: '', id: uuid() },
	...
}

	uuid(some_channel):
{
	<id>: {title: '', content: '', read: false, url: '', id: '', link: '', date: '', channel: '<channel_id>' },
	...
}
"""

DB_FOLDER = Path.home().joinpath("syndicate")
DB_FILE = DB_FOLDER.joinpath("syndicate.db")
DB_FOLDER.mkdir(exist_ok=True)

DB_FOLDER.mkdir(exist_ok=True)

# FIXME: folder need to be created
class ChannelList:
    def __init__(self, db_file_name=DB_FILE):
        self.db_file = db_file_name
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()
        self.channel_table_name = "channel"
        self.item_table_name = "item"
        self._callback = None

    @property
    def channel_links(self):
        self.cursor.execute(f"SELECT link from {self.channel_table_name}")
        rows = self.cursor.fetchall()
        rows = [row[0] for row in rows]
        return rows

    @property
    def channel_id_and_title(self):
        self.cursor.execute(f"SELECT id, name from {self.channel_table_name}")
        rows = self.cursor.fetchall()
        rows = [(row[0], row[1]) for row in rows]
        return rows

    def get_feed(self, channel_id):
        self.cursor.execute(
            f"SELECT * FROM {self.item_table_name} WHERE channel = ?", (channel_id,)
        )
        rows = self.cursor.fetchall()

        feed = {}
        for row in rows:
            id = row[0]
            feed[id] = {
                "title": row[1],
                "link": row[3],
                "id": id,
                "date": row[4],
                "read": bool(row[5]),
                "content": row[2],
                "channel": channel_id,
            }

        return feed

    def open(self):
        self._create_db()

    def _create_db(self):
        self.cursor.execute(
            f"""
			CREATE TABLE IF NOT EXISTS {self.channel_table_name} (
				id 		VARCHAR(36) NOT NULL PRIMARY KEY,
				name	VARCHAR(30) NOT NULL,
				link  	VARCHAR(120)
			);
		"""
        )

        self.cursor.execute(
            f"""
			CREATE TABLE IF NOT EXISTS {self.item_table_name} (
				id 		VARCHAR(36) NOT NULL PRIMARY KEY,
				title 	VARCHAR(160) NOT NULL,
				content VARCHAR(4000) NOT NULL,
				link 	VARCHAR(120) NOT NULL,
				date	DATE NOT NULL,
				read	INTEGER DEFAULT FALSE,
				channel	VARCHAR(36) NOT NULL,
				FOREIGN KEY(channel) REFERENCES {self.channel_table_name}(id)
			);
		"""
        )
        self.conn.commit()

    def subscribe(self, callback):
        self._callback = callback

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

    def _feed_exists(self, id, channel_id):
        self.cursor.execute(
            f"SELECT title FROM {self.item_table_name} WHERE id=? and channel=?",
            (id, channel_id),
        )
        exists = len(self.cursor.fetchall()) == 1
        return exists

    def add_channel(self, name, url):
        ch_id = uuid_from_url(url)
        if self.channel_exists(ch_id):
            raise FeedError(f'"{name}" channel (of id: {ch_id}) already exists')

        self.cursor.execute(
            f"INSERT INTO {self.channel_table_name} (id, name, link) VALUES (?,?,?)",
            (ch_id, name, url),
        )
        self.conn.commit()
        return ch_id

    def add_feed_item(self, title, content, link, item_id, date, channel_id):
        if self._feed_exists(item_id, channel_id):
            # ignore if already exists...
            return

        self.cursor.execute(
            f"INSERT INTO {self.item_table_name} (id, title, content, link, date, channel) VALUES (?,?,?,?,?,?)",
            (item_id, title, content, link, date, channel_id),
        )
        self.conn.commit()

        item = {
            "title": title,
            "link": link,
            "id": item_id,
            "date": date,
            "read": False,
            "content": content,
            "channel": channel_id,
        }

        # Notify of new items
        # TODO: since this already is returning the item, maybe create a
        # new method just to check if is a new item and notify? But
        # in this case we should add a func only to load the items
        # that already are on the json.
        # NOTE: since we don't call it on another thread, if the
        # callback does something on the thread and never
        # returns (like  funcs calling other funcs forever..)
        # we may encounter some troubles
        if self._callback is not None:
            self._callback(item)

        return item

    def mark_feed_item_as(self, channel_id, item_id, is_read):
        if not self._feed_exists(item_id, channel_id):
            raise FeedError(
                f"Could not set feed's reading status. The item with {item_id} id does not exists"
            )

        self.cursor.execute(
            f"UPDATE {self.item_table_name} SET read=? WHERE id=?",
            (int(is_read), item_id),
        )
        self.conn.commit()


# FIXME: it seems it doesnt add a second channel to the feed
# i think it does not anymore, check it out


def mili_to_date(float):
    return datetime.fromtimestamp(float)


def str_date_to_mili(str_date: str) -> int:
    """Construct a POSIX timestamp from a date string."""
    try:
        return int(dateutil.parser.parse((str_date)).timestamp())
    except ValueError as ex:
        print("str_date_to_mili:", str_date, ex)
        return 0


def fetch_rss(url):
    # TODO: error handling when is not 200
    return requests.get(url, timeout=2).text


def parse_rss(feed, content, url, channel_name=""):
    channel = RssParser(content).parse()

    ch_id = uuid_from_url(url)
    channel_name = channel_name or channel.title
    if not feed.channel_exists(ch_id):
        ch_id = feed.add_channel(
            channel_name, url
        )  # feed's url, not the embeded link inside of it


    for  item in channel.items.values():
        feed.add_feed_item(
            item.title,
            item.description,
            item.link,
            item.guid[0],
            item.pub_date.timestamp() if item.pub_date else 0,
            ch_id,
        )

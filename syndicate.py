import xml.etree.ElementTree as ET
from datetime import datetime
import urllib.request as req
from pathlib import Path
import certifi
import copy
import json
import uuid


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

class ChannelList:
    def __init__(self):
        self.conf_dir = Path.home().joinpath('syndicate')
        self.channel_list_file = self.conf_dir.joinpath('channels.json')
        self._channel_contents = dict()
        self._feed_contents = dict() # [channel_id][item_id]

    @property
    def channel_contents(self):
        return copy.deepcopy(self._channel_contents)

    def get_feed(self, channel_id):
        return copy.deepcopy(self._feed_contents[channel_id])
    
    def open(self):
        self._create_path()

    def _create_path(self):
        if not self.conf_dir.exists():
            self.conf_dir.mkdir()
            
        if self.channel_list_file.exists():
            self._load_channels()

        for channel_id in self._channel_contents.keys():
            self._load_feed(channel_id)
    
    def _load_channels(self):
        file_exits = self.channel_list_file.exists()
        mode = 'r+' if file_exits else 'w+'

        try:
            with self.channel_list_file.open(mode) as file: 
                self._channel_contents = json.loads(file.read())
        except json.decoder.JSONDecodeError:
            pass

    def _load_feed(self, channel_id):
        path = self.conf_dir.joinpath(channel_id + '.json')

        if not path.exists():
            raise FeedError(f"No feed file found in {str(path)}")

        try:
            with path.open('r+') as file: 
                self._feed_contents[channel_id] = json.loads(file.read())
        except json.decoder.JSONDecodeError:
            # TODO: _load_channels just pass and act like is a empty
            # file if the parsing fail, maybe we should just delete
            # the file and say no items/feed was create to make
            # it work in a similar fashion
            raise FeedError("Bad formated feed file" + str(path))

    def close(self):
        with self.channel_list_file.open('a+') as file:
            txt = json.dumps(self._channel_contents)
            file.truncate(0)
            file.write(txt)

        for item_id, item in self._feed_contents.items():
            filename = self.conf_dir.joinpath(item_id + '.json')
            with filename.open('a+') as file:
                file.truncate(0)
                file.write(json.dumps(item))

    def add_channel(self, title, url):
        id = uuid_from_url(url)
        if id in self._channel_contents:
            return
        
        self._channel_contents[id] = {'title': title, 'url': url, 'syndycate_id': id}
        self._create_channel_file(id)
        return id

    def _create_channel_file(self, id):
        # TODO: this is confusing so is better we creat a new clas
        # that handles the file pointer and its contents

        path = self.conf_dir.joinpath(id + '.json')
        with path.open('w') as _:
            pass
        
        self._feed_contents[id] = {}

    def add_feed_item(self, title, content, link, id, date, channel_id):
        if not self._channel_contents.get(channel_id, False):
            # maybe throw exception here or return false...
            return

        # TODO: maybe check if the item already exists

        item = {
            'title': title,
            'link': link,
            'id': id,
            'date': date,
            'read': False,
            'content': content,
            'channel': channel_id # not really necesary since its the filename
        }

        self._feed_contents[channel_id][id] = item
        return item

    def mark_feed_item_as(self, channel_id, id, is_read):
        if not self._channel_contents.get(channel_id, False):
            return
        
        if not self._channel_contents[channel_id].get(id, False):
            return
        
        item = self._feed_contents[channel_id][id]
        item['read'] = is_read


feed = ChannelList()

# FIXME: it seems it doesnt add a second channel to the feed
# FIXME: it seems guid is recovering date instead

# Do i really need a func to destroy everything? maybe for testing...
# def drop_all():
#     global CONTENTS
#     CONTENTS = {}

def mili_to_date(float):
    return datetime.fromtimestamp(float)

def str_date_to_mili(str):
    """Construct a POSIX timestamp from a date string.

    Accepted format: %a, %d %b %Y %H:%M:%S %z,
    """
    # I'm not sure if all feeds follow this structure
    # If not, put some regex to figure out wich type
    # is and then add more types
    date = datetime.strptime(str,"%a, %d %b %Y %H:%M:%S %z")

    # since datetime is not resializable, let store the 
    # timestamp and convert it back when is need
    return datetime.timestamp(date)


def fetch_rss(url):
    # TODO: error handling when is not 200
    raw_text = ''
    with req.urlopen(url, cafile=certifi.where()) as response:
        raw_text = response.read()

    return raw_text



def parse_rss(text, url):
    # this is the happy path, we need to handle malformated xml
    global feed

    root = ET.fromstring(text)
    channel = root.find('channel')
    channel_name = channel.find('title').text
    ch_id = feed.add_channel(channel_name, url) # feed's url, not the embeded link inside of it

    # FIXME: hack to não explode db with too many channels
    # remove and add way to fetch x last from the db later
    i = 1
    for item in channel.findall('item'):
        feed.add_feed_item(
            item.find('title').text,
            item.find('description').text,
            item.find('link').text,
            item.find('guid').text,
            # since for now were listing it on js, maybe the format should match to
            # make able to be parsed easily to a js date
            str_date_to_mili(item.find('pubDate').text),
            ch_id
        )

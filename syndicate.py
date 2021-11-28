import xml.etree.ElementTree as ET
from datetime import datetime
import urllib.request as req
from pathlib import Path
import certifi
import copy
import json
import uuid
import re

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
	def __init__(self, db_dir_name='syndicate'):
		self.conf_dir = Path.home().joinpath(db_dir_name)
		self.channel_list_file = self.conf_dir.joinpath('channels.json')
		self._channel_contents = dict()
		self._feed_contents = dict() # [channel_id][item_id]
		self._callback = None

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

	def subscribe(self, callback):
		self._callback = callback
	
	def close(self):
		if not self.conf_dir.exists():
			return
		
		with self.channel_list_file.open('a+') as file:
			txt = json.dumps(self._channel_contents)
			file.truncate(0)
			file.write(txt)

		for item_id, item in self._feed_contents.items():
			filename = self.conf_dir.joinpath(item_id + '.json')
			with filename.open('a+') as file:
				file.truncate(0)
				file.write(json.dumps(item))

	def channel_exists(self, id):
		return id in self._channel_contents
	
	def add_channel(self, title, url):
		id = uuid_from_url(url)
		if self.channel_exists(id):
			raise FeedError(f'"{title}" channel (of id: {id}) already exists')
		
		self._channel_contents[id] = {'title': title, 'url': url, 'syndycate_id': id}
		self._create_channel_file(id)
		return id

	def _create_channel_file(self, id):
		# TODO: this is confusing so is better we create a new class
		# that handles the file pointer and its contents

		path = self.conf_dir.joinpath(id + '.json')
		with path.open('w') as _:
			pass
		
		self._feed_contents[id] = {}

	def add_feed_item(self, title, content, link, id, date, channel_id):
		if not self.channel_exists(channel_id):
			raise FeedError(f"Can not add feed because channel with {channel_id} id does not exists")

		if id in self._feed_contents[channel_id]:
			# ignore if already exists...
			return

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

	def mark_feed_item_as(self, channel_id, id, is_read):
		if channel_id not in self._channel_contents:
			raise FeedError(f"Could not set feed's reading status. The channel with {channel_id} id does not exists")
		
		if id not in self._feed_contents[channel_id]:
			raise FeedError(f"Could not set feed's reading status. The item with {id} id does not exists")
		
		item = self._feed_contents[channel_id][id]
		item['read'] = is_read


# FIXME: it seems it doesnt add a second channel to the feed
# i think it does not anymore, check it out

def mili_to_date(float):
	return datetime.fromtimestamp(float)


def str_date_to_mili(str_date):
	"""Construct a POSIX timestamp from a date string.

	Accepted formats: 
		%a, %d %b %Y %H:%M:%S %z,
		%a, %d %b %Y %H:%M:%S %Z
	"""
	base_pattern = '[A-Z]([a-z]{2}|[a-z]), \d{2} [A-Z][a-z]{2} \d{4} \d{2}:\d{2}:\d{2}'
	date_no_offset_or_tz = re.compile(base_pattern + '$')
	date_with_utc_offset = re.compile(base_pattern + ' \+\d{4}') 
	date_with_timezone = re.compile(base_pattern + ' [A-Z]{3}')
	
	strptime_no_z = "%a, %d %b %Y %H:%M:%S"
	strptime_with_offset = strptime_no_z + ' %z'
	strptime_with_timezone = strptime_no_z + ' %Z'
	
	date = 0
	if date_no_offset_or_tz.match(str_date):
		date = datetime.strptime(str_date, strptime_no_z)
	elif date_with_utc_offset.match(str_date):
		date = datetime.strptime(str_date, strptime_with_offset)
	elif date_with_timezone.match(str_date):
		# NOTE: %Z is very buggy (https://bugs.python.org/issue22377)
		# and only recognizes UTC/GMT so lets remove anything else
		# since it can also accepts nothing (well, it WILL treat
		# it as UTC but at this point i dont care *shrugs*)
		if  not (str_date.endswith('UTC') or str_date.endswith('GMT')):
			str_date = str_date[0:-4] 
			date = datetime.strptime(str_date, strptime_no_z)
		else:
			date = datetime.strptime(str_date, strptime_with_timezone)
	else:
		raise ValueError(f"Unkown date format {str_date}")

	# since datetime is not serializable, let store the 
	# timestamp and convert it back when is need
	return datetime.timestamp(date)


def fetch_rss(url):
	# TODO: error handling when is not 200
	raw_text = ''
	with req.urlopen(url, cafile=certifi.where()) as response:
		raw_text = response.read()

	return raw_text



def parse_rss(feed, text, url, channel_name=''):
	# this is the happy path, we need to handle malformated xml

	root = ET.fromstring(text)
	channel = root.find('channel')
	if channel_name == '':
		channel_name = channel.find('title').text

	ch_id = uuid_from_url(url)
	if not feed.channel_exists(ch_id):
		ch_id = feed.add_channel(channel_name, url) # feed's url, not the embeded link inside of it
	
	for item in channel.findall('item'):
		feed.add_feed_item(
			# TODO: can't figure how get <content:encoded> tag with etree, so we're going with description instead
			item.find('title').text,
			item.find('description').text,
			item.find('link').text,
			item.find('guid').text,
			str_date_to_mili(item.find('pubDate').text),
			ch_id
		)

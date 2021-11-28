from syndicate import ChannelList, uuid_from_url
from pathlib import Path
import unittest
import shutil

TEST_FOLDER = 'syndicate_test'

def del_test_db_folder():
	global TEST_FOLDER
	directory = Path.home().joinpath(TEST_FOLDER)
	if directory.exists():
		shutil.rmtree(directory)


class ChannelListTest(unittest.TestCase):
	feed = None

	def setUp(self):
		global TEST_FOLDER
		del_test_db_folder()
		self.feed = ChannelList(TEST_FOLDER)
		self.feed.open()

	def tearDown(self):
		del_test_db_folder()
		self.feed.close()
		self.feed = None
	
	def test_add_channel(self):
		test_url = 'test url'
		self.feed.add_channel('test channel', test_url)

		ch_id = uuid_from_url(test_url)
		exists = self.feed.channel_exists(ch_id)

		self.assertTrue(exists)

	def test_add_channel_not_exists(self):
		self.feed.add_channel('test channel', 'test url')

		ch_id = uuid_from_url('anothertest url')
		exists = self.feed.channel_exists(ch_id)

		self.assertFalse(exists)

	def test_add_item(self):
		test_url = 'test url'
		self.feed.add_channel('test channel', test_url)

		ch_id = uuid_from_url(test_url)
		contents = 'content1'
		title = 'item1'
		link = 'link'
		date = 55555
		uid = 11

		item = self.feed.add_feed_item(title, contents, link, uid, date, ch_id)

		self.assertEqual(item['content'], contents)
		self.assertEqual(item['channel'], ch_id)
		self.assertEqual(item['title'], title)
		self.assertEqual(item['read'], False)
		self.assertEqual(item['link'], link)
		self.assertEqual(item['date'], date)
		self.assertEqual(item['id'], uid)

	def test_mark_item_as_read(self):
		test_url = 'test url'
		ch_id = uuid_from_url(test_url)
		uid = 11

		self.feed.add_channel('test channel', test_url)
		self.feed.add_feed_item('item1', 'content1', 'link', uid, 55555, ch_id)
		self.feed.mark_feed_item_as(ch_id, uid, True)

		items = self.feed.get_feed(ch_id)
		self.assertEqual(items[uid]['read'], True)

	def test_subscribe(self):
		test_url = 'test url'
		ch_id = uuid_from_url(test_url)
		item_name = 'item1'

		self.feed.add_channel('test channel', test_url)

		self.feed.subscribe(lambda item: self.assertEquals(item_name, item['title']))
		self.feed.add_feed_item(item_name, 'content1', 'link', 1, 55555, ch_id)


if __name__ == '__main__':
	unittest.main()

import unittest
from syndicate import ChannelList, uuid_from_url
from rss.parser.tests.test_document import *
from rss.parser.tests.test_item import *


class ChannelListTest(unittest.TestCase):
    feed: ChannelList

    def setUp(self):
        self.feed = ChannelList(":memory:")
        self.feed.open()

    def tearDown(self):
        self.feed.close()

    def test_add_channel(self):
        test_url = "test url"
        self.feed.add_channel("test channel", test_url)

    def test_add_channel(self):
        test_url = "test url"
        self.feed.add_channel("test channel", test_url)

        ch_id = uuid_from_url(test_url)
        exists = self.feed.channel_exists(ch_id)

        self.assertTrue(exists)

    def test_add_channel_not_exists(self):
        self.feed.add_channel("test channel", "test url")

        ch_id = uuid_from_url("anothertest url")
        exists = self.feed.channel_exists(ch_id)

        self.assertFalse(exists)

    def test_add_item(self):
        test_url = "test url"
        self.feed.add_channel("test channel", test_url)

        ch_id = uuid_from_url(test_url)
        contents = "content1"
        title = "item1"
        link = "link"
        date = 55555
        uid = 11

        item = self.feed.add_feed_item(title, contents, link, uid, date, ch_id)

        self.assertEqual(item["content"], contents)
        self.assertEqual(item["channel"], ch_id)
        self.assertEqual(item["title"], title)
        self.assertEqual(item["read"], False)
        self.assertEqual(item["link"], link)
        self.assertEqual(item["date"], date)
        self.assertEqual(item["id"], uid)

    def test_mark_item_as_read(self):
        test_url = "test url"
        ch_id = uuid_from_url(test_url)
        uid = "11"

        self.feed.add_channel("test channel", test_url)
        self.feed.add_feed_item("item1", "content1", "link", uid, 55555, ch_id)
        self.feed.mark_feed_item_as(ch_id, uid, True)

        items = self.feed.get_feed(ch_id)
        self.assertEqual(items[uid]["read"], True)

    def test_subscribe(self):
        test_url = "test url"
        ch_id = uuid_from_url(test_url)
        item_name = "item1"

        self.feed.add_channel("test channel", test_url)

        self.feed.subscribe(lambda item: self.assertEqual(item_name, item["title"]))
        self.feed.add_feed_item(item_name, "content1", "link", 1, 55555, ch_id)

    def test_multiple_channels_with_items(self):
        ch1_url = "test url"
        ch1_id = uuid_from_url(ch1_url)
        ch1_item1_id = "1"
        self.feed.add_channel("test channel", ch1_url)
        self.feed.add_feed_item("ch1 item1", "", "", ch1_item1_id, 0, ch1_id)

        ch2_url = "test url2"
        ch2_id = uuid_from_url(ch2_url)
        ch2_item1_id = "3"
        self.feed.add_channel("test channel", ch2_url)
        self.feed.add_feed_item("ch1 item1", "", "", ch2_item1_id, 0, ch2_id)

        ch1_item2_id = "2"
        self.feed.add_feed_item("ch1 item2", "", "", ch1_item2_id, 0, ch1_id)

        ch1_items = self.feed.get_feed(ch1_id)
        ch2_items = self.feed.get_feed(ch2_id)

        self.assertEqual(len(ch1_items.keys()), 2)
        self.assertEqual(ch1_items[ch1_item1_id]["id"], ch1_item1_id)
        self.assertEqual(ch1_items[ch1_item2_id]["id"], ch1_item2_id)
        self.assertEqual(ch2_items[ch2_item1_id]["id"], ch2_item1_id)


if __name__ == "__main__":
    unittest.main()

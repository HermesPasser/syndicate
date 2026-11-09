import unittest

from cli import build_parser


class RssCliParserTests(unittest.TestCase):
    def setUp(self):
        self.parser = build_parser()

    def parse(self, *args):
        return self.parser.parse_args(args)

    def test_no_arguments_defaults_to_home_list(self):
        args = self.parse()
        self.assertEqual(args.resource, "channel")
        self.assertEqual(args.action, "list")

    def test_channel_add(self):
        args = self.parse(
            "channel", "add", "https://example.com/feed.xml", "--name", "Example"
        )
        self.assertEqual(args.resource, "channel")
        self.assertEqual(args.action, "add")
        self.assertEqual(args.url, "https://example.com/feed.xml")
        self.assertEqual(args.name, "Example")

    def test_channel_refresh_all(self):
        args = self.parse("channel", "refresh")
        self.assertIsNone(args.channel)

    def test_channel_refresh_one(self):
        args = self.parse("channel", "refresh", "Example")
        self.assertEqual(args.channel, "Example")

    def test_item_list_filters_and_limit(self):
        args = self.parse("item", "list", "Example", "--unread", "--limit", "10")
        self.assertEqual(args.resource, "item")
        self.assertEqual(args.action, "list")
        self.assertEqual(args.channel, "Example")
        self.assertTrue(args.unread)
        self.assertEqual(args.limit, 10)

    def test_item_read(self):
        args = self.parse("item", "read", "item-123")
        self.assertEqual(args.action, "read")
        self.assertEqual(args.id, "item-123")

    def test_mark_all_read_without_channel(self):
        args = self.parse("item", "mark-all-read")
        self.assertIsNone(args.channel)

    def test_search_with_channel(self):
        args = self.parse("search", "python", "--channel", "Example")
        self.assertEqual(args.term, "python")
        self.assertEqual(args.channel, "Example")

    def test_channel_action_is_required(self):
        with self.assertRaises(SystemExit):
            self.parse("channel")

    def test_item_download(self):
        args = self.parse("item", "download", "item-123")
        self.assertEqual(args.action, "download")
        self.assertEqual(args.id, "item-123")
        self.assertIsNone(args.output)

    def test_item_download_with_output(self):
        args = self.parse("item", "download", "item-123", "--output", "episode.mp3")
        self.assertEqual(args.action, "download")
        self.assertEqual(args.id, "item-123")
        self.assertEqual(args.output, "episode.mp3")


if __name__ == "__main__":
    unittest.main()

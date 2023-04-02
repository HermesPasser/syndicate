import unittest
from pathlib import Path
from pprint import pformat
from rss.parser import RssParser, model


class RssParserTest(unittest.TestCase):
    maxDiff = None

    def namedtuple_with_optional(self, named_tuple, kwargs: dict):
        as_dict = dict(map(lambda field: (field, None), named_tuple._fields))
        return named_tuple(**{**as_dict, **kwargs})

    def assertNamedtupleEqual(self, t0, t1):
        # We _could_ compare the tuples bare but considering its length,
        # the diff would be truncated making seeing the actuall field
        # difference that makes the test fail impossible to see, so we
        # format with each field in one line.
        self.assertEqual(pformat(t0._asdict()), pformat(t1._asdict()))

    def test_can_parse_channel_with_only_required_elements(self):
        given = RssParser(
            """
            <rss version="2.0">
                <channel>
                    <title>Channel Title</title>
                    <link>https://test.test</link>
                    <description>Sample description</description>
                </channel>
            </rss>
        """
        ).parse()

        expected = self.namedtuple_with_optional(
            model.FeedChannel,
            {
                "title": "Channel Title",
                "link": "https://test.test",
                "description": "Sample description",
                "categories": [],
                "items": {},
            },
        )

        self.assertNamedtupleEqual(given, expected)

    def test_can_parse_channel_item_with_only_required_elements(self):
        given = RssParser(
            """
            <rss version="2.0">
                <channel>
                    <title>Channel Title</title>
                    <link>https://test.test</link>
                    <description>Sample description</description>
                    <item>
                        <title>Item Title</title>
                        <link>http://test.test</link>
                        <guid>http://test.test/0000</guid>
                        <description>description</description>                        
                    </item>
                </channel>
            </rss>
        """
        ).parse()

        item_id = "http://test.test/0000"
        expected_item = self.namedtuple_with_optional(
            model.FeedItem,
            {
                "title": "Item Title",
                "link": "http://test.test",
                "description": "description",
                "guid": (item_id, True),
                "categories": [],
                "errors": [],
            },
        )
        expected_ch = self.namedtuple_with_optional(
            model.FeedChannel,
            {
                "title": "Channel Title",
                "link": "https://test.test",
                "description": "Sample description",
                "categories": [],
                "items": {item_id: expected_item},
            },
        )

        self.assertEqual(len(given.items), 1)
        self.assertNamedtupleEqual(given, expected_ch)

    def test_parsing_channel_item_does_not_overshadow_element_with_xmlns(self):
        given = RssParser(
            """
            <rss xmlns:atom="http://www.w3.org/2005/Atom" version="2.0">
                <channel>
                    <title>Channel Title</title>
                    <link>https://test.test</link>

                    <description>Sample description</description>
                    <item>
                        <title>Item Title</title>
                        <atom:link href="http://test.t/category/podcast/feed/" rel="self" type="application/rss+xml"/>
                        <link>http://test.test</link>
                        <guid>http://test.test/0000</guid>
                        <description>description</description>                        
                    </item>
                </channel>
            </rss>
        """
        ).parse()

        item_id = "http://test.test/0000"
        self.assertEqual(len(given.items), 1)
        self.assertEqual(given.items[item_id].link, "http://test.test")

    def test_parsing_channel_item_uses_link_as_guid_fallback(self):
        given = RssParser(
            """
            <rss version="2.0">
                <channel>
                    <title>Channel Title</title>
                    <link>https://test.test</link>

                    <description>Sample description</description>
                    <item>
                        <title>Item Title</title>
                        <link>http://test.test</link>
                        <description>description</description>                        
                    </item>
                </channel>
            </rss>
        """
        ).parse()

        item_id = "http://test.test"
        self.assertEqual(len(given.items), 1)
        self.assertEqual(given.items[item_id].link, item_id)
        self.assertEqual(given.items[item_id].guid, (item_id, False))

    def test_parsing_channel_item_guid_permalink_as_default(self):
        given = RssParser(
            """
            <rss version="2.0">
                <channel>
                    <title>Channel Title</title>
                    <link>https://test.test</link>

                    <description>Sample description</description>
                    <item>
                        <title>Item Title</title>
                        <link>http://test.test</link>
                        <guid>http://test.test/0000</guid>
                        <description>description</description>                        
                    </item>
                </channel>
            </rss>
        """
        ).parse()

        item_id = "http://test.test/0000"
        self.assertEqual(given.items[item_id].guid, (item_id, True))

    def test_parsing_channel_item_guid_permalink(self):
        given = RssParser(
            """
            <rss version="2.0">
                <channel>
                    <title>Channel Title</title>
                    <link>https://test.test</link>

                    <description>Sample description</description>
                    <item>
                        <title>Item Title</title>
                        <link>http://test.test</link>
                        <guid isPermaLink>http://test.test/0000</guid>
                        <description>description</description>                        
                    </item>
                </channel>
            </rss>
        """
        ).parse()

        item_id = "http://test.test/0000"
        self.assertEqual(given.items[item_id].guid, (item_id, True))

    def test_parsing_channel_item_guid_not_permalink(self):
        given = RssParser(
            """
            <rss version="2.0">
                <channel>
                    <title>Channel Title</title>
                    <link>https://test.test</link>

                    <description>Sample description</description>
                    <item>
                        <title>Item Title</title>
                        <link>http://test.test</link>
                        <guid isPermaLink="false">http://test.test/0000</guid>
                        <description>description</description>                        
                    </item>
                </channel>
            </rss>
        """
        ).parse()

        item_id = "http://test.test/0000"
        self.assertEqual(given.items[item_id].guid, (item_id, False))

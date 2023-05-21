from rss import model
from rss.parser import RssParser
from rss.parser.item import RssItemParser
from rss.parser.tests.test_base import RssParserBaseTest
from xml.parser import XmlParser


class RssParserItemTest(RssParserBaseTest):
    def parse_item(self, content):
        return RssItemParser(XmlParser.parse(content)).parse()

    def test_can_parse_channel_item_with_only_required_elements(self):
        given = self.parse_item(
            """
            <rss version="2.0">
				<item>
					<title>Item Title</title>
					<link>http://test.test</link>
					<guid>http://test.test/0000</guid>
					<description>description</description>
				</item>
            </rss>
        """
        )

        expected = self.namedtuple_with_optional(
            model.FeedItem,
            {
                "title": "Item Title",
                "link": "http://test.test",
                "description": "description",
                "guid": ("http://test.test/0000", True),
                "categories": [],
                "errors": [],
            },
        )

        self.assertNamedtupleEqual(given, expected)

    def test_parsing_channel_item_does_not_overshadow_element_with_xmlns(self):
        given = self.parse_item(
            """
			<rss xmlns:atom="http://www.w3.org/2005/Atom" version="2.0">
				<item>
					<title>Item Title</title>
					<atom:link href="http://test.t/category/podcast/feed/" rel="self" type="application/rss+xml"/>
					<link>http://test.test</link>
					<guid>http://test.test/0000</guid>
					<description>description</description>
				</item>
			</rss>
		"""
        )
        self.assertEqual(given.link, "http://test.test")

    def test_parsing_channel_item_uses_link_as_guid_fallback(self):
        given = self.parse_item(
            """
				<rss version="2.0">
					<item>
						<title>Item Title</title>
						<link>http://test.test</link>
						<description>description</description>
					</item>
				</rss>
			"""
        )

        link = "http://test.test"
        self.assertEqual(given.link, link)
        self.assertEqual(given.guid, (link, False))

    def test_parsing_channel_item_guid_permalink_as_default(self):
        given = self.parse_item(
            """
            <rss version="2.0">
				<item>
					<title>Item Title</title>
					<link>http://test.test</link>
					<guid>http://test.test/0000</guid>
					<description>description</description>
				</item>
            </rss>
        """
        )

        item_id = "http://test.test/0000"
        self.assertEqual(given.guid, (item_id, True))

    def test_parsing_channel_item_guid_permalink(self):
        given = self.parse_item(
            """
            <rss version="2.0">
				<item>
					<title>Item Title</title>
					<link>http://test.test</link>
					<guid isPermaLink>http://test.test/0000</guid>
					<description>description</description>
				</item>
            </rss>
        """
        )

        item_id = "http://test.test/0000"
        self.assertEqual(given.guid, (item_id, True))

    def test_parsing_channel_item_guid_not_permalink(self):
        given = self.parse_item(
            """
            <rss version="2.0">
				<item>
					<title>Item Title</title>
					<link>http://test.test</link>
					<guid isPermaLink="false">http://test.test/0000</guid>
					<description>description</description>
				</item>
            </rss>
        """
        )

        item_id = "http://test.test/0000"
        self.assertEqual(given.guid, (item_id, False))

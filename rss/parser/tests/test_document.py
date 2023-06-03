from rss import model
from rss.parser import RssParser
from rss.parser.tests.test_base import RssParserBaseTest


class RssParserTest(RssParserBaseTest):
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
                "categories": set(),
                "items": {},
            },
        )

        self.assertNamedtupleEqual(given, expected)

    def test_parsing_channel_image_required_elements(self):
        given = RssParser(
            """
            <rss version="2.0">
                <channel>
                    <title>Channel Title</title>
                    <link>https://test.test</link>

                    <description>Sample description</description>
                    <image>
                        <url>https://www.test.test/images/logo.gif</url>
                        <title>Image title</title>
                        <link>https://www.test.test/</link>
                    </image>
                </channel>
            </rss>
        """
        ).parse()

        self.assertEqual(given.image.url, "https://www.test.test/images/logo.gif")
        self.assertEqual(given.image.title, "Image title")
        self.assertEqual(given.image.link, "https://www.test.test/")
        self.assertEqual(given.image.height, 31)
        self.assertEqual(given.image.width, 88)
        self.assertEqual(given.image.description, None)

    def test_parsing_channel_image_optional_elements(self):
        given = RssParser(
            """
            <rss version="2.0">
                <channel>
                    <title>Channel Title</title>
                    <link>https://test.test</link>

                    <description>Sample description</description>
                    <image>
                        <url>https://www.test.test/images/logo.gif</url>
                        <title>Image title</title>
                        <description>this describes the image</description>
                        <link>https://www.test.test/</link>
                        <height>22</height>
                        <width>55</width>
                    </image>
                </channel>
            </rss>
        """
        ).parse()

        self.assertEqual(given.image.url, "https://www.test.test/images/logo.gif")
        self.assertEqual(given.image.title, "Image title")
        self.assertEqual(given.image.link, "https://www.test.test/")
        self.assertEqual(given.image.height, 22)
        self.assertEqual(given.image.width, 55)
        self.assertEqual(given.image.description, "this describes the image")

    def test_parsing_channel_textfield(self):
        given = RssParser(
            """
            <rss version="2.0">
                <channel>
                    <title>Channel Title</title>
                    <link>https://test.test</link>

                    <description>Sample description</description>
                    <textinput>
                        <title>Title</title>
                        <description>Search Google</description>
                        <link>https://test.test/foo</link>
                        <name>Name</name>
                    </textinput>
                </channel>
            </rss>
        """
        ).parse()

        self.assertEqual(given.text_input.name, "Name")
        self.assertEqual(given.text_input.title, "Title")
        self.assertEqual(given.text_input.link, "https://test.test/foo")
        self.assertEqual(given.text_input.description, "Search Google")

    def test_parse_channel_items(self):
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
                    <item>
                        <title>Item2Title</title>
                        <link>http://test.two</link>
                        <guid>http://test.two/0001</guid>
                        <description>description of item 2</description>
                    </item>
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
                "categories": set(),
                "items": {
                    "http://test.test/0000": self.namedtuple_with_optional(
                        model.FeedItem,
                        {
                            "title": "Item Title",
                            "link": "http://test.test",
                            "description": "description",
                            "guid": ("http://test.test/0000", True),
                            "categories": set(),
                            "errors": [],
                        },
                    ),
                    "http://test.two/0001": self.namedtuple_with_optional(
                        model.FeedItem,
                        {
                            "title": "Item2Title",
                            "link": "http://test.two",
                            "description": "description of item 2",
                            "guid": ("http://test.two/0001", True),
                            "categories": set(),
                            "errors": [],
                        },
                    ),
                },
            },
        )

        self.assertEqual(len(given.items), 2)
        self.assertNamedtupleEqual(given, expected)

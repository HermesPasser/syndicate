from dateutil import parser as dateutil_parser
from xml_parser.parser import XmlParser
from rss import model
from rss.parser.item import RssItemParser
from rss.parser.category import RssCategoryParser


# https://www.rssboard.org/rss-specification, https://www.w3schools.com/xml/xml_rss.asp


class RssParser:
    "Naive rss parser that does the minimum validation on the rss payload that ignores namespaced elements"

    def __init__(self, xml: str):
        self._xml_content = xml
        self._root = None

    @property
    def xml(self, value: str):
        self._xml_content = value

    def _parse_channel(self):
        # TODO: make this a property so we dont need to pass it everywhere
        channel_element = self._root.select_one("channel")

        # https://www.rssboard.org/rss-specification#requiredChannelElements
        # This element is REQUIRED and MUST contain three child elements:
        # description, link and title.
        title = channel_element.select_one("title").text
        link = channel_element.select_one("link").text
        desc = channel_element.select_one("description").text
        return model.FeedChannel(
            title=title,
            description=desc,
            link=link,
            # https://www.rssboard.org/rss-specification#optionalChannelElements
            # The channel MAY contain each of the following OPTIONAL elements:
            language=channel_element.select_content("language"),
            copyright=channel_element.select_content("copyright"),
            managing_editor=channel_element.select_content("managingEditor"),
            webmaster=channel_element.select_content("webMaster"),
            generator=channel_element.select_content("generator"),
            docs=channel_element.select_content("docs"),
            rating=channel_element.select_content("rating"),
            ttl=channel_element.select_content("ttl", cast_to=int),
            skip_hours=channel_element.select_content("skipHours", cast_to=int),
            skip_days=channel_element.select_content("skipDays", cast_to=int),
            pub_date=channel_element.select_content(
                "pubDate", cast_to=dateutil_parser.parse
            ),
            last_build_date=channel_element.select_content(
                "lastBuildDate", cast_to=dateutil_parser.parse
            ),
            categories=RssCategoryParser(channel_element).parse(),
            cloud=self._parse_cloud(channel_element.select_one("cloud")),
            image=self._parse_image(channel_element.select_one("image")),
            text_input=self._parse_textinput(channel_element.select_one("textinput")),
            items={},
        )

    def _parse_cloud(self, cloud_element):
        # https://www.rssboard.org/rss-specification#ltcloudgtSubelementOfLtchannelgt
        # It specifies a web service that supports the rssCloud interface which can be
        # implemented in HTTP-POST, XML-RPC or SOAP 1.1.

        if not cloud_element:
            return None

        return model.Cloud(
            domain=cloud_element.get("domain"),
            path=cloud_element.get("path"),
            # this should be an enumeration since there is only 3 possible values
            protocol=cloud_element.get("protocol"),
            register_procedure=cloud_element.get("registerProcedure"),
            port=int(cloud_element.get("port")),
        )

    def _parse_image(self, image_element):
        if not image_element:
            return None

        # The image must be of type GIF, JPEG or PNG
        return model.Image(
            # Required
            link=image_element.select_one("link").text,
            url=image_element.select_one("url").text,
            title=image_element.select_one("title").text,
            description=image_element.select_content("description"),
            # Optional. Defines the height of the image. Default is 31. Maximum value is 400
            height=image_element.select_content("height", cast_to=int) or 31,
            # Optional. Defines the width of the image. Default is 88. Maximum value is 144
            width=image_element.select_content("width", cast_to=int) or 88,
        )

    def _parse_textinput(self, textinput_element):
        if not textinput_element:
            return None

        return model.TextInput(
            description=textinput_element.select_one("description").text,
            name=textinput_element.select_one("name").text,
            link=textinput_element.select_one("link").text,
            title=textinput_element.select_one("title").text,
        )

    def _parse_items(self) -> list[model.FeedItem]:
        # A channel may contain any number of <item>s.
        items = []

        for item_element in self._root.select("channel item"):
            items.append(RssItemParser(item_element).parse())

        return items

    def parse(self):
        self._root = XmlParser.parse(self._xml_content)
        channel = self._parse_channel()
        for item in self._parse_items():
            # TODO: guid may be null
            channel.items[item.guid[0]] = item

        return channel

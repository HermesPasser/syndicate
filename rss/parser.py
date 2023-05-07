from dateutil import parser as dateutil_parser
from bs4 import BeautifulSoup
from rss import model

# TODO: move item parsing for its own subclass since we'll need to test it
#      so it shouldn't remain as an private method.

# https://www.rssboard.org/rss-specification, https://www.w3schools.com/xml/xml_rss.asp


class RssParser:
    "Naive rss parser that does the minimum validation on the rss payload that ignores namespaced elements"

    def __init__(self, xml: str):
        self._xml_content = xml
        self._root = None

    @property
    def xml(self, value: str):
        self._xml_content = value

    def _get_one_or_none(self, element, selector, cast_to=None):
        if item := element.select_one(selector):
            if cast_to:
                return cast_to(item.text)
            return item.text
        return None

    def _parse_channel(self):
        # TODO: make this a property so we dont need to pass it everywhere
        channel_element = self._root.select_one("channel")

        # https://www.rssboard.org/rss-specification#requiredChannelElements
        # This element is REQUIRED and MUST contain three child elements:
        # description, link and title.
        title = channel_element.select_one("|title").text
        link = channel_element.select_one("|link").text
        desc = channel_element.select_one("|description").text

        return model.FeedChannel(
            title=title,
            description=desc,
            link=link,
            # https://www.rssboard.org/rss-specification#optionalChannelElements
            # The channel MAY contain each of the following OPTIONAL elements:
            language=self._get_one_or_none(channel_element, "|language"),
            copyright=self._get_one_or_none(channel_element, "|copyright"),
            managingEditor=self._get_one_or_none(channel_element, "|managingEditor"),
            webMaster=self._get_one_or_none(channel_element, "|webMaster"),
            generator=self._get_one_or_none(channel_element, "|generator"),
            docs=self._get_one_or_none(channel_element, "|docs"),
            rating=self._get_one_or_none(channel_element, "|rating"),
            ttl=self._get_one_or_none(channel_element, "|ttl", cast_to=int),
            skipHours=self._get_one_or_none(channel_element, "|skipHours", cast_to=int),
            skipDays=self._get_one_or_none(channel_element, "|skipDays", cast_to=int),
            pubDate=self._get_one_or_none(
                channel_element, "|pubDate", cast_to=dateutil_parser.parse
            ),
            lastBuildDate=self._get_one_or_none(
                channel_element, "|lastBuildDate", cast_to=dateutil_parser.parse
            ),
            categories=self._parse_categories(channel_element),
            cloud=self._parse_cloud(channel_element.select_one("|cloud")),
            image=self._parse_image(channel_element.select_one("|image")),
            textInput=self._parse_textinput(channel_element.select_one("|textinput")),
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
            registerProcedure=cloud_element.get("registerProcedure"),
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
            description=self._get_one_or_none(image_element, "|description"),
            # Optional. Defines the height of the image. Default is 31. Maximum value is 400
            height=int(self._get_one_or_none(image_element, "|height") or 31),
            # Optional. Defines the width of the image. Default is 88. Maximum value is 144
            width=int(self._get_one_or_none(image_element, "|width") or 88),
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

    def _parse_items(self):
        # A channel may contain any number of <item>s. An item may represent a "story" -- much
        # like a story in a newspaper or magazine; if so its description is a synopsis of the
        # story, and the link points to the full story. An item may also be complete in itself,
        # if so, the description contains the text (entity-encoded HTML is allowed), and the
        # link and title may be omitted. All elements of an item are optional, however at least
        # one of title or description must be present.

        items = []

        for item_element in self._root.select("channel item"):
            # An item MUST contain either a title or description.
            title, link, desc, errors = self._parse_required_item_elements(item_element)

            # An item MAY contain the following child elements: author, category,
            # comments, description, enclosure, guid, link, pubDate, source and title.
            # All of these elements are OPTIONAL.
            enclosure = self._parse_enclosure(item_element.select_one("|enclosure"))
            categories = self._parse_categories(item_element)
            author = self._get_one_or_none(item_element, "|author")
            comments = self._get_one_or_none(item_element, "|comments")
            pub_date = self._get_one_or_none(
                item_element, "|pubDate", cast_to=dateutil_parser.parse
            )

            # If the guid element has an attribute named isPermaLink with a value of true,
            # the reader may assume that it is a permalink to the item, that is, a url that
            # can be opened in a Web browser, that points to the full item described by the
            # <item> element. An example:
            guid = (link, False)  # fallback value
            if guid_element := item_element.select_one("|guid"):
                possible_vals = {"false": False, "0": False, "true": True, "1": True}
                is_perma_link = possible_vals[guid_element.get("isPermaLink", "true")]
                guid = (guid_element.text, is_perma_link)

            # Its value is the name of the RSS channel that the item came from, derived from its
            # <title>. It has one required attribute, url, which links to the XMLization of the
            # source.
            source = None
            if source_element := item_element.select_one("|source"):
                source = (source_element.text, source_element.get("url", ""))

            items.append(
                model.FeedItem(
                    title=title,
                    link=link,
                    description=desc,
                    guid=guid,
                    enclosure=enclosure,
                    author=author,
                    source=source,
                    comments=comments,
                    categories=categories,
                    pub_date=pub_date,
                    errors=errors,
                )
            )

        return items

    def _parse_required_item_elements(self, item_element):
        errors = []

        title = ""
        if element := item_element.select_one("|title"):
            title = element.text
        else:
            errors.append("Missing required element title")

        link = ""
        if element := item_element.select_one("|link"):
            link = element.text
        else:
            errors.append("Missing required element link")

        desc = ""
        if element := item_element.select_one("|description"):
            desc = element.text
        else:
            errors.append("Missing required element description")

        return (title, link, desc, errors)

    def _parse_enclosure(self, enclosure_element):
        # It has three required attributes. url says where the enclosure is located, length says how
        # big it is in bytes, and type says what its type is, a standard MIME type.
        if not enclosure_element:
            return None

        return model.Enclosure(
            url=enclosure_element.get("url"),
            length=int(enclosure_element.get("length")),
            mime_type=enclosure_element.get("type"),
        )

    def _parse_categories(self, item_element) -> list[model.Category]:
        categories = []

        for category_element in item_element.select("|category"):
            # It has one optional attribute, domain, a string that identifies a categorization
            # taxonomy.
            domain = category_element.get("domain")

            # The value of the element is a forward-slash-separated string that identifies a
            # hierarchiclocation in the indicated taxonomy. Processors may establish conventions
            # for theinterpretation of categories.
            for cat in category_element.text.split("/"):
                categories.append(model.Category(domain=domain, name=cat))

        return categories

    def parse(self):
        self._root = BeautifulSoup(self._xml_content, features="lxml-xml")
        channel = self._parse_channel()
        for item in self._parse_items():
            channel.items[item.guid[0]] = item

        return channel

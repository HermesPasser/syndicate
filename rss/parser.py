from dateutil import parser as dateutil_parser
from rss import model
from xml.parser import XmlParser

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
            categories=self._parse_categories(channel_element),
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
            enclosure = self._parse_enclosure(item_element.select_one("enclosure"))
            categories = self._parse_categories(item_element)
            author = item_element.select_content("author")
            comments = item_element.select_content("comments")
            pub_date = item_element.select_content(
                "pubDate", cast_to=dateutil_parser.parse
            )

            # If the guid element has an attribute named isPermaLink with a value of true,
            # the reader may assume that it is a permalink to the item, that is, a url that
            # can be opened in a Web browser, that points to the full item described by the
            # <item> element. An example:
            guid = (link, False)  # fallback value
            if guid_element := item_element.select_one("guid"):
                possible_vals = {"false": False, "0": False, "true": True, "1": True}
                is_perma_link = possible_vals[guid_element.get("isPermaLink", "true")]
                guid = (guid_element.text, is_perma_link)

            # Its value is the name of the RSS channel that the item came from, derived from its
            # <title>. It has one required attribute, url, which links to the XMLization of the
            # source.
            source = None
            if source_element := item_element.select_one("source"):
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
        if element := item_element.select_one("title"):
            title = element.text
        else:
            errors.append("Missing required element title")

        link = ""
        if element := item_element.select_one("link"):
            link = element.text
        else:
            errors.append("Missing required element link")

        desc = ""
        if element := item_element.select_one("description"):
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

        for category_element in item_element.select("category"):
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
        self._root = XmlParser.parse(self._xml_content)
        channel = self._parse_channel()
        for item in self._parse_items():
            channel.items[item.guid[0]] = item

        return channel

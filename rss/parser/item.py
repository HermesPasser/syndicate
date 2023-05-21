from dateutil import parser as dateutil_parser
from rss import model
from rss.parser.category import RssCategoryParser
from xml.parser import XmlParser


class RssItemParser:
    def __init__(self, node: XmlParser.XmlDocument):
        self._node = node

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

    def _parse_required_item_elements(self):
        errors = []

        title = ""
        if element := self._node.select_one("title"):
            title = element.text
        else:
            errors.append("Missing required element title")

        link = ""
        if element := self._node.select_one("link"):
            link = element.text
        else:
            errors.append("Missing required element link")

        desc = ""
        if element := self._node.select_one("description"):
            desc = element.text
        else:
            errors.append("Missing required element description")

        return (title, link, desc, errors)

    def parse(self):
        # An item may represent a "story" -- much
        # like a story in a newspaper or magazine; if so its description is a synopsis of the
        # story, and the link points to the full story. An item may also be complete in itself,
        # if so, the description contains the text (entity-encoded HTML is allowed), and the
        # link and title may be omitted. All elements of an item are optional, however at least
        # one of title or description must be present.
        # An item MUST contain either a title or description.
        title, link, desc, errors = self._parse_required_item_elements()

        # An item MAY contain the following child elements: author, category,
        # comments, description, enclosure, guid, link, pubDate, source and title.
        # All of these elements are OPTIONAL.
        enclosure = self._parse_enclosure(self._node.select_one("enclosure"))
        categories = RssCategoryParser(self._node).parse()
        author = self._node.select_content("author")
        comments = self._node.select_content("comments")
        pub_date = self._node.select_content("pubDate", cast_to=dateutil_parser.parse)

        # If the guid element has an attribute named isPermaLink with a value of true,
        # the reader may assume that it is a permalink to the item, that is, a url that
        # can be opened in a Web browser, that points to the full item described by the
        # <item> element. An example:
        guid = (link, False)  # fallback value
        if guid_element := self._node.select_one("guid"):
            possible_vals = {"false": False, "0": False, "true": True, "1": True}
            is_perma_link = possible_vals[guid_element.get("isPermaLink", "true")]
            guid = (guid_element.text, is_perma_link)

        # Its value is the name of the RSS channel that the item came from, derived from its
        # <title>. It has one required attribute, url, which links to the XMLization of the
        # source.
        source = None
        if source_element := self._node.select_one("source"):
            source = (source_element.text, source_element.get("url", ""))

        return model.FeedItem(
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

from rss import model
from xml.parser import XmlParser


class RssCategoryParser:
    def __init__(self, root: XmlParser.XmlDocument):
        self._root = root

    def parse(self):
        categories = []

        for category_element in self._root.select("category"):
            # It has one optional attribute, domain, a string that identifies a categorization
            # taxonomy.
            domain = category_element.get("domain")

            # The value of the element is a forward-slash-separated string that identifies a
            # hierarchiclocation in the indicated taxonomy. Processors may establish conventions
            # for theinterpretation of categories.
            for cat in category_element.text.split("/"):
                categories.append(model.Category(domain=domain, name=cat))

        return categories

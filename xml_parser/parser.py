from __future__ import annotations
from typing import TypeVar
from bs4 import BeautifulSoup

T = TypeVar("T")


class XmlParser:
    class XmlDocument:
        """Wrapper around witchever xml parser we're using"""

        def __init__(self, node, ignore_namespace=True):
            self._node = node
            self._ignore_namespace = ignore_namespace

        @property
        def text(self):
            return self._node.text

        def get(self, attr: str, default: str = None):
            return self._node.get(attr, default)

        def _prepare_selector(self, selector):
            if self._ignore_namespace and not selector.startswith("|"):
                selector = "|" + selector

            return selector

        def select_one(self, selector: str) -> XmlParser.XmlDocument | None:
            if node := self._node.select_one(self._prepare_selector(selector)):
                return type(self)(node)

            return None

        def select_content(self, selector: str, cast_to: T = None) -> T | None:
            if item := self._node.select_one(self._prepare_selector(selector)):
                if cast_to:
                    return cast_to(item.text)
                return item.text

            return None

        def select(self, selector: str) -> list[XmlParser.XmlDocument]:
            nodes = self._node.select(self._prepare_selector(selector))
            if len(nodes) > 0:
                nodes = [type(self)(node) for node in nodes]

            return nodes

    @staticmethod
    def parse(content: str) -> XmlParser.XmlDocument:
        root = BeautifulSoup(content, features="lxml-xml")
        return XmlParser.XmlDocument(root)

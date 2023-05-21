import unittest
from pathlib import Path
from pprint import pformat
from rss import model
from rss.parser import RssParser


class RssParserBaseTest(unittest.TestCase):
    maxDiff = None

    def namedtuple_with_optional(self, named_tuple, kwargs: dict):
        as_dict = dict(map(lambda field: (field, None), named_tuple._fields))
        return named_tuple(**{**as_dict, **kwargs})

    def assertNamedtupleEqual(self, t0, t1):
        # We _could_ compare the tuples bare but considering its length,
        # the diff would be truncated making seeing the actual field
        # difference that makes the test fail difficult to visualize,
        # so we format with each field in one line.
        self.assertEqual(pformat(t0._asdict()), pformat(t1._asdict()))

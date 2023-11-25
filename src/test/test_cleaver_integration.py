"""
Integration tests against http-hosted content.
"""

import unittest

import urllib.request
import logging

from html_cleaver.cleaver import (
    get_cleaver,
)
from test.test_cleaver import (
    EXPECT_CHUNKS,
    assert_equal_chunks,
)

LOG = logging.getLogger(__name__)

URL_BASE = "https://presidiovantage.com/html-cleaver/"
EXPECT_CHUNKS = [
    {"uri": f"{URL_BASE}{x['uri']}",
     "pos": x["pos"], "text": x["text"], "meta": x["meta"]}
    for x in EXPECT_CHUNKS]


class TestHtmlCleaverIntegration(unittest.TestCase):

    def test_1basic(self):
        url = f"{URL_BASE}test1basic.html"
        
        chunk_list = get_cleaver("xml").parse_queue(url)
        self.assertEqualData(EXPECT_CHUNKS, chunk_list, True)
        
        chunk_list = get_cleaver("lxml").parse_queue(url)
        self.assertEqualData(EXPECT_CHUNKS, chunk_list, True)

        with get_cleaver("selenium") as cleaver:
            chunk_list = cleaver.parse_queue(url)
        self.assertEqualData(EXPECT_CHUNKS, chunk_list, True)

    def test_6illformed(self):
        url = f"{URL_BASE}test6illformed.html"
        chunk_list = get_cleaver("lxml").parse_queue(url)
        self.assertEqualData(EXPECT_CHUNKS, chunk_list, False)

    def test_7javascript(self):
        url = f"{URL_BASE}test7javascript.html"
        with get_cleaver("selenium") as cleaver:
            chunk_list = cleaver.parse_queue(url)
        self.assertEqualData(EXPECT_CHUNKS, chunk_list, False)

    def test_HttpIO(self):
        url = f"{URL_BASE}test1basic.html"

        with urllib.request.urlopen(url) as c:
            chunk_list = get_cleaver("xml").parse_queue(c)
        self.assertEqualData(EXPECT_CHUNKS, chunk_list, True)

        with urllib.request.urlopen(url) as c:
            chunk_list = get_cleaver("lxml").parse_queue(c)
        self.assertEqualData(EXPECT_CHUNKS, chunk_list, True)

        # N.B. selenium api requires string input!

    def assertEqualData(self, l1, l2, strict=False):
        assert_equal_chunks(self, l1, l2, strict)


if __name__ == '__main__':
    unittest.main()

    # logging.basicConfig(level=logging.DEBUG)
    # unittest.main(defaultTest=[
    #     "TestHtmlCleaverIntegration.test_1basic",
    #     # "TestHtmlCleaverIntegration.test_6illformed",
    #     # "TestHtmlCleaverIntegration.test_7javascript",
    #     # "TestHtmlCleaverIntegration.test_HttpIO",
    # ])

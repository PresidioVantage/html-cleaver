"""
testing results with various inputs.
tests that each input file yields the expected sequence of chunks.
"""

import unittest
from collections.abc import (
    Iterable,
)

import logging
from io import StringIO

from html_cleaver.cleaver import get_cleaver, HTMLCleaver

LOG = logging.getLogger(__name__)

# default cleaver (lxml) does not actually require context-manager (e.g. "with")
DEFAULT_CLEAVER: HTMLCleaver = get_cleaver()

EXPECT_CHUNKS = [
    {'uri': 'test1basic.html', 'pos': '[1]html[2]body[2]div[2]div[1]p', 'text': 'The universe is a large place.',
     'meta': {'h1': 'The Universe'}},
    {'uri': 'test1basic.html', 'pos': '[1]html[2]body[2]div[2]div[2]p', 'text': 'It contains lots of stuff.',
     'meta': {'h1': 'The Universe'}},
    {'uri': 'test1basic.html', 'pos': '[1]html[2]body[2]div[2]div[4]div[1]p',
     'text': 'Andromeda is our nearest large galaxy.', 'meta': {'h1': 'The Universe', 'h2': 'Andromeda'}},
    {'uri': 'test1basic.html', 'pos': '[1]html[2]body[2]div[2]div[4]div[2]p', 'text': 'It is a spiral galaxy.',
     'meta': {'h1': 'The Universe', 'h2': 'Andromeda'}},
    {'uri': 'test1basic.html', 'pos': '[1]html[2]body[2]div[2]div[6]div[1]p',
     'text': 'Our galaxy is called the Milky Way.', 'meta': {'h1': 'The Universe', 'h2': 'Milky Way'}},
    {'uri': 'test1basic.html', 'pos': '[1]html[2]body[2]div[2]div[6]div[2]p', 'text': 'It is also a spiral galaxy.',
     'meta': {'h1': 'The Universe', 'h2': 'Milky Way'}},
    {'uri': 'test1basic.html', 'pos': '[1]html[2]body[2]div[2]div[6]div[4]div[1]p',
     'text': 'The nearest star is Proxima Centauri.',
     'meta': {'h1': 'The Universe', 'h2': 'Milky Way', 'h3': 'Proxima Centauri'}},
    {'uri': 'test1basic.html', 'pos': '[1]html[2]body[2]div[2]div[6]div[4]div[2]p',
     'text': 'It is a relatively-small star.',
     'meta': {'h1': 'The Universe', 'h2': 'Milky Way', 'h3': 'Proxima Centauri'}},
    {'uri': 'test1basic.html', 'pos': '[1]html[2]body[2]div[2]div[6]div[6]div[1]p',
     'text': 'The Sun is our star, the center of our solar system.',
     'meta': {'h1': 'The Universe', 'h2': 'Milky Way', 'h3': 'The Sun'}},
    {'uri': 'test1basic.html', 'pos': '[1]html[2]body[2]div[2]div[6]div[6]div[2]h4', 'text': '',
     'meta': {'h1': 'The Universe', 'h2': 'Milky Way', 'h3': 'The Sun', 'h4': 'Pluto'}},
    {'uri': 'test1basic.html', 'pos': '[1]html[2]body[2]div[2]div[6]div[6]div[4]div[1]p',
     'text': 'We live on planet Earth.',
     'meta': {'h1': 'The Universe', 'h2': 'Milky Way', 'h3': 'The Sun', 'h4': 'Earth'}},
    {'uri': 'test1basic.html', 'pos': '[1]html[2]body[2]div[2]div[6]div[6]div[4]div[2]p',
     'text': 'This planet is particularly nice.',
     'meta': {'h1': 'The Universe', 'h2': 'Milky Way', 'h3': 'The Sun', 'h4': 'Earth'}},
    {'uri': 'test1basic.html', 'pos': '[1]html[2]body[2]div[2]div[6]div[6]div[4]div[3]p', 'text': 'Are we?',
     'meta': {'h1': 'The Universe', 'h2': 'Milky Way', 'h3': 'The Sun', 'h4': 'Earth'}},
    {'uri': 'test1basic.html', 'pos': '[1]html[2]body[2]div[2]div[6]div[6]div[6]div[1]p',
     'text': 'The Sun is much larger than the Earth.',
     'meta': {'h1': 'The Universe', 'h2': 'Milky Way', 'h3': 'The Sun', 'D2 h2': 'Physics of the Sun'}},
    {'uri': 'test1basic.html', 'pos': '[1]html[2]body[2]div[2]div[6]div[6]div[6]div[2]p',
     'text': 'The Sun is much hotter than the Earth.',
     'meta': {'h1': 'The Universe', 'h2': 'Milky Way', 'h3': 'The Sun', 'D2 h2': 'Physics of the Sun'}},
]


def filter_list(the_list: Iterable[dict[str, any]]):
    """
    given a list of chunks, return only text and meta
    """
    return [{k: x[k] for k in ["text", "meta"]} for x in the_list]


def assert_equal_chunks(the_test, l1, l2, strict=False):
    the_test.assertSequenceEqual(
        l1 if strict else filter_list(l1),
        l2 if strict else filter_list(l2))


class TestHtmlCleaver(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        import os
        os.chdir(os.path.dirname(__file__))
    
    def test_1basic(self):
        chunk_list = get_cleaver("xml").parse_queue("test1basic.html")
        self.assertEqualData(EXPECT_CHUNKS, chunk_list, True)
        chunk_list = get_cleaver("lxml").parse_queue("test1basic.html")
        self.assertEqualData(EXPECT_CHUNKS, chunk_list, True)

        with get_cleaver("selenium") as cleaver:
            chunk_list = cleaver.parse_queue("test1basic.html")
        self.assertEqualData(EXPECT_CHUNKS, chunk_list, True)

    def test_2flat(self):
        chunk_list = DEFAULT_CLEAVER.parse_queue("test2flat.html")
        self.assertEqualData(EXPECT_CHUNKS, chunk_list, False)

    def test_3semantic(self):
        chunk_list = DEFAULT_CLEAVER.parse_queue("test3semantic.html")
        self.assertEqualData(EXPECT_CHUNKS, chunk_list, False)

    def test_4deep(self):
        chunk_list = DEFAULT_CLEAVER.parse_queue("test4deep.html")
        self.assertEqualData(EXPECT_CHUNKS, chunk_list, False)

    def test_5fail(self):
        # build the expected list with a fresh parse,
        # so we can mutate it without mutating EXPECT_CHUNKS
        chunk_list_basic = list(DEFAULT_CLEAVER.parse_queue("test1basic.html"))

        # two "p" chunks become an empty header chunk and 2 "p" chunks *without* said header
        chunk_list_basic.insert(2, chunk_list_basic[2].copy())
        chunk_list_basic[2]["meta"] = chunk_list_basic[3]["meta"].copy()
        chunk_list_basic[2]["text"] = ""
        del chunk_list_basic[3]["meta"]["h2"]
        del chunk_list_basic[4]["meta"]["h2"]

        chunk_list = DEFAULT_CLEAVER.parse_queue("test5fail.html")
        self.assertEqualData(chunk_list_basic, chunk_list, False)

    def test_6illformed(self):
        chunk_list = get_cleaver("lxml").parse_queue("test6illformed.html")
        self.assertEqualData(EXPECT_CHUNKS, chunk_list, False)

    def test_7javascript(self):
        with get_cleaver("selenium") as cleaver:
            chunk_link = cleaver.parse_queue("test7javascript.html")
        self.assertEqualData(EXPECT_CHUNKS, chunk_link, False)

    def test_queue(self):
        g = DEFAULT_CLEAVER.parse_chunk_sequence([
            "test1basic.html",
            "test2flat.html"])
        self.assertEqualData(EXPECT_CHUNKS + EXPECT_CHUNKS, g, False)

    def test_StringIO(self):
        with open("test1basic.html", "r") as f:
            text = f.read()
        expect = [{"uri": None, "pos": x["pos"], "text": x["text"], "meta": x["meta"]} for x in EXPECT_CHUNKS]

        chunk_list = get_cleaver("lxml").parse_queue(StringIO(text))
        self.assertEqualData(expect, chunk_list, True)

        chunk_list = get_cleaver("xml").parse_queue(StringIO(text))
        self.assertEqualData(expect, chunk_list, True)

        # Selenium cleaver does not support IO sources, only string references

    def test_FileIO(self):
        with open("test1basic.html", "r") as f:
            chunk_list = get_cleaver("lxml").parse_queue(f)
            self.assertEqualData(EXPECT_CHUNKS, chunk_list, True)

        with open("test1basic.html", "r") as f:
            chunk_list = get_cleaver("xml").parse_queue(f)
            self.assertEqualData(EXPECT_CHUNKS, chunk_list, True)

        # Selenium cleaver does not support IO sources, only string references

    # def test_get_cleaver(self):
    #     for s in ["xml", "lxml", "selenium"]:
    #         with get_cleaver(s) as cleaver:
    #             l = cleaver.parse_queue("test1basic.html")
    #             self.assertEqualData(EXPECT_CHUNKS, l, True)

    def assertEqualData(self, l1, l2, strict=False):
        assert_equal_chunks(self, l1, l2, strict)


if __name__ == '__main__':
    unittest.main()

    # logging.basicConfig(level=logging.DEBUG)
    # unittest.main(defaultTest=[
    #     "TestHtmlCleaver.test_1basic",
    #     # "TestHtmlCleaver.test_2flat",
    #     # "TestHtmlCleaver.test_7javascript",
    # ])

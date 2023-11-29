"""
testing results with various inputs.
tests that each input file yields the expected sequence of chunks.
"""

import unittest
from collections.abc import (
    Iterable,
    Iterator
)

import logging
from io import StringIO

from html_cleaver.cleaver import get_cleaver, HTMLCleaver
from pickle import NONE

LOG = logging.getLogger(__name__)

# default cleaver (lxml) does not actually require context-manager (e.g. "with")
DEFAULT_CLEAVER: HTMLCleaver = get_cleaver()

EXPECT_CHUNKS = [
    {'uri': 'test1basic.html', 'pos': '[1]html[2]body[2]div[2]div[1]p',
     'text': 'The universe is a large place.',
     'meta': {'h1': 'The Universe'}},
    {'uri': 'test1basic.html', 'pos': '[1]html[2]body[2]div[2]div[2]p',
     'text': 'It contains lots of stuff.',
     'meta': {'h1': 'The Universe'}},
    {'uri': 'test1basic.html', 'pos': '[1]html[2]body[2]div[2]div[4]div[1]p',
     'text': 'Andromeda is our nearest large galaxy.',
     'meta': {'h1': 'The Universe', 'h2': 'Andromeda'}},
    {'uri': 'test1basic.html', 'pos': '[1]html[2]body[2]div[2]div[4]div[2]p',
     'text': 'It is a spiral galaxy.',
     'meta': {'h1': 'The Universe', 'h2': 'Andromeda'}},
    {'uri': 'test1basic.html', 'pos': '[1]html[2]body[2]div[2]div[6]div[1]p',
     'text': 'Our galaxy is called the Milky Way.',
     'meta': {'h1': 'The Universe', 'h2': 'Milky Way'}},
    {'uri': 'test1basic.html', 'pos': '[1]html[2]body[2]div[2]div[6]div[2]p',
     'text': 'It is also a spiral galaxy.',
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
    {'uri': 'test1basic.html', 'pos': '[1]html[2]body[2]div[2]div[6]div[6]div[2]h4',
     'text': '',
     'meta': {'h1': 'The Universe', 'h2': 'Milky Way', 'h3': 'The Sun', 'h4': 'Pluto'}},
    {'uri': 'test1basic.html', 'pos': '[1]html[2]body[2]div[2]div[6]div[6]div[4]div[1]p',
     'text': 'We live on planet Earth.',
     'meta': {'h1': 'The Universe', 'h2': 'Milky Way', 'h3': 'The Sun', 'h4': 'Earth'}},
    {'uri': 'test1basic.html', 'pos': '[1]html[2]body[2]div[2]div[6]div[6]div[4]div[2]p',
     'text': 'This planet is particularly nice.',
     'meta': {'h1': 'The Universe', 'h2': 'Milky Way', 'h3': 'The Sun', 'h4': 'Earth'}},
    {'uri': 'test1basic.html', 'pos': '[1]html[2]body[2]div[2]div[6]div[6]div[4]div[3]p',
     'text': 'Are we?',
     'meta': {'h1': 'The Universe', 'h2': 'Milky Way', 'h3': 'The Sun', 'h4': 'Earth'}},
    {'uri': 'test1basic.html', 'pos': '[1]html[2]body[2]div[2]div[6]div[6]div[6]div[1]p',
     'text': 'The Sun is much larger than the Earth.',
     'meta': {'h1': 'The Universe', 'h2': 'Milky Way', 'h3': 'The Sun', 'D2 h2': 'Physics of the Sun'}},
    {'uri': 'test1basic.html', 'pos': '[1]html[2]body[2]div[2]div[6]div[6]div[6]div[2]p',
     'text': 'The Sun is much hotter than the Earth.',
     'meta': {'h1': 'The Universe', 'h2': 'Milky Way', 'h3': 'The Sun', 'D2 h2': 'Physics of the Sun'}},
]


def filter_sequence(the_list: Iterable[dict[str, any]]):
    """
    given a list of chunks, return only text and meta
    """
    for x in the_list:
        yield {k: x[k] for k in ["text", "meta"]}


# this alternative to stock TestCase.assertSequenceEqual supports delayed collections
def assert_iterable_equal(
    the_test,
    l1: Iterable[dict[str, any]],
    l2: Iterable[dict[str, any]]
):
    i1: Iterator[dict[str, any]] = iter(l1)
    i2: Iterator[dict[str, any]] = iter(l2)
    sentinel = object()
    i = 0
    e1 = None
    e2 = None
    while e1 is not sentinel and e2 is not sentinel:
        e1 = next(i1, sentinel)
        e2 = next(i2, sentinel)
        the_test.assertEqual(e1, e2,
            f"|l1|={i}, |l2|>{i}: l2[{i}]={e2}" if e1 is sentinel else
            f"|l2|={i}, |l1|>{i}: l1[{i}]={e1}" if e2 is sentinel else
            f"iterables differ at index [{i}]")
        i += 1

def assert_equal_chunks(
    the_test,
    l1: Iterable[dict[str, any]],
    l2: Iterable[dict[str, any]],
    strict=False
):
    assert_iterable_equal(the_test,
        l1 if strict else filter_sequence(l1),
        l2 if strict else filter_sequence(l2))
    # the_test.assertSequenceEqual(
    #     [x for x in (l1 if strict else filter_sequence(l1))],
    #     [x for x in (l2 if strict else filter_sequence(l2))])


class TestHtmlCleaver(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        import os
        os.chdir(os.path.dirname(__file__))
    
    def test_1basic(self):
        chunk_list = get_cleaver("xml").parse_chunk_sequence(["test1basic.html"])
        self.assertEqualData(EXPECT_CHUNKS, chunk_list, True)
        chunk_list = get_cleaver("lxml").parse_chunk_sequence(["test1basic.html"])
        self.assertEqualData(EXPECT_CHUNKS, chunk_list, True)

        with get_cleaver("selenium") as cleaver:
            chunk_list = cleaver.parse_chunk_sequence(["test1basic.html"])
            self.assertEqualData(EXPECT_CHUNKS, chunk_list, True)

    def test_2flat(self):
        chunk_list = DEFAULT_CLEAVER.parse_chunk_sequence(["test2flat.html"])
        self.assertEqualData(EXPECT_CHUNKS, chunk_list, False)

    def test_3semantic(self):
        chunk_list = DEFAULT_CLEAVER.parse_chunk_sequence(["test3semantic.html"])
        self.assertEqualData(EXPECT_CHUNKS, chunk_list, False)

    def test_4deep(self):
        chunk_list = DEFAULT_CLEAVER.parse_chunk_sequence(["test4deep.html"])
        self.assertEqualData(EXPECT_CHUNKS, chunk_list, False)

    def test_5fail(self):
        # build the expected list with a fresh parse,
        # so we can mutate it without mutating EXPECT_CHUNKS
        chunk_list_basic = list(DEFAULT_CLEAVER.parse_chunk_sequence(["test1basic.html"]))

        # two "p" chunks become an empty header chunk and 2 "p" chunks *without* said header
        chunk_list_basic.insert(2, chunk_list_basic[2].copy())
        chunk_list_basic[2]["meta"] = chunk_list_basic[3]["meta"].copy()
        chunk_list_basic[2]["text"] = ""
        del chunk_list_basic[3]["meta"]["h2"]
        del chunk_list_basic[4]["meta"]["h2"]

        chunk_list = DEFAULT_CLEAVER.parse_chunk_sequence(["test5fail.html"])
        self.assertEqualData(chunk_list_basic, chunk_list, False)

    def test_6illformed(self):
        chunk_list = get_cleaver("lxml").parse_chunk_sequence(["test6illformed.html"])
        self.assertEqualData(EXPECT_CHUNKS, chunk_list, False)

    def test_7javascript(self):
        with get_cleaver("selenium") as cleaver:
            chunk_list = cleaver.parse_chunk_sequence(["test7javascript.html"])
            self.assertEqualData(EXPECT_CHUNKS, chunk_list, False)

    def test_queue(self):
        g = DEFAULT_CLEAVER.parse_chunk_sequence([
            "test1basic.html",
            "test2flat.html"])
        self.assertEqualData(EXPECT_CHUNKS + EXPECT_CHUNKS, g, False)

    def test_StringIO(self):
        with open("test1basic.html", "r") as f:
            text = f.read()
        expect = [{"uri": None, "pos": x["pos"], "text": x["text"], "meta": x["meta"]} for x in EXPECT_CHUNKS]

        chunk_list = get_cleaver("lxml").parse_chunk_sequence([StringIO(text)])
        self.assertEqualData(expect, chunk_list, True)

        chunk_list = get_cleaver("xml").parse_chunk_sequence([StringIO(text)])
        self.assertEqualData(expect, chunk_list, True)

        # Selenium cleaver does not support IO sources, only string references

    def test_FileIO(self):
        with open("test1basic.html", "r") as f:
            chunk_list = get_cleaver("lxml").parse_chunk_sequence([f])
            self.assertEqualData(EXPECT_CHUNKS, chunk_list, True)

        with open("test1basic.html", "r") as f:
            chunk_list = get_cleaver("xml").parse_chunk_sequence([f])
            self.assertEqualData(EXPECT_CHUNKS, chunk_list, True)

        # Selenium cleaver does not support IO sources, only string references

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

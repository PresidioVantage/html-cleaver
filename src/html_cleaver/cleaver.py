"""
# HTML Cleaver

Utility for parsing HTML into a sequence of "chunks."
Each chunk includes some metadata, including all "relevant" HTML headers (h1, h2, ...h6).
Chunks are always delimited by headers,
but also by a (configurable) set of tags between-which to chunk.

for reference, see https://www.w3.org/WAI/tutorials/page-structure/headings/

the SeleniumCleaver subclass uses/requires Selenium

see README.md for example usage
see handler.py for logical implementation and developer docs
"""

from typing import (
    Callable,
    Generator,
    Literal,
    Optional,
)
from collections import deque
from collections.abc import (
    Iterable,
    Collection,
)
import logging

from xml.sax.handler import ContentHandler

from html_cleaver.util import parse_html
from html_cleaver.handle import CleaverHandle

LOG = logging.getLogger(__name__)


def get_cleaver(
        parse_render: Literal["xml", "lxml", "selenium"] = "lxml",
        header_tags: Optional[Collection[str]] = None,
        chunk_tags: Optional[Collection[str]] = None,
) -> "HTMLCleaver":
    """
    should be called in a 'with' statement, to ensure Selenium case works.
    """
    return \
        SeleniumCleaver(header_tags, chunk_tags) if "selenium" == parse_render else \
        HTMLCleaver("xml" == parse_render, header_tags, chunk_tags)


def _check_iterable_not_string(x: Iterable[any]):
    if not _is_iterable_not_string(x):
        raise Exception(f"a sequence is required: {x}")


def _is_iterable_not_string(x: Iterable[any]):
    return isinstance(x, Iterable) and not isinstance(x, str)


class HTMLCleaver:
    """
    for single-threaded, sequential parsing only.
    instances should be context-managed (e.g. using 'with' statement).

    this uses lxml.html parser to tolerate html's lax tag structure,
    which significantly degrades performance (including a full DOM parse).
    the "strict" argument controls whether to use built-in xml.sax instead of lxml.html+lxml.sax
    this is lighter and faster but requires the document have balanced tags (~well-formed xml)

    the "source" argument is passed directly to the parser (with exceptions):
    lxml.html for loose parsing:
        filename_or_url: "a filename, URL, or file-like object"
        (https://lxml.de/apidoc/lxml.html.html#lxml.html.parse)
        http/https URLs are not supported by lxml, so they are converted to http connections (IO)
    xml.sax for strict parsing:
        filename_or_stream: "can be a filename or a file object"
        (https://docs.python.org/3/library/xml.sax.html)
    """

    def __init__(
            self,
            strict: bool = False,
            header_tags: Optional[Collection[str]] = None,
            chunk_tags: Optional[Collection[str]] = None,
    ):
        self.strict: bool = strict
        self.header_tags: Optional[Collection[str]] = header_tags
        self.chunk_tags: Optional[Collection[str]] = chunk_tags

        self._parse_sax: Callable[[any, ContentHandler], None] = \
            parse_html.xml_get_sax if self.strict else parse_html.lxml_get_sax

    # trivial implementation of context-manager, for consistency with Selenium version below
    def __enter__(self) -> "HTMLCleaver":
        return self

    def __exit__(self, *args):
        pass

    def parse_chunk_sequence(
            self,
            sources: Iterable[any],
    ) -> Generator[dict[str, any], None, None]:
        for q in self._parse_queue_sequence(sources):
            yield from q

    def _parse_queue_sequence(
            self,
            sources: Iterable[any],
    ) -> Generator[deque[dict[str, any]], None, None]:
        _check_iterable_not_string(sources)
        for source in sources:
            yield self.parse_queue(source)

    def parse_queue(
            self,
            source: any,
    ) -> deque[dict[str, any], None, None]:
        the_q = deque()
        handler: ContentHandler = self._new_handler(the_q.append)
        self._parse_sax(source, handler)
        return the_q

    def parse_events(
            self,
            sources: Iterable[any],
            callback: Callable[[dict[str, any]], any],
    ):
        _check_iterable_not_string(sources)
        handler: ContentHandler = self._new_handler(callback)
        for source in sources:
            self._parse_sax(source, handler)

    # Helper Methods:

    def _new_handler(
            self,
            callback: Callable[[dict[str, any]], any]
    ) -> ContentHandler:

        return CleaverHandle(
            callback,
            self.header_tags,
            self.chunk_tags)


class SeleniumCleaver(HTMLCleaver):
    """
    requires selenium.
    to ensure setup and teardown of Selenium driver,
    instances MUST be context-managed (e.g. 'with').
    """

    def __init__(
            self,

            header_tags: Optional[Collection[str]] = None,
            chunk_tags: Optional[Collection[str]] = None,

            browser: Literal["chrome", "firefox"] = "chrome",
            args: tuple[str] = ("--headless", "--no-sandbox"),
            binary_location: Optional[str] = None,
            executable_path: Optional[str] = None,
    ):
        from selenium.webdriver.remote.webdriver import WebDriver

        super().__init__(
            False,  # does not matter as we do not use superclass' parser
            header_tags,
            chunk_tags)

        self.driver: Optional[WebDriver] = None
        self.browser: Literal["chrome", "firefox"] = browser
        self.args: tuple[str] = args
        self.binary_location: Optional[str] = binary_location
        self.executable_path: Optional[str] = executable_path

        self._parse_sax = lambda source, handler: parse_html.selenium_get_sax(
            source,
            handler,
            self._get_driver())

    def __enter__(self) -> "SeleniumCleaver":
        from html_cleaver.util import render_selenium
        self.driver = render_selenium.selenium_get_driver(
            self.browser,
            self.args,
            self.binary_location,
            self.executable_path)

        return self

    def __exit__(self, *args):
        self.driver.quit()
        self.driver = None

    def _get_driver(self):
        if self.driver is None:
            raise Exception("SeleniumCleaver context-manager is not open. Use this object in a 'with' statement.")
        return self.driver


if __name__ == "__main__":
    import sys

    main_verbose = False

    # main_parse_render: Literal["xml", "lxml", "selenium"] = "xml"
    main_parse_render: Literal["xml", "lxml", "selenium"] = "lxml"
    # main_parse_render: Literal["xml", "lxml", "selenium"] = "selenium"

    # strictly xml compliant
    default_file = "../test/test1basic.html"
    # requires lxml
    # default_file = "../test/test6illformed.html"
    # requires selenium
    # default_file = "../test/test7javascript.html"

    # if no sources are specified by command-line args, use default(s)
    main_sources = sys.argv[1:] if 1 < len(sys.argv) else [default_file]

    if main_verbose:
        logging.basicConfig(level=logging.DEBUG)
        main_callback = LOG.info
    else:
        main_callback = print

    main_callback("# CLEAVING:\n\t" + "\n\t".join(main_sources))
    with get_cleaver(main_parse_render) as cleaver:
        cleaver.parse_events(main_sources, main_callback)

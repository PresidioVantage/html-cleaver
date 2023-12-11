"""
# SAX ContentHandler for HTMLCleaver

A lightweight (SAX) HTML parse, "chunked" into sequence of contiguous text segments.
This is the internal parsing logic used by HTMLCleaver.

This code builds 3 data structures via the classes ElemPos, Header, and ChunkPos.
An instance of each is maintained throughout (between/during each event of) the SAX parse.
Each class represents a tree structure, and stores only a (singly-linked list) pointer "upward" recursively to a root.
ElemPos models a tree of Element(position)s consistent with the DOM itself.
Header permits parent("prior") references to prior-siblings *in-addition-to* ancestors.
ChunkPos models a tree similar to Header, but also containing non-header "chunking" elements in the hierarchy.

TODO consider capturing 'title' tag as one additional field (aggregate text)
"""

from typing import (
    Callable,
    Optional,
)
from collections.abc import (
    Collection,
)

import logging

from xml.sax.xmlreader import Locator
from xml.sax.handler import ContentHandler


LOG = logging.getLogger(__name__)
ALL_HEADER_TAGS = [
    "h1", "h2", "h3", "h4", "h5", "h6"]


# CONFIGS
TUPLES_NOT_DICT = False
FLATTEN_TAGS = [
    "header", "hgroup"]
SUPPRESS_TAGS = [
    "head", "script", "style"]  # TODO consider adding meta/link to this list?

DEFAULT_HEADER_TAGS = ALL_HEADER_TAGS
# to capture all text content, recommended: ["body"]+DEFAULT_CHUNK_TAGS
DEFAULT_CHUNK_TAGS = [
    "div", "p", "blockquote", "ol", "ul"]  # TODO consider adding "article" to this list?


class CleaverHandle(ContentHandler):
    """
    for single-threaded, sequential parsing only.
    """

    def __init__(
        self,
        yield_function: Callable[[dict], any] = None,
        header_tags: Optional[Collection[str]] = None,
        chunk_tags: Optional[Collection[str]] = None
    ):

        super().__init__()
        
        self.yield_function: Callable[[dict], any] = \
            yield_function if yield_function else lambda x: None
        
        self.header_tags: Collection[str] = header_tags if header_tags is not None \
            else DEFAULT_HEADER_TAGS.copy()
        if not all(x in ALL_HEADER_TAGS for x in self.header_tags):
            raise Exception(f"invalid header_tags {self.header_tags}")
        
        self.chunk_tags = chunk_tags if chunk_tags is not None \
            else DEFAULT_CHUNK_TAGS.copy()
        if any(x in ALL_HEADER_TAGS for x in self.chunk_tags):
            raise Exception(f"invalid chunk_tags: {self.chunk_tags}")

        # mutable state, esp. tracking pointers between/during parse events:
        self.uri: Optional[str] = None
        self.current: Optional[ElemPos] = None
        self.prior_headers: Optional[Header] = None
        self.header_sent: bool = False
        self.chunk: Optional[ChunkPos] = None
        self.text: Optional[str] = None
        self.building_header: Optional[Header] = None
        self.suppress: Optional[ElemPos] = None

    # ignore namespace information
    def startElementNS(self, nsname: tuple[str, str], qname, attrs):
        self.startElement(nsname[1], attrs)

    def endElementNS(self, nsname: tuple[str, str], qname):
        self.endElement(nsname[1])

    def setDocumentLocator(self, loc: Locator):
        # xml.sax does this when given an open URLConnection, unfortunately
        if loc is None or loc.getSystemId() is None:
            LOG.debug(f"suppressed setDocumentLocator(None), maintained {self.uri} ({loc})")
        else:
            LOG.debug(f"setDocumentLocator({loc.getSystemId()}) replacing {self.uri}")

            self.uri = loc.getSystemId()

    def startDocument(self):
        LOG.debug("startDocument()")

    def endDocument(self):
        LOG.debug("endDocument()")
        self.uri = None

    def startElement(self, name: str, attrs):
        if name.lower() in FLATTEN_TAGS:
            LOG.debug(f"<FLATTEN '{name}'")
            return

        self.current = ElemPos(self.current, name.lower(), self.prior_headers)
        LOG.debug(f"<{self.current}")

        # already suppressing:
        if self.suppress:
            LOG.debug(f"<X '{name}'")
            return;
        # start suppressing:
        if name.lower() in SUPPRESS_TAGS:
            LOG.debug(f"<SUPPRESS '{name}'")
            self.suppress = self.current
            return

        # if already actively building a header, no other logic (except one validation)
        if self.building_header:
            if self.current.tag in self.header_tags:
                raise Exception(f"start {name} within {self.building_header}")

        else:
            if self.current.tag in self.header_tags:
                self.building_header = Header(self.prior_headers, self.current)

                # if this header supersedes the prior,
                # and the prior-header hasn't been sent yet,
                # then force it to be sent even if empty.
                force_chunk = \
                    not self.header_sent and \
                    self.prior_headers != self.building_header.prior_higher
                self.send_chunk(force_chunk)

                self.prior_headers = self.building_header
                self.current.head = self.building_header
                self.header_sent = False

                if self.chunk:
                    self.chunk = ChunkPos(self.chunk, self.current)
                    LOG.debug(f"#{self.chunk}")

            # a header tag which is not-captured is still a helpful place to slice the current ChunkPos
            elif self.current.tag in ALL_HEADER_TAGS:
                self.send_chunk()

            elif self.current.tag in self.chunk_tags:
                if not self.send_chunk():
                    self.text = ""

                self.chunk = ChunkPos(self.chunk, self.current)
                LOG.debug(f"#{self.chunk}")

    def endElement(self, name: str):
        if name.lower() in FLATTEN_TAGS:
            LOG.debug(f"/FLATTEN '{name}'")
            return

        if self.current is None:
            raise Exception(f"end <{name}> in None")
        if name != self.current.tag:
            raise Exception(f"end <{name}> in <{self.current.tag}>")
        LOG.debug(f"/{self.current}")

        if self.suppress:
            if self.suppress == self.current:
                LOG.debug(f"/SUPPRESS '{name}'")
                self.suppress = None;

        elif self.building_header:
            # building_header mode does nothing, except flag when it is over
            if self.current == self.building_header.pos:
                self.building_header.text = self.building_header.text.strip()
                LOG.debug(f"#{self.building_header}")
                self.building_header = None

        else:
            # this tag ends an element which is not a Header itself

            if self.prior_headers != self.current.head:
                self.send_chunk(not self.header_sent)

                self.prior_headers = self.current.head
                while self.chunk and self.chunk.pos.parent == self.current:
                    self.chunk = self.chunk.par
                if self.chunk is None:
                    self.text = None

            if self.current.tag in self.chunk_tags:
                self.send_chunk()

                end_chunk = self.chunk
                while end_chunk.pos != self.current:
                    end_chunk = end_chunk.par
                self.chunk = end_chunk.par
                if self.chunk is None:
                    self.text = None

        self.current = self.current.parent

    def characters(self, content: str):
        # if content.strip():
        if self.current is None:
            raise Exception(f"characters in None: {content}")

        if self.suppress:
            LOG.debug("XT" + self.current.get_indent(1) + content.strip())
            return
        else:
            LOG.debug("T" + self.current.get_indent(1) + content.strip())

        if self.building_header:
            self.building_header.text += content

        elif self.chunk:
            self.text += content

    def send_chunk(
        self,
        send_blank=False
    ) -> Optional[dict[str, any]]:
        LOG.debug(f"send_chunk{'!' if send_blank else ''}({self.chunk})")
        if self.chunk:
            retval = {
                "uri": self.uri,
                "pos": self.chunk.pos.get_identifier(),
                "text": self.text.strip(),
                "meta": self.chunk.pos.get_meta() if TUPLES_NOT_DICT else dict(self.chunk.pos.get_meta())}

            if send_blank or retval["text"]:
                self.yield_function(retval)
                self.header_sent = True

            self.text = ""

            return retval
        else:
            return None


class ElemPos:
    """
    an HTML Element node, including:
      a pointer to its Parent Element (or None if root element)
      a pointer to its "Nearest" Header (or None)

    'parent' is a singly-linked-list to the root.
    'head' is a chain of self-or-prior-sibling headers, "nearest by level."
    'tag' is the only other "semantic" data.
    'index' and 'child_elem_count' are merely for identification/debugging purposes.
    """

    def __init__(
        self,
        parent: "ElemPos",
        tag: str,
        head: "Header",
    ):

        if not tag:
            raise Exception(f"ElemPos({tag})")

        self.parent: ElemPos = parent
        self.tag: str = tag
        self.head: Header = head
        self.index: int = 1
        # mutable state, gets incremented by every child __init__:
        self.child_elem_count: int = 0

        if self.parent:
            self.parent.child_elem_count = 1 + self.parent.child_elem_count
            self.index = self.parent.child_elem_count

    def get_meta(self):
        return self.head.get_dict() if self.head else []

    # these functions only used for logging/debugging:
    def __str__(self):
        return f"{self.get_indent()}E{self.get_identifier()}"

    def get_depth(self):
        return 1 + (self.parent.get_depth() if self.parent else 0)

    def get_indent(self, offset: int = 0):
        return "  " * (offset + self.get_depth())

    def get_identifier(self):
        return (self.parent.get_identifier() if self.parent else "") \
            + f"[{self.index}]{self.tag}"

    def get_xpath(self):
        return (self.parent.get_xpath() if self.parent else "") \
            + f"/*[{self.index}]"


class Header:
    """
    an HTML Header Element node (i.e. H1 ... H6), including:
      a pointer to its "Nearest Prior Higher" Header (or None if there is none)
    """

    def __init__(
        self,
        prior_higher: "Header",
        elem: ElemPos
    ):

        if elem is None:
            raise Exception("Header(None)")
        if elem.tag not in ALL_HEADER_TAGS:
            raise Exception(f"bad header tag {elem.tag}")

        self.prior_higher: Header = prior_higher
        self.pos: ElemPos = elem
        self.level: int = int(elem.tag[1])
        self.depth: int = 1
        # mutable state, appended-to until header-tag is closed:
        self.text: str = ""

        # supersede prior if is a sibling and lower-level (higher number)
        while \
                self.prior_higher and \
                self.prior_higher.pos.parent == self.pos.parent and \
                self._is_lowerlevel_than_prior():
            self.prior_higher = self.prior_higher.prior_higher

        if self.prior_higher:
            self.depth = self.prior_higher.depth + self._is_lowerlevel_than_prior()
        else:
            self.depth = 1

    # this abstraction was required due to spurious compiler warnings
    def _is_lowerlevel_than_prior(self):
        return self.prior_higher.level >= self.level

    def get_dict(self):
        return (self.prior_higher.get_dict() if self.prior_higher else []) \
            + [self.get_val()]

    def get_val(self):
        return (f"D{self.depth} " if 1 < self.depth and not TUPLES_NOT_DICT else "") + self.pos.tag, self.text

    # these functions only used for logging/debugging:
    def __str__(self):
        return f"{self.pos.get_indent(1)}H{(self.get_header_path(), self.text)}"
        # return f"H{self.get_dict()}";

    def get_header_path(self):
        return (self.prior_higher.get_header_path() if self.prior_higher else "") \
            + ("~" if self.prior_higher and self.prior_higher.depth == self.depth else " / ") \
            + self.pos.tag


class ChunkPos:
    """
    a pointer to trace all "applicable" chunking elements (for a given position).
    this is informational-only, and it is not used-by / needed-for the actual chunking logic.
    """

    def __init__(
        self,
        parent_chunk: "ChunkPos",
        elem: ElemPos
    ):

        if elem is None:
            raise Exception("ChunkPos(elem=None)")

        self.par: ChunkPos = parent_chunk
        self.pos: ElemPos = elem

        # if this is a header, and chunk-parent is a prior-sibling, we're both Headers and
        # chunk-parent must have header-level less than this header-level.
        if self.pos.tag in ALL_HEADER_TAGS:
            while \
                    self.par and \
                    self.par.pos.parent == self.pos.parent and \
                    self.par.pos.head.level >= self.pos.head.level:
                self.par = self.par.par

    def get_chunk_path(self):
        return (self.par.get_chunk_path() + "/" if self.par else "") \
            + self.pos.tag

    def __str__(self):
        return f"{self.pos.get_indent(1)}C({self.get_chunk_path()})"


if __name__ == "__main__":
    import os
    from html_cleaver.util import parse_html
    
    main_verbose = False
    
    if main_verbose:
        logging.basicConfig(level=logging.DEBUG)
        main_callback = LOG.info
    else:
        main_callback = print
    handler = CleaverHandle(main_callback)
    
    uri_base = "https://presidiovantage.com/html-cleaver/"
    parse_html.xml_get_sax(uri_base + "test1basic.html", handler)
    parse_html.lxml_get_sax(uri_base + "test6illformed.html", handler)
    parse_html.selenium_get_sax(uri_base + "test7javascript.html", handler)

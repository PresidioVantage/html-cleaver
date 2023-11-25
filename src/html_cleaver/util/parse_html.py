"""
contains utilities for parsing html into common structures e.g. dom/sax/etree.
methods are library-specific, and the libraries are imported optionally/lazily.

most libraries are light-weight (to initialize), and methods are single-source.
"""
import urllib.request
from typing import Optional, Callable
from io import StringIO
import logging

import xml.sax
from xml.sax.handler import ContentHandler
from xml.sax.xmlreader import Locator

LOG = logging.getLogger(__name__)


# **strict, built-in XML**

def xml_get_sax(
        source: any,
        handler: ContentHandler,
):
    # xml.sax sets null url for open HttpConnections
    # (it works fine for String paths/urls and FileIO)
    if not isinstance(source, str) and getattr(source, "url", None):
        handler.setDocumentLocator(SystemIdLocator(source.url))

    xml.sax.parse(source, handler)


# **LXML external library**

def lxml_get_sax(
        source: any,
        handler: ContentHandler,
):
    """
    requires lxml
    """
    import lxml.sax

    # lxml sax has zero support for setDocumentLocator
    system_id: Optional[str] = get_system_id(source)
    if system_id:
        handler.setDocumentLocator(SystemIdLocator(system_id))

    tree = _lxml_get_etree(source)  # TODO type-hint
    lxml.sax.saxify(tree, handler)


## TODO publicize once return type is resolved
def _lxml_get_etree(
        source: any,
) -> any:  # TODO best etree(lxml.html) return type?!
    """
    requires lxml
    """
    import lxml.html

    # lxml does not support http references?! (despite documentation otherwise)
    if isinstance(source, str) and (source.startswith("http://") or source.startswith("https://")):
        with urllib.request.urlopen(source) as c:
            tree = lxml.html.parse(c)
    else:
        tree = lxml.html.parse(source)

    LOG.debug(f"lxml_get_etree({source}): {tree}\n\t{tree.docinfo.URL}")

    return tree


# **Selenium external library**
def selenium_get_sax(
        source: str,
        handler: ContentHandler,
        selenium_webdriver=None,  # Optional[selenium.webdriver.remote.webdriver.WebDriver]
):
    """
    requires selenium and lxml
    """
    from . import render_selenium

    if selenium_webdriver is None:
        with render_selenium.selenium_get_driver() as driver:
            html = render_selenium.selenium_get_html(
                driver,
                source)
    else:
        html = render_selenium.selenium_get_html(
            selenium_webdriver,
            source)

    handler.setDocumentLocator(SystemIdLocator(source))
    lxml_get_sax(StringIO(html), handler)


# **Utilities**

def get_system_id(
        source: any
) -> Optional[str]:
    system_id: Optional[str] = None

    # string represents a url or filename
    if isinstance(source, str):
        system_id = source
    # e.g. a url-connection e.g. urllib.request.urlopen(<url>)
    elif getattr(source, "url", None):
        system_id = source.url
    # e.g. a file e.g. open(<filename>, "r")
    elif getattr(source, "name", None):
        system_id = source.name

    return system_id


class SystemIdLocator(Locator):
    """
    simple adapter to obtain a Locator from a system-id alone
    """

    def __init__(self, system_id):
        self.system_id = system_id

    def getSystemId(self):
        return self.system_id


class CallbackHandler(ContentHandler):
    """
    primarily for testing/debugging
    """

    def __init__(
            self,
            callback: Callable[[tuple], any],
            whitespace: bool = False
    ):
        super().__init__()
        self.callback: Callable[[tuple], any] = callback
        self.whitespace: bool = whitespace

    def setDocumentLocator(self, loc: Locator):
        self.callback(
            ('setDocumentLocator', loc))

    def startDocument(self):
        self.callback(
            ('startDocument',))

    def endDocument(self):
        self.callback(
            ('endDocument',))

    def startElement(self, name: str, attrs):
        self.callback(
            ('startElement', name, {x: attrs.getValue(x) for x in attrs.getNames()}))

    def endElement(self, name: str):
        self.callback(
            ('endElement', name))

    def startElementNS(self, nsname: tuple[str, str], qname: str, attrs):
        self.callback(
            ('startElementNS', nsname, qname, {x: attrs.getValue(x) for x in attrs.getNames()}))

    def endElementNS(self, nsname: tuple[str, str], qname: str):
        self.callback(
            ('endElementNS', nsname, qname))

    def characters(self, text: str):
        if self.whitespace or text.strip():
            self.callback(
                ('characters', text))


if __name__ == "__main__":
    main_verbose = False

    if main_verbose:
        logging.basicConfig(level=logging.DEBUG)
        main_callback = LOG.info
    else:
        main_callback = print
    main_handler = CallbackHandler(main_callback)

    xml_get_sax("../../test/test1basic.html", main_handler)
    lxml_get_sax("../../test/test6illformed.html", main_handler)
    selenium_get_sax("../../test/test7javascript.html", main_handler)

"""
selenium simulates a browser to "renders" a url/filepath (string)
into an html-string representation of that page *post-javascript-loading*.
"""

from typing import Literal, Optional
import logging

import pathlib
from os.path import abspath

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.service import Service
from selenium.webdriver.common.options import ArgOptions

LOG = logging.getLogger(__name__)

SUPPORTED_BROWSERS: type[Literal] = Literal[
    "chrome",
    "firefox",
]
DEFAULT_BROWSER: str = "chrome"
# "=new" per https://www.selenium.dev/blog/2023/headless-is-going-away/
DEFAULT_ARGS: tuple[str] = (
    "--headless=new",
    # headless old:
    # "--headless",
    "--no-sandbox",
)


def selenium_get_html(
    driver: WebDriver,
    source: str,
) -> str:
    driver.get(_fix_url_for_file(source))
    html = driver.page_source
    LOG.debug(f"selenium_get_html({source}):\n\t{html}")
    return html
# sadly there's no adapter from selenium.webdriver.remote.webelement.WebElement to xml.dom and/or etree
# def selenium_get_dom(
#     driver: WebDriver,
#     source: str,
# ):
#     driver.get(_fix_url_for_file(source))
#
#     # jsresult: selenium.webdriver.remote.webelement.WebElement
#     jsresult = driver.execute_script(
#         # "return document")
#         "return document.documentElement")
#         # "return document.documentElement.outerHTML")
#     return jsresult


def selenium_get_driver(
    browser: SUPPORTED_BROWSERS = DEFAULT_BROWSER,
    selenium_arguments: tuple[str] = DEFAULT_ARGS,
    binary_location: Optional[str] = None,
    executable_path: Optional[str] = None,
) -> WebDriver:
    """
    Create and return a WebDriver instance based on the specified browser.
    It is the caller's responsibility call ".quit()" on the driver when finished (or use 'with').
    
    
    Args:
        selenium_arguments: for "chrome" with argument "--headless", "--no-sandbox" is also recommended.
    Raises:
        ValueError: If an invalid browser is specified.
    Returns:
        WebDriver: A Chrome|Firefox instance for the specified browser.
    """
    
    driver_class: type[WebDriver]
    service_class: type[Service]
    options_class: type[ArgOptions]
    driver_class, service_class, options_class = _selenium_get_driver_classes(browser)
    
    options: ArgOptions = options_class()
    if binary_location:
        options.binary_location = binary_location
    for arg in selenium_arguments:
        options.add_argument(arg)
    
    if executable_path:
        return driver_class(
            options=options,
            service=service_class(
                executable_path=executable_path))
    else:
        return driver_class(
            options=options)


def _selenium_get_driver_classes(
    browser: SUPPORTED_BROWSERS,
) -> tuple[type[WebDriver], type[Service], type[ArgOptions]]:
    """
    Create and return a WebDriver instance based on the specified browser.
    for chrome, if 'arguments' contains "--headless", then "--no-sandbox" is also recommended.
    Args:

    Raises:
        ValueError: If an invalid browser is specified.
    Returns:
        WebDriver: A Chrome|Firefox instance for the specified browser.
    """
    
    driver_class: type[WebDriver]
    service_class: type[Service]
    options_class: type[ArgOptions]
    
    match browser.lower():
        case "chrome":
            from selenium.webdriver import Chrome, ChromeService, ChromeOptions
            driver_class, service_class, options_class = Chrome, ChromeService, ChromeOptions
        case "firefox":
            from selenium.webdriver import Firefox, FirefoxService, FirefoxOptions
            driver_class, service_class, options_class = Firefox, FirefoxService, FirefoxOptions
        case _:
            raise ValueError(f"Invalid browser ({browser}) specified. Use 'chrome' or 'firefox'.")
    
    return driver_class, service_class, options_class


def _fix_url_for_file(
    source: str
) -> str:
    if not isinstance(source, str):
        raise Exception(f"source must be a string (either url or file location). got: {source}")
    if source.startswith("http://") or source.startswith("https://"):
        return source
    else:
        return pathlib.Path(abspath(source)).as_uri()

    
if __name__ == "__main__":
    with selenium_get_driver() as x:
        test_driver = "test7javascript.html"
        y = selenium_get_html(x, test_driver)
        print(f"{test_driver}\n{y}")

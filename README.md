[![License: MIT](https://img.shields.io/badge/License-MIT-blue)](https://raw.githubusercontent.com/PresidioVantage/html-cleaver/main/LICENSE.txt)
[![GitHub Latest Release](https://img.shields.io/github/release/PresidioVantage/html-cleaver?logo=github)](https://github.com/PresidioVantage/html-cleaver/releases)

[![GitHub Latest Pre-Release](https://img.shields.io/github/release/PresidioVantage/html-cleaver?logo=github&include_prereleases&label=pre-release)](https://github.com/PresidioVantage/html-cleaver/releases)
[![GitHub Continuous Integration](https://github.com/PresidioVantage/html-cleaver/actions/workflows/html_cleaver_CI.yml/badge.svg)](https://github.com/PresidioVantage/html-cleaver/actions)

# HTML Cleaver 🍀🦫

Tool for parsing HTML into a chain of chunks with relevant headers.  

The API entry-point is in `src/html_cleaver/cleaver`.  
The logical algorithm and data-structures are in `src/html_cleaver/handler`.

This is a "tree-capitator" if you will,  
cleaving text apart and cleaving headers together.

### Installation:
`pip install html-cleaver`

Optionally, if you're working with HTML which requires javascript rendering:  
`pip install selenium`

### Testing:
`python -m unittest discover -s src`
The tests require Selenium.

### Example usage:
```python

from html_cleaver.cleaver import get_cleaver

# default parser is "lxml" for loose html
with get_cleaver() as cleaver:
    
    # example of favorable structure yielding high-quality chunks
    # (prints chunk-events directly)
    cleaver.parse_events(
        ["https://plato.stanford.edu/entries/goedel/"],
        print)
    
    # example of moderate structure yielding medium-quality chunks
    # (gets collection of chunks and loops through them)
    q = cleaver.parse_queue(
        ["https://en.wikipedia.org/wiki/Kurt_G%C3%B6del"])
    while q:
        print(q.popleft())
    
    # examples of challenging structure yielding poor-quality chunks
    # (loops through sequence of chunks from sequence of pages)
    l = [
        "https://www.gutenberg.org/cache/epub/56852/pg56852-images.html",
        "https://www.cnn.com/2023/09/25/opinions/opinion-vincent-doumeizel-seaweed-scn-climate-c2e-spc-intl"]
    for c in cleaver.parse_chunk_sequence(l):
        print(c)

# example of mitigating/improving challenging structure by focusing on certain headers
with get_cleaver("lxml", ["h4", "h5"]) as cleaver:
    cleaver.parse_events(
        ["https://www.gutenberg.org/cache/epub/56852/pg56852-images.html"],
        print)

# example of using selenium on a page which requires javascript to load contents
print("using default lxml produces very few chunks:")
with get_cleaver() as cleaver:
    cleaver.parse_events(
        ["https://www.youtube.com/watch?v=rfscVS0vtbw"],
        print)
print("using selenium produces many more chunks:")
with get_cleaver("selenium") as cleaver:
    cleaver.parse_events(
        ["https://www.youtube.com/watch?v=rfscVS0vtbw"],
        print)
```

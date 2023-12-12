[![License: MIT](https://img.shields.io/badge/License-MIT-blue)](https://raw.githubusercontent.com/PresidioVantage/html-cleaver/main/LICENSE.txt)
[![GitHub Latest Release](https://img.shields.io/github/release/PresidioVantage/html-cleaver?logo=github)](https://github.com/PresidioVantage/html-cleaver/releases)

[![GitHub Latest Pre-Release](https://img.shields.io/github/release/PresidioVantage/html-cleaver?logo=github&include_prereleases&label=pre-release)](https://github.com/PresidioVantage/html-cleaver/releases)
[![GitHub Continuous Integration](https://github.com/PresidioVantage/html-cleaver/actions/workflows/html_cleaver_CI.yml/badge.svg)](https://github.com/PresidioVantage/html-cleaver/actions)

# HTML Cleaver ![🍀](https://fonts.gstatic.com/s/e/notoemoji/15.0/1f340/512.png=s32 "clover")![🦫](https://fonts.gstatic.com/s/e/notoemoji/15.0/1f9ab/512.png=s32 "beaver")

Tool for parsing HTML into a chain of chunks with relevant headers.  

The API entry-point is in `src/html_cleaver/cleaver`.  
The logical algorithm and data-structures are in `src/html_cleaver/handler`.

This is a "tree-capitator" if you will,  
cleaving headers together while cleaving text apart.

## Quickstart:
`pip install html-cleaver`

Optionally, if you're working with HTML that requires javascript rendering:  
`pip install selenium`

Testing an example on the command-line:
`python -m html_cleaver.cleaver https://plato.stanford.edu/entries/goedel/`

### Example usage:
Cleaving pages of varying difficulties:

```python
from html_cleaver.cleaver import get_cleaver

# default parser is "lxml" for loose html
with get_cleaver() as cleaver:
    
    # handle chunk-events directly
    # (example of favorable structure yielding high-quality chunks)
    cleaver.parse_events(
        ["https://plato.stanford.edu/entries/goedel/"],
        print)
    
    # get collection of chunks
    # (example of moderate structure yielding medium-quality chunks)
    for c in cleaver.parse_chunk_sequence(
            ["https://en.wikipedia.org/wiki/Kurt_G%C3%B6del"]):
        print(c)
    
    # sequence of chunks from sequence of pages
    # (examples of challenging structure yielding poor-quality chunks/headers)
    l = [
        "https://www.gutenberg.org/cache/epub/56852/pg56852-images.html",
        "https://www.cnn.com/2023/09/25/opinions/opinion-vincent-doumeizel-seaweed-scn-climate-c2e-spc-intl",
        "https://www.space.com/november-full-moon-tonight-2023"]
    for c in cleaver.parse_chunk_sequence(l):
        print(c)

# example of mitigating/improving challenging structure by focusing on certain headers
with get_cleaver("lxml", ["h4", "h5"]) as cleaver:
    cleaver.parse_events(
        ["https://www.gutenberg.org/cache/epub/56852/pg56852-images.html"],
        print)
```

### Example usage with Selenium:
Using selenium on a page that requires javascript to load contents:

```python
from html_cleaver.cleaver import get_cleaver

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


## Development:
### Testing:
Testing without Poetry:  
`pip install lxml`  
`pip install selenium`  
`python -m unittest discover -s src`

Testing with Poetry:  
`poetry install`  
`poetry run pytest`

### Build:
Building from source:  
`rm dist/*`  
`python -m build`

Installing from the build:  
`pip install dist/*.whl`

Publishing from the build:  
`python -m twine upload --skip-existing -u __token__ -p $TESTPYPI_TOKEN --repository testpypi dist/*`  
`python -m twine upload --skip-existing -u __token__ -p $PYPI_TOKEN dist/*`

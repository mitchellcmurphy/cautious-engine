import re
import warnings

from bs4 import BeautifulSoup, Tag, XMLParsedAsHTMLWarning

# SEC filings are often declared as XML but are structurally HTML + inline
# XBRL; we deliberately parse with the HTML parser for table/tag semantics.
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

_STRIP_TAGS = ("script", "style", "ix:header")


def extract_text(html: str) -> str:
    """Converts a filing's (often inline-XBRL) HTML into plain text.

    Tables are flattened into one line per row (cells space-separated)
    rather than dropped, since financial highlights frequently live only
    inside tables. Inline-XBRL documents also carry a non-visible
    `<ix:header>` metadata block and ad-hoc `display:none` elements (raw
    XBRL facts not meant to be rendered) which are stripped so they don't
    bloat the text sent to the LLM.
    """
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(_STRIP_TAGS):
        tag.decompose()

    for hidden in soup.select('[style*="display:none"], [style*="display: none"]'):
        hidden.decompose()

    for table in soup.find_all("table"):
        _flatten_table(table)

    text = soup.get_text(separator="\n")
    return _collapse_whitespace(text)


def _flatten_table(table: Tag) -> None:
    lines = []
    for row in table.find_all("tr"):
        cells = [cell.get_text(strip=True) for cell in row.find_all(["td", "th"])]
        cells = [c for c in cells if c]
        if cells:
            lines.append(" | ".join(cells))
    table.replace_with("\n".join(lines))


def _collapse_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]*\n+", "\n\n", text)
    return text.strip()

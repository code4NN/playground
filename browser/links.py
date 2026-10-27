"""Parse and classify links from HTML."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class Link:
    href: str
    text: str

    def label(self, *, use_text: bool) -> str:
        if use_text:
            cleaned = " ".join(self.text.split())
            return cleaned or self.href
        return self.href


def _origin(url: str) -> str | None:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}".lower()


def extract_links(html: str, base_url: str) -> list[Link]:
    """
    Collect unique absolute http(s) links from anchor tags.

    Order follows first appearance in the document.
    """
    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    links: list[Link] = []

    for anchor in soup.find_all("a", href=True):
        raw_href = str(anchor.get("href", "")).strip()
        if not raw_href or raw_href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        absolute = urljoin(base_url, raw_href)
        parsed = urlparse(absolute)
        if parsed.scheme not in {"http", "https"}:
            continue

        # Drop fragment-only differences for uniqueness
        key = absolute.split("#", 1)[0]
        if key in seen:
            continue
        seen.add(key)

        text = anchor.get_text(" ", strip=True) or ""
        links.append(Link(href=key, text=text))

    return links


def partition_by_origin(links: list[Link], page_url: str) -> tuple[list[Link], list[Link]]:
    """Split links into (same_or_unknown_origin, different_origin)."""
    page_origin = _origin(page_url)
    same: list[Link] = []
    different: list[Link] = []

    for link in links:
        link_origin = _origin(link.href)
        if page_origin and link_origin and link_origin != page_origin:
            different.append(link)
        else:
            same.append(link)

    return same, different

"""Browser helpers: fetch pages and extract links."""

from .fetch import fetch_html, normalize_url
from .links import Link, extract_links, partition_by_origin

__all__ = [
    "Link",
    "extract_links",
    "fetch_html",
    "normalize_url",
    "partition_by_origin",
]

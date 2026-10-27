"""Fetch remote HTML for preview."""

from __future__ import annotations

from urllib.parse import urlparse

import requests

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; TinyBrowser/1.0; +https://localhost) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def normalize_url(raw: str) -> str:
    """Ensure the URL has a scheme so requests can fetch it."""
    value = (raw or "").strip()
    if not value:
        return ""
    parsed = urlparse(value)
    if not parsed.scheme:
        value = f"https://{value}"
    return value


def fetch_html(url: str, timeout: float = 15.0) -> tuple[str, str]:
    """
    Fetch HTML for `url`.

    Returns (final_url, html). Raises ValueError / requests.RequestException on failure.
    """
    target = normalize_url(url)
    if not target:
        raise ValueError("Enter a URL to fetch.")

    parsed = urlparse(target)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http and https URLs are supported.")

    response = requests.get(
        target,
        headers=DEFAULT_HEADERS,
        timeout=timeout,
        allow_redirects=True,
    )
    response.raise_for_status()

    content_type = (response.headers.get("Content-Type") or "").lower()
    if "html" not in content_type and not response.text.lstrip().lower().startswith(
        ("<!doctype", "<html")
    ):
        raise ValueError(f"Response does not look like HTML ({content_type or 'unknown type'}).")

    return response.url, response.text

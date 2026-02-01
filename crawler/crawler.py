"""Crawl a site starting from a seed URL."""

from typing import List
from urllib.parse import urljoin, urlparse

from config import get_config
from models import PageData

from .parser import fetch_page, parse_page


def _same_domain(base_url: str, link: str) -> bool:
    """Return True if link belongs to the same domain as base_url."""
    base = urlparse(base_url)
    other = urlparse(link)
    return base.netloc == other.netloc


def _normalize(url: str) -> str:
    """Normalize URL for deduplication (strip fragment, trailing slash)."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/") or "/"
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def crawl_site(seed_url: str, max_pages: int | None = None) -> List[PageData]:
    """
    Crawl up to max_pages starting from seed_url.

    Only follows same-domain links. Returns a list of PageData (one per page).

    Args:
        seed_url: Starting URL (e.g. https://example.com).
        max_pages: Max number of pages to crawl; uses config default if None.

    Returns:
        List of PageData for each successfully parsed page.
    """
    cfg = get_config()
    limit = max_pages if max_pages is not None else cfg.crawl.max_pages
    timeout = cfg.crawl.request_timeout_seconds
    user_agent = cfg.crawl.user_agent

    base_parsed = urlparse(seed_url)
    base_netloc = base_parsed.netloc
    to_visit: List[str] = [_normalize(seed_url)]
    visited: set[str] = set()
    results: List[PageData] = []

    while to_visit and len(results) < limit:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)

        status_code, html = fetch_page(url, timeout=timeout, user_agent=user_agent)
        if status_code != 200 or not html:
            continue

        page_data = parse_page(url, html, status_code=status_code)
        results.append(page_data)

        # Queue same-domain links we haven't seen
        for link in page_data.internal_links:
            norm = _normalize(link)
            if norm not in visited and norm not in to_visit and _same_domain(seed_url, link):
                to_visit.append(norm)

    return results

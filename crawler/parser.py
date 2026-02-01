"""Parse HTML into structured page data for audit checks."""

from typing import List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from models import PageData


def parse_page(url: str, html: str, status_code: int = 200) -> PageData:
    """
    Parse raw HTML into PageData for analyzers.

    Args:
        url: Page URL (used for resolving relative links).
        html: Raw HTML string.
        status_code: HTTP status code of the response.

    Returns:
        PageData with titles, meta, headings, links, forms, images.
    """
    soup = BeautifulSoup(html, "lxml")
    base = urlparse(url)

    # Title and meta
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None

    meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find(
        "meta", attrs={"property": "og:description"}
    )
    meta_description = None
    if meta_desc and meta_desc.get("content"):
        meta_description = meta_desc["content"].strip()

    # Headings in order
    headings: List[dict] = []
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        headings.append({"tag": tag.name, "text": tag.get_text(strip=True)})

    # Internal links (same host)
    internal_links: List[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        full = urljoin(url, href)
        parsed = urlparse(full)
        if parsed.netloc == base.netloc:
            internal_links.append(full)

    # Forms
    forms: List[dict] = []
    for form in soup.find_all("form"):
        action = form.get("action") or url
        action_full = urljoin(url, action)
        inputs = []
        for inp in form.find_all(["input", "textarea"]):
            name = inp.get("name")
            if name:
                inputs.append(
                    {
                        "name": name,
                        "type": inp.get("type", "text"),
                    }
                )
        forms.append({"action": action_full, "inputs": inputs})

    # Images (for alt check)
    images: List[dict] = []
    for img in soup.find_all("img"):
        images.append(
            {
                "src": urljoin(url, img.get("src", "")),
                "alt": img.get("alt"),
            }
        )

    # Snippet for heuristics (first 20k chars)
    html_snippet = html[:20_000] if html else None

    # Heuristic: common infinite-scroll patterns in HTML
    has_infinite_scroll_indicators = (
        "infinite" in html.lower()
        or "data-load-more" in html.lower()
        or "scroll-load" in html.lower()
    )

    return PageData(
        url=url,
        status_code=status_code,
        title=title,
        meta_description=meta_description,
        headings=headings,
        internal_links=list(dict.fromkeys(internal_links)),
        forms=forms,
        images=images,
        html_snippet=html_snippet,
        has_infinite_scroll_indicators=has_infinite_scroll_indicators,
    )


def fetch_page(url: str, timeout: int = 15, user_agent: Optional[str] = None) -> tuple[int, str]:
    """
    Fetch a single page. Returns (status_code, body_text).

    Args:
        url: URL to fetch.
        timeout: Request timeout in seconds.
        user_agent: Optional User-Agent header.

    Returns:
        (status_code, response text). On failure, (0, "").
    """
    headers = {"User-Agent": user_agent or "MAGEN-WebAudit/1.0"}
    try:
        r = requests.get(url, timeout=timeout, headers=headers)
        return r.status_code, r.text
    except requests.RequestException:
        return 0, ""

"""Crawler module: fetch and parse web pages."""

from .crawler import crawl_site
from .parser import parse_page

__all__ = ["crawl_site", "parse_page"]

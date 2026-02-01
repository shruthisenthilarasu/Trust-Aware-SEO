"""Configuration for the Trust-Aware Web Audit Tool."""

from dataclasses import dataclass
from typing import Optional
import os


@dataclass
class CrawlConfig:
    """Crawler settings."""

    max_pages: int = 50
    request_timeout_seconds: int = 15
    user_agent: str = (
        "MAGEN-WebAudit/1.0 (Trust-Aware SEO/UX Audit; +https://magen.trust)"
    )
    follow_same_domain_only: bool = True


@dataclass
class AppConfig:
    """Application configuration."""

    crawl: CrawlConfig = None
    debug: bool = False

    def __post_init__(self) -> None:
        if self.crawl is None:
            self.crawl = CrawlConfig(
                max_pages=int(os.environ.get("AUDIT_MAX_PAGES", "50")),
            )


def get_config() -> AppConfig:
    """Return application config (env-aware)."""
    return AppConfig(
        debug=os.environ.get("DEBUG", "").lower() in ("1", "true", "yes"),
    )

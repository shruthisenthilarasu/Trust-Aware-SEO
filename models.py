"""Shared data models for the audit tool."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class Severity(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class Impact(str, Enum):
    HUMANS = "Humans"
    BOTS = "Bots"
    BOTH = "Both"


class FixEffort(str, Enum):
    QUICK_WIN = "Quick win"
    MODERATE = "Moderate"
    COMPLEX = "Complex"


@dataclass
class AuditIssue:
    """A single finding from an audit check."""

    id: str
    title: str
    description: str
    category: str  # "SEO" | "UX" | "Trust"
    severity: Severity
    impact: Impact
    fix_effort: FixEffort
    why_it_matters: str
    how_to_fix: str
    affected_url: Optional[str] = None
    affected_element: Optional[str] = None  # e.g. selector or snippet
    raw_value: Optional[str] = None  # for debugging / display


@dataclass
class PageData:
    """Parsed data from a single crawled page."""

    url: str
    status_code: int
    title: Optional[str] = None
    meta_description: Optional[str] = None
    headings: List[dict] = field(default_factory=list)  # [{"tag": "h1", "text": "..."}]
    internal_links: List[str] = field(default_factory=list)
    forms: List[dict] = field(default_factory=list)
    images: List[dict] = field(default_factory=list)
    load_time_ms: Optional[float] = None
    content_length: Optional[int] = None
    html_snippet: Optional[str] = None  # first N chars for heuristics
    has_infinite_scroll_indicators: bool = False


@dataclass
class AuditScores:
    """Three scores 0-100."""

    seo_health: float
    ux_clarity: float
    trust_exposure: float  # lower = less exposed (better)


@dataclass
class AuditReport:
    """Full audit result."""

    target_url: str
    pages_crawled: int
    scores: AuditScores
    issues: List[AuditIssue]
    quick_wins: List[AuditIssue] = field(default_factory=list)

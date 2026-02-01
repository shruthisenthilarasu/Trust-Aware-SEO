"""Run all analyzers and collect issues."""

from typing import List

from models import AuditIssue, PageData

from .seo import SEOAnalyzer
from .ux import UXAnalyzer
from .trust import TrustAnalyzer


def run_all_analyzers(pages: List[PageData]) -> List[AuditIssue]:
    """
    Run SEO, UX, and Trust analyzers on crawled pages.

    Args:
        pages: List of PageData from the crawler.

    Returns:
        Combined list of AuditIssue from all analyzers.
    """
    analyzers = [SEOAnalyzer(), UXAnalyzer(), TrustAnalyzer()]
    issues: List[AuditIssue] = []
    for analyzer in analyzers:
        issues.extend(analyzer.analyze(pages))
    return issues

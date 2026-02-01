"""Base class for audit analyzers."""

from abc import ABC, abstractmethod
from typing import List

from models import AuditIssue, PageData


class BaseAnalyzer(ABC):
    """Base for SEO, UX, and Trust analyzers. Subclass and implement analyze()."""

    name: str = "base"
    category: str = "General"

    @abstractmethod
    def analyze(self, pages: List[PageData]) -> List[AuditIssue]:
        """
        Run checks on crawled pages and return issues.

        Args:
            pages: List of parsed PageData from the crawler.

        Returns:
            List of AuditIssue (can be empty).
        """
        pass

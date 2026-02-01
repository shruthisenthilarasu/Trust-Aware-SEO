"""UX checks: human vs. bot experience, layout, load, navigation depth."""

from typing import List

from models import AuditIssue, PageData, Severity, Impact, FixEffort

from .base import BaseAnalyzer


class UXAnalyzer(BaseAnalyzer):
    """Checks for UX issues that often affect humans more than bots."""

    name = "ux"
    category = "UX"

    def analyze(self, pages: List[PageData]) -> List[AuditIssue]:
        issues: List[AuditIssue] = []

        for page in pages:
            # 1) Infinite scroll without pagination fallback (heuristic: we detect scroll patterns in HTML)
            if page.has_infinite_scroll_indicators:
                issues.append(
                    AuditIssue(
                        id="ux-infinite-scroll-no-fallback",
                        title="Infinite scroll without pagination fallback",
                        description="Page appears to use infinite scroll with no obvious pagination or anchor links.",
                        category=self.category,
                        severity=Severity.MEDIUM,
                        impact=Impact.HUMANS,
                        fix_effort=FixEffort.MODERATE,
                        why_it_matters="Infinite scroll makes it hard to bookmark, share, or return to a specific item. Bots can follow scroll; humans get lost. Accessibility and keyboard users suffer.",
                        how_to_fix="Add a 'Load more' or pagination (e.g. /page/2) so users and assistive tech can reach content predictably.",
                        affected_url=page.url,
                    )
                )

            # 2) Very large HTML (proxy for heavy JS / slow for humans)
            if page.html_snippet and len(page.html_snippet) > 500_000:
                issues.append(
                    AuditIssue(
                        id="ux-heavy-page",
                        title="Very large page size",
                        description=f"Page HTML is very large (>500KB), which can slow load for users.",
                        category=self.category,
                        severity=Severity.LOW,
                        impact=Impact.HUMANS,
                        fix_effort=FixEffort.MODERATE,
                        why_it_matters="Heavy pages load slowly on real devices and networks. Crawlers often get fast servers; users may not. This widens the human vs. bot experience gap.",
                        how_to_fix="Reduce HTML/JS size: lazy-load below-the-fold content, code-split, and minimize render-blocking resources.",
                        affected_url=page.url,
                        raw_value=f"~{len(page.html_snippet) // 1024} KB",
                    )
                )

            # 3) Critical content only in JS (heuristic: little text in first chunk)
            if page.html_snippet:
                text_len = sum(len(t) for t in page.html_snippet.split(">") if "<" not in t)
                if len(page.html_snippet) > 10_000 and text_len < 500:
                    issues.append(
                        AuditIssue(
                            id="ux-js-heavy-content",
                            title="Content may be loaded mainly via JavaScript",
                            description="Most of the page body appears to be scripts or structure; little visible text in initial HTML.",
                            category=self.category,
                            severity=Severity.MEDIUM,
                            impact=Impact.HUMANS,
                            fix_effort=FixEffort.COMPLEX,
                            why_it_matters="If critical content is only injected by JS, users on slow devices or with JS disabled see little. Bots that execute JS get the content; others don't.",
                            how_to_fix="Ensure key content is in the initial HTML where possible, or provide a noscript/static fallback for critical info.",
                            affected_url=page.url,
                        )
                    )

        return issues

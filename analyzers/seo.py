"""SEO checks: meta tags, headings, links, alt text, indexability."""

from typing import List

from models import AuditIssue, PageData, Severity, Impact, FixEffort

from .base import BaseAnalyzer


class SEOAnalyzer(BaseAnalyzer):
    """Checks for common SEO issues."""

    name = "seo"
    category = "SEO"

    def analyze(self, pages: List[PageData]) -> List[AuditIssue]:
        issues: List[AuditIssue] = []

        # 1) Missing or duplicate meta description
        seen_descriptions: set[str] = set()
        for page in pages:
            if not page.meta_description or not page.meta_description.strip():
                issues.append(
                    AuditIssue(
                        id="seo-missing-meta-description",
                        title="Missing meta description",
                        description=f"Page has no meta description.",
                        category=self.category,
                        severity=Severity.MEDIUM,
                        impact=Impact.BOTH,
                        fix_effort=FixEffort.QUICK_WIN,
                        why_it_matters="Search engines and users rely on descriptions for snippets. Missing descriptions can hurt CTR and clarity.",
                        how_to_fix="Add a <meta name=\"description\" content=\"...\"> with a concise 150–160 character summary of the page.",
                        affected_url=page.url,
                    )
                )
            elif page.meta_description.strip() in seen_descriptions:
                issues.append(
                    AuditIssue(
                        id="seo-duplicate-meta-description",
                        title="Duplicate meta description",
                        description=f"Same meta description used on another page.",
                        category=self.category,
                        severity=Severity.LOW,
                        impact=Impact.BOTH,
                        fix_effort=FixEffort.QUICK_WIN,
                        why_it_matters="Duplicate descriptions make pages look identical to search engines and can dilute relevance.",
                        how_to_fix="Write a unique meta description for each page that reflects its specific content.",
                        affected_url=page.url,
                        raw_value=page.meta_description[:80],
                    )
                )
            else:
                seen_descriptions.add(page.meta_description.strip())

        # 2) Missing or multiple H1
        for page in pages:
            h1s = [h for h in page.headings if h["tag"] == "h1"]
            if not h1s:
                issues.append(
                    AuditIssue(
                        id="seo-missing-h1",
                        title="Missing H1 heading",
                        description="Page has no H1 heading.",
                        category=self.category,
                        severity=Severity.MEDIUM,
                        impact=Impact.BOTH,
                        fix_effort=FixEffort.QUICK_WIN,
                        why_it_matters="H1 helps search engines and users understand the main topic. One clear H1 improves SEO and accessibility.",
                        how_to_fix="Add a single <h1> that describes the main purpose of the page.",
                        affected_url=page.url,
                    )
                )
            elif len(h1s) > 1:
                issues.append(
                    AuditIssue(
                        id="seo-multiple-h1",
                        title="Multiple H1 headings",
                        description=f"Page has {len(h1s)} H1 headings; typically one is preferred.",
                        category=self.category,
                        severity=Severity.LOW,
                        impact=Impact.BOTH,
                        fix_effort=FixEffort.MODERATE,
                        why_it_matters="Multiple H1s can dilute topical focus and confuse assistive tech and crawlers.",
                        how_to_fix="Use one H1 for the main title and H2–H6 for sections.",
                        affected_url=page.url,
                        raw_value=", ".join(h["text"][:40] for h in h1s[:3]),
                    )
                )

        # 3) Images missing alt text
        for page in pages:
            missing_alt = [img for img in page.images if img.get("alt") is None or not str(img.get("alt", "")).strip()]
            if missing_alt:
                issues.append(
                    AuditIssue(
                        id="seo-missing-alt",
                        title="Images missing alt text",
                        description=f"{len(missing_alt)} image(s) without alt text.",
                        category=self.category,
                        severity=Severity.MEDIUM,
                        impact=Impact.HUMANS,
                        fix_effort=FixEffort.QUICK_WIN,
                        why_it_matters="Alt text is essential for accessibility and gives search engines context. Missing alt hurts screen reader users and image SEO.",
                        how_to_fix="Add meaningful alt attributes to every <img>. Use alt=\"\" only for purely decorative images.",
                        affected_url=page.url,
                        affected_element=f"{len(missing_alt)} images",
                    )
                )

        return issues

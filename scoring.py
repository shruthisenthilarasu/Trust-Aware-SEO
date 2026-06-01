"""Compute SEO, UX, and Trust scores from audit issues."""

from typing import List

from models import AuditIssue, AuditScores, FixEffort, Impact, Severity


# Points deducted per issue by (severity, category)
# Higher score = better. Penalties deducted per issue severity.
SEVERITY_PENALTY = {
    Severity.HIGH: 10,
    Severity.MEDIUM: 5,
    Severity.LOW: 2,
}


def _score_for_category(issues: List[AuditIssue], category: str) -> float:
    """Compute 0-100 score for one category. Start at 100, subtract penalties.

    Each distinct issue ID counts once — the same problem on 10 pages is one
    finding, not 10 penalties.
    """
    category_issues = [i for i in issues if i.category == category]
    seen: set[str] = set()
    unique_issues = [i for i in category_issues if not (i.id in seen or seen.add(i.id))]
    penalty = sum(SEVERITY_PENALTY.get(i.severity, 5) for i in unique_issues)
    raw = max(0.0, 100.0 - penalty)
    return round(min(100.0, raw), 1)


def compute_scores(issues: List[AuditIssue]) -> AuditScores:
    """Compute SEO Health, UX Clarity, and Trust Safety scores (0-100, higher = better)."""
    return AuditScores(
        seo_health=_score_for_category(issues, "SEO"),
        ux_clarity=_score_for_category(issues, "UX"),
        trust_safety=_score_for_category(issues, "Trust"),
    )


def get_quick_wins(issues: List[AuditIssue]) -> List[AuditIssue]:
    """Return issues that are Quick win and High or Medium severity (high impact, low effort)."""
    return [
        i
        for i in issues
        if i.fix_effort == FixEffort.QUICK_WIN
        and i.severity in (Severity.HIGH, Severity.MEDIUM)
    ]

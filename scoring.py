"""Compute SEO, UX, and Trust scores from audit issues."""

from typing import List

from models import AuditIssue, AuditScores, FixEffort, Impact, Severity


# Points deducted per issue by (severity, category)
# Trust exposure: more issues = higher exposure = lower score (we want lower exposure = higher score)
SEVERITY_PENALTY = {
    Severity.HIGH: 15,
    Severity.MEDIUM: 8,
    Severity.LOW: 3,
}


def _score_for_category(issues: List[AuditIssue], category: str) -> float:
    """
    Compute 0-100 score for one category.
    Start at 100, subtract penalties. Trust: lower exposure = higher score.
    """
    category_issues = [i for i in issues if i.category == category]
    penalty = sum(SEVERITY_PENALTY.get(i.severity, 5) for i in category_issues)
    raw = max(0.0, 100.0 - penalty)
    return round(min(100.0, raw), 1)


def compute_scores(issues: List[AuditIssue]) -> AuditScores:
    """
    Compute SEO Health, UX Clarity, and Trust Exposure scores (0-100).

    For Trust Exposure: 100 = no exposure (best), 0 = many high-severity issues (worst).
    """
    return AuditScores(
        seo_health=_score_for_category(issues, "SEO"),
        ux_clarity=_score_for_category(issues, "UX"),
        trust_exposure=_score_for_category(issues, "Trust"),
    )


def get_quick_wins(issues: List[AuditIssue]) -> List[AuditIssue]:
    """Return issues that are Quick win and High or Medium severity (high impact, low effort)."""
    return [
        i
        for i in issues
        if i.fix_effort == FixEffort.QUICK_WIN
        and i.severity in (Severity.HIGH, Severity.MEDIUM)
    ]

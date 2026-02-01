"""Generate HTML audit report from AuditReport."""

from pathlib import Path
from typing import List

from jinja2 import Environment, FileSystemLoader, select_autoescape

from models import AuditIssue, AuditReport, AuditScores


def _group_issues_by_category(issues: List[AuditIssue]) -> dict[str, List[AuditIssue]]:
    out: dict[str, List[AuditIssue]] = {"SEO": [], "UX": [], "Trust": []}
    for i in issues:
        if i.category in out:
            out[i.category].append(i)
    return out


def generate_html_report(report: AuditReport) -> str:
    """
    Render the audit report as HTML.

    Args:
        report: Full AuditReport (scores, issues, quick wins).

    Returns:
        HTML string.
    """
    templates_dir = Path(__file__).resolve().parent / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("report.html")

    grouped = _group_issues_by_category(report.issues)
    scores = report.scores

    return template.render(
        target_url=report.target_url,
        pages_crawled=report.pages_crawled,
        seo_score=scores.seo_health,
        ux_score=scores.ux_clarity,
        trust_score=scores.trust_exposure,
        issues_by_category=grouped,
        quick_wins=report.quick_wins,
        total_issues=len(report.issues),
    )

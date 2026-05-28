"""Generate HTML audit report from AuditReport."""

from pathlib import Path
from typing import List

from jinja2 import Environment, FileSystemLoader, select_autoescape

from models import AuditIssue, AuditReport, AuditScores

_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def _make_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )


def generate_index_html() -> str:
    return _make_env().get_template("index.html").render()


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
    template = _make_env().get_template("report.html")

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

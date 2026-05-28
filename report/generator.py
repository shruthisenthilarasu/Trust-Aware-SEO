"""Generate HTML audit report from AuditReport."""

from collections import defaultdict
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


def _rollup_issues(issues: List[AuditIssue]) -> List[dict]:
    """Group issues of the same type into rolled-up findings."""
    groups: dict[str, List[AuditIssue]] = defaultdict(list)
    for issue in issues:
        groups[issue.id].append(issue)

    rollups = []
    for group in groups.values():
        first = group[0]
        affected_urls = [i.affected_url for i in group if i.affected_url]
        rollups.append({
            "id": first.id,
            "title": first.title,
            "description": first.description,
            "category": first.category,
            "severity": first.severity,
            "impact": first.impact,
            "fix_effort": first.fix_effort,
            "why_it_matters": first.why_it_matters,
            "how_to_fix": first.how_to_fix,
            "count": len(group),
            "affected_urls": affected_urls,
            "raw_value": first.raw_value,
        })
    return rollups


def _group_rollups_by_category(rollups: List[dict]) -> dict[str, List[dict]]:
    out: dict[str, List[dict]] = {"SEO": [], "UX": [], "Trust": []}
    for r in rollups:
        if r["category"] in out:
            out[r["category"]].append(r)
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

    rollups = _rollup_issues(report.issues)
    grouped = _group_rollups_by_category(rollups)
    quick_win_rollups = _rollup_issues(report.quick_wins)
    scores = report.scores

    return template.render(
        target_url=report.target_url,
        pages_crawled=report.pages_crawled,
        seo_score=scores.seo_health,
        ux_score=scores.ux_clarity,
        trust_score=scores.trust_exposure,
        issues_by_category=grouped,
        quick_wins=quick_win_rollups,
        total_issues=len(rollups),
    )

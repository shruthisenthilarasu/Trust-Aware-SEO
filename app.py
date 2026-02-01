"""
Trust-Aware Web Audit Tool — FastAPI app.

Run: uvicorn app:app --reload
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from config import get_config
from crawler import crawl_site
from analyzers import run_all_analyzers
from scoring import compute_scores, get_quick_wins
from report import generate_html_report
from models import AuditReport, AuditScores

app = FastAPI(
    title="Trust-Aware Web Audit Tool",
    description="Crawls sites and reports SEO, UX, and trust/bot-exposure issues for MAGEN Trust.",
    version="0.1.0",
)


def run_audit(target_url: str, max_pages: int | None = None) -> AuditReport:
    """Crawl target, run analyzers, score, and build report."""
    config = get_config()
    limit = max_pages if max_pages is not None else config.crawl.max_pages

    pages = crawl_site(target_url, max_pages=limit)
    if not pages:
        raise HTTPException(
            status_code=422,
            detail=f"Could not crawl any pages from {target_url}. Check URL and connectivity.",
        )

    issues = run_all_analyzers(pages)
    scores = compute_scores(issues)
    quick_wins = get_quick_wins(issues)

    return AuditReport(
        target_url=target_url,
        pages_crawled=len(pages),
        scores=scores,
        issues=issues,
        quick_wins=quick_wins,
    )


@app.get("/")
def root() -> dict:
    """Health / info."""
    return {
        "name": "Trust-Aware Web Audit Tool",
        "docs": "/docs",
        "audit": "GET /audit?url=<target_url>",
    }


@app.get("/audit", response_class=HTMLResponse)
def audit(
    url: str = Query(..., description="Target URL to audit"),
    max_pages: int | None = Query(None, ge=1, le=100, description="Max pages to crawl (default from config)"),
) -> HTMLResponse:
    """
    Run a full audit on the given URL and return an HTML report.
    """
    report = run_audit(url, max_pages=max_pages)
    html = generate_html_report(report)
    return HTMLResponse(html)


@app.get("/audit/json")
def audit_json(
    url: str = Query(..., description="Target URL to audit"),
    max_pages: int | None = Query(None, ge=1, le=100),
) -> dict:
    """Run audit and return report as JSON (for API consumers)."""
    report = run_audit(url, max_pages=max_pages)
    return {
        "target_url": report.target_url,
        "pages_crawled": report.pages_crawled,
        "scores": {
            "seo_health": report.scores.seo_health,
            "ux_clarity": report.scores.ux_clarity,
            "trust_exposure": report.scores.trust_exposure,
        },
        "total_issues": len(report.issues),
        "quick_wins_count": len(report.quick_wins),
        "issues": [
            {
                "id": i.id,
                "title": i.title,
                "category": i.category,
                "severity": i.severity.value,
                "impact": i.impact.value,
                "fix_effort": i.fix_effort.value,
                "affected_url": i.affected_url,
            }
            for i in report.issues
        ],
    }

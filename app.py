"""
Trust-Aware Web Audit Tool — FastAPI app.

Run: uvicorn app:app --reload
"""

import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from config import get_config
from crawler import crawl_site
from analyzers import run_all_analyzers
from scoring import compute_scores, get_quick_wins
from report import generate_html_report, generate_index_html
from models import AuditReport

app = FastAPI(
    title="Trust-Aware Web Audit Tool",
    description="Crawls sites and reports SEO, UX, and trust/bot-exposure issues.",
    version="0.2.0",
)


# ---------------------------------------------------------------------------
# Job store
# ---------------------------------------------------------------------------

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


@dataclass
class Job:
    id: str
    url: str
    status: JobStatus = JobStatus.PENDING
    phase: str = "crawling"   # crawling | analyzing | reporting
    html: Optional[str] = None
    error: Optional[str] = None


_jobs: dict[str, Job] = {}


def _run_audit_job(job_id: str, target_url: str, max_pages: Optional[int]) -> None:
    job = _jobs[job_id]
    try:
        config = get_config()
        limit = max_pages if max_pages is not None else config.crawl.max_pages

        job.status = JobStatus.RUNNING
        job.phase = "crawling"
        pages = crawl_site(target_url, max_pages=limit)
        if not pages:
            job.status = JobStatus.ERROR
            job.error = f"Could not crawl any pages from {target_url}. Check the URL and try again."
            return

        job.phase = "analyzing"
        issues = run_all_analyzers(pages)
        scores = compute_scores(issues)
        quick_wins = get_quick_wins(issues)

        job.phase = "reporting"
        report = AuditReport(
            target_url=target_url,
            pages_crawled=len(pages),
            scores=scores,
            issues=issues,
            quick_wins=quick_wins,
        )
        job.html = generate_html_report(report)
        job.status = JobStatus.DONE

    except Exception as exc:
        job.status = JobStatus.ERROR
        job.error = str(exc) or "Unexpected error during audit."


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def root() -> HTMLResponse:
    return HTMLResponse(generate_index_html())


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "0.2.0", "docs": "/docs"}


@app.get("/audit/start")
def audit_start(
    background_tasks: BackgroundTasks,
    url: str = Query(..., description="Target URL to audit"),
    max_pages: Optional[int] = Query(None, ge=1, le=100),
) -> dict:
    job_id = uuid.uuid4().hex[:10]
    _jobs[job_id] = Job(id=job_id, url=url)
    background_tasks.add_task(_run_audit_job, job_id, url, max_pages)
    return {"job_id": job_id}


@app.get("/audit/status/{job_id}")
def audit_status(job_id: str) -> dict:
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return {"status": job.status, "phase": job.phase, "error": job.error}


@app.get("/audit/result/{job_id}", response_class=HTMLResponse)
def audit_result(job_id: str) -> HTMLResponse:
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.status != JobStatus.DONE:
        raise HTTPException(status_code=409, detail=f"Job is {job.status}.")
    return HTMLResponse(job.html)


@app.get("/audit/json")
def audit_json(
    url: str = Query(..., description="Target URL to audit"),
    max_pages: Optional[int] = Query(None, ge=1, le=100),
) -> dict:
    """Synchronous audit returning JSON — for API consumers and the CLI."""
    config = get_config()
    limit = max_pages if max_pages is not None else config.crawl.max_pages
    pages = crawl_site(url, max_pages=limit)
    if not pages:
        raise HTTPException(status_code=422, detail=f"Could not crawl any pages from {url}.")
    issues = run_all_analyzers(pages)
    scores = compute_scores(issues)
    quick_wins = get_quick_wins(issues)
    report = AuditReport(
        target_url=url,
        pages_crawled=len(pages),
        scores=scores,
        issues=issues,
        quick_wins=quick_wins,
    )
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

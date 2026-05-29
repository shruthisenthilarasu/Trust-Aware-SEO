# Trust-Aware Web Audit Tool

Audit any website for **SEO health**, **UX clarity**, and **trust/bot exposure** — the dimension traditional SEO tools miss entirely.

Originally prototyped as a feature for a cybersecurity startup in San Antonio, TX. The core insight: most SEO audits don't ask whether your site is *easier for bots to use than for real people*. This one does.

---

## What you get

Submit a URL and get back a prioritized HTML report with three scores (0–100) and actionable fixes:

| Score | What it measures |
|---|---|
| **SEO Health** | Meta tags, headings, alt text, crawlability |
| **UX Clarity** | Page weight, JS-heavy content, navigation friction |
| **Trust Exposure** | Open endpoints, predictable URLs, form vulnerabilities, scraping surfaces |

Each finding explains what's wrong, who it affects (humans, bots, or both), and exactly how to fix it. High-impact, low-effort fixes are surfaced first as **Quick Wins**.

---

## Why trust exposure matters

Traditional audits catch missing alt text. This tool also catches:

- **Open search/filter endpoints** with no rate limiting — easy targets for bulk scraping
- **Sequential numeric IDs** in URLs — lets bots enumerate your entire content
- **Public forms without friction** — no CAPTCHA, no honeypot, wide open to spam
- **JS-heavy pages** that crawlers handle fine but real users wait for
- **Infinite scroll without pagination fallback** — bots parse the DOM; humans get stuck

---

## Deploy to Render

1. Fork or push this repo to GitHub
2. Go to [render.com](https://render.com) → **New** → **Web Service**
3. Connect your GitHub repo
4. Render detects the `Dockerfile` automatically — leave settings as defaults
5. Click **Deploy**

Your app will be live at `https://<your-service>.onrender.com` in a few minutes.

> **Note:** The free tier spins down after 15 minutes of inactivity. The first request after idle takes ~30 seconds to cold-start. This is a Render free tier limitation, not a bug.

**Environment variables** (set in Render dashboard → Environment):

| Variable | Default | Description |
|---|---|---|
| `AUDIT_MAX_PAGES` | `20` | Keep this at 20 or lower on the free tier to avoid timeouts |
| `DEBUG` | `false` | |

---

## Quick start

```bash
git clone https://github.com/shruthisenthilarasu/Trust-Aware-SEO.git
cd Trust-Aware-SEO
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Web app

```bash
uvicorn app:app --reload
```

Open **http://localhost:8000** — enter any URL and run an audit from the browser.

| Endpoint | Description |
|---|---|
| `GET /` | Landing page with audit form |
| `GET /audit/start?url=<url>` | Start an async audit, returns `job_id` |
| `GET /audit/status/<job_id>` | Poll for status: `pending` → `running` → `done` |
| `GET /audit/result/<job_id>` | Fetch the completed HTML report |
| `GET /audit/json?url=<url>` | Synchronous audit returning JSON |
| `GET /docs` | Interactive API docs (Swagger) |

### CLI

```bash
python cli.py https://example.com --max-pages 10 --output report.html
```

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `AUDIT_MAX_PAGES` | `50` | Max pages to crawl per audit |
| `DEBUG` | `false` | Enable FastAPI debug mode |

---

## Adding a new check

1. Create a class in `analyzers/` extending `BaseAnalyzer`:

```python
class MyAnalyzer(BaseAnalyzer):
    def analyze(self, pages: List[PageData]) -> List[AuditIssue]:
        issues = []
        for page in pages:
            # your logic here
            issues.append(AuditIssue(
                id="my-check",
                title="...",
                category="SEO",  # SEO | UX | Trust
                severity=Severity.HIGH,
                impact=Impact.HUMANS,
                fix_effort=FixEffort.QUICK_WIN,
                description="...",
                why_it_matters="...",
                how_to_fix="...",
                affected_url=page.url,
            ))
        return issues
```

2. Register it in `analyzers/runner.py` → `run_all_analyzers()`.

---

## Project structure

```
├── app.py              # FastAPI app + async job endpoints
├── cli.py              # CLI interface
├── config.py           # Crawl limits, env vars
├── models.py           # AuditIssue, PageData, AuditReport
├── scoring.py          # 0–100 scores + quick wins
├── requirements.txt
├── crawler/
│   ├── crawler.py      # BFS crawler (same-domain)
│   └── parser.py       # HTML parsing with BeautifulSoup
├── analyzers/
│   ├── seo.py          # Meta, H1, alt text
│   ├── ux.py           # Page weight, JS content, infinite scroll
│   ├── trust.py        # Endpoints, URLs, forms, query params
│   └── runner.py       # Runs all analyzers
├── report/
│   ├── generator.py
│   └── templates/
│       ├── index.html  # Landing page
│       └── report.html # Audit report
└── examples/
    ├── sample-report.html
    └── sample-report.json
```

---

## Tech stack

- **FastAPI** — async web framework with background task support
- **Requests + BeautifulSoup** — crawling and HTML parsing
- **Jinja2** — report templating
- **Python 3.11+**

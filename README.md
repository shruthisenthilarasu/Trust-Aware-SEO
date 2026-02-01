# Trust-Aware Web Audit Tool

A web audit tool for **MAGEN Trust** that goes beyond traditional SEO and UX checks to surface **trust and bot exposure** issues. It identifies patterns that make sites easy for automation to scrape while frustrating real users—exactly the surface area MAGEN protects.

## 🎯 Why This Tool Exists

Traditional SEO audits miss a critical dimension: **trust and bot exposure**. Many nonprofit and small business sites are:

- **Easy for bots to scrape but hard for humans to use** — predictable URLs, open search endpoints, and forms without friction invite automation while confusing real users.
- **Vulnerable to automation without realizing it** — scraping, spam, and data harvesting thrive where there’s no rate limiting or friction.
- **Unintentionally widening the human vs. bot gap** — JS-heavy content, infinite scroll without fallback, and slow loads affect humans more than crawlers.

This tool bridges SEO/UX analysis with security thinking—identifying patterns that affect both user experience and site vulnerability. Built with inspiration from [MAGEN Trust](https://magentrust.com)’s work on distinguishing human vs. automated behavior.

## What it does

- **Standard SEO**: meta tags, headings, internal links, alt text, indexability
- **UX issues that favor bots over humans**: infinite scroll without fallback, JS-heavy content, heavy pages, layout/load concerns
- **Trust & bot exposure**: open endpoints, predictable URLs, forms without friction, excessive query parameters

The tool produces a **prioritized HTML report** with three scores (0–100), issues grouped by category, and a **Quick Wins** section (high-impact, low-effort fixes). Each issue explains why it matters, who it impacts (humans, bots, or both), and how to fix it.

### Trust & Bot Exposure Checks

What sets this apart from traditional SEO tools:

- **🤖 Open endpoints** — Detects search pages, filters, and forms without rate limiting
- **🔍 Predictable URLs** — Identifies sequential IDs and guessable path patterns
- **📝 Form vulnerabilities** — Flags public forms lacking CAPTCHA or honeypots
- **🎯 Scraping vectors** — Finds pages with excessive queryable parameters
- **👤 Human vs. bot UX** — Spots patterns that favor automation over real users

## Tech stack

- **Python**: FastAPI backend, Requests + BeautifulSoup for crawling
- **Analyzers**: Modular SEO, UX, and Trust checks (easy to extend)
- **Scoring**: Heuristic 0–100 scores for SEO Health, UX Clarity, Trust Exposure
- **Report**: Jinja2 HTML template; optional PDF via WeasyPrint

## 📊 Example Output

See what a report looks like before running the tool:

- **[Sample HTML report](examples/sample-report.html)** — Full audit report (scores, quick wins, issues by category). Open in a browser.
- **[Sample JSON](examples/sample-report.json)** — Same audit as JSON for API consumers.

To regenerate examples after changing the tool:

```bash
python cli.py https://example.com --max-pages 3 --output examples/sample-report.html
```

## Documentation

- **[System Design](docs/SYSTEM_DESIGN.md)** — Architecture, components, data flow, API, scalability, and trade-offs.

## Project structure

```
.
├── app.py              # FastAPI app (GET /audit?url=...)
├── cli.py              # CLI: python cli.py <url> [--output report.html]
├── config.py           # Crawl limits, user-agent
├── models.py           # AuditIssue, PageData, AuditReport, scores
├── scoring.py          # Score computation, quick wins
├── requirements.txt
├── examples/           # Sample report output (see Example Output above)
├── crawler/
│   ├── crawler.py      # crawl_site(seed_url, max_pages)
│   └── parser.py       # parse_page(), fetch_page()
├── analyzers/
│   ├── base.py         # BaseAnalyzer
│   ├── seo.py          # Meta, H1, alt text, etc.
│   ├── ux.py           # Infinite scroll, heavy page, JS-only content
│   ├── trust.py        # Open endpoints, predictable URLs, forms, query params
│   └── runner.py       # run_all_analyzers()
└── report/
    ├── generator.py    # generate_html_report()
    └── templates/
        └── report.html
```

## Quick start

### Install

```bash
cd "Trust-Aware SEO and UX Audit Tool"
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run as web app

```bash
uvicorn app:app --reload
```

Then open:

- **API docs**: http://127.0.0.1:8000/docs  
- **Audit report**: http://127.0.0.1:8000/audit?url=https://example.com  
- **JSON**: http://127.0.0.1:8000/audit/json?url=https://example.com  

### Run as CLI

```bash
python cli.py https://example.com --max-pages 10 --output report.html
```

## Configuration

- **Max pages**: Set `AUDIT_MAX_PAGES` (default 50) or pass `max_pages` in the API/CLI.
- **User-Agent**: Defined in `config.py` (MAGEN-WebAudit/1.0).

## Adding new checks

1. **New analyzer**: Create a class in `analyzers/` that extends `BaseAnalyzer` and implements `analyze(pages) -> List[AuditIssue]`.
2. **Register**: Add it to `run_all_analyzers()` in `analyzers/runner.py`.
3. **Issue fields**: Use `AuditIssue` with `category` one of `"SEO"`, `"UX"`, `"Trust"`, plus severity, impact, fix_effort, why_it_matters, how_to_fix.

---

Built for MAGEN Trust — explainable trust at the web layer.

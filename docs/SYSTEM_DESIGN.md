# Trust-Aware Web Audit Tool — System Design

System design document for the MAGEN Trust web audit tool: architecture, components, data flow, and trade-offs.

---

## 1. Overview & Goals

### Purpose

Build a tool that crawls websites and produces **prioritized audit reports** covering:

1. **SEO** — meta tags, headings, links, alt text, indexability  
2. **UX** — issues that affect humans more than bots (infinite scroll, JS-heavy content, heavy pages)  
3. **Trust / bot exposure** — patterns that increase scraping and automation surface (open endpoints, predictable URLs, forms without friction)

### Design Goals

- **Modular**: Add new checks without changing crawler or report layer  
- **Explainable**: Every issue has severity, impact (Humans/Bots/Both), fix effort, and plain-language “why” and “how to fix”  
- **Portfolio-friendly**: Simple stack (Python, FastAPI, Requests + BeautifulSoup), type hints, docstrings, no black-box ML  
- **Dual interface**: Web API (HTML + JSON) and CLI for scripting/CI

### Non-Goals (Current Scope)

- No headless browser (JS execution) — heuristics only  
- No ML; all rules are explicit heuristics  
- No persistent storage; each audit is request-scoped  
- No distributed crawling; single process, configurable page limit

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ENTRY POINTS                                    │
├─────────────────────────────────┬───────────────────────────────────────────┤
│  FastAPI (Web)                   │  CLI (cli.py)                              │
│  GET /audit?url=...              │  python cli.py <url> [--output file.html] │
│  GET /audit/json?url=...         │                                            │
└────────────────┬────────────────┴───────────────────┬───────────────────────┘
                 │                                     │
                 ▼                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATION (app.run_audit)                         │
│  1. Crawl → 2. Analyze → 3. Score → 4. Quick Wins → 5. Report               │
└─────────────────────────────────────────────────────────────────────────────┘
                 │
     ┌───────────┼───────────┬───────────────┬──────────────┐
     ▼           ▼           ▼               ▼              ▼
┌─────────┐ ┌─────────┐ ┌─────────┐   ┌──────────┐   ┌─────────────┐
│ Crawler │ │ Parser  │ │Analyzers│   │ Scoring  │   │   Report    │
│         │ │         │ │ SEO/UX  │   │ 0–100 x3 │   │ HTML / JSON │
│ BFS     │ │ BS4     │ │ Trust   │   │ Quick    │   │ Jinja2      │
│ same    │ │ extract │ │ heur.   │   │ wins     │   │ template    │
│ domain  │ │ links   │ │         │   │          │   │             │
└─────────┘ └─────────┘ └─────────┘   └──────────┘   └─────────────┘
     │           │           │               │              │
     └───────────┴───────────┴───────────────┴──────────────┘
                              │
                    ┌─────────┴─────────┐
                    │  Shared Models     │
                    │  PageData          │
                    │  AuditIssue        │
                    │  AuditReport       │
                    │  AuditScores       │
                    └───────────────────┘
```

**Data flow**: URL in → Crawler produces `List[PageData]` → Analyzers produce `List[AuditIssue]` → Scoring produces `AuditScores` + quick wins → Report produces HTML or JSON.

---

## 3. Component Design

### 3.1 Crawler

**Responsibility**: Discover and fetch pages from a seed URL, same-domain only, up to a configurable limit.

**Algorithm**:

- BFS from seed URL  
- Normalize URLs (strip fragment, trailing slash) for deduplication  
- Only enqueue links with same `netloc` as seed  
- Stop when `max_pages` reached or queue empty  

**Output**: `List[PageData]` (one per successfully fetched + parsed page).

**Config**: `max_pages` (default 50), `request_timeout_seconds`, `user_agent`, `follow_same_domain_only`.

**Trade-offs**:

- No sitemap parsing (could add for faster discovery)  
- No robots.txt enforcement (optional future)  
- Sequential fetch (could parallelize with a pool for speed)

---

### 3.2 Parser

**Responsibility**: Turn raw HTML into structured `PageData` for analyzers.

**Extracts**:

- Title, meta description (including og:description)  
- Heading list `[{tag, text}]`  
- Internal links (same host), deduplicated  
- Forms: action URL + input names/types  
- Images: src + alt  
- Optional: first N chars of HTML for heuristics (`html_snippet`)  
- Boolean flags, e.g. `has_infinite_scroll_indicators` (keyword heuristic in HTML)

**Dependencies**: `requests` for fetch, `BeautifulSoup` (lxml) for parse.

**Trade-offs**:

- No JS execution — “infinite scroll” and “JS-only content” are heuristics  
- No Lighthouse/performance yet — `load_time_ms` / `content_length` can be filled by a future performance step

---

### 3.3 Analyzers

**Responsibility**: Run rule-based checks on `List[PageData]` and emit `List[AuditIssue]`.

**Contract**: Each analyzer implements `BaseAnalyzer.analyze(pages: List[PageData]) -> List[AuditIssue]`.

| Analyzer | Category | Example checks |
|----------|----------|----------------|
| **SEO**  | SEO      | Missing/duplicate meta description; missing/multiple H1; images without alt |
| **UX**   | UX       | Infinite scroll without fallback; very large HTML; little text in initial HTML (JS-heavy heuristic) |
| **Trust**| Trust    | Open/search-like URLs; predictable numeric IDs in path; forms without CAPTCHA/CSRF/honeypot; excessive query params |

**Issue schema**: Each `AuditIssue` has `id`, `title`, `description`, `category`, `severity`, `impact`, `fix_effort`, `why_it_matters`, `how_to_fix`, optional `affected_url` / `affected_element` / `raw_value`.

**Runner**: `run_all_analyzers(pages)` runs SEO, UX, and Trust in sequence and concatenates issues. Order of analyzers is independent (stateless).

**Extensibility**: New analyzer = new class extending `BaseAnalyzer` + register in `run_all_analyzers()`.

---

### 3.4 Scoring

**Responsibility**: Convert `List[AuditIssue]` into three 0–100 scores and a “quick wins” list.

**Formula**:

- Start at 100 per category  
- Subtract a fixed penalty per issue by severity (e.g. High 15, Medium 8, Low 3)  
- Clamp to [0, 100]  

**Trust interpretation**: “Trust Exposure” score is “how well you’re protected”; higher = less exposed (fewer trust issues).

**Quick wins**: Issues where `fix_effort == Quick win` and `severity` in (High, Medium). Sorted by category in report; could be extended to sort by severity.

**Trade-offs**: No weighting by URL importance or recency; all pages treated equally. Could add weights later (e.g. homepage vs deep page).

---

### 3.5 Report

**Responsibility**: Turn `AuditReport` (scores + issues + quick wins) into HTML or JSON.

**HTML**:

- Jinja2 template with executive summary (three scores), Quick Wins section, then issues grouped by category (SEO, UX, Trust)  
- Each issue: title, tags (severity, impact, effort), description, “why it matters,” “how to fix,” affected URL  
- Self-contained CSS (dark theme); no JS required  

**JSON** (API): Same data as `AuditReport` flattened for API consumers (scores, issue list with id/title/category/severity/impact/fix_effort/affected_url).

**PDF**: Not implemented; could add WeasyPrint or similar on top of the same HTML.

---

## 4. Data Flow (Sequence)

```
Client          API/CLI       run_audit      Crawler      Parser       Analyzers      Scoring      Report
  │                │               │             │           │              │             │           │
  │  url           │               │             │           │              │             │           │
  │────────────────►               │             │           │             │             │           │
  │                │  crawl_site()  │             │           │              │             │           │
  │                │───────────────►│  BFS fetch  │           │              │             │           │
  │                │               │────────────►│  parse    │              │             │           │
  │                │               │             │──────────►│              │             │           │
  │                │               │             │  PageData │              │             │           │
  │                │               │◄────────────┴───────────┘              │             │           │
  │                │               │  run_all_analyzers(pages)              │             │           │
  │                │               │───────────────────────────────────────►│             │           │
  │                │               │               AuditIssue[]             │             │           │
  │                │               │◄─────────────────────────────────────┘             │           │
  │                │               │  compute_scores(); get_quick_wins()    │             │           │
  │                │               │──────────────────────────────────────────────────────►│           │
  │                │               │  AuditReport                           │             │           │
  │                │               │◄────────────────────────────────────────────────────┘           │
  │                │               │  generate_html_report(report)         │             │           │
  │                │               │──────────────────────────────────────────────────────────────────►│
  │                │               │  HTML / JSON                          │             │           │
  │  response      │               │                                      │             │           │
  │◄───────────────┴───────────────┴──────────────────────────────────────────────────────────────────┘
```

---

## 5. Data Models

### Core entities

| Model | Role |
|-------|------|
| **PageData** | One crawled page: url, status_code, title, meta_description, headings[], internal_links[], forms[], images[], html_snippet, has_infinite_scroll_indicators, optional load_time_ms, content_length |
| **AuditIssue** | One finding: id, title, description, category (SEO/UX/Trust), severity, impact, fix_effort, why_it_matters, how_to_fix, affected_url, affected_element, raw_value |
| **AuditScores** | seo_health, ux_clarity, trust_exposure (0–100) |
| **AuditReport** | target_url, pages_crawled, scores, issues[], quick_wins[] |

### Enums

- **Severity**: High, Medium, Low  
- **Impact**: Humans, Bots, Both  
- **FixEffort**: Quick win, Moderate, Complex  

---

## 6. API Design

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service info + link to docs and audit |
| GET | `/audit?url=<target>&max_pages=<n>` | Full audit; returns **HTML** report |
| GET | `/audit/json?url=<target>&max_pages=<n>` | Full audit; returns **JSON** (scores + issues) |

**Errors**: 422 if crawl returns no pages (invalid URL or unreachable). No auth in current design.

**Idempotency**: GET with same URL may yield different results over time (target site changes). No caching specified.

---

## 7. Configuration & Environment

| Source | Key | Default | Purpose |
|--------|-----|---------|---------|
| Config / env | `AUDIT_MAX_PAGES` | 50 | Max pages per crawl |
| Config | `request_timeout_seconds` | 15 | HTTP timeout |
| Config | `user_agent` | MAGEN-WebAudit/1.0 | User-Agent header |
| Config | `follow_same_domain_only` | true | Restrict crawl to seed domain |

---

## 8. Scalability & Trade-offs

### Current scale

- Single process, synchronous crawl (one page after another)  
- In-memory only; no DB or queue  
- Suited for ad-hoc audits and small/medium sites (e.g. up to 50 pages)

### Bottlenecks

1. **Crawl time**: Dominated by network; parallel fetches (e.g. asyncio + aiohttp or thread pool) would reduce wall-clock time  
2. **Memory**: Full HTML kept per page (and a 20k-char snippet); for very large pages or high limits, consider streaming or discarding body after parse  
3. **CPU**: Parsing and heuristics are cheap; scoring is O(issues); report render is O(issues)

### Trade-offs

- **No JS execution**: Faster and simpler; some UX/trust signals (e.g. client-side routing, lazy content) are only heuristic  
- **Heuristic rules**: Transparent and portable; may have false positives/negatives vs. ML  
- **No persistence**: Simple deployment; no audit history unless caller stores HTML/JSON

### Failure modes

- **Target down or TLS error**: Crawl returns 0 pages → 422  
- **Timeout**: Single page skipped; crawl continues  
- **Malformed HTML**: BeautifulSoup is tolerant; parser returns what it can  
- **Large site**: Crawl stops at `max_pages`; report is partial but valid

---

## 9. Future Extensions

| Extension | Description |
|-----------|-------------|
| **Lighthouse / PageSpeed** | Fetch LCP, CLS, TBT; attach to PageData; add UX checks (e.g. “high CLS”) |
| **Sitemap discovery** | Parse sitemap.xml to seed crawl or prioritize URLs |
| **robots.txt** | Respect disallow before fetching (optional, configurable) |
| **Async crawler** | asyncio + aiohttp for concurrent fetches; same PageData contract |
| **Queue-based pipeline** | Crawl → queue → worker analyzers for very large audits |
| **PDF export** | WeasyPrint (or similar) on current HTML report |
| **Auth / API key** | Optional API key or JWT for /audit and /audit/json |
| **Caching** | Short TTL cache keyed by (url, max_pages) to avoid re-crawling same site repeatedly |

---

## 10. Summary

The system is a **linear pipeline**: Crawl → Parse → Analyze → Score → Report. Components are **modular** and share only the **PageData** and **AuditIssue** models. The design prioritizes **clarity and extensibility** (new analyzers, new checks) over scale or real-time performance, and keeps **trust reasoning explainable** (no black-box scoring). This fits a portfolio or internal MAGEN Trust tool that can later be extended with Lighthouse, async crawling, or persistence as requirements grow.

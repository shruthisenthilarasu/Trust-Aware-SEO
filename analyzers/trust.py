"""Trust & bot exposure checks: open endpoints, predictable URLs, forms, APIs."""

import re
from typing import List
from urllib.parse import urlparse, parse_qs

from models import AuditIssue, PageData, Severity, Impact, FixEffort

from .base import BaseAnalyzer


# Patterns that suggest open/search endpoints or guessable paths
OPEN_ENDPOINT_PATTERNS = [
    r"/search\b",
    r"/filter\b",
    r"/query\b",
    r"/api/",
    r"\?q=|\?search=|\?query=",
]
PREDICTABLE_ID_PATTERN = re.compile(r"/(\d{2,})[/?]|/id/\d+|/item/\d+|/page/\d+", re.I)


class TrustAnalyzer(BaseAnalyzer):
    """Checks for trust and bot exposure: scraping surface, friction, predictability."""

    name = "trust"
    category = "Trust"

    def analyze(self, pages: List[PageData]) -> List[AuditIssue]:
        issues: List[AuditIssue] = []

        all_urls = [p.url for p in pages]
        seen_paths: set[str] = set()

        for page in pages:
            parsed = urlparse(page.url)
            path = parsed.path or "/"

            # 1) Open/search-like endpoints (no rate limiting implied in HTML)
            for pattern in OPEN_ENDPOINT_PATTERNS:
                if re.search(pattern, page.url):
                    issues.append(
                        AuditIssue(
                            id="trust-open-endpoint",
                            title="Open or search-like endpoint",
                            description=f"URL looks like a search/filter/API endpoint: {page.url[:80]}...",
                            category=self.category,
                            severity=Severity.MEDIUM,
                            impact=Impact.BOTS,
                            fix_effort=FixEffort.MODERATE,
                            why_it_matters="Open endpoints without rate limiting or friction are easy for bots to scrape and enumerate. They increase automation surface.",
                            how_to_fix="Add rate limiting, CAPTCHA/friction for anonymous bulk requests, or require authentication for sensitive listing/search endpoints.",
                            affected_url=page.url,
                        )
                    )
                    break

            # 2) Predictable URL patterns (sequential IDs, guessable paths)
            if PREDICTABLE_ID_PATTERN.search(page.url):
                issues.append(
                    AuditIssue(
                        id="trust-predictable-url",
                        title="Predictable URL pattern",
                        description="URL contains numeric IDs or sequential path segments that are easy to guess or enumerate.",
                        category=self.category,
                        severity=Severity.MEDIUM,
                        impact=Impact.BOTS,
                        fix_effort=FixEffort.MODERATE,
                        why_it_matters="Bots can iterate over /item/1, /item/2, etc., and scrape all content. Predictable URLs increase scraping and enumeration risk.",
                        how_to_fix="Use non-guessable identifiers (UUIDs, slugs, or tokens) or require authentication for sensitive resources.",
                        affected_url=page.url,
                    )
                )

            # 3) Forms without CAPTCHA or friction
            for form in page.forms:
                if not form.get("inputs"):
                    continue
                # Heuristic: no common "friction" field names (captcha, token, honeypot)
                input_names = {inp.get("name", "").lower() for inp in form["inputs"]}
                friction_indicators = {"captcha", "g-recaptcha-response", "h-captcha", "cf-turnstile", "token", "csrf", "honeypot"}
                has_friction = bool(input_names & friction_indicators)
                if not has_friction and len(form["inputs"]) >= 2:
                    issues.append(
                        AuditIssue(
                            id="trust-form-no-friction",
                            title="Form without CAPTCHA or friction",
                            description=f"Form at {form.get('action', page.url)} has no obvious CAPTCHA, CSRF token, or honeypot.",
                            category=self.category,
                            severity=Severity.HIGH,
                            impact=Impact.BOTS,
                            fix_effort=FixEffort.MODERATE,
                            why_it_matters="Forms without friction are easy for bots to submit at scale (spam, scraping, account abuse). Humans can still complete them with a CAPTCHA or similar.",
                            how_to_fix="Add reCAPTCHA, hCaptcha, Turnstile, or a honeypot + rate limiting to reduce automated form submission.",
                            affected_url=page.url,
                            affected_element=form.get("action"),
                        )
                    )
                    break

            # 4) Excessive query parameters (many optional params = more surface)
            query = parsed.query
            if query:
                params = parse_qs(query)
                if len(params) > 8:
                    issues.append(
                        AuditIssue(
                            id="trust-excessive-query-params",
                            title="Excessive query parameters",
                            description=f"URL has {len(params)} query parameters, increasing combinatory surface for bots.",
                            category=self.category,
                            severity=Severity.LOW,
                            impact=Impact.BOTS,
                            fix_effort=FixEffort.MODERATE,
                            why_it_matters="Many query parameters let bots build huge numbers of URLs and probe your site. This expands scraping and enumeration surface.",
                            how_to_fix="Reduce optional query params where possible; use POST for complex filters; add rate limiting or authentication for list/search endpoints.",
                            affected_url=page.url,
                            raw_value=str(list(params.keys())[:10]),
                        )
                    )

        return issues

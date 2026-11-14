---
name: web-product-analysis
description: >-
  Use when the user wants to analyze a web product, its features, pricing, or positioning. Includes the specific `agent-browser` extraction scripts for single-page applications and Next.js sites where `curl` fails.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [product-analysis, agent-browser, extraction, competitive-analysis]
    related_skills: [skills-hub, agent-browser]
---

# Web Product Analysis Workflow

## Overview

This workflow analyzes web products by extracting and synthesizing information from their public documentation, marketing pages, and technical content.

## Extraction Techniques

### agent-browser (SPA / Next.js)
For JavaScript-heavy single-page applications and Next.js sites where `curl` returns an empty shell, use `agent-browser navigate <url>` followed by `agent-browser snapshot --full` to get the rendered page content.

### Static pages (curl + strip)
For statically-rendered pages where `curl -sL <url>` returns complete HTML, extract the main content by fetching the response and stripping tags:

```bash
curl -sL <url> | sed 's/<[^>]*>//g; s/^[[:space:]]*//; /^$/d'
```

### Doc site batch crawl (Starlight / Docusaurus / MkDocs)
Documentation sites typically list all pages in an HTML sidebar. To crawl every page:

1. **Extract all internal links** from the landing page HTML:
   ```bash
   # Download landing page
   curl -sL https://docs.example.com/zh-cn/ | grep -oP 'href="(/zh-cn/[^"]+)"' | cut -d'"' -f2
   ```
   
2. **Filter to only doc pages** (exclude .css, .js, .png, .svg etc.)

3. **Batch-fetch** using a Python script saved to /tmp/ and run via `python3 /tmp/crawler.py`:
   - Uses `subprocess.run(["curl", "-sL", url])` per page
   - Adds 0.2-0.5s delay between requests
   - Saves each page as a markdown file with frontmatter (title, source_url, sha256)
   - Handles 100+ pages without hitting tool-call limits

4. **Use the results** downstream — either save to wiki `raw/articles/`, analyze for product features, etc.

**Pitfall:** Respect `robots.txt` and use reasonable delays. Most doc sites don't have anti-scraping, but aggressive concurrency may trigger rate limits.

## Reference
- `references/deeptutor-crawl-2026-07-28.md` — Real-world crawl of a Starlight documentation site (41 pages, 336KB), including link extraction pattern and page taxonomy.
- User asks to "analyze this website/product: https://..."
- You need to extract pricing tiers, feature lists, or value propositions from a SaaS site
- A target website returns React hydration errors or empty DOMs when fetched via `curl`
- You are executing a "Blueprint" that requires deep website research

## Workflow

### 1. Identify the Core Pages

Modern SaaS products usually spread their core identity across three paths:
- `/` (Homepage) - Value proposition, target audience
- `/features` - Feature breakdown
- `/pricing` - Pricing tiers and gating

### 2. Extract Using DOM Injection

Since snapshots (`agent-browser snapshot -i`) only show interactive elements (links/buttons) and omit the rich text describing the product, you **must use DOM injection** (`agent-browser eval --stdin`) to extract the readable text.

#### Open the page
```bash
agent-browser open "https://example.com/pricing"
agent-browser wait --load networkidle
```

#### Extract specific structural data (Pricing Example)
```bash
cat <<'EOF' | agent-browser eval --stdin
const extractText = (selector) => {
  const el = document.querySelector(selector);
  return el ? el.innerText.trim() : "Not found";
};

// If standard querySelectors fail, fall back to string splitting on the whole body
const bodyText = document.body.innerText;
const extractAfter = (keyword, length = 1000) => {
  const parts = bodyText.split(keyword);
  if (parts.length > 1) {
    return parts[1].substring(0, length);
  }
  return "Not found";
};

return {
  rawText: bodyText.substring(0, 3000), // First 3k chars usually contain the headers
  afterPricing: extractAfter('Pricing')
};
EOF
```

### 3. Handle Interactive SPAs

If the site uses client-side routing, opening a new URL directly via `agent-browser open` is slower. Instead, use refs to navigate or use `pushstate` if available:

```bash
agent-browser snapshot -i
# Find the "Features" or "Pricing" link, e.g., @e42
agent-browser click @e42
agent-browser wait --load networkidle
```

### 4. Synthesize the Analysis

Format your final output as a structured Markdown report covering:

1. **Core Positioning (Value Proposition)**
   - Slogan / Tagline
   - Target Audience
   - Main Mission
2. **Feature Breakdown**
   - Categorize features logically (e.g., Sales, Inventory, Reporting)
3. **Pricing Strategy**
   - Free tiers vs. Paid tiers
   - Gating mechanisms (What limits push users to upgrade? e.g., Users, Storage, Transactions)
4. **Competitive Assessment (SWOT)**
   - Identify the moat (e.g., local integrations, specific compliance)
   - Identify weaknesses (e.g., lack of global marketplace)
5. **Corporate & Leadership OSINT**
   - Legal Operating Entity (SSM / corporate registration ID)
   - Key Founders, Executives & Tech Leadership (LinkedIn profiles, background, domain expertise)

### 5. Full-Site Crawling & Deep Product Research

When analyzing an entire product ecosystem (including main SaaS domain and Intercom/Helpdesk knowledge bases):
1. **Two-Stage Architecture**:
   - **Stage 1 (Discovery)**: Parse `sitemap.xml` (e.g., `https://domain.com/sitemap.xml`, `https://intercom.help/domain/en/sitemap.xml`) combined with BFS link extraction into `urls_index.json` and `site_tree.json`.
   - **Stage 2 (Extraction)**: Use concurrent `agent-browser` or async HTTP sessions to save complete raw HTML to `raw_html/`, capture full-page screenshots to `screenshots/` via `agent-browser screenshot <path> --full`, and convert clean text to Markdown in `content/` with YAML frontmatter (`title`, `source_url`, `crawled_at`, `domain`).
2. **Full-Page Visual Capture Pattern**:
   - Always pair HTML capture with `agent-browser screenshot "<path>" --full` to preserve visual layouts for multimodal/vision model analysis.
3. **Aggressive Crawling & Resume Strategy**: For sites without strict anti-scraping mechanisms, run concurrent async fetchers with retry limits, recording status in `urls_index.json` to enable resume capability.
4. **Ecosystem Artifact Generation**:
   - **LLM Wiki**: Synthesize captured pages into `wiki/entities/` and `wiki/concepts/` with `[[wikilinks]]`.
   - **OpenAPI 3.0 Spec**: Reverse-engineer domain API contracts (e.g., regulatory submission payloads, third-party webhook structures) into `docs/openapi-spec.yaml`.
   - **SVG System Architecture Diagram**: Generate an interactive dark-themed SVG architecture HTML (`architecture-diagram` skill) illustrating client, core backend, database, compliance, and third-party integration boundaries.
   - **Standalone Web Reader**: Build a self-contained `index.html` with an embedded JSON/JS `DOC_STORE` (avoiding `file://` CORS fetch blocks) to browse the wiki and executive reports.

## Common Pitfalls

1. **Relying on `curl` for modern sites**: Next.js sites will return `<div id="__next_error__">` or hydration bundles. **Always use `agent-browser`**.
2. **Syntax errors in `agent-browser eval`**: Avoid implicit returns if using blocks. Either use `return` explicitly or ensure the heredoc evaluates to a single expression.
   ```bash
   # WRONG
   cat <<'EOF' | agent-browser eval --stdin
   const text = document.body.innerText;
   text.split('Pricing')[1]
   EOF

   # RIGHT
   cat <<'EOF' | agent-browser eval --stdin
   const text = document.body.innerText;
   return text.split('Pricing')[1];
   EOF
   ```
3. **Snapshot & Get Text/HTML Blindness**: `agent-browser snapshot -i` omits paragraphs and headers; use `agent-browser get html "html"` or `agent-browser get html "body"` (note: `agent-browser get html` requires a selector parameter like `"html"` or `"body"`, calling it without a selector throws an error).
4. **SSL Verification Issues on Help Centers**: When crawling third-party knowledge bases (e.g., `intercom.help`), Python `aiohttp` may fail with `SSLCertVerificationError`. Use `agent-browser open "<url>"` directly or configure SSL bypass in `aiohttp.TCPConnector(ssl=ssl_context)` (`ssl_context.check_hostname = False; ssl_context.verify_mode = ssl.CERT_NONE`).
5. **Subagent File Collision in Background Tasks**: When invoking subagents via `delegate_task` to write or update scripts (e.g., `build_phase1_core.py`), sibling subagents or the parent process may attempt to overwrite the same path. Always inspect existing file state and ensure subagents are given non-overlapping target files or serialized execution steps.
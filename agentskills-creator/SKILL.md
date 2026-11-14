---
name: agentskills-creator
description: Create, structure, document, evaluate, and optimize AI agent skills following the agentskills.io specification. Covers SKILL.md frontmatter, best practices, directory layout, script running, eval configuration, and skill testing.
metadata:
  related_skills:
    - skills-spec-compliance
    - hermes-agent-skill-authoring
  source: https://context7.com/websites/agentskills_io/llms.txt
---

# AgentSkills Creator

Reference: https://agentskills.io (mirror: https://context7.com/websites/agentskills_io/llms.txt)

## When to use

Use this skill when the user asks to:
- Create a new AI agent skill (SKILL.md + directory structure)
- Validate or fix SKILL.md frontmatter
- Structure skill instructions with best practices
- Add eval test cases for a skill
- Decide how to run scripts from a skill (uv, bun, deno, etc.)
- Understand the agentskills.io specification fields
- Troubleshoot malformed YAML or invalid skill naming

## Specification: SKILL.md frontmatter

### Required fields

```yaml
name: skill-name          # lowercase, hyphens, no consecutive hyphens, no leading hyphen
description: >            # clear, specific, not vague
  What this skill does and when to trigger it. Avoid one-liners like "Helps with PDFs."
```

### Optional fields

```yaml
license: Apache-2.0       # or Proprietary, MIT, etc.

metadata:
  author: your-org
  version: "1.0"          # use unique key names to avoid conflicts

compatibility: |          # environment requirements
  Requires Python 3.14+ and uv
  # or: Designed for Claude Code (or similar products)
  # or: Requires git, docker, jq, and access to the internet

allowed-tools: |          # experimental; space-delimited pre-approved tool specs
  Bash(git:*) Bash(jq:*) Read
```

### Naming rules

| Valid                    | Invalid                     |
|--------------------------|-----------------------------|
| `pdf-processing`         | `PDF-Processing` (uppercase)|
| `data-analysis`          | `-pdf` (leading hyphen)     |
| `code-review`            | `pdf--processing` (consecutive hyphens) |

## Directory structure

```
skill-name/
├── SKILL.md          # Required: frontmatter + instructions
├── scripts/          # Optional: executable code
│   ├── extract.py
│   ├── validate.sh
│   └── process.py
├── references/       # Optional: docs, schemas
├── assets/           # Optional: templates, resources
├── evals/            # Optional: evaluation test cases
│   ├── evals.json
│   └── files/        # Input files for eval runs
└── ...
```

All relative paths in SKILL.md are relative to the skill directory root, not the user's cwd.

## Running scripts from skills

Use the appropriate tool for the script language:

### Python

```bash
# PEP 723 script with inline dependencies (recommended)
uv run scripts/extract.py

# One-off package without install
uvx ruff@0.8.0 check .
uvx black@24.10.0 .

# pipx alternative
pipx run 'black==24.10.0' .
pipx run 'ruff==0.8.0' check .
```

### TypeScript / JavaScript

```bash
# Bun
bun run scripts/extract.ts
bunx eslint@9 --fix .
bunx create-vite@6 my-app

# Deno
deno run scripts/extract.ts
deno run npm:create-vite@6 my-app
deno run --allow-read npm:eslint@9 -- --fix .
```

### Ruby

```bash
ruby scripts/extract.rb
```

### Shell

```bash
bash scripts/validate.sh "$INPUT_FILE"
python3 scripts/process.py --input results.json
```

### Script requirements for agents

- **No interactive prompts** — agents run non-interactively. Use CLI flags, env vars, or stdin for input. Never block on TTY prompts, password dialogs, or confirmation menus.
- **Structured output** — prefer JSON, CSV, or TSV on stdout; diagnostics/errors to stderr. Avoid whitespace-aligned output that is hard to parse programmatically.
- **Helpful error messages** — explain what went wrong, what was expected, and suggest a fix.
- **Self-contained dependencies** — use PEP 723 `/`/` script` markers for Python, `npm:` specifiers for Deno.

### PEP 723 inline dependency script

```python
# /// script
# dependencies = [
#   "beautifulsoup4",
# ]
# ///

from bs4 import BeautifulSoup
# ...
```

## Writing skill instructions (best practices)

### Procedural over specific

```
# Bad — only useful for one exact query
Join orders to customers on customer_id, filter region='EMEA', sum amount.

# Good — reusable method for any analytical query
1. Read schema from references/schema.yaml to find relevant tables
2. Join tables using _id foreign key convention
3. Apply filters from user request as WHERE clauses
4. Aggregate numeric columns and format as markdown table
```

### Avoid telling the agent what it already knows

```
# Bad — the agent knows what PDFs are
PDF (Portable Document Format) files are a common file format...

# Good — straight to what the agent wouldn't know
Use pdfplumber for PDF text extraction. The project has custom form-filling
logic in scripts/fill_form.py — call it with field_values.json.
```

### Exhaustive documentation gathering

When creating a skill from a website's documentation, do not stop at the landing page.
Fetch ALL linked sub-pages before writing — the landing page often summarises but omits
details (full command lists, config fields, error messages, edge cases).

- Identify all sidebar/nav links from the main page.
- Fetch every sub-page in parallel (delegate_task with multiple URLs or individual fetches).
- Only start writing after ALL pages are collected and cross-referenced.
- If a section has CLI commands, verify the list is complete by checking for alternative
  command groups (e.g. `workbench:*` vs `package:*`), not just the first group found.
- When in doubt, a structured output like `help` or `--list` from the actual tool is more
  authoritative than any prose page — check generated help output when available.

### Environment-specific gotchas

```markdown
## Gotchas

- The `users` table uses soft deletes. Always include `WHERE deleted_at IS NULL`.
- user_id in DB = uid in auth service = accountId in billing API — same value.
- /health returns 200 even when DB is down. Use /ready for full health check.
```

### Code review checklist

```markdown
## Code review process

1. Check all DB queries for SQL injection (use parameterized queries)
2. Verify auth checks on every endpoint
3. Look for race conditions in concurrent code paths
4. Confirm error messages don't leak internal details
```

### Output format templates

```markdown
## Report structure

# [Analysis Title]

## Executive summary
[One-paragraph overview of key findings]

## Key findings
- Finding 1 with supporting data
- Finding 2 with supporting data

## Recommendations
1. Specific actionable recommendation
2. Specific actionable recommendation
```

## Evaluation test cases

Configuration file: `evals/evals.json`

```json
{
  "skill_name": "csv-analyzer",
  "evals": [
    {
      "id": 1,
      "prompt": "I have a CSV of monthly sales data in data/sales_2025.csv. Can you find the top 3 months by revenue and make a bar chart?",
      "expected_output": "A bar chart image showing the top 3 months by revenue, with labeled axes and values.",
      "files": ["evals/files/sales_2025.csv"],
      "assertions": [
        "The output includes a bar chart image file",
        "The chart shows exactly 3 months",
        "Both axes are labeled",
        "The chart title or caption mentions revenue"
      ]
    }
  ]
}
```

### Eval queries (trigger testing)

```json
[
  { "query": "I've got a spreadsheet... can you add a profit margin column?", "should_trigger": true },
  { "query": "whats the quickest way to convert this json file to yaml", "should_trigger": false }
]
```

### Grading results structure

```json
{
  "assertion_results": [
    {"text": "Description of assertion", "passed": true, "evidence": "Found chart.png (45KB)"}
  ],
  "summary": {
    "passed": 3,
    "failed": 1,
    "total": 4,
    "pass_rate": 0.75
  }
}
```

### Performance metrics

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332
}
```

### Feedback per test case

```json
{
  "eval-top-months-chart": "The chart is missing axis labels...",
  "eval-clean-missing-emails": ""
}
```

## Validation

### Quick check

```bash
skills-ref validate ./my-skill
```

### Full audit

For comprehensive validation (non-standard fields, allowed-tools format, name/directory matching), use the companion skill:

```
skill_view('skills-spec-compliance')
```

It includes an audit script that scans an entire skills directory and auto-fix patterns for common violations.

> For Hermes Agent-specific skill authoring conventions (in-repo SKILL.md, plan mode, Heremes catalog), see `hermes-agent-skill-authoring`.

## Sourcing documentation from websites

When creating a skill from a website's documentation, the standard `web_extract` tool
may not be available (e.g. SearXNG-only backends cannot extract page content).
Use this fallback workflow:

### 1. Discover relevant pages

```text
web_search(query="site:example.com documentation topic", limit=5)
```

Identify key pages from search results.

### 2. Fetch page content

**Single page** — use `browser_navigate` then extract via the console:

```
browser_navigate(url) → browser_console(expression='document.body.innerText')
```

**Multiple pages** — use `delegate_task` for parallel fetching, or `curl` + Python
HTML stripping in the terminal:

```bash
curl -sL <url> > /tmp/page.html
python3 -c "
import re, html
text = open('/tmp/page.html').read()
text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
text = re.sub(r'<[^>]+>', '\n', text)
text = html.unescape(text)
lines = [l.strip() for l in text.split('\n')]
lines = [l for l in lines if l and len(l) > 3]
open('/tmp/page.txt', 'w').write('\n'.join(lines))
"
```

### 3. Read extracted content

The terminal tool may compress large output (CCR — content compression).
To read raw text around this:

```text
# Read in small chunks
head -40 /tmp/page.txt
sed -n '41,80p' /tmp/page.txt

# Or split into smaller files
split -l 20 /tmp/page.txt /tmp/pagechunk_
cat /tmp/pagechunk_aa /tmp/pagechunk_ab
```

### 4. Compile and deduplicate

Save all sections to a combined file, then read each section in small chunks
before writing the skill. This avoids CCR truncation while preserving the
full documentation context.

### Pitfalls

- `web_extract` may silently fail when the extract backend is SearXNG-only.
  Always check `success: false` in the response.
- Terminal output over ~2KB may be CCR-compressed. Reading in small chunks
  (20-40 lines at a time) or using `split` bypasses this.
- Pipe `git` output to `cat` to prevent pager hangs: `git log --oneline | cat`.
- Use `| cat` for any command that might invoke a pager (git, less, etc.).

## XML skill representation

When disclosing skills to a model, use this XML structure:

```xml
<available_skills>
  <skill>
    <name>pdf-processing</name>
    <description>Extract PDF text, fill forms, merge files. Use when handling PDFs.</description>
    <location>/home/user/.agents/skills/pdf-processing/SKILL.md</location>
  </skill>
</available_skills>
```

For skill content wrapping:

```xml
<skill_content name="pdf-processing">
# PDF Processing

[SKILL.md body]

Skill directory: /home/user/.agents/skills/pdf-processing
Relative paths in this skill are relative to the skill directory.

<skill_resources>
  <file>scripts/extract.py</file>
  <file>references/pdf-spec-summary.md</file>
</skill_resources>
</skill_content>
```

## YAML pitfalls

Colons in description values break YAML parsing:

```yaml
# BAD — unquoted colon breaks parsing
description: Use this skill when: the user asks about PDFs

# GOOD
description: "Use this skill when: the user asks about PDFs"
```

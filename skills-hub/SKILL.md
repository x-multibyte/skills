---
name: skills-hub
description: >-
  Discover, evaluate, install, and complete community skills from the
  Hermes Skills Hub (hermes-agent.nousresearch.com/docs/skills), skills.sh,
  ClawHub, and other registries. Covers search, quality verification,
  installation, and patching missing supporting files.
---

# Skills Hub

## Overview

The Hermes Skills Hub catalogs 86,000+ skills across 12 registries (Built-in,
Optional, skills.sh, ClawHub, LobeHub, browse.sh, gstack, etc.). This skill
covers the end-to-end workflow of finding, vetting, installing, and completing
community-hosted skills.

## When to Use

- User asks to search for skills on a topic (ansible, kubernetes, etc.)
- User asks to install a specific skill from a community registry
- You need to verify a skill's quality before installing
- After installing, you need to fetch the skill's supporting files

## Workflow

### 1. Search the Skills Hub

The Hub page at https://hermes-agent.nousresearch.com/docs/skills renders dynamically (SPA) and relies heavily on client-side JS. **Browser snapshot often times out or fails to capture the dynamic search results**, and its internal API endpoints are not publicly accessible via simple `curl`.

When searching the Skills Hub, **always use the browser's eval capability (JS injection)** to extract the rendered DOM instead of relying on `browser_snapshot` or `curl`:

```bash
# 1. Open the page
agent-browser open https://hermes-agent.nousresearch.com/docs/skills

# 2. Type your query into the search box (wait for network idle or 1000ms for results to render)
agent-browser snapshot -i  # Find search box ref
agent-browser fill @e19 "your query"
agent-browser wait 1500

# 3. Extract the DOM dynamically (do NOT rely on snapshot for the results list)
cat <<'EOF' | agent-browser eval --stdin
document.querySelector('main')?.innerText || "Not found"
EOF
```

If the Hub times out or blocks access, fall back to searching community registries directly via `curl` and `python3`:

**ClawHub Search**
```bash
curl -sL "https://clawhub.ai/search?q=your+query" | python3 -c "
import sys, re
html = sys.stdin.read()
text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
text = re.sub(r'<[^>]+>', ' ', text)
print(re.sub(r'\s+', ' ', text).strip()[:3000])
"
```

**GitHub / skills.sh Search**
```bash
curl -sL "https://api.github.com/search/repositories?q=skills+your+query+language:md&sort=stars&per_page=10" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for item in data.get('items', [])[:10]:
    print(f\"{item['full_name']}: {item.get('description', 'N/A')[:120]}\")
"
```

Check the source before trusting a community skill:

- **ClawHub skills** — show inline descriptions on the hub page
- **skills.sh skills** — indexed from GitHub, look up the upstream repo
  (e.g. `aj-geddes/useful-ai-prompts`). Check:
  - Star count and fork count (signals community trust)
  - Whether the repo has a `skills/<skill-name>/` directory
  - The raw SKILL.md content at `raw.githubusercontent.com/...`
  - Whether the skill has `references/`, `templates/`, `scripts/` dirs

To inspect raw SKILL.md:
```
curl -sL "https://raw.githubusercontent.com/<owner>/<repo>/main/skills/<name>/SKILL.md"
```

### 3. Install from URL

```
hermes skills install "https://raw.githubusercontent.com/<owner>/<repo>/main/skills/<name>/SKILL.md" --category <category> -y
```

Use `-y` to skip confirmation in terminal mode.

### 3b. Install a whole skill collection via `npx skills add`

For repos that ship a collection of skills (multiple `SKILL.md` packages, e.g.
`deeptutor/skills/builtin/*/SKILL.md`), the `skills` CLI (Vercel/agentskills,
v1.5.x) is the right tool. It clones the repo, discovers skill packages, runs a
security scan, and installs into agent skill dirs (`~/.hermes/skills/<name>/`
for Hermes).

Interactive form (TUI multi-select):
```bash
npx --yes skills add "https://github.com/<owner>/<repo>"
```

Non-interactive form (use the flags — avoids hanging on the TUI):
```bash
npx --yes skills add "https://github.com/<owner>/<repo>" -s '*' -a hermes-agent -g -y --copy
```
- `-s '<names|*>'` — select specific skills or all (also usable to pick a subset)
- `-a hermes-agent` — target Hermes agent dir specifically
- `-g` — global (user-level) install
- `-y` — skip confirmation
- `--copy` — copy files instead of symlinking
- `-l` — list available skills in the repo without installing

**CRITICAL PITFALL — root SKILL.md gets silently skipped**: the CLI skips any
`SKILL.md` that lacks the required `name:` / `description:` frontmatter fields,
with only a `⚠ Skipped ... missing required frontmatter field(s)` line. The
repo-root SKILL.md is often the most valuable skill (the project's main CLI
playbook) and is exactly the one that gets dropped. After `skills add`, check
the output for `Skipped` lines, then manually install the skipped skill: add
proper frontmatter and place it at `~/.hermes/skills/<name>/SKILL.md`.

```bash
# Example: salvage a skipped root SKILL.md
{ printf -- '---\nname: <name>\ndescription: <one-line description>\n---\n\n'; cat SKILL.md; } \
  > ~/.hermes/skills/<name>/SKILL.md
```

Also note: `skills list` (the CLI) searches local dirs (`.claude/skills`,
`~/.agents/skills`, `~/.hermes/skills`, ...) — it is NOT the right tool for
searching remote repos. Use `npx skills add <url>` to inspect a repo's skills.

### 4. Fetch Supporting Files (CRITICAL PITFALL)

**`hermes skills install` only downloads SKILL.md.** It does NOT fetch the
skill's `references/`, `templates/`, or `scripts/` directories. This is a
known gap — you MUST manually download them.

```bash
SKILL_DIR="$HOME/.hermes/skills/<category>/<name>"
mkdir -p "$SKILL_DIR/references" "$SKILL_DIR/templates" "$SKILL_DIR/scripts"

# Discover files via GitHub Contents API
curl -s "https://api.github.com/repos/<owner>/<repo>/contents/skills/<name>"

# Download each subdirectory
BASE="https://raw.githubusercontent.com/<owner>/<repo>/main/skills/<name>"
curl -sL "$BASE/references/<file>" -o "$SKILL_DIR/references/<file>"
curl -sL "$BASE/templates/<file>" -o "$SKILL_DIR/templates/<file>"
curl -sL "$BASE/scripts/<file>" -o "$SKILL_DIR/scripts/<file>"
chmod +x "$SKILL_DIR/scripts/"*.sh
```

### 5. Verify Installation

```bash
skill_view(name='<name>')
```

Check `linked_files` in the output — references, templates, scripts should
all be listed.

## Pitfalls

- **Missing support files**: After `hermes skills install`, the skill's
  references/ templates/ scripts/ are NOT installed. The SKILL.md may
  reference them, but they won't exist. Always check and manually fetch.
- **Security scan verdict**: Watch for `Verdict: BLOCKED` during install.
  Community sources are usually `SAFE` but blocked skills require `--force`.
- **Browser snapshot truncation**: The Hub page renders dynamically; long
  result lists may truncate in `browser_snapshot`. Use `browser_console`
  with `document.querySelector('main')?.innerText` to extract full text.
- **GitHub API rate limits**: Unauthenticated calls to `api.github.com` are
  limited to 60/hr. For bulk discovery, batch requests.

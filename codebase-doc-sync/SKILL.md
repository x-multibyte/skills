---
name: codebase-doc-sync
description: "Sync project documentation (wiki, README, docs) with code changes using git diff + knowledge graph + LLM analysis."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [wiki, documentation, code-analysis, git, knowledge-graph]
    category: software-development
    related_skills: [llm-wiki, wiki-publishing]
---

# Codebase Documentation Sync

Keep project documentation synchronized with code changes using a three-layer
detection pipeline: git diff (file level), static mapping (deterministic), and
knowledge graph (semantic). The script detects; the LLM analyzes and decides.

## When This Skill Activates

- User asks to sync wiki/docs with code changes
- User runs a `sync-*.py` script for their project
- User says "code changed, update wiki/docs"
- User asks for impact analysis of recent code changes on documentation

## The Three-Layer Model

```
Layer 1: git diff ────→ file list       (cheap, always available)
Layer 2: mapping  ────→ wiki page slugs (deterministic, no deps)
Layer 3: kgraph   ────→ symbol impact   (richest, needs indexing)
```

### Layer 1: Git Diff

Run `git diff --name-status <last-sync-commit>..HEAD` to list changed files.
Store the last-sync commit in a state file (e.g. `.sync-state.json`) so
subsequent runs are incremental, not full re-scans.

The state file is a JSON object:

```json
{
  "last_commit": "abc123def456...",
  "last_sync": "2026-07-18T04:00:00",
  "notes": "Rebuilt after wiki update"
}
```

The sync script supports these commands:

| Command | What it does |
|---------|-------------|
| `python3 sync-wiki.py` | Detect changes, print structured report |
| `python3 sync-wiki.py --rebuild` | Rebuild HTML viewer + record sync state |
| `python3 sync-wiki.py --status` | Show current sync state |
| `python3 sync-wiki.py --reset` | Reset baseline to HEAD |

### Layer 2: Static File-to-Doc Mapping

Define a mapping that matches changed file paths to documentation pages.
Three relevance tiers:

| Tier | Meaning | Example |
|------|---------|---------|
| `direct` | Must update | Model schema change → entity page |
| `related` | Should review | Service change → architecture concept |
| `minor` | Consider, skip most | Controller, Route, Config changes |

Typical mapping coverage for a web app:

```
Models/*.php            → entities/{model-name}.md       [direct]
Services/*.php          → entities/{related-entity}.md   [direct]
                          concepts/service-layer.md      [related]
Enums/*.php             → concepts/state-machine.md      [direct]
Controllers/*.php       → concepts/architecture.md       [minor]
routes/web.php          → concepts/architecture.md       [minor]
resources/views/        → concepts/frontend-stack.md     [related]
tests/Feature/*.php     → concepts/testing-strategy.md   [direct]
database/migrations/*   → (flag for manual review)       [minor]
Dockerfile / compose    → concepts/infrastructure.md     [direct]
```

### Layer 3: Knowledge Graph Analysis (Optional)

Use code-intelligence tools for symbol-level change context before editing
documentation. Available tools depend on what's indexed:

- **GitNexus CLI** (`node .gitnexus/run.cjs`):
  - `detect-changes --scope compare --base-ref <commit>` — hunks to symbols
  - `impact <symbol>` — blast radius of changing a symbol
  - `context <symbol>` — callers, callees, execution flows

- **codebase-memory-mcp** (via LLM MCP tools):
  - `search_graph("FunctionName")` — find by name
  - `trace_path(symbol, direction)` — call graph traversal
  - `get_code_snippet(qualified_name)` — read full source

- **codegraph** (via MCP):
  - `codegraph_explore("ServiceName")` — source + call path

Run the analysis AFTER the sync script's report, not before. The script's
output tells you which pages are affected; the knowledge graph tells you
why and how deep the impact goes.

## LLM Analysis Flow

After the sync script produces its report, the LLM does the following:

1. Read the changed files list from the report
2. Read the actual diff/source of significant files (use `get_code_snippet`
   or direct file read; don't rely on the file name alone)
3. Use knowledge graph tools to trace impact on critical symbols
4. Cross-reference against existing documentation pages
5. Update affected pages — new facts, updated dates, cross-references
6. Create new pages if new entities/concepts emerged
7. Update navigation index if pages were added
8. Append to change log
9. Run `--rebuild` command to regenerate static viewer if applicable

## Pitfalls

- **Never let the script decide what to write** — it detects and maps. The LLM
  reads actual code and decides. Auto-generated content misses nuance.
- **Always read the actual source, not just the file name** — a file changed
  doesn't mean the wiki-relevant part changed. Read the diff to be sure.
- **Store sync state explicitly** — without it, every run is a full re-scan.
- **Knowledge graph analysis is optional** — layers 1+2 work without it.
  Use layer 3 for critical symbols only (it adds ~35s for re-indexing).
- **Batch updates** — when many files changed, group related wiki page edits
  into one pass instead of N separate edits.
- **Don't force full re-index on every sync** — only re-index the knowledge
  graph when the user explicitly asks for deep analysis or when modifying
  critical domain code (Models, Services, core logic).

## Related Tools

- `llm-wiki` — the wiki content management skill this sync pattern pairs with
- `wiki-publishing` — building static HTML from wiki markdown
- GitNexus — knowledge graph indexer and impact analyzer

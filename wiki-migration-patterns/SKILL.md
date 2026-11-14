---
name: wiki-migration-patterns
description: "Migrate existing project documentation (linear docs, README dirs, ARCHITECTURE.md) into LLM Wiki format as a sub-wiki under the global wiki root."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [wiki, knowledge-base, migration, documentation]
    category: research
    related_skills: [llm-wiki]
---

# Wiki Migration Patterns

Companion to the [llm-wiki] skill. Covers **migration-specific** workflows that the
bundled llm-wiki skill doesn't address — converting existing project documentation
into a structured Karpathy-style wiki as a **sub-wiki** under the global wiki root.

The llm-wiki skill handles day-to-day operations (ingest, query, lint, update). This
skill handles the initial setup when the source is non-trivial documentation that needs
to be restructured, not just ingested as a single article.

## When This Skill Activates

- User asks to create a project-specific wiki from existing project docs
- Source material is a directory of markdown files (numbered 01-xx, or a docs/ tree, or an ARCHITECTURE.md)
- The wiki should live **outside** the project directory (not tracked in git)
- The user has a global wiki at `~/wiki/` and wants a project sub-wiki

## Decision: Sub-Wiki vs Standalone

Ask the user where the wiki should live:

| Location | When |
|----------|------|
| `~/wiki/<project>/` | User wants wiki independent of project directory — survives project deletion, portable across machines, not in git |
| `<project>/wiki/` | User wants wiki version-controlled with the codebase — travels with the repo on clone |
| `~/wiki/` (root level) | User wants project content merged into their global wiki domain |

Prefer `~/wiki/<project>/` when the user expresses concern about project dir pollution
or wants the wiki to outlive the project.

## Migration Workflows

### 1. Linear Numbered Documentation (01-xx files)

Source pattern: auto-generated or hand-written docs in numbered files like
`01-overview.md`, `02-architecture.md`, ... `21-glossary.md`. Common output from
tools like Trae, Cursor, or documentation generators.

**Workflow:**

1. **Create the sub-wiki directory** at `~/wiki/<project>/` with full structure:
   `raw/<source-dir>/`, `entities/`, `concepts/`, `decisions/`, `queries/`

2. **Wholesale copy** all source files into `raw/<source-dir>/` — immutable reference.

3. **Scan the full set** before creating wiki pages:
   - Read the README/index to understand scope
   - Skim every file to classify content into three buckets:
     - **Entity documentation** (customer, order, invoice) → will become entity pages
     - **Architectural concepts** (state machine, service layer, testing) → will become concept pages
     - **Pure reference** (roadmap, running-the-app, glossary) → stays in raw/ only
   - Note files that cover multiple entities (e.g. "Module: Customers & Products" covers
     both Customer and Product) — these should be split across wiki pages

4. **Write the project SCHEMA.md** with domain-specific tag taxonomy and conventions.

5. **Create entity pages** — one per business domain model:
   - Include: database schema, business rules, relationships, key service interactions
   - Frontmatter: `sources: [raw/<source-dir>/<source-file>.md]`

6. **Create concept pages** — one per architectural concern:
   - Include: explanation, design rationale, trade-offs, related concepts via [[wikilinks]]
   - Do not create pages for pure-reference chapters

7. **Establish wikilinks immediately** — every page must link to at least 2 other pages.
   Linear docs have no cross-references, so this step is critical.

8. **Write index.md** and **log.md**, then report the delta (e.g. "22 raw files → 13 wiki pages").

**Key difference from structured KB import:** Linear docs require upfront classification
and splitting. You must decide which numbered chapter maps to which entity/concept,
rather than mirroring the source structure.

### 2. Single Large Document (ARCHITECTURE.md, README)

Source pattern: one comprehensive markdown file covering the whole project.

**Workflow:**

1. Copy to `raw/<project>-architecture.md` with frontmatter.
2. Identify section-level boundaries — each major heading typically maps to an entity or concept.
3. Create individual wiki pages per section, preserving provenance via `sources:` frontmatter
   pointing to the same raw file.
4. Cross-reference between pages via [[wikilinks]].
5. The raw file remains searchable for sections that didn't warrant their own page.

### 3. Structured Documentation Directory (docs/ with sub-folders)

Source pattern: a multi-file directory tree with its own index (e.g. VuePress, Docusaurus,
or manually organized docs).

**Workflow:**

1. Wholesale copy into `raw/<source-dir>/`.
2. Follow the llm-wiki skill's "Import from an Existing Wiki" workflow (master page +
   selective deeper pages).
3. If the docs use `[[wikilinks]]` or Obsidian format, preserve the link structure in
   the migration — convert source wikilinks to point to the new wiki pages.

## Setting Up SCHEMA.md for a Project Wiki

The project SCHEMA.md should differ from the global wiki's schema:

```yaml
# Key differences:
# - Domain: specific to the project (e.g. "ERP business logic"), not the user's broad domain
# - Tag taxonomy: project-specific tags, not global ones
# - Entity pages: focus on business domain models, not hardware/software entities
```

Use this template:

```markdown
# Wiki Schema — <Project Name>

## Domain
<Specific project domain>

## Conventions
(standard llm-wiki conventions, adapted to project specifics)

## Tag Taxonomy
- Domain: <business entities relevant to the project>
- Architecture: <architectural concepts>
- Tech: <technology stack>
- Process: <development process tags>

## Page Thresholds
- Create a page when... (standard thresholds)
- Split at ~200 lines
```

## Pitfalls

- **Do not duplicate the global wiki's content** — project wiki is for project-specific
  knowledge. If something belongs to the user's global domain (e.g. general homelab
  knowledge), put it there instead.
- **Do not skip classification** — the most common mistake is mirroring the source file
  structure instead of restructuring into entities + concepts. A source file titled
  "Module: Customers & Products" should become TWO wiki pages.
- **Do not create pages for reference-only content** — roadmap, running-the-app, glossary,
  and changelogs belong only in raw/. They are searchable but don't need dedicated pages.
- **Orientation matters** — after creating a project sub-wiki, orient by reading that
  sub-wiki's SCHEMA/index/log, not the global wiki's (unless the task spans both).
- **`valet link` doesn't need restart** — `valet link` only creates a symlink in
  `~/.config/valet/Sites/`. Valet's nginx config already wildcard-matches `*.test`
  domains, so no restart is required.

## Post-Migration: Keeping the Wiki in Sync

A project wiki linked to a codebase needs periodic updates as code changes.
The `sync-wiki.py` pattern automates change detection and maps project changes
to the wiki pages they affect.

### Sync Script

Create a `sync-wiki.py` in the wiki directory that:

1. Compares the current git commit against the last-synced commit
2. Maps changed project files to affected wiki pages via a relevance table
3. Outputs a structured report grouped by relevance (direct / related / minor)
4. After the LLM updates wiki pages, rebuilds the HTML viewer via `--rebuild`

**Mapping table: three relevance levels:**
  - **direct** — must be updated (e.g. Model change -> entity page)
  - **related** — should be reviewed (e.g. Service change -> concept page)
  - **minor** — consider (e.g. Controller change, thin layer, low impact)

```python
MAPPING = [
    (r"^app/Models/Customer\.php$", [
        ("entities/customer", "direct", "Model schema, relationships"),
    ]),
    (r"^app/Enums/.*\.php$", [
        ("concepts/state-machines", "direct", "Enum definitions, transitions"),
    ]),
    (r"^app/Services/OrderService\.php$", [
        ("entities/order", "direct", "Order lifecycle"),
        ("entities/delivery-order", "direct", "D.O. creation on confirm"),
        ("concepts/service-layer", "related", "Service implementation"),
    ]),
]
```

See `scripts/sync-wiki.py` in this skill for a full implementation.

### Using MCP Tools for Semantic Analysis

For richer analysis beyond file-path mapping, the LLM can use knowledge-graph
MCP tools (GitNexus, codebase-memory-mcp) for semantic impact:

- `impact("OrderService::confirm")` — what functions, tests, and flows are
  affected, revealing wiki pages beyond the path mapping
- `context("Customer")` — full 360-degree symbol view
- `detect_changes()` — structured diff of affected symbols with risk levels

**Full workflow:**
1. `sync-wiki.py` produces the file-path report
2. LLM uses MCP tools on critical changed symbols for impact analysis
3. LLM updates wiki pages based on combined file + semantic analysis
4. `python3 sync-wiki.py --rebuild` regenerates the HTML viewer

### Repeat Commands

```bash
cd ~/wiki/<project>
uv run --with markdown python3 sync-wiki.py           # detect and report
uv run --with markdown python3 sync-wiki.py --rebuild  # rebuild after edits
python3 sync-wiki.py --status                           # check sync state
python3 sync-wiki.py --reset                            # reset to HEAD
```

## Related

- [llm-wiki] skill — day-to-day operations after the migration is done
- [wiki-publishing] skill — builds and serves the HTML viewer
- `references/` directory in this skill — session-specific migration recipes
- `scripts/sync-wiki.py` in this skill — sync implementation

---
name: hermes-agent-skill-authoring
description: "Author in-repo SKILL.md: frontmatter, validator, structure."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [skills, authoring, hermes-agent, conventions, skill-md]
    related_skills: [plan, requesting-code-review, agentskills-creator]
---

# Authoring Hermes-Agent Skills (in-repo)

## Overview

There are three places a SKILL.md can live:

1. **Universal agentskills.io directory:** `~/.agents/skills/<name>/SKILL.md` — the standard location defined by the Agent Skills specification (agentskills.io). Skills here are consumed by any compatible agent tool (Claude Code, Codex, OpenCode, Hermes, etc.). Must strictly follow the agentskills.io spec — no Hermes-only extensions at the top level. Non-spec fields (`inputs`, `references`, etc.) should go inside `metadata:`.

2. **User-local (Hermes):** `~/.hermes/skills/<maybe-category>/<name>/SKILL.md` — personal, not shared. Created via `skill_manage(action='create')`. Can use Hermes-specific extensions (`inputs:` at top level is read by the Hermes skill loader).

3. **In-repo (this skill is about this case):** `/home/bb/hermes-agent/skills/<category>/<name>/SKILL.md` — committed, shipped with the package. Use `write_file` + `git add`. `skill_manage(action='create')` does NOT target this tree.

**Important distinction:** skills in `~/.agents/skills/` serve the entire agentskills.io ecosystem, not just Hermes. If you add a Hermes-only extension (`inputs:`, `version:`, etc.) at the top level there, it is technically outside the spec. When you have a non-spec field, prefer `metadata.<field>` over a top-level key — this keeps the skill spec-compliant while preserving the data.

## When to Use

- User asks you to add a skill "in this branch / repo / commit"
- You're committing a reusable workflow that should ship with hermes-agent
- You're editing an existing skill under `/home/bb/hermes-agent/skills/` (use `patch` for small edits, `write_file` for rewrites; `skill_manage` still works for patch on in-repo skills, but not for `create`)

## Required Frontmatter

Two layers of requirements apply:

1. **agentskills.io spec** — the open Agent Skills specification at https://agentskills.io/specification. Defines the portable format that any agent client can read.
2. **Hermes validator** — `tools/skill_manager_tool.py::_validate_frontmatter`. Hermes-specific hard requirements over and above the spec.

Always satisfy both. The spec is the authoritative reference for portable fields; the Hermes validator adds constraints for the Hermes runtime.

### agentskills.io fields

| Field | Required | Format |
|-------|----------|--------|
| `name` | Yes | Max 64 chars. Lowercase letters, numbers, hyphens only. **Must match the parent directory name.** |
| `description` | Yes | Max 1024 chars. Describe what the skill does AND when to use it. |
| `license` | No | License name or reference to a bundled file. |
| `compatibility` | No | Max 500 chars. Environment requirements. |
| `metadata` | No | Arbitrary key-value mapping. |
| `allowed-tools` | No | **Space-separated string** (not YAML list). Example: `allowed-tools: Bash(git:*) Bash(jq:*) Read` |

**Critical: `allowed-tools` is a space-separated string per the spec**. Do NOT use YAML list format:

```yaml
# CORRECT (space-separated string)
allowed-tools: Bash(firecrawl *) Bash(npx firecrawl *)

# WRONG (YAML list — violates agentskills.io spec)
allowed-tools:
  - Bash(firecrawl *)
  - Bash(npx firecrawl *)
```

### Hermes-specific top-level extensions

These are NOT in the agentskills.io spec but are used by Hermes at runtime:

- `inputs:` — declares required/optional env-var or config inputs (e.g. API keys). Used by the skill loader to prompt the user for missing configuration. List of `{name, description?, required?}` objects.
- `version`, `author`, `license` at top level — convention from Hermes peer skills, not spec-enforced.

When adding a field not in the agentskills.io spec, consider whether it belongs inside `metadata:` instead of at the top level. Example: `inputs:` is used as top-level by many firecrawl workflow skills, but strictly belongs outside the portable spec.

### Hermes validator requirements

Source of truth: `tools/skill_manager_tool.py::_validate_frontmatter`. Hard requirements:

- Starts with `---` as the first bytes (no leading blank line).
- Closes with `\n---\n` before the body.
- Parses as a YAML mapping.
- `name` field present.
- `description` field present, ≤ **1024 chars** (`MAX_DESCRIPTION_LENGTH`).
- Non-empty body after the closing `---`.

Peer-matched shape used by every skill under `skills/software-development/`:

```yaml
---
name: my-skill-name               # lowercase, hyphens, ≤64 chars (MAX_NAME_LENGTH)
description: Use when <trigger>. <one-line behavior>.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [short, descriptive, tags]
    related_skills: [other-skill, another-skill]
---
```

`version` / `author` / `license` / `metadata` are NOT enforced by the validator, but every peer has them — omit and your skill sticks out.

## Size Limits

- Description: ≤ 1024 chars (enforced).
- Full SKILL.md: ≤ 100,000 chars (enforced as `MAX_SKILL_CONTENT_CHARS`, ~36k tokens).
- Peer skills in `software-development/` sit at **8-14k chars**. Aim for that range. If you're pushing past 20k, split into `references/*.md` and reference them from SKILL.md.

## Peer-Matched Structure

Every in-repo skill follows roughly:

```
# <Title>

## Overview
One or two paragraphs: what and why.

## When to Use
- Bulleted triggers
- "Don't use for:" counter-triggers

## <Topic sections specific to the skill>
- Quick-reference tables are common
- Code blocks with exact commands
- Hermes-specific recipes (tests via scripts/run_tests.sh, ui-tui paths, etc.)

## Common Pitfalls
Numbered list of mistakes and their fixes.

## Verification Checklist
- [ ] Checkbox list of post-action verifications

## One-Shot Recipes (optional)
Named scenarios → concrete command sequences.
```

Not every section is mandatory, but `Overview` + `When to Use` + actionable body + pitfalls are the minimum for the skill to feel like a peer.

## Directory Placement

```
skills/<category>/<skill-name>/SKILL.md
```

Categories currently in repo (confirm with `ls skills/`): `autonomous-ai-agents`, `creative`, `data-science`, `devops`, `dogfood`, `email`, `gaming`, `github`, `leisure`, `mcp`, `media`, `mlops/*`, `note-taking`, `productivity`, `red-teaming`, `research`, `smart-home`, `social-media`, `software-development`.

Pick the closest existing category. Don't invent new top-level categories casually.

## Workflow

1. **Survey peers** in the target category:
   ```
   ls skills/<category>/
   ```
   Read 2-3 peer SKILL.md files to match tone and structure.
2. **Check validator constraints** in `tools/skill_manager_tool.py` if unsure.
3. **Draft** with `write_file` to `skills/<category>/<name>/SKILL.md`.
4. **Validate locally**:
   ```python
   import yaml, re, pathlib
   content = pathlib.Path("skills/<category>/<name>/SKILL.md").read_text()
   assert content.startswith("---")
   m = re.search(r'\n---\s*\n', content[3:])
   fm = yaml.safe_load(content[3:m.start()+3])
   assert "name" in fm and "description" in fm
   assert len(fm["description"]) <= 1024
   assert len(content) <= 100_000
   ```
5. **Git add + commit** on the active branch.
6. **Note:** the CURRENT session's skill loader is cached — `skill_view` / `skills_list` will not see the new skill until a new session. This is expected, not a bug.

## Cross-Referencing Other Skills

`metadata.hermes.related_skills` unions both trees (`skills/` in-repo and `~/.hermes/skills/`) at load time. You CAN reference a user-local skill from an in-repo skill, but it won't resolve for other users who clone the repo fresh. Prefer referencing only in-repo skills from in-repo skills. If a frequently-referenced skill lives only in `~/.hermes/skills/`, consider promoting it to the repo.

## Editing Existing In-Repo Skills

- **Small fix (typo, added pitfall, tightened trigger):** `skill_manage(action='patch', name=..., old_string=..., new_string=...)` works fine on in-repo skills.
- **Major rewrite:** `write_file` the whole SKILL.md. `skill_manage(action='edit')` also works but requires supplying the full new content.
- **Adding supporting files:** `write_file` to `skills/<category>/<name>/references/<file>.md`, `templates/<file>`, or `scripts/<file>`. `skill_manage(action='write_file')` also works and enforces the references/templates/scripts/assets subdir allowlist.
- **Always commit** the edit — in-repo skills are source, not runtime state.

## Common Pitfalls

1. **Using `skill_manage(action='create')` for an in-repo skill.** It writes to `~/.hermes/skills/`, not the repo tree. Use `write_file` for in-repo creation.

2. **Leading whitespace before `---`.** The validator checks `content.startswith("---")`; any leading blank line or BOM fails validation.

3. **Description too generic.** Peer descriptions start with "Use when ..." and describe the *trigger class*, not the one task. "Use when debugging X" > "Debug X".

4. **Forgetting the author/license/metadata block.** Not validator-enforced, but every peer has it; omitting makes the skill look half-finished.

5. **Writing a skill that duplicates a peer.** Before creating, `ls skills/<category>/` and open 2-3 peers. Prefer extending an existing skill to creating a narrow sibling.

6. **Expecting the current session to see the new skill.** It won't. The skill loader is initialized at session start. Verify in a fresh session or via `skill_view` using the exact path.

7. **Linking to skills that don't exist in-repo.** `related_skills: [some-user-local-skill]` works for you but breaks for other clones. Prefer only in-repo links.

8. **External scripts read credentials from env vars only, ignoring Hermes config.** When your skill ships a script (Python, shell, etc.) that needs API credentials — base URL, token, API key — use a fallback chain: **Hermes config (`hermes config set skillname.key value`) > environment variable > default**. This keeps credentials in Hermes's unified config system rather than scattered across shell profiles.

    Pure-stdlib config reader (no PyYAML needed):

    ```python
    import os, re

    def _read_hermes_config() -> dict:
        home = os.environ.get("HERMES_HOME") or os.path.join(os.path.expanduser("~"), ".hermes")
        path = os.path.join(home, "config.yaml")
        if not os.path.isfile(path):
            return {}
        result = {}
        current_section = None
        with open(path) as f:
            for line in f:
                stripped = line.rstrip()
                if not stripped or stripped.startswith("#"):
                    continue
                if not stripped[0].isspace():
                    if ":" in stripped and not stripped.lstrip().startswith("-"):
                        key = stripped.split(":", 1)[0].strip()
                        if key and " " not in key:
                            current_section = key
                    else:
                        current_section = None
                elif current_section and stripped[0].isspace():
                    m = re.match(r"^\s+([\w.-]+)\s*:\s*(.*)", stripped)
                    if m:
                        full_key = f"{current_section}.{m.group(1)}"
                        val = m.group(2).strip().strip("\"'")
                        result[full_key] = val
        return result

    cfg = _read_hermes_config()
    base_url = cfg.get("tds.base_url") or os.environ.get("TDS_BASE") or "http://localhost:5380"
    token    = cfg.get("tds.token")    or os.environ.get("TDS_TOKEN") or ""
    ```

    Document the `hermes config set` commands in the skill's Configuration section so the user knows how to set them. The `technitium-dns` skill is a worked example.

9. **Using YAML list format for `allowed-tools`.** Per agentskills.io/specification, `allowed-tools` must be a space-separated string, not a YAML list. The Hermes validator may accept either, but the open spec only guarantees the string form. Use:
    ```yaml
    allowed-tools: Bash(firecrawl *) Bash(npx firecrawl *)
    ```
    Not:
    ```yaml
    allowed-tools:
      - Bash(firecrawl *)
      - Bash(npx firecrawl *)
    ```

10. **Adding a top-level field that belongs in `metadata`.** The agentskills.io spec defines only: `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`. Fields like `inputs`, `version`, `author`, `homepage`, `source` are not spec fields. Put custom metadata inside `metadata:` (or use top-level only when Hermes explicitly reads it, e.g. `inputs:`). Check the spec first before inventing a new top-level key.

11. **Bulk frontmatter transformation walking into YAML literal blocks.** When moving `inputs:` to `metadata.inputs:` across many files, a line-based text approach (`read_file` + regex on frontmatter lines) will corrupt files whose `description:` uses a literal block scalar (`|`):

    ```yaml
    description: |
      This description spans multiple lines
      and looks like `  inputs:` could be a continuation line
      unless you track YAML indentation levels properly.
    ```

    A naive script sees `  inputs:` on a continuation line and treats it as the top-level field — embedding the entire inputs block inside the description. **Always use a proper YAML parser** (`yaml.safe_load`) for structural changes to frontmatter, or if using text-based methods, detect and skip lines that are inside a `|` literal block by tracking the block scalar state.

    Safe workflow for bulk migration:
    ```python
    import yaml, re
    # Read → split on --- → yaml.safe_load(fm) → modify dict → yaml.dump → reconstruct → validate → write
    # Never: line-by-line regex substitution on frontmatter
    ```

12. **Skipping YAML validation after automated transformation.** After any scripted change to frontmatter (especially bulk operations), run a validation pass across all touched files before declaring done:

    ```bash
    cd ~/.agents/skills
    python3 -c "
    import yaml, glob
    for f in sorted(glob.glob('firecrawl*/SKILL.md')):
        content = open(f).read()
        assert content.startswith('---'), f'{f}: no leading ---'
        fm = content.split('---', 2)[1]
        data = yaml.safe_load(fm)
        assert isinstance(data, dict), f'{f}: not a mapping'
        assert 'name' in data, f'{f}: missing name'
        assert 'description' in data, f'{f}: missing description'
        spec_keys = {'name','description','license','compatibility','metadata','allowed-tools'}
        extras = set(data.keys()) - spec_keys
        if extras:
            print(f'WARN {f}: non-spec top-level keys: {extras}')
        print(f'OK {f}')
    "
    ```

    This catches corrupted literal blocks, YAML parse errors, and stray non-standard keys in one pass.

## Verification Checklist

- [ ] File is at `skills/<category>/<name>/SKILL.md` (not in `~/.hermes/skills/`)
- [ ] Frontmatter starts at byte 0 with `---`, closes with `\n---\n`
- [ ] `name`, `description`, `version`, `author`, `license`, `metadata.hermes.{tags, related_skills}` all present
- [ ] Name ≤ 64 chars, lowercase + hyphens, matches parent directory name
- [ ] Description ≤ 1024 chars and starts with "Use when ..."
- [ ] `allowed-tools` is a **space-separated string** (not YAML list) per agentskills.io spec
- [ ] Custom top-level fields (`inputs`, etc.) are documented as Hermes extensions, not spec fields
- [ ] Total file ≤ 100,000 chars (aim for 8-15k)
- [ ] Structure: `# Title` → `## Overview` → `## When to Use` → body → `## Common Pitfalls` → `## Verification Checklist`
- [ ] `related_skills` references resolve in-repo (or are explicitly OK to be user-local)
- [ ] `git add skills/<category>/<name>/ && git commit` completed on the intended branch

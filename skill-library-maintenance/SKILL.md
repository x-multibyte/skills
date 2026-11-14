---
name: skill-library-maintenance
description: Onboard external skills into Hermes and normalize to spec.
metadata:
  related_skills:
    - skills-spec-compliance
    - agentskills-creator
---

# Skill Library Maintenance

Install external skills, audit them, and normalize frontmatter to the agentskills.io spec.

## When to Use

- User says "run `npx skills add <repo-url>`" or wants skills from a GitHub repo installed into Hermes
- Auditing `~/.hermes/skills/` for spec violations (non-standard top-level keys, bad allowed-tools format, name/dir mismatch)
- Bulk-normalizing many skills at once (move `category`/`version`/`platforms`/`tags`/`requires`/`hidden` into `metadata`)
- Verifying a skill with `skills-ref validate`

## Spec Quick Reference

Allowed top-level frontmatter keys (agentskills.io/specification):

```
name, description, license, compatibility, metadata, allowed-tools
```

Anything else at top level (`category`, `version`, `platforms`, `tags`, `requires`, `hidden`, `when_to_use`, `languages`, `context`, `inputs`, `references`) is non-standard and should live inside `metadata:`.

## Step 1 — Install from a repo

```bash
# Interactive (multi-select prompt)
npx --yes skills add "https://github.com/<owner>/<repo>"

# Non-interactive: all skills, Hermes only, global scope, no prompts, copy (not symlink)
npx --yes skills add "<repo-url>" -s '*' -a hermes-agent -g -y --copy

# Preview what a repo contains without installing
npx --yes skills add "<repo-url>" -l
```

- `-s` selects skill names (`'*'` = all), `-a` targets agents (`hermes-agent`), `-g` = global (`~/.hermes/skills/`), `-y` skips prompts, `--copy` copies instead of symlinking (recommended so edits don't break).
- Installed skills land in `~/.hermes/skills/<name>/SKILL.md`.
- The CLI runs a safety scan and prints Safe/Risk per skill before installing.

### Critical quirk: repo-root SKILL.md is silently skipped

`npx skills add` only detects skills whose SKILL.md has `name` + `description` in frontmatter. A repo that ships a root-level `SKILL.md` WITHOUT YAML frontmatter (common — e.g. hkuds/deeptutor) is skipped with:

```
⚠ Skipped .../SKILL.md — missing required frontmatter field(s): name, description
```

To install it anyway, prepend frontmatter and copy manually:

```bash
mkdir -p ~/.hermes/skills/<name>/
printf -- '---\nname: <dir-name>\ndescription: <one-line trigger, "Use when ...">\n---\n\n' > ~/.hermes/skills/<name>/SKILL.md
cat /path/to/skipped/SKILL.md >> ~/.hermes/skills/<name>/SKILL.md
```

## Step 2 — Audit

Run `scripts/audit_spec.py` from the skills dir (see scripts/). It flags, per skill:
- top-level non-standard keys
- `allowed-tools` in YAML-list form (must be space-separated string)
- `name` not matching the parent directory name

```bash
cd ~/.hermes/skills && python3 ~/.hermes/skills/skill-library-maintenance/scripts/audit_spec.py
```

Always re-run after any transformation.

## Step 3 — Normalize

### Move non-standard top-level keys into metadata

```yaml
# BEFORE
category: mlops/inference
version: 1.1.0
platforms: [linux, macos, windows]
tags:
- tool
requires:
  sandbox: shell

# AFTER
metadata:
  category: mlops/inference
  version: 1.1.0
  platforms: [linux, macos, windows]
  tags: [tool]
  requires:
    sandbox: shell
```

- Hermes convention: `category` maps to `metadata.hermes.category` when the skill already has a `metadata.hermes` block (grouping key Hermes reads at load).
- Hermes only reads `name`/`description`/`metadata` — moving `version`/`platforms` into metadata is safe and does NOT break functionality, even though Hermes's own bundled templates use them at top level.

### Fix allowed-tools separator

Comma-separated is wrong; space-separated string is the spec:

```yaml
allowed-tools: Bash(agent-browser:*) Bash(npx agent-browser:*)   # right
allowed-tools: Bash(agent-browser:*), Bash(npx agent-browser:*)  # wrong
```

### Convert inline JSON metadata to YAML block

Some skills carry `metadata:` as a single-line JSON object:

```yaml
metadata:
  {"openclaw":{"emoji":"x","os":["linux","darwin"]}}
```

Parse with `json.loads`, re-emit as nested YAML:

```yaml
metadata:
  version: 1.1.0
  openclaw:
    emoji: x
    os: [linux, darwin]
```

### Normalize line endings

When editing files with mixed CRLF (Windows-authored skills), normalize to LF first — a line-based transform on CRLF content produces corrupt output.

## Step 4 — Validate

```bash
npx --yes skills-ref validate ./<skill>      # per skill
# or loop over all:  for d in */; do npx skills-ref validate "./${d%/}"; done
```

Full-loop check for "ALL VALID" before reporting done.

## Pitfalls

1. **Per-key metadata insertion creates duplicate `metadata:` blocks.** A loop that does `content.replace('\n---\n', f'\nmetadata:\n  {k}: {v}\n---\n', 1)` for each key yields repeated `metadata:` mappings → `YAMLException: duplicated mapping key`. Collect ALL non-standard keys first, then emit ONE metadata block with all keys.

2. **Line-based regex on frontmatter corrupts `description: |` literal blocks.** A continuation line inside a literal block looks like a top-level key to a naive parser. Prefer `yaml.safe_load` for structural edits; if text-based, track block-scalar state.

3. **Backup before bulk edits.** `cp -r` the target skill dirs to /tmp first; rollback is a copy away.

4. **`npx skills add` may target the wrong agent scope.** Without `-a hermes-agent`, skills install to every detected agent dir (~/.claude/skills, ~/.agents/skills, etc.). Use `-a hermes-agent` for Hermes-only installs.

5. **Hub skills installed into other agent dirs still show up in `npx skills list`** with local provenance — don't confuse "already installed somewhere" with "installed for Hermes".

6. **The audit only walks top-level dirs.** Nested categories (e.g. `software-development/<name>/`) need the script pointed at that subtree, or a recursive walk.

## Verification Checklist

- [ ] `npx skills add` ran with `-a hermes-agent -g -y` (or user confirmed scope)
- [ ] Repo-root SKILL.md without frontmatter was checked and installed manually if relevant
- [ ] Audit: 0 non-standard top-level keys, 0 name/dir mismatches, 0 list-form allowed-tools
- [ ] `npx skills-ref validate` → Valid for every touched skill
- [ ] Backup dir exists before any bulk edit

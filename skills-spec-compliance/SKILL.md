---
name: skills-spec-compliance
description: >
  Validate and fix skills against the Agent Skills specification
  (agentskills.io/specification). Detects non-standard top-level
  fields (inputs, references), wrong allowed-tools format (YAML list
  vs space-separated string), and enforces name/directory matching.
  Use when onboarding skills from any source or auditing a skills
  directory for universal spec compliance.
metadata:
  related_skills:
    - agentskills-creator
---

# Skills Spec Compliance

Audit and repair an Agent Skills directory against the [agentskills.io specification](https://agentskills.io/specification).

## Spec Summary

| Field | Required | Format |
|-------|----------|--------|
| `name` | Yes | lowercase + numbers + hyphens, max 64 chars, must match directory name |
| `description` | Yes | max 1024 chars |
| `license` | No | short name or file reference |
| `compatibility` | No | max 500 chars |
| `metadata` | No | arbitrary key-value map |
| `allowed-tools` | No | **space-separated string** (not YAML list), experimental |

Any other top-level key (e.g. `inputs`, `references`) is non-standard and should be moved into `metadata` with 2-char indentation.

## Common Violations to Check

### 1. `allowed-tools` uses YAML list (wrong)

```yaml
# WRONG — YAML list
allowed-tools:
  - Bash(firecrawl *)
  - Bash(npx firecrawl *)
```

```yaml
# RIGHT — space-separated string
allowed-tools: Bash(firecrawl *) Bash(npx firecrawl *)
```

### 2. `inputs` at top level (wrong)

```yaml
# WRONG — top-level inputs
metadata:
  author: firecrawl
inputs:
  - name: API_KEY
    required: true
```

```yaml
# RIGHT — nested under metadata
metadata:
  author: firecrawl
  inputs:
    - name: API_KEY
      required: true
```

### 3. `references` at top level (wrong)

Same as `inputs` — move to `metadata.references`.

## Audit Script

Use this to scan all SKILL.md files in a directory:

```bash
cd /path/to/skills/dir

python3 << 'PYEOF'
import os, re

SKILLS_DIR = "."
SPEC_KEYS = {'name', 'description', 'license', 'compatibility', 'metadata', 'allowed-tools'}

errors = []
ok = []

for f in sorted(os.listdir(SKILLS_DIR)):
    path = os.path.join(SKILLS_DIR, f, 'SKILL.md')
    if not os.path.isfile(path):
        continue

    with open(path) as fh:
        content = fh.read()

    if not content.startswith('---'):
        errors.append(f'{f}: no leading ---')
        continue

    parts = content.split('---', 2)
    if len(parts) < 3:
        errors.append(f'{f}: malformed frontmatter')
        continue

    fm = parts[1]

    # Check non-standard top-level keys
    non_standard = []
    for line in fm.split('\n'):
        stripped = line.rstrip()
        if not stripped or stripped.startswith(' '):
            continue
        m = re.match(r'^([a-zA-Z][a-zA-Z0-9_-]*):', stripped)
        if m and m.group(1) not in SPEC_KEYS:
            non_standard.append(m.group(1))

    # Check name matches dir
    name_match = re.search(r'^name:\s*(\S+)', fm, re.MULTILINE)
    name_val = name_match.group(1) if name_match else None

    # Check allowed-tools uses list form (YAML list on next line)
    at_match = re.search(r'^allowed-tools:\s*\n', fm, re.MULTILINE)

    issues = []
    if non_standard:
        issues.append(f'top-level non-standard keys: {non_standard}')
    if at_match:
        issues.append('allowed-tools uses list format, not space-separated string')
    if name_val and name_val != f:
        issues.append(f'name "{name_val}" != dir "{f}"')

    if issues:
        errors.append(f'{f}: {" | ".join(issues)}')
    else:
        ok.append(f)

print(f'Total: {len(ok)+len(errors)} skills')
print(f'OK: {len(ok)}')
print(f'Issues: {len(errors)}')
if errors:
    for e in errors:
        print(f'  FAIL  {e}')
    exit(1)
PYEOF
```

## Auto-Fix Patterns (Python)

### Fix `allowed-tools` list → string

```python
import re

for sk_file in all_firecrawl_sk_files:
    with open(sk_file) as f:
        content = f.read()
    # Replace 2-line list with 1-line string
    content = content.replace(
        'allowed-tools:\n  - Bash(firecrawl *)\n  - Bash(npx firecrawl *)',
        'allowed-tools: Bash(firecrawl *) Bash(npx firecrawl *)'
    )
    with open(sk_file, 'w') as f:
        f.write(content)
```

### Move `inputs` / `references` into `metadata`

Use a line-based parser: identify non-standard top-level keys, collect their block lines, remove them from top level, and append them inside the `metadata:` block with 2-char extra indentation.

**Caveats:**
- Skills using `description: |` (literal block scalar) — ensure the `inputs:` block doesn't accidentally get absorbed into the description content
- When metadata has empty lines or comments between keys, the insertion position logic must account for that
- After moving blocks in, a second pass may be needed to reorder keys within metadata (put `inputs`/`references` after standard keys like `author`, `version`, `homepage`, `source`)

## Related

For a complete reference on creating skills — including best practices,
directory layout, script running, and eval configuration — see the
`agentskills-creator` skill (skill_view('agentskills-creator')).
This skill focuses narrowly on spec compliance validation; the broader
skill covers the full creation lifecycle.

---

## Pitfalls

- **`description: |` literal blocks**: The `inputs:` text can be accidentally consumed as continuation of a YAML literal block. Always verify YAML structure after automated edits, especially for multi-line descriptions.
- **`name` must match the parent directory name**, not the repository path or any other name.
- **`allowed-tools` is experimental** — some agents may not support it. But when present, the format must be space-separated string, not YAML list.
- **Tools using `skills-ref validate`** will catch these issues. Run `npx skills-ref validate ./my-skill` on each skill after fixing.

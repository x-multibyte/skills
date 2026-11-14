#!/usr/bin/env python3
"""Audit a skills directory against the agentskills.io spec.

Flags, per SKILL.md:
  - top-level non-standard frontmatter keys (anything not in SPEC_KEYS)
  - allowed-tools in YAML-list form (must be space-separated string)
  - name not matching parent directory name

Usage:
  python3 audit_spec.py [DIR]     # default: current directory, top-level walk

Exit code 1 when issues found (so it can gate CI / post-edit checks).
"""
import os
import re
import sys

SPEC_KEYS = {'name', 'description', 'license', 'compatibility', 'metadata', 'allowed-tools'}


def audit_dir(skills_dir: str) -> tuple[list[str], list[str]]:
    errors, ok = [], []
    for f in sorted(os.listdir(skills_dir)):
        path = os.path.join(skills_dir, f, 'SKILL.md')
        if not os.path.isfile(path):
            continue
        with open(path, encoding='utf-8') as fh:
            content = fh.read()

        if not content.startswith('---'):
            errors.append(f'{f}: no leading ---')
            continue

        parts = content.split('---', 2)
        if len(parts) < 3:
            errors.append(f'{f}: malformed frontmatter')
            continue
        fm = parts[1]

        # Non-standard top-level keys (skip indented continuation lines)
        non_standard = []
        for line in fm.split('\n'):
            stripped = line.rstrip()
            if not stripped or stripped.startswith(' '):
                continue
            m = re.match(r'^([a-zA-Z][a-zA-Z0-9_-]*):', stripped)
            if m and m.group(1) not in SPEC_KEYS:
                non_standard.append(m.group(1))

        # name must match directory name
        name_match = re.search(r'^name:\s*(\S+)', fm, re.MULTILINE)
        name_val = name_match.group(1) if name_match else None

        # allowed-tools must be a space-separated string, not a YAML list
        at_list = re.search(r'^allowed-tools:\s*\n', fm, re.MULTILINE)

        issues = []
        if non_standard:
            issues.append(f'top-level non-standard keys: {non_standard}')
        if at_list:
            issues.append('allowed-tools uses list format, not space-separated string')
        if name_val and name_val != f:
            issues.append(f'name "{name_val}" != dir "{f}"')

        if issues:
            errors.append(f'{f}: {" | ".join(issues)}')
        else:
            ok.append(f)

    return ok, errors


def main() -> int:
    skills_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    ok, errors = audit_dir(skills_dir)
    print(f'Total: {len(ok) + len(errors)} | OK: {len(ok)} | Issues: {len(errors)}')
    for e in errors:
        print(f'  FAIL  {e}')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""
Sync a project wiki with codebase changes.
Detects git changes, maps them to wiki pages via a rule table,
and reports what needs updating.

Usage:
    uv run --with markdown python3 scripts/sync-wiki.py              # detect and report
    uv run --with markdown python3 scripts/sync-wiki.py --rebuild    # rebuild viewer
    python3 scripts/sync-wiki.py --status                            # check sync state
    python3 scripts/sync-wiki.py --reset                             # reset to HEAD

Customise for each project:
    1. Set WIKI and PROJECT paths
    2. Adjust MAPPING table for your project's file-to-page relationships
"""

import json, os, re, subprocess, sys
from datetime import datetime
from pathlib import Path

# ── CONFIGURE THESE ───────────────────────────────────────────────────
WIKI = Path.home() / "wiki" / "your-project"       # wiki directory
PROJECT = Path.home() / "code" / "your-project"     # codebase directory
STATE_FILE = WIKI / ".sync-state.json"
BUILD_SCRIPT = WIKI / "build-wiki.py"

# ── FILE-TO-WIKI MAPPING ─────────────────────────────────────────────
# Pattern: (regex, [(wiki_slug, relevance, reason), ...])
# relevance: direct | related | minor

MAPPING = [
    # Models -> entity pages
    (r"^app/Models/(.+)\.php$", [
        ("entities/{slug}", "direct", "Model schema, relationships, casts"),
    ]),
    # Enums -> state machine concept
    (r"^app/Enums/.*\.php$", [
        ("concepts/state-machines", "direct", "Enum definitions, transitions"),
    ]),
    # Services -> one or more entity + service concept
    (r"^app/Services/OrderService\.php$", [
        ("entities/order", "direct", "Order lifecycle"),
        ("entities/delivery-order", "direct", "D.O. creation"),
        ("concepts/service-layer", "related", "Service implementation"),
    ]),
    # Tests -> testing concept
    (r"^tests/Feature/.*Test\.php$", [
        ("concepts/testing-strategy", "direct", "Feature test changes"),
    ]),
    # Docker / Compose -> infrastructure concept
    (r"^(docker/|compose\.yaml)", [
        ("concepts/infrastructure", "direct", "Infrastructure changes"),
    ]),
    # Config files -> infrastructure concept
    (r"^(composer\.json|package\.json)", [
        ("concepts/infrastructure", "related", "Dependency changes"),
    ]),
]


# ── helpers ──────────────────────────────────────────────────────────

def run(cmd, cwd=None):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd or PROJECT, timeout=30)
        return r.stdout.strip(), r.returncode
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "", -1


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"last_commit": None, "last_sync": None, "notes": ""}


def save_state(data):
    STATE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def git_log_since(ref, max_count=20):
    if ref:
        out, _ = run(["git", "log", f"{ref}..HEAD", "--oneline", f"--max-count={max_count}"])
    else:
        out, _ = run(["git", "log", f"--max-count={max_count}", "--oneline"])
    return out.split("\n") if out else []


def git_diff_files(ref):
    if ref:
        out, _ = run(["git", "diff", "--name-status", f"{ref}..HEAD"])
    else:
        out, _ = run(["git", "diff", "--name-status", "HEAD~5..HEAD"])
    return out.split("\n") if out else []


def git_current_commit():
    out, _ = run(["git", "rev-parse", "HEAD"])
    return out


def git_current_branch():
    out, _ = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    return out


def match_file(filepath):
    """Match a changed file against the mapping table."""
    results = []
    for pattern, targets in MAPPING:
        m = re.match(pattern, filepath)
        if m:
            captures = m.groups()
            for slug_template, relevance, reason in targets:
                # Substitute {slug} from capture groups (lowercased, hyphens)
                slug = slug_template
                if capture_group and '{slug}' in slug:
                    slug = slug.replace('{slug}', captures[0].replace('_', '-').lower())
                results.append((slug.strip('/'), relevance, reason))
    return results


def categorize_changes(changed_files):
    categories = {"direct": {}, "related": {}, "minor": {}}
    for line in changed_files:
        if not line.strip() or "\t" not in line:
            continue
        status, filepath = line.split("\t", 1)
        matches = match_file(filepath)
        for slug, relevance, reason in matches:
            if slug not in categories[relevance]:
                categories[relevance][slug] = {"files": [], "reasons": set()}
            categories[relevance][slug]["files"].append((status, filepath))
            categories[relevance][slug]["reasons"].add(reason)
    return categories


def format_report(state, commits, categories):
    lines = []
    lines.append("# Wiki Sync Report")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**Project:** {PROJECT}")
    lines.append(f"**Branch:** {git_current_branch()}")
    lines.append(f"**HEAD:** {git_current_commit()[:12]}")
    last = state.get('last_commit')
    lines.append(f"**Last synced:** {last[:12] if last else '(never)'}")
    lines.append("")

    if commits:
        lines.append("## Recent Commits")
        for c in commits:
            parts = c.split(" ", 1)
            lines.append(f"- `{parts[0]}` {parts[1] if len(parts) > 1 else ''}")
        lines.append("")

    total = sum(len(v) for v in categories.values())
    if total == 0:
        lines.append("## No changes detected — wiki is in sync.")
        return "\n".join(lines)

    lines.append(f"## Suggested Wiki Updates ({total} pages affected)")
    labels = [("direct", "Direct — must update"),
              ("related", "Related — should review"),
              ("minor", "Minor — consider reviewing")]
    for key, label in labels:
        items = categories.get(key, {})
        if not items:
            continue
        lines.append(f"\n### {label}\n")
        for slug, info in sorted(items.items()):
            page = WIKI / f"{slug}.md"
            exists = "OK" if page.exists() else "NEW (create)"
            lines.append(f"**{slug}** [{exists}]")
            for f in info["files"]:
                lines.append(f"  - {f[0]} `{f[1]}`")
            for r in info["reasons"]:
                lines.append(f"  - Reason: {r}")
            lines.append("")

    lines.append("---")
    lines.append("After updating wiki pages, run:")
    lines.append("  uv run --with markdown python3 scripts/sync-wiki.py --rebuild")
    return "\n".join(lines)


# ── main ─────────────────────────────────────────────────────────────

def main():
    if not PROJECT.exists():
        print(f"Project not found: {PROJECT}"); sys.exit(1)
    if not WIKI.exists():
        print(f"Wiki not found: {WIKI}"); sys.exit(1)

    # status
    if "--status" in sys.argv:
        s = load_state()
        print(f"Last commit: {s.get('last_commit', '(never)')}")
        print(f"Last sync:   {s.get('last_sync', '(never)')}")
        print(f"HEAD:        {git_current_commit()}")
        return

    # reset
    if "--reset" in sys.argv:
        head = git_current_commit()
        save_state({"last_commit": head, "last_sync": datetime.now().isoformat(), "notes": "Reset"})
        print(f"Reset to {head[:12]}")
        return

    # rebuild
    if "--rebuild" in sys.argv:
        if BUILD_SCRIPT.exists():
            r = subprocess.run(["uv", "run", "--with", "markdown", "python3", str(BUILD_SCRIPT)],
                               capture_output=True, text=True, timeout=60)
            print(r.stdout)
            if r.returncode != 0:
                print(f"Build failed: {r.stderr}"); sys.exit(1)
            head = git_current_commit()
            s = load_state()
            s["last_commit"] = head
            s["last_sync"] = datetime.now().isoformat()
            s["notes"] = "Rebuilt after wiki update"
            save_state(s)
            print(f"Sync state saved (commit: {head[:12]})")
        else:
            print(f"Build script not found: {BUILD_SCRIPT}")
        return

    # detect
    state = load_state()
    last = state.get("last_commit")
    commits = git_log_since(last) if last else git_log_since(None, 10)
    files = git_diff_files(last) if last else []
    if not files and not commits:
        print("No changes since last sync.")
        return

    categories = categorize_changes(files)
    print(format_report(state, commits, categories))

    d = len(categories["direct"])
    r = len(categories["related"])
    m = len(categories["minor"])
    print(f"--- Summary: {d} direct, {r} review, {m} minor ---")


if __name__ == "__main__":
    main()

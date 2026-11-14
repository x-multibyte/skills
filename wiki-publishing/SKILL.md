---
name: wiki-publishing
description: "Build a browsable static HTML site from a Karpathy-style LLM Wiki, serve locally or via Valet, and maintain the viewer alongside wiki content."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [wiki, html, viewer, static-site, markdown, valet]
    category: research
    related_skills: [llm-wiki, obsidian]
---

# Wiki Publishing

Generate a self-contained HTML viewer from a Karpathy-style LLM Wiki (`~/wiki/`
directory), so the knowledge base is browseable in any browser without Obsidian,
a server, or special tooling.

This skill complements the `llm-wiki` skill, which handles content creation and
maintenance. This skill handles browsing and serving.

## When This Skill Activates

Use this skill when the user:
- Asks for a way to view or browse their wiki in a browser
- Wants to serve their wiki via a local domain
- Asks to "build" or "generate" an HTML site from a wiki directory
- Needs a static HTML viewer for their wiki that works from `file://`
- Mentions hosting their wiki locally (macOS Valet, Linux nginx, etc.)

## Architecture

```
~/wiki/<sub-wiki>/
├── entities/
├── concepts/
├── index.html          # ← generated static HTML viewer
├── build-wiki.py       # ← your build script (customized per wiki)
└── SCHEMA.md
```

The viewer is a **single self-contained HTML file** that embeds all wiki pages
as JSON data. No build step dependencies at runtime — the HTML works from
`file://` or any static file server once generated.

## Script Template

Below is the canonical build script. Customise it per wiki:

  1. Adjust `WIKI` path to point at your sub-wiki
  2. Adjust sections and display order in `order` list
  3. Run: `uv run --with markdown python3 build-wiki.py`

```python
#!/usr/bin/env python3
"""Build a self-contained HTML viewer for a Karpathy-style wiki."""
import json, os, re, hashlib
from pathlib import Path
from markdown import markdown as md_render

WIKI = Path.home() / "wiki" / "erp-lite"  # ← CHANGE THIS

def parse_frontmatter(text):
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    if not m:
        return {}, text
    fm = {}
    for line in m.group(1).strip().split('\n'):
        line = line.strip()
        if ':' not in line:
            continue
        key, _, val = line.partition(':')
        key, val = key.strip(), val.strip()
        if val.startswith('[') and val.endswith(']'):
            val = [v.strip().strip("'\"") for v in val[1:-1].split(',') if v.strip()]
        elif val.lower() in ('true', 'false'):
            val = val.lower() == 'true'
        else:
            val = val.strip("'\"")
        fm[key] = val
    return fm, text[m.end():]

def resolve_wikilinks(html, pages):
    def repl(m):
        target = m.group(1).strip()
        for p in pages:
            if p['slug'] == target or p['title'] == target:
                return f'<a href="#{p["slug"]}" class="wikilink">{p["title"]}</a>'
        return f'<span class="wikilink broken" title="page not found">{target}</span>'
    return re.sub(r'\[\[([^\]]+)\]\]', repl, html)

def slug_from_path(path):
    return path.with_suffix('').name

pages = []
order = ['Entities', 'Concepts', 'Decisions', 'Queries']

for dir_name in ['entities', 'concepts', 'decisions', 'queries']:
    dir_path = WIKI / dir_name
    if not dir_path.exists():
        continue
    for f in sorted(dir_path.glob('*.md')):
        text = f.read_text(encoding='utf-8')
        fm, body = parse_frontmatter(text)
        slug = slug_from_path(f)
        pages.append({
            'slug': slug,
            'title': fm.get('title', slug.replace('-', ' ').title()),
            'type': fm.get('type', ''),
            'section': dir_name.title(),
            'tags': fm.get('tags', []),
            'created': fm.get('created', ''),
            'updated': fm.get('updated', ''),
            'html': resolve_wikilinks(md_render(body, extensions=['fenced_code', 'tables']), pages),  # noqa
        })

# ... (then embed into HTML template — see the full script in scripts/build-wiki-viewer.py)
# This is a condensed version showing the core logic.
```

**Full template:** See `scripts/build-wiki-viewer.py` in this skill directory for the
complete HTML/CSS/JS template with dark theme, search, tag display, and wikilink navigation.

## Setting Up Local Serving

### macOS (Laravel Valet)

```bash
cd ~/wiki/<sub-wiki>
valet link <sub-wiki-name>
# Access at http://<sub-wiki-name>.test
```

Valet nginx already wildcard-matches `*.test` — `valet link` only creates a symlink
in `~/.config/valet/Sites/`, so no restart is needed.

**Using dots in the name** groups related sub-wikis:
```bash
valet link erp-lite.wiki        # -> http://erp-lite.wiki.test
valet link another-project.wiki # -> http://another-project.wiki.test
```

No PHP needed — the wiki serves static HTML/CSS/JS.

### Linux (nginx)

```nginx
server {
    listen 80;
    server_name wiki.local;
    root /home/user/wiki/<sub-wiki>;
    index index.html;
}
```

### Any OS (Python one-liner)

```bash
cd ~/wiki/<sub-wiki>
python3 -m http.server 8080
# Access at http://localhost:8080
```

## Regenerating After Wiki Updates

```bash
cd ~/wiki/<sub-wiki>
uv run --with markdown python3 build-wiki.py
open index.html  # or reload browser
```

After regeneration, the static viewer is self-contained — no server restart needed
if accessed via `file://`. If served via Valet/nginx, just reload.

## Key Design Decisions

1. **Single file, no runtime deps** — embeds all content as JSON or JavaScript object store. Works offline and overcomes `file://` CORS restrictions when opened directly in a browser without a web server.
2. **No server needed** — open from `file://` on any machine (embed raw strings/store into JS object to avoid `fetch()` CORS blocks).
3. **Wikilinks preserved** — `[[page-name]]` becomes a clickable internal link.
4. **YAML frontmatter rendered** — created/updated dates, tags, type displayed.
5. **Dark theme by default** — matches the Obsidian/terminal aesthetic.
6. **Search/filter** — real-time filtering of sidebar pages by title or tags.

## Obsidian Publish Notes

## Pitfalls

- **Avoid `fetch()` for `file://` HTML Readers** — Browsers block `fetch()` on `file://` URLs due to CORS security policies. Always embed text content directly in an inline JavaScript object (`DOC_STORE` / `pages` array) inside `index.html` so the reader works standalone when double-clicked.

## Obsidian Publish Notes

- **Obsidian Publish pages are JS SPAs**: Chinese-language Obsidian Help pages (`obsidian.md/zh/help/...`) return 404 from Firecrawl and Exa returns the SPA shell only. Reliable extraction methods: (a) Obsidian Publish REST API at `https://publish-01.obsidian.md/access/<uid>/<slug>.md`, (b) browser rendering to get hydrated DOM, or (c) extract the preloaded markdown URL from `<script>` tags.
- **Name the output `index.html`, not `browse.html`** — so Valet/nginx serves it as the directory index automatically.
- **Rebuild after wiki updates** — the viewer is a static snapshot. If you add a new
  entity page, you must re-run the build script.
- **File size** — a wiki with 50+ pages may produce an index.html of 500KB+. This is
  fine to serve locally but may be slow to load over a cellular connection.
- **Broken wikilinks** — the build script highlights broken `[[links]]` in red. Fix
  them by creating the missing page or correcting the link.
- **`markdown` library** — not in Python stdlib. Use `uv run --with markdown python3 build-wiki.py`
  to install on-the-fly without permanently adding it.
- **Do not check `index.html` or `build-wiki.py` into version control** — they are
  derived artifacts of the wiki content, not source. Add to `.gitignore` if the build
  script lives inside a project repo.

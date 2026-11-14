#!/usr/bin/env python3
"""
Build a self-contained HTML viewer for a Karpathy-style LLM Wiki.
Usage:  uv run --with markdown python3 scripts/build-wiki-viewer.py

Output: index.html (self-contained, open in browser, works from file://)

Customise for each wiki:
  1. Change WIKI path to your wiki directory
  2. Adjust the 'order' list if your wiki uses different section directories
  3. Run the uv command above to regenerate
"""
import json
import re
from pathlib import Path

WIKI = Path.home() / "wiki"  # ← CHANGE THIS to your wiki or sub-wiki path

# ── helpers ──────────────────────────────────────────────────────────

def parse_frontmatter(text):
    """Parse YAML frontmatter from a markdown file (stdlib only, no pyyaml)."""
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


def slug_from_path(path):
    return path.with_suffix('').name


def resolve_wikilinks(html, pages):
    """Convert [[page-name]] to <a href="#slug"> links."""
    def repl(m):
        target = m.group(1).strip()
        for p in pages:
            if p['slug'] == target or p['title'] == target:
                return f'<a href="#{p["slug"]}" class="wikilink">{p["title"]}</a>'
        return f'<span class="wikilink broken" title="page not found">{target}</span>'
    return re.sub(r'\[\[([^\]]+)\]\]', repl, html)


# ── collect pages ─────────────────────────────────────────────────────

from markdown import markdown as md_render

sections = {
    'entities': 'Entities',
    'concepts': 'Concepts',
    'comparisons': 'Comparisons',
    'queries': 'Queries',
    'decisions': 'Decisions',
}

pages = []

for dir_name, section_label in sections.items():
    dir_path = WIKI / dir_name
    if not dir_path.exists():
        continue
    for f in sorted(dir_path.glob('*.md')):
        text = f.read_text(encoding='utf-8')
        fm, body = parse_frontmatter(text)
        slug = slug_from_path(f)
        title = fm.get('title', slug.replace('-', ' ').title())
        page_type = fm.get('type', '')
        tags = fm.get('tags', [])
        if isinstance(tags, str):
            tags = [tags]
        html = md_render(body, extensions=['fenced_code', 'tables'])
        pages.append({
            'slug': slug,
            'title': title,
            'type': page_type,
            'section': section_label,
            'tags': tags,
            'created': fm.get('created', ''),
            'updated': fm.get('updated', ''),
            'html': resolve_wikilinks(html, pages),
        })

# ── HTML/CSS/JS template ─────────────────────────────────────────────

HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__WIKI_TITLE__</title>
<style>
  :root {
    --bg: #1a1b1e; --bg2: #222428; --bg3: #2d2f33;
    --fg: #e4e4e7; --fg2: #a1a1aa; --fg3: #71717a;
    --accent: #6366f1; --accent-hover: #818cf8;
    --border: #3f3f46; --heading: #f4f4f5;
    --link: #818cf8; --sidebar-w: 280px;
    --tag-bg: #312e81; --tag-fg: #a5b4fc;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html, body { height: 100%; background: var(--bg); color: var(--fg); }
  body { display: flex; overflow: hidden; }

  #sidebar {
    width: var(--sidebar-w); min-width: var(--sidebar-w);
    background: var(--bg2); border-right: 1px solid var(--border);
    display: flex; flex-direction: column; height: 100vh; overflow: hidden;
  }
  #sidebar h1 {
    font-size: 14px; font-weight: 600; padding: 14px 16px;
    color: var(--heading); border-bottom: 1px solid var(--border);
  }
  #sidebar h1 small { font-weight: 400; font-size: 11px; color: var(--fg3); display: block; margin-top: 2px; }
  #search-wrap { padding: 8px 12px; border-bottom: 1px solid var(--border); }
  #search {
    width: 100%; padding: 7px 10px; border-radius: 6px;
    border: 1px solid var(--border); background: var(--bg3);
    color: var(--fg); font-size: 13px; outline: none;
  }
  #search:focus { border-color: var(--accent); }
  #search::placeholder { color: var(--fg3); }

  #nav-wrap { flex: 1; overflow-y: auto; padding: 8px 0; }
  .section-label {
    font-size: 10px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.08em; color: var(--fg3); padding: 12px 16px 4px;
  }
  .nav-item {
    display: block; padding: 6px 16px; font-size: 13px;
    color: var(--fg2); cursor: pointer; text-decoration: none;
    border-left: 2px solid transparent; transition: all 0.1s;
  }
  .nav-item:hover { background: var(--bg3); color: var(--fg); }
  .nav-item.active {
    color: var(--accent-hover); border-left-color: var(--accent);
    background: rgba(99,102,241,0.08);
  }
  .tag-dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; margin-right: 8px; vertical-align: middle; }
  .tag-dot.entity { background: #22c55e; }
  .tag-dot.concept { background: #3b82f6; }
  .tag-dot.decision { background: #eab308; }
  .tag-dot.query { background: #a855f7; }
  .tag-dot.comparison { background: #ec4899; }

  #main { flex: 1; overflow-y: auto; height: 100vh; }
  #content { max-width: 820px; margin: 0 auto; padding: 40px 48px 80px; }

  .page-header { margin-bottom: 28px; }
  .page-header h2 { font-size: 28px; font-weight: 700; color: var(--heading); margin-bottom: 8px; }
  .page-meta { display: flex; gap: 12px; font-size: 12px; color: var(--fg3); margin-bottom: 12px; flex-wrap: wrap; }
  .page-tags { display: flex; gap: 6px; flex-wrap: wrap; }
  .page-tags .tag { padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 500; background: var(--tag-bg); color: var(--tag-fg); }

  #body h1 { font-size: 1.6em; color: var(--heading); margin: 1.2em 0 0.4em; }
  #body h2 { font-size: 1.3em; color: var(--heading); margin: 1.2em 0 0.4em; padding-bottom: 6px; border-bottom: 1px solid var(--border); }
  #body h3 { font-size: 1.1em; color: var(--heading); margin: 1em 0 0.3em; }
  #body p { line-height: 1.65; margin: 0.6em 0; }
  #body a { color: var(--link); text-decoration: none; }
  #body a:hover { text-decoration: underline; }
  #body a.wikilink {
    padding: 1px 6px; border-radius: 4px;
    background: rgba(99,102,241,0.12); color: var(--accent-hover);
    font-weight: 500; border: 1px solid rgba(99,102,241,0.2);
  }
  #body a.wikilink:hover { background: rgba(99,102,241,0.25); text-decoration: none; }
  #body a.wikilink.broken { background: rgba(239,68,68,0.12); color: #f87171; border-color: rgba(239,68,68,0.2); }
  #body ul, #body ol { margin: 0.4em 0 0.4em 1.6em; }
  #body li { line-height: 1.65; margin: 0.2em 0; }
  #body code { font-family: 'SF Mono', 'Fira Code', monospace; background: var(--bg3); padding: 2px 6px; border-radius: 4px; font-size: 0.88em; color: #f472b6; }
  #body pre { background: var(--bg3); border: 1px solid var(--border); border-radius: 8px; padding: 16px; overflow-x: auto; margin: 0.8em 0; }
  #body pre code { background: none; padding: 0; color: var(--fg); font-size: 13px; line-height: 1.5; }
  #body table { border-collapse: collapse; width: 100%; margin: 0.8em 0; font-size: 13px; }
  #body th { background: var(--bg2); text-align: left; padding: 8px 12px; border: 1px solid var(--border); font-weight: 600; color: var(--fg); }
  #body td { padding: 8px 12px; border: 1px solid var(--border); vertical-align: top; }
  #body tr:nth-child(even) { background: rgba(0,0,0,0.1); }
  #body blockquote { border-left: 3px solid var(--accent); padding: 8px 16px; margin: 0.8em 0; background: var(--bg2); border-radius: 0 6px 6px 0; color: var(--fg2); }
  #body hr { border: none; border-top: 1px solid var(--border); margin: 1.5em 0; }
  #body img { max-width: 100%; border-radius: 6px; }

  #empty { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 60vh; color: var(--fg3); text-align: center; }
  #empty h2 { font-size: 18px; margin-bottom: 8px; color: var(--fg2); }
  #empty p { font-size: 13px; max-width: 360px; line-height: 1.6; }

  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
</head>
<body>

<div id="sidebar">
  <h1>__WIKI_TITLE__<small>__PAGE_COUNT__ pages &middot; <a href="#" onclick="return showHome()" style="color:var(--accent-hover);text-decoration:none;">index</a></small></h1>
  <div id="search-wrap">
    <input id="search" type="text" placeholder="Filter pages..." oninput="filterPages(this.value)">
  </div>
  <div id="nav-wrap"></div>
</div>

<div id="main">
  <div id="content">
    <div id="empty">
      <h2>__WIKI_TITLE__</h2>
      <p>Select a page from the sidebar to view its content.</p>
    </div>
    <div id="body" style="display:none;"></div>
  </div>
</div>

<script>
const PAGES = __PAGES_DATA__;
let currentSlug = null;

function renderNav(pages, filter) {
  const wrap = document.getElementById('nav-wrap');
  const f = filter ? filter.toLowerCase() : '';
  const sections = {};
  const order = ['Entities', 'Concepts', 'Comparisons', 'Decisions', 'Queries'];
  for (const p of pages) {
    if (f && !p.title.toLowerCase().includes(f) && !p.tags.some(t => t.toLowerCase().includes(f))) continue;
    (sections[p.section] = sections[p.section] || []).push(p);
  }
  let html = '';
  for (const label of order) {
    if (!sections[label]) continue;
    html += `<div class="section-label">${label}</div>`;
    for (const p of sections[label]) {
      const cls = p.type || 'concept';
      const active = p.slug === currentSlug ? ' active' : '';
      html += `<a href="#${p.slug}" class="nav-item${active}" data-slug="${p.slug}" onclick="return navigate('${p.slug}')"><span class="tag-dot ${cls}"></span>${p.title}</a>`;
    }
  }
  for (const label of Object.keys(sections).filter(k => !order.includes(k))) {
    html += `<div class="section-label">${label}</div>`;
    for (const p of sections[label]) {
      const cls = p.type || 'concept';
      const active = p.slug === currentSlug ? ' active' : '';
      html += `<a href="#${p.slug}" class="nav-item${active}" data-slug="${p.slug}" onclick="return navigate('${p.slug}')"><span class="tag-dot ${cls}"></span>${p.title}</a>`;
    }
  }
  wrap.innerHTML = html;
}

function navigate(slug) {
  currentSlug = slug;
  const page = PAGES.find(p => p.slug === slug);
  if (!page) return false;
  document.getElementById('empty').style.display = 'none';
  const body = document.getElementById('body');
  body.style.display = 'block';
  const tags = page.tags && page.tags.length ? `<div class="page-tags">${page.tags.map(t => '<span class="tag">' + t + '</span>').join('')}</div>` : '';
  const meta = [];
  if (page.created) meta.push('<span>Created: ' + page.created + '</span>');
  if (page.updated) meta.push('<span>Updated: ' + page.updated + '</span>');
  if (page.type) meta.push('<span>Type: ' + page.type + '</span>');
  body.innerHTML = '<div class="page-header"><h2>' + page.title + '</h2>' + (meta.length ? '<div class="page-meta">' + meta.join('') + '</div>' : '') + tags + '</div>' + page.html;
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
  const navEl = document.querySelector('.nav-item[data-slug="' + slug + '"]');
  if (navEl) navEl.classList.add('active');
  document.getElementById('main').scrollTop = 0;
  history.replaceState(null, '', '#' + slug);
  return false;
}

function showHome() {
  currentSlug = null;
  document.getElementById('empty').style.display = 'flex';
  document.getElementById('body').style.display = 'none';
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
  history.replaceState(null, '', '#');
  return false;
}

function filterPages(val) { renderNav(PAGES, val); }

renderNav(PAGES, '');
window.addEventListener('hashchange', () => {
  const slug = window.location.hash.slice(1);
  if (slug && PAGES.find(p => p.slug === slug)) { navigate(slug); } else { showHome(); }
});
if (window.location.hash) { const slug = window.location.hash.slice(1); if (PAGES.find(p => p.slug === slug)) navigate(slug); }
</script>
</body>
</html>'''

# ── assemble ─────────────────────────────────────────────────────────

wiki_title = WIKI.name.replace('-', ' ').title() + ' Wiki'
html = HTML_TEMPLATE
html = html.replace('__WIKI_TITLE__', wiki_title)
html = html.replace('__PAGE_COUNT__', str(len(pages)))
html = html.replace('__PAGES_DATA__', json.dumps(pages, ensure_ascii=False, indent=2))

output = WIKI / 'index.html'
output.write_text(html, encoding='utf-8')
print(f'[ok] Generated {output} — {len(pages)} pages')

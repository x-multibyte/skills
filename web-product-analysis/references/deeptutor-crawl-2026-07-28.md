# DeepTutor Docs Crawl Reference

## Source
https://docs.deeptutor.info/zh-cn/

## Crawl Date
2026-07-28

## Total Pages Found
41 internal doc pages

## Extraction Pattern Used
Starlight-based documentation site. Sidebar links extracted via regex from landing page HTML:

```python
import re, subprocess
html = subprocess.run(["curl", "-sL", url], capture_output=True, text=True).stdout
links = set()
for m in re.finditer(r'href="(/zh-cn/[^"]+)"', html):
    path = m.group(1)
    # filter out asset files
    if not any(path.endswith(ext) for ext in skip_exts):
        links.add(path)
```

## Page Structure
- 总览 (homepage + contributing): 2 pages
- 快速上手 (get-started): 8 pages (pypi, from-source, docker, cli-only, multi-user, providers, troubleshooting)
- 探索 (explore): 10 pages (chat-workspace, partners, subagents, co-writer, book, space, memory, knowledge, settings)
- 伙伴与渠道 (partners): 16 pages (channels, weixin, wecom, qq, telegram, discord, slack, feishu, dingtalk, matrix, zulip, mattermost, whatsapp, email, mochat, msteams)
- CLI: 5 pages (commands, chat-repl, agent-handoff, server-api)

## Rate Limiting
300ms delay between requests. All 41 pages fetched successfully.

## Results
43 raw articles saved (including landing page and a pre-existing one).
336KB total, 1 file per page with YAML frontmatter (title, source_url, sha256).

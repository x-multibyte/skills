# ai-memory: Full Reference

Project: https://github.com/akitaonrails/ai-memory
Version: 1.14.0 (tagged release)
Native binary: single Rust binary (Axum + SQLite + git2)

## Architecture at a Glance

ai-memory is a Karpathy-style LLM wiki for AI coding agents. Core invariant:
markdown on disk is the source of truth; SQLite is the derived index.

**Data flow:** Agent lifecycle hooks -> POST /hook -> sanitizer -> writer actor ->
wiki/(markdown) + db/memory.sqlite(FTS5 index). Session-end triggers consolidation
(LLM rewrites raw observations into coherent wiki pages). Handoff records let
the next agent resume where the last left off.

**Memory tiers (M8 retention policy):**
- Working: current session only, hard-dropped on session end
- Episodic: 30d hot -> 180d cold -> evict (salience * exp(-lambda * age) + ...)
- Semantic: indefinite, only supersedeable via LLM rewrite
- Procedural: indefinite, frequency-decay if not re-observed
- Pinned pages (`pinned: true` in frontmatter) exempt from all decay

**Search:** FTS5 + link-neighbour RRF, optional vector cosine (when an embedder
is configured). Raw observation FTS as bounded fallback. Zero-LLM mode works
with FTS5 alone.

**Key design decisions (from design-decisions.md):**
- Single Rust binary (not TypeScript + separate Rust engine like agentmemory)
- SQLite WAL mode, single writer actor via mpsc (no 5s data loss window)
- Per-project isolation by UUID `<wiki>/<workspace>/<project>/...`
- Embeddings and LLM are OPTIONAL — system works without any provider key
- Docker recommended for server; native binary for macOS
- Claude Haiku 4.5 is the recommended consolidation LLM (best cost/quality tradeoff)

## Complete Environment Variable Inventory

### Server Core

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_MEMORY_BIND` | `127.0.0.1:49374` | HTTP listen address |
| `AI_MEMORY_ALLOWED_HOSTS` | `localhost,127.0.0.1,::1` | Host header allowlist (required for non-loopback bind) |
| `AI_MEMORY_AUTH_TOKEN` | unset | Bearer token for API auth (required for LAN exposure) |
| `AI_MEMORY_AUTH_HEADER` | `Authorization` | Custom auth header field name |
| `AI_MEMORY_DATA_DIR` | platform default | Data directory (config.toml, wiki/, db/, raw/, models/) |
| `AI_MEMORY_HOME` | unset | Alternative home path |
| `AI_MEMORY_BASE_PATH` | unset | URL base path for reverse proxy |
| `AI_MEMORY_CORS_ALLOW_ORIGINS` | unset | CORS origins for /api/v1 |
| `AI_MEMORY_CONSOLIDATE_ON_SESSION_END` | `true` | Auto-consolidate at session end |
| `AI_MEMORY_ENABLE_WEB` | unset | Enable /web read-only UI |
| `AI_MEMORY_NO_VERSION_CHECK` | unset | Skip version check |
| `AI_MEMORY_PROJECT_STRATEGY` | `basename` | Project detection: `basename`(cwd) or `repo-root`(git root) |

### Web UI

| Variable | Description |
|----------|-------------|
| `AI_MEMORY_WEB_SLUG` | Web UI URL path prefix |
| `AI_MEMORY_WEB_UI_DIR` | Custom web UI directory |
| `AI_MEMORY_WEB_TAILWIND_CSS` | Custom Tailwind CSS path |

### LLM Provider

| Variable | Description |
|----------|-------------|
| `AI_MEMORY_LLM_PROVIDER` | One of: `anthropic`, `openai`, `openai-oauth`, `copilot`, `gemini`, `openai-compat`, `opencode`, `anthropic-oauth` |
| `AI_MEMORY_LLM_MODEL` | Model name (e.g. `claude-sonnet-4-6`, `gpt-5.5`, `gemini-2.5-flash`) |
| `AI_MEMORY_LLM_BASE_URL` | Custom API endpoint (for `openai-compat`) |
| `AI_MEMORY_LLM_COMPAT_STRICT` | Strict mode for openai-compat |

### Embedding Provider

| Variable | Description |
|----------|-------------|
| `AI_MEMORY_EMBEDDING_PROVIDER` | One of: `openai`, `voyage`, `google`, `gemini` |
| `AI_MEMORY_EMBEDDING_MODEL` | e.g. `text-embedding-3-small`, `gemini-embedding-001` |
| `AI_MEMORY_EMBEDDING_BASE_URL` | Custom embedding endpoint (OpenAI-compatible) |
| `AI_MEMORY_EMBEDDING_DIM` | Dimension (1536 OpenAI, 1024 Voyage, 768 Google) |

### Hook System

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_MEMORY_HOOK_URL` | unset | Custom hook endpoint URL |
| `AI_MEMORY_HOOK_PLATFORM` | auto | Hook script platform: `posix-native` or `posix` |
| `AI_MEMORY_HOOK_RATE_PER_SEC` | 0 (disabled) | Hook ingest rate limit per actor/session |
| `AI_MEMORY_HOOK_RATE_BURST` | = rate | Burst limit (min 1 when enabled) |
| `AI_MEMORY_HOOK_START_BUDGET_MINUTES` | unset | Session start time budget |
| `AI_MEMORY_HOOK_DRAIN_TIMEOUT_MINUTES` | unset | Hook drain timeout |
| `AI_MEMORY_HOOK_HANDOFF_TIMEOUT_MINUTES` | unset | Handoff write timeout |
| `AI_MEMORY_HOOK_BACKGROUND_DRAIN_BUDGET_MINUTES` | unset | Background drain budget |
| `AI_MEMORY_HOOK_INCREMENTAL_THRESHOLD` | unset | Incremental capture threshold |
| `AI_MEMORY_HOOKS_HOST_ROOT` | unset | Host-side hooks directory root |

### Client / CLI

| Variable | Description |
|----------|-------------|
| `AI_MEMORY_SERVER_URL` | Server URL for CLI commands (status, search, backup, etc.) |
| `AI_MEMORY_SESSION_ID` | Override session ID |
| `AI_MEMORY_HOST_CWD` | Override current working directory |
| `AI_MEMORY_DATA_VOLUME` | Docker data volume name |
| `AI_MEMORY_WRAPPER_URL` | Wrapper script download URL |

### Auto-Scope

| Variable | Description |
|----------|-------------|
| `AI_MEMORY_AUTO_SCOPE__MODE` | Scope mode |
| `AI_MEMORY_AUTO_SCOPE__MAX_ENTRIES` | Max entries |
| `AI_MEMORY_AUTO_SCOPE__SESSION_TTL_SECS` | Session TTL (seconds) |

### Other / Internal

| Variable | Description |
|----------|-------------|
| `AI_MEMORY_ADMISSION_WEBHOOKS_JSON` | Admission webhook JSON config |
| `AI_MEMORY_COPILOT_CLIENT_ID` | Custom Copilot client ID |
| `AI_MEMORY_DOCKER` | Set when running inside Docker |
| `AI_MEMORY_NATIVE_TEST_BOX` | Test internal |
| `AI_MEMORY_NATIVE_TEST_IMAGE` | Test internal |
| `AI_MEMORY_NATIVE_TEST_KEEP_BOX` | Test internal |
| `AI_MEMORY_TEST_NO_PROCESS_GUARD` | Test internal |
| `AI_MEMORY_X__` | Internal |
| `RUST_LOG` | Standard tracing log level (e.g. `info`, `debug`) |

### Provider API Keys (non-AI_MEMORY_ prefix)

| Variable | Used For |
|----------|----------|
| `ANTHROPIC_API_KEY` | Anthropic LLM provider |
| `ANTHROPIC_OAUTH_TOKEN` / `CLAUDE_CODE_OAUTH_TOKEN` | Anthropic OAuth (Claude subscription) |
| `OPENAI_API_KEY` | OpenAI LLM or embedding provider |
| `GEMINI_API_KEY` / `GOOGLE_API_KEY` | Gemini LLM or embedding |
| `VOYAGE_API_KEY` | Voyage embedding |
| `LLM_API_KEY` | openai-compat generic, OpenRouter |
| `OPENCODE_API_KEY` | OpenCode Zen |
| `OPENROUTER_API_KEY` | OpenRouter (for evals) |
| `COPILOT_GITHUB_TOKEN` / `GH_TOKEN` / `GITHUB_TOKEN` | Copilot provider |
| `GITHUB_COPILOT_API_TOKEN` | Pre-minted Copilot API token |
| `COPILOT_API_URL` | Copilot API base URL override |

## Provider Tiers

From the README comparison table, these models have been A/B tested for consolidation:

| Model | Cost/run | Latency | Verdict |
|-------|----------|---------|---------|
| Claude Haiku 4.5 | ~$0.02 | 7s | **Default.** Best classification and restraint |
| GPT-5.4-mini | ~$0.005 | 4s | Cheaper, mild over-classification |
| qwen3:32b (Ollama) | $0 | 92s | Free if local server available |
| DeepSeek V4 Flash | ~$0.005 | 22s | Works, no edge over GPT-mini |
| Sonnet 4.5 | ~$0.06 | 11s | Displaced by Haiku |
| Kimi-K2.6 | n/a | hangs | Ineligible (reasoning model) |

## Deployment Patterns

### Native Binary (macOS, Apple Silicon)

Recommended for single-user laptop. Download release tarball:

```
mkdir -p ~/Applications/ai-memory && cd ~/Applications/ai-memory
curl -fsSL -O https://github.com/akitaonrails/ai-memory/releases/latest/download/ai-memory-macos-aarch64.tar.gz
tar -xzf ai-memory-macos-aarch64.tar.gz
./ai-memory init    # creates data dir at ~/Library/Application Support/ai-memory/
./ai-memory serve --transport http --bind 127.0.0.1:49374
```

### Docker (Linux server / homelab VM)

```
docker run -d --name ai-memory \
    --restart unless-stopped \
    -p 0.0.0.0:49374:49374 \
    -v ai-memory-data:/data \
    -e AI_MEMORY_AUTH_TOKEN="$(ai-memory generate-auth-token)" \
    -e AI_MEMORY_ALLOWED_HOSTS="<server-ip>,localhost,127.0.0.1" \
    -e AI_MEMORY_LLM_PROVIDER=anthropic \
    -e ANTHROPIC_API_KEY=sk-ant-... \
    akitaonrails/ai-memory:latest
```

### Key Config Rules for LAN/Homelab

- Non-loopback bind (`0.0.0.0:49374`) requires BOTH `AI_MEMORY_AUTH_TOKEN` and `AI_MEMORY_ALLOWED_HOSTS`
- `ALLOWED_HOSTS` is a host-header allowlist (DNS rebinding defence) — no wildcard `*` support, list all hostnames/IPs explicitly
- `/web` UI is read-only, mounted on same port as MCP, enabled with `--enable-web` or `AI_MEMORY_ENABLE_WEB`
- No systemd integration on macOS; use `screen`/`tmux` or a launchd plist

## Security

- Loopback-only (127.0.0.1) with no auth is safe for single-user laptop
- LAN exposure requires bearer auth: `AI_MEMORY_AUTH_TOKEN`
- Auth protects: `/mcp`, `/hook`, `/handoff`, `/admin/*`, `/web/*`
- Browser `/web` uses HTTP Basic auth with token as password
- Embed backend hashing: `ai-memory backup --to <tarball>` uses SQLite online backup API

## Docs Map (what to read in what order)

| File | What it covers |
|------|---------------|
| `README.md` | Overview, quick start, use cases, provider table |
| `docs/ARCHITECTURE.md` | Full architecture: data flow, storage tiers, crate layout, invariants |
| `docs/install.md` | All install paths (Docker, native, AUR, source) |
| `docs/deploy.md` | Production deployment (auth, HTTPS, Cloudflare Tunnel) |
| `docs/design-decisions.md` | Why each decision was made (with issue refs from prior art) |
| `docs/macos.md` | macOS-specific: native binary, source build, Docker wrapper |
| `docs/issues-agentmemory.md` | Full postmortem of agentmemory's structural problems |
| `docs/llm-provider-comparison.md` | A/B test results for consolidation models |
| `docs/marker-file.md` | `.ai-memory.toml` project marker configuration |
| `crates/ai-memory-store/src/` | SQLite schema, decay math, writer actor |
| `crates/ai-memory-llm/src/` | Provider trait + embedder trait implementation |

## Hermes Plugin

The community `ai-memory-hermes-plugin` (by MrLuciano) integrates ai-memory
as a Hermes MemoryProvider. Source: `/Users/roy/ai-memory/src/ai-memory-hermes-plugin/`

**Tools registered:** `ai_memory_search`, `ai_memory_write`, `ai_memory_status`

**Lifecycle mapping:**
- `prefetch(query)` -> `GET /admin/search?q=<query>` (sync)
- `sync_turn(user, assistant)` -> `POST /hook?event=user-prompt` (async daemon)
- `on_session_end(messages)` -> `POST /hook?event=session-end` (async daemon)
- `on_memory_write()` -> `POST /admin/write-page` (sync)

**Config** (`$HERMES_HOME/ai-memory.json`):
```json
{
  "server_url": "http://127.0.0.1:49374",
  "workspace": "hermes",
  "project": "hermes-default"
}
```

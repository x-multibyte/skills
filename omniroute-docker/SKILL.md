---
name: omniroute-docker
description: "Configure and reason about OmniRoute Docker Compose deployment (profiles, ports, .env, Redis, Qdrant/Bifrost, pull-only images). Use when inspecting or editing docker-compose.yml / docker-compose.prod.yml / Dockerfile / .env for OmniRoute, listing compose ports, or choosing base/web/cli/host. CLIProxyAPI: prefer embedded Dashboard service, not compose sidecar. Prefer live compose files over docs when they disagree."
---

# OmniRoute Docker Compose

Class-level skill for the OmniRoute repo Docker stack (local path often `~/docker/OmniRoute`).

## When to use

- User asks how OmniRoute is deployed with Docker / compose
- Changing ports, profiles, volumes, Redis, memory, bifrost
- CLIProxyAPI install/start/failure under Docker (embedded vs compose)
- Copying/editing `.env` for compose (never print secret values)
- Listing ports for a profile

## User format preferences (this user)

- **Port lists**: short list only — `port — service` or a tiny table. No essay, no optional digression unless they ask.
- **Practical stack ports**: answer the **real combined stack** they will run (app profile + always-on Redis + any real sidecar), not pedantic "profile alone only publishes N". Lead with the full host port table first.
- **Config-only mode**: "先别部署 / 要修改配置" → edit files only; never `compose up` / `run` / deploy until they reverse it.
- **Prefer pull, not build (this personal box)**: local `docker compose build` OOMs (builder heap ~4GB). Default path is **official image pull** (`diegosouzapw/omniroute:latest` / `:latest-web`). Never push `--build` unless they explicitly need `cli` or a custom image.
- **Long builds**: if build is unavoidable, do **not** run it inside the Hermes session (timeout). Hand local terminal / tmux / nohup; this session only does config + post-start checks.
- **Autonomous defaults**: pick reasonable ports/values and apply; don't ask "要不要改成 X" for low-stakes choices.
- Language: Chinese unless they switch.

## Source of truth (order)

1. Live files: `docker-compose.yml`, `docker-compose.prod.yml`, `Dockerfile`, `.env` / `.env.example`
2. **OmniRoute project itself** for feature design (embedded services, CLIProxyAPI, etc.): local tree + `gh search` / issues / PRs on `diegosouzapw/OmniRoute`. Do **not** start with third-party project docs when diagnosing OmniRoute behavior.
3. `docs/guides/DOCKER_GUIDE.md` — useful but can lag
4. `docs/architecture/cluster-decisions.md` / `docs/frameworks/EMBEDDED-SERVICES.md`

If guide ≠ yml, trust yml. If compose sidecar ≠ embedded design docs/code, trust **embedded** as the supported path.

## Compose files

| File | Role |
|------|------|
| `docker-compose.yml` | Dev/daily — profile-gated app + always-on Redis + optional sidecars |
| `docker-compose.prod.yml` | Isolated prod snapshot (different names/ports/volumes) |
| `Dockerfile` | Stages: `builder` → `runner-base` / `runner-web` / `runner-cli` |

## Profiles (`docker-compose.yml`)

| Profile | Service | Image (local compose after pull-only change) | Use |
|---------|---------|-----------------------------------------------|-----|
| `base` | `omniroute-base` | **pull** `diegosouzapw/omniroute:latest` (`OMNIROUTE_IMAGE`) | Minimal, no CLI / no Chromium — **default daily stack** |
| `web` | `omniroute-web` | **pull** `diegosouzapw/omniroute:latest-web` (`OMNIROUTE_WEB_IMAGE`) | gemini-web / claude-web / claude-turnstile |
| `cli` | `omniroute-cli` | **local build** `runner-cli` only (upstream does not publish) | Codex / Claude Code / Droid / OpenClaw in container — OOM-prone, avoid on this box |
| `host` | `omniroute-host` | same official image as `base` | Mount host CLIs (Linux-first) |
| `cliproxyapi-legacy` | `cliproxyapi` | `eceasy/cli-proxy-api` | **Do not use** — incomplete sidecar (see CLIProxyAPI section) |
| `memory` | `qdrant` | qdrant | Semantic memory opt-in |
| `bifrost` | `bifrost` | maximhq/bifrost | Tier-1 router opt-in |

Official publish (`docker-publish.yml`) ships **runner-base + runner-web** only (tags `latest` / `X.Y.Z` and `latest-web` / `X.Y.Z-web`). No public `cli` tag.

**Redis has no profile** — starts with any `compose up` that includes the project services.

## CLIProxyAPI — embedded, not compose sidecar

**Supported path (OmniRoute design, #902 / EMBEDDED-SERVICES.md):**

1. Run only: `docker compose --profile base up -d` (no cliproxy profile)
2. Dashboard → **Providers → Services → CLIProxyAPI** → Install → Start
3. OmniRoute writes `$DATA_DIR/services/cliproxy/config.yaml` and spawns the binary under `$DATA_DIR/bin/cliproxyapi`
4. Env for app→CPA: `CLIPROXYAPI_HOST=127.0.0.1`, `CLIPROXYAPI_PORT=8317` (embedded default)

**Compose sidecar is NOT the product path:**

- Profile kept only as `cliproxyapi-legacy` for reference
- Sidecar mounts auth-dir (`/root/.cli-proxy-api`) but **not** `/CLIProxyAPI/config.yaml`
- Result: `failed to load config: open /CLIProxyAPI/config.yaml: no such file or directory`
- Upstream compose image in yml was `ghcr.io/router-for-me/cliproxyapi:v6.9.7` — can be **manifest unknown**; swapping to `eceasy/cli-proxy-api` still needs a full config mount to boot
- Do **not** debug by reading CLIProxyAPI upstream docs first — search OmniRoute code/issues (`gh`, `processManager.ts`, `installers/cliproxy.ts`, #902, #6877)

When user hits the config.yaml error on the sidecar: stop/remove the container, drop the profile, point them at Dashboard embedded install.

App services share `x-common`: `env_file: .env`, `DATA_DIR=/app/data`, `./data:/app/data`, healthcheck `node healthcheck.mjs`, `stop_grace_period: 40s`.

## Default ports (host)

Compose defaults (override via `.env`):

| Port | Env | Service |
|------|-----|---------|
| 20128 | `PORT` / `DASHBOARD_PORT` | OmniRoute dashboard |
| 20129 | `API_PORT` | Optional split API |
| 20132 | `LIVE_WS_PORT` | Live WS |
| 6379 | `REDIS_PORT` | Redis host map → container 6379 |
| 8317 | `CLIPROXYAPI_PORT` | Embedded CLIProxyAPI default (not compose) |
| 6333 / 6334 | `QDRANT_PORT` / `QDRANT_GRPC_PORT` | Qdrant (memory profile) |
| 8080 | `BIFROST_PORT` | Bifrost (bifrost profile) |

Prod compose host defaults: dashboard **20130**, API **20131**, Live WS **20132**.

### Port-list answers

1. Prefer the **practical stack** the user will run. Daily default = `base` + Redis.
2. Always include Redis (no profile; it starts with the stack).
3. Keep the answer to a tiny table. No prose unless they ask why/how to change.

Example — local daily stack (`--profile base`, non-default map):

| Port | Service |
|------|---------|
| 30128 | Dashboard |
| 40129 | API |
| 50132 | Live WS |
| 60133 | Redis host map |

Embedded CLIProxyAPI (when started from Dashboard) uses **8317** inside/on the app host path — do not mix with the old sidecar map **18317**.

### Host-port strategy (this personal box)

- Keep OmniRoute Docker host ports **off** the repo defaults (20128/20129/20132/6379) so later local `npm run dev` / local Redis don't collide.
- Current local `.env` map: Dashboard **30128**, API **40129**, Live WS **50132**, Redis host **60133**.
- Redis is a **dedicated** OmniRoute container (do not share with other projects). Keep host publish (60133) so other tools can health-check; app still uses `REDIS_URL=redis://redis:6379` inside the compose network.
- Container-internal Redis stays 6379; only the host mapping moves.

## Env workflow

```bash
cp -n .env.example .env
# Required before first real boot: JWT_SECRET, API_KEY_SECRET, INITIAL_PASSWORD
```

Docker-relevant:

- Compose forces `DATA_DIR=/app/data` (must match volume).
- In compose network use `REDIS_URL=redis://redis:6379` (service name + **container** port).
- `REDIS_PORT` only changes **host** publish mapping.
- CLIProxyAPI (embedded): `CLIPROXYAPI_HOST=127.0.0.1`, `CLIPROXYAPI_PORT=8317`. `.env.example` may mention 5544 for other contexts — do not conflate with compose legacy 18317.
- App executor resolves CPA via settings `cliproxyapi_url` then env then `127.0.0.1:8317`.

Never dump `.env` secrets into chat. Prefer editing via targeted shell/python upserts when the secret-file read guard blocks `read_file`.

## Common commands (hand to user)

**Default (方案 A — pull only, no OOM, no CPA sidecar):**

```bash
cd ~/docker/OmniRoute   # or repo root

docker pull diegosouzapw/omniroute:latest
docker pull redis:7-alpine

# NEVER add --build for base/web/host on this box
# NEVER add --profile cliproxyapi (legacy/broken)
docker compose --profile base up -d

# Pin version if needed:
# OMNIROUTE_IMAGE=diegosouzapw/omniroute:3.8.48 docker compose --profile base up -d

# Post-start checks (local non-default ports):
curl -sS http://localhost:30128/api/monitoring/health
docker exec omniroute-redis redis-cli ping
```

**CLIProxyAPI after OmniRoute is up:** Dashboard → Providers → Services → CLIProxyAPI → Install / Start (embedded). Not compose.

**Only if local image build is unavoidable** (custom code / `cli` profile): run in user's terminal / tmux / nohup, not Hermes:

```bash
docker compose --profile cli build   # heavy; OOM-prone
docker compose --profile cli up -d
```

**GitHub Actions alternative** (when code must be built): fork workflow `.github/workflows/build-fork.yml` is a template; it is hard-gated to `kang-heewon/OmniRoute` + `ghcr.io/kang-heewon/omniroute` — rewrite repo/image to the user's fork before using. Upstream official images already cover personal deploy without Actions.

## Pitfalls

1. **Docs lag**: DOCKER_GUIDE may omit profiles / still document cliproxy sidecar — verify live yml + embedded docs.
2. **Redis always on**: dedicated sidecar, not shared across projects; scale off only if user insists (`--scale redis=0`); rate limit falls back to memory.
3. **CLIProxyAPI compose sidecar is broken by design gap**: no `config.yaml` mount → boot loop. Use Dashboard embedded service. Profile renamed `cliproxyapi-legacy`.
4. **Research direction**: OmniRoute feature bugs → search `diegosouzapw/OmniRoute` (code + `gh`) first, not third-party CLIProxyAPI docs.
5. **`.env.example` 5544 / legacy 18317 / embedded 8317**: different contexts — embedded default is **8317**.
6. **SQLite WAL**: honor 40s stop grace; no hard kill in runbooks.
7. **MITM stub in Docker**: `OMNIROUTE_MITM_STUB=1` in Dockerfile builder — expected.
8. **Config-only sessions**: user said don't deploy → no `up`/`build` unless they reverse that.
9. **Local build OOM**: Dockerfile builder defaults `OMNIROUTE_BUILD_MEMORY_MB=4096`. Prefer official pull; if forced, user's terminal only.
10. **Never `--build` for base/web/host after pull-only compose**: those services have no `build:` key.
11. **Hermes session ≠ long Docker build**: local terminal / tmux / nohup only.
12. **Verify compose/runtime with `docker compose config` + health curl**, not `npm test` (config-only / deploy ops).
13. **Open PR #6877**: embedded CPA config flag/preserve issues — still relevant if Dashboard start fails.

## Support files

- `references/compose-ports.md` — condensed port/profile map, image strategy, CPA embedded path
- `references/cliproxyapi-embedded.md` — why sidecar fails + embedded install path + OmniRoute sources

## Related

- Live compose header comments in `docker-compose.yml`
- `docs/guides/DOCKER_GUIDE.md`
- `docs/frameworks/EMBEDDED-SERVICES.md`
- `docs/architecture/cluster-decisions.md`
- Issue #902, PR #6877

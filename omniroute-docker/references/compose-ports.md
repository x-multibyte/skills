# OmniRoute Compose ports (condensed)

Source of truth: live `docker-compose.yml` / `docker-compose.prod.yml` in the OmniRoute repo. Re-check after upgrades.

## Image strategy (this personal box — 方案 A)

| Profile | Image source |
|---------|----------------|
| `base` / `host` | **Pull** `diegosouzapw/omniroute:latest` (override `OMNIROUTE_IMAGE`, e.g. `:3.8.48`) |
| `web` | **Pull** `diegosouzapw/omniroute:latest-web` (`OMNIROUTE_WEB_IMAGE`) |
| `cli` | Local **build** `runner-cli` only — upstream does **not** publish a cli tag; OOM-prone |
| Redis / Qdrant / Bifrost | Always pull |

Official CI (`docker-publish.yml`) publishes multi-arch **runner-base + runner-web** only. Local `compose build` of the full Next app needs ~4GB Node heap and regularly OOM on personal machines.

```bash
# Daily path — no --build, no cliproxy profile
docker pull diegosouzapw/omniroute:latest
docker compose --profile base up -d
```

## Profiles that publish ports (repo defaults)

| Profile | Host ports (defaults) |
|---------|------------------------|
| *(always)* Redis | `REDIS_PORT` → container 6379 |
| `base` / `web` / `cli` / `host` | 20128 dashboard, 20129 API, 20132 Live WS |
| `cliproxyapi-legacy` | **avoid** — incomplete sidecar |
| `memory` | 6333 HTTP, 6334 gRPC |
| `bifrost` | 8080 |

Redis has **no** profile — any compose up that starts the project brings Redis.

## Local overrides (this personal box)

Intentional non-defaults so Docker does not steal later local-dev ports:

| Host port | Env | Service |
|-----------|-----|---------|
| **30128** | `PORT` / `DASHBOARD_PORT` | Dashboard / main |
| **40129** | `API_PORT` | API |
| **50132** | `LIVE_WS_PORT` | Live WS |
| **60133** | `REDIS_PORT` | Redis host map → container 6379 |

- In-compose Redis URL: `REDIS_URL=redis://redis:6379`.
- Redis is **OmniRoute-only**. Host map kept for external health checks.
- Embedded CLIProxyAPI: `CLIPROXYAPI_HOST=127.0.0.1`, `CLIPROXYAPI_PORT=8317` (not the old sidecar 18317).

## Practical daily stack

```bash
docker compose --profile base up -d
```

Host ports (local map) — **4 total**:

1. 30128 — Dashboard
2. 40129 — API
3. 50132 — Live WS
4. 60133 — Redis

CLIProxyAPI is **not** a compose port in the daily path. Start via Dashboard → Providers → Services if needed (embedded, port 8317).

## CLIProxyAPI compose sidecar (do not use)

Symptom:

```text
failed to load config: failed to read config file: open /CLIProxyAPI/config.yaml: no such file or directory
```

Cause (OmniRoute compose gap): volume only mounts `cliproxyapi-data:/root/.cli-proxy-api` — no `config.yaml` at `/CLIProxyAPI/config.yaml`. Profile retained as `cliproxyapi-legacy` only.

Fix: remove sidecar; use embedded service. See `references/cliproxyapi-embedded.md`.

## prod compose (`docker-compose.prod.yml`)

| Host env | Default | Maps to container |
|----------|---------|-------------------|
| `PROD_DASHBOARD_PORT` | 20130 | dashboard 20128 |
| `PROD_API_PORT` | 20131 | API 20129 |
| `PROD_LIVE_WS_PORT` | 20132 | Live WS 20132 |
| Redis | no host publish in prod file | internal only |

## Build alternatives (when pull is not enough)

1. **Avoid** local build on this box (OOM).
2. **GitHub Actions**: `.github/workflows/build-fork.yml` is a fork template; rewrite hard-coded `kang-heewon/OmniRoute` + `ghcr.io/kang-heewon/omniroute` before use.
3. If forced local build: user's terminal only; optional `--build-arg OMNIROUTE_BUILD_MEMORY_MB=3072`.

## Answer template (user prefers short)

Daily ports:

```
| 端口 | 服务 |
|------|------|
| 30128 | Dashboard |
| 40129 | API |
| 50132 | Live WS |
| 60133 | Redis |
```

No prose unless they ask why / how to change.

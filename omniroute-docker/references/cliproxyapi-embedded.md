# CLIProxyAPI under OmniRoute (embedded path)

## Decision (this personal box)

**Do not run the compose `cliproxyapi` / `cliproxyapi-legacy` sidecar.**

Use OmniRoute's **embedded** service:

Dashboard → Providers → Services → CLIProxyAPI → Install → Start

## Why the compose sidecar fails

OmniRoute `docker-compose.yml` historically defined:

```yaml
cliproxyapi:
  image: ghcr.io/router-for-me/cliproxyapi:v6.9.7  # often manifest unknown
  volumes:
    - cliproxyapi-data:/root/.cli-proxy-api   # auth dir only
  environment:
    - PORT=...
    - HOST=0.0.0.0
```

Missing: host/bind mount for `/CLIProxyAPI/config.yaml`.

Runtime error from `eceasy/cli-proxy-api` / CLIProxyAPI binary:

```text
failed to load config: failed to read config file: open /CLIProxyAPI/config.yaml: no such file or directory
```

Official CLIProxyAPI compose mounts `./config.yaml:/CLIProxyAPI/config.yaml` + `./auths:/root/.cli-proxy-api`. OmniRoute's profile never did that fully. Local rename: `cliproxyapi-legacy`.

## Supported OmniRoute design

Sources (search these first — not third-party docs):

| Source | Role |
|--------|------|
| Issue #902 | Feature design: settings fallback + version manager + Docker coexistence notes |
| `docs/frameworks/EMBEDDED-SERVICES.md` | Supervised child process model |
| `src/lib/services/installers/cliproxy.ts` | Writes `$DATA_DIR/services/cliproxy/config.yaml`, spawn args |
| `src/lib/versionManager/processManager.ts` | Older process manager / config write |
| `open-sse/executors/cliproxyapi.ts` | App → CPA URL via settings / `CLIPROXYAPI_HOST` / `CLIPROXYAPI_PORT` (default 8317) |
| `/api/services/cliproxy/*` | LOCAL_ONLY lifecycle API |
| PR #6877 | Open: embedded config flag/preserve (`--config` vs `-c`) |

Binary / config layout:

- Binary: `$DATA_DIR/bin/cliproxyapi` (symlink to versioned dir)
- Config: `$DATA_DIR/services/cliproxy/config.yaml` (auto-written on start)
- Auth dir default: `~/.cli-proxy-api` or `CLIPROXYAPI_CONFIG_DIR`

## Env for Docker OmniRoute → embedded CPA

```env
CLIPROXYAPI_HOST=127.0.0.1
CLIPROXYAPI_PORT=8317
```

Notes:

- Embedded default port is **8317**, not the old local sidecar map **18317**.
- Inside a container, loopback CPA only works if CPA runs **in the same network namespace** as the OmniRoute process (embedded child does). A separate compose service would need service DNS + shared network + working config — still not the supported path here.
- `.env.example` may show `5544` for other/local contexts — ignore for embedded default.

## Recovery checklist when sidecar is crash-looping

```bash
docker compose --profile base stop cliproxyapi 2>/dev/null || true
docker rm -f cliproxyapi 2>/dev/null || true
docker compose --profile base up -d
curl -sS http://localhost:30128/api/monitoring/health
# Then use Dashboard embedded Install/Start if CPA is needed
```

## Research rule

When OmniRoute + CLIProxyAPI misbehaves: **`gh` + local OmniRoute tree first**. User correction: do not start from router-for-me upstream docs when the failure is in OmniRoute's integration/compose.
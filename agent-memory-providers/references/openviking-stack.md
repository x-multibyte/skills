# OpenViking Stack Specification & Operations

## Configuration Schema (`ov.conf`)

Default host location: `~/.openviking/ov.conf` (mapped to `/app/.openviking/ov.conf` in Docker).

```json
{
  "storage": {
    "workspace": "/app/.openviking/data"
  },
  "embedding": {
    "dense": {
      "provider": "openai",
      "api_base": "http://host.docker.internal:1235/v1",
      "api_key": "mlx-local",
      "model": "mlx-community/Qwen3-Embedding-0.6B-4bit-DWQ",
      "dimension": 1024
    }
  },
  "vlm": {
    "provider": "openai",
    "api_base": "http://host.docker.internal:20128/v1",
    "api_key": "9router",
    "model": "ag/gemini-3.6-flash-low"
  },
  "server": {
    "host": "0.0.0.0",
    "port": 1933,
    "auth_mode": "api_key",
    "root_api_key": "<CLUSTER_ROOT_KEY>"
  }
}
```

## Client Configuration (`ovcli.conf`)

Default host location: `~/.openviking/ovcli.conf` (chmod 0600).

```json
{
  "url": "http://127.0.0.1:1933",
  "api_key": "<TENANT_USER_KEY>"
}
```

## REST API Key Endpoints

- Health Check: `GET /health` (Expected response: `{"status":"ok","healthy":true,"version":"...","auth_mode":"api_key"}`)
- System Status: `GET /api/v1/system/status`
- List Users in Account: `GET /api/v1/admin/accounts/{account_id}/users` (Requires Root Key)
- Register User: `POST /api/v1/admin/accounts/{account_id}/users` (Requires Root Key)
- Submit Message: `POST /api/v1/sessions/{session_id}/messages` (Requires User Key)
- Commit Session: `POST /api/v1/sessions/{session_id}/commit` (Requires User Key)
- Semantic Search: `POST /api/v1/search/search` or `POST /api/v1/search/recall` (Requires User Key)
- Hierarchical Read: `POST /api/v1/content/read` or `POST /api/v1/content/overview` (Requires User Key)

## Docker Deployment Verification (SOP Path C)

When running containerized instances (e.g. `openviking-macos`):
```bash
# Verify container liveness & port binding
docker ps --filter "name=openviking" --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'

# Probe health endpoint
curl -s http://127.0.0.1:1933/health

# Inspect active container configuration & generated client token
docker exec openviking-macos cat /app/.openviking/ov.conf
docker exec openviking-macos cat /app/.openviking/ovcli.conf
```

## Web Studio

OpenViking packages an interactive web visualizer for knowledge trees, memories, and audit logs:
- URL: `http://localhost:1933/studio`

## 9Router Unified Upstream Pattern

When routing both Embedding and VLM through a local 9Router gateway on the host:
- Set `api_base` to `http://host.docker.internal:20128/v1` in both `embedding.dense` and `vlm` sections.
- Verify embedding dimensions before configuring `ov.conf`:
  ```bash
  curl -s -X POST http://localhost:20128/v1/embeddings \
    -H "Content-Type: application/json" \
    -d '{"model":"<MODEL_NAME>","input":"probe"}' | jq '.data[0].embedding | length'
  ```
- If the new model dimension differs from the old index, stop the container, rename/backup `~/.openviking/data/vectordb`, update `ov.conf`, and restart.

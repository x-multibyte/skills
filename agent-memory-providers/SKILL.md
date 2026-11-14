---
name: agent-memory-providers
description: "Use when deploying or configuring AI agent memory backends."
version: 1.0.0
platforms: [linux, macos]
metadata:
  category: devops
  tags: [memory, openviking, mem0, agent, context-database, vector-search]
---

# Agent Memory Providers

Procedures and operational rules for deploying, configuring, and maintaining persistent memory backends (such as OpenViking, Mem0, and Honcho) for AI agents.

## Architectural Principles

1. **Dual-plane Security Separation**:
   - Administrative APIs (account creation, key issuance, ACLs) require root credentials.
   - Data plane operations (session tracking, memory extraction, vector search, hierarchical reads) strictly require tenant user tokens.
2. **Decoupled Extraction Pipeline**:
   - Modern context databases ingest chat turns synchronously but extract structured entities and events asynchronously via LLM workers.
3. **Local Embedding Dimensionality Alignment**:
   - The vector storage index dimension must match the dense embedding model dimensions exactly (e.g. Qwen3-Embedding-0.6B outputs 1024 dimensions).

## Deployment & Configuration Workflow

### Step 1: Upstream Model & Storage Wiring

When deploying containerized context stores (e.g. OpenViking in Docker):
- Bind mounts must target persistent host directories (e.g. `~/.openviking:/app/.openviking`).
- Endpoints on the host machine must be referenced via `http://host.docker.internal:<port>` rather than `localhost`.
- Audit embedding model dimensions before initializing vector collections.

### Step 2: Tenant User Key Provisioning

Never configure agent runtimes with root management keys:
1. Initialize the cluster with a root key.
2. Call the administrative endpoint to register the tenant account and issue a dedicated User Key:
   ```bash
   curl -s -X POST \
     -H "Authorization: Bearer <ROOT_API_KEY>" \
     -H "Content-Type: application/json" \
     -d '{"user_id": "default", "role": "admin"}' \
     http://127.0.0.1:<PORT>/api/v1/admin/accounts/default/users
   ```
3. Store client connection profiles with restricted permissions (`chmod 0600`).

### Step 3: Hermes Agent Integration

- **Security Gate Compliance**: Never write directly to `~/.hermes/config.yaml`. The agent core blocks raw modifications to security-sensitive configurations. Always use the CLI setter:
  ```bash
  hermes config set memory.provider <provider_name>
  ```
- **Secret Isolation**: Store endpoints and API keys in `~/.hermes/.env`. Keep settings in `config.yaml`.
- **Clean Fallback on Switch**: When evaluating a new provider, disable previous credentials via comment tags instead of deleting them. This preserves legacy configuration for instant rollback.
- **Environment Reload**: In scripts and subshells, `load_env()` parses key-values into a dict; execute `reload_env()` to export them into `os.environ`.

## Verification & Health Check Runbook

Always verify end-to-end functionality across four distinct operational phases:

1. **Service Liveness & Status**:
   - Verify HTTP 200 on `/health` and status endpoints.
   - Confirm active provider registration via `hermes memory status`.
2. **Session Submission (`remember`)**:
   - Submit a test fact payload. Ensure HTTP 200/202 with an assigned `task_id` and `session_uri`.
3. **Semantic Retrieval (`search`)**:
   - Execute a vector query. Verify return codes, similarity scores, and URI structures.
4. **Hierarchical Content Read (`read`)**:
   - Read extracted L0 (abstract), L1 (overview), or L2 (full) context nodes.

## Operational Pitfalls

| Symptom / Error | Root Cause | Preventive Rule |
| :--- | :--- | :--- |
| `PERMISSION_DENIED: ROOT API keys cannot access tenant-scoped data APIs` | Root key passed to data plane endpoints | Always issue and pass a tenant user key for session and memory operations. |
| Vector search returns empty or dimension errors | Embedding model output dimension mismatch with index definition | Explicitly define `dimension` in the dense model configuration matching the served model. |
| Hermes provider changes do not take effect | Edited `config.yaml` manually or `.env` not reloaded | Apply config changes via `hermes config set` and invoke `reload_env()` in sub-processes. |
| Container cannot reach local LM Studio / 9Router | Used `127.0.0.1` inside container config | Use `host.docker.internal` for cross-network loopback communication into macOS/Linux host services. |
| Hermes logs `openviking-server was not found on PATH` | OpenViking runs in Docker container rather than native host binary | Hermes cannot auto-start containerized servers; ensure container has restart policy (`restart: unless-stopped`) or is running before agent launch. |
| Single dense embedding model constraint | `ov.conf` schema accepts only a single model under `embedding.dense` | Do not pass fallback lists in `ov.conf`; select one primary model verified against the upstream provider. |
| Upstream embedding rejects `base64` encoding | OpenViking internally sends `encoding_format: "base64"` to OpenAI-compatible endpoints; models rejecting base64 (e.g. `openrouter/nvidia/*` returning HTTP 400) will break search and ingestion | Select upstream models supporting `base64` embeddings (e.g. `openrouter/liquid/*`, `openrouter/openai/*`, or local MLX/vLLM) when proxying through gateways. |
| Vector dimension/space mismatch after switching model | Switching embedding models invalidates existing vector embeddings | Backup and clear `~/.openviking/data/vectordb/` before restarting server with new model/dimensions; text data in `viking/` is preserved. |

## References

- `references/openviking-stack.md` - OpenViking REST API contracts, configuration schemas, and diagnostic commands.

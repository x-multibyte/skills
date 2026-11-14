---
name: lightrag-deployment
description: "Deploy/run LightRAG: audit .env storage config first."
---

# LightRAG Local Deployment

Deploying and running the LightRAG RAG framework on a single machine (macOS dev box or Linux). Covers the decision of *which* stack to run, uv-based venv setup, and server lifecycle.

## Golden rule: audit `.env` BEFORE choosing a deployment path

The repo ships many deployment docs (AppleContainerSetup.md, DockerDeployment.md, InteractiveSetup.md) that assume production DB backends. The user's actual `.env` decides what is needed. Read these keys first:

- `LIGHTRAG_KV_STORAGE`, `LIGHTRAG_GRAPH_STORAGE`, `LIGHTRAG_VECTOR_STORAGE`, `LIGHTRAG_DOC_STATUS_STORAGE`
- `LLM_BINDING*`, `EMBEDDING_BINDING*`, `RERANK_BINDING`

If storages are `JsonKVStorage` / `NetworkXStorage` / `NanoVectorDBStorage` (file-based defaults), **zero database containers are required** — the whole Postgres/Neo4j/Milvus stack is dead weight. Run the server directly (uv) or as a single container. Do not steer the user toward the Apple-container or full-compose stack without checking this first.

## Deployment paths (in increasing complexity)

| Path | When | Effort |
|---|---|---|
| A. Local uv venv (`uv sync --extra api` + `lightrag-server`) | File storage; want plain process management | Lowest |
| B. Single container (repo `docker-compose.yml`) | File storage; want isolation/restart policy; docker runtime already present | Lowest |
| C. Apple `container` full stack (`scripts/setup/apple-container.sh`) | Need production Postgres/Neo4j/Milvus; NO Docker/OrbStack available | Highest |
| D. Interactive setup (`make env-base`) → `docker-compose.final.yml` | Full GPU stack (vLLM embed/rerank); NVIDIA hosts only | High, GPU-only |

Key facts:
- `docker-compose-full.yml` is NVIDIA GPU-targeted (vLLM services with `runtime: nvidia`) — cannot run on Apple Silicon. Do not recommend it there.
- Apple `container` (macOS 26+) has no Compose, no healthcheck, no service DNS; `apple-container.sh` reimplements all of it with IP wiring. Requires bash 4+ (`brew install bash`) and the `container` CLI. Only worth it when no Docker-compatible runtime exists.
- If the user already has OrbStack/Docker Desktop, path C is pure self-inflicted pain.

## Quickstart (path A)

```bash
cd <repo-root>
uv sync --extra api          # PITFALL: plain `uv sync` omits fastapi → lightrag-server crashes
.venv/bin/lightrag-server --host 127.0.0.1 --port 9621
```

Verify: `http://127.0.0.1:9621/health`, WebUI at `/webui`. `./data/` (rag_storage, inputs) auto-created on first run. Storage config lives in `.env`; LLM/embedding endpoints are set by `LLM_BINDING_HOST` / `EMBEDDING_BINDING_HOST` — see the local wiring section below for the 9Router + LM Studio pattern.

## WebUI build (frontend) — MUST restart the server afterward

The repo ships the WebUI as a separate Bun project (`lightrag_webui/`). A fresh clone has no built assets: `GET /health` shows `webui_available: false` and `GET /webui` 404s (or the log says `WebUI assets not available`). Build:

```bash
cd lightrag_webui
bun install --frozen-lockfile
bun run build        # outputs into ../lightrag/api/webui/assets/
```

Critical: the server detects/mounts the assets at **startup**, not at request time. After building, **restart `lightrag-server`** or the WebUI route stays unmounted. Verify after restart: `GET /health` → `webui_available: true`, and `GET /webui` returns the app (browser render of Documents/Knowledge Graph/Retrieval/API tabs confirms it). Note: `bun run dev`'s Vite long-polling can make browser `networkidle` time out — use DOM-content-loaded + selector waits.

## Multi-version / multi-project document sets — use workspace isolation

LightRAG has **no version or document-set concept**: everything you ingest into one instance collapses into a *shared* knowledge graph, so same-named entities from different versions collide. For versioned docs (e.g. Laravel 5.0→13.x), do **one `workspace` per major version or per project** — never one pool for all.

- **Workspace is a SERVER STARTUP parameter, not per-request.** `--workspace` fixes the instance; query routes (`/query`, graph routes) do NOT read any per-request workspace — only `/health`/status honors the `LIGHTRAG-WORKSPACE` header, and the WebUI never sends it. One server process = one workspace. Data is partitioned per-storage-type (file subdirs, prefix, workspace column, Qdrant payload) under the shared `working_dir`.
- **Bulk import via a library script, not HTTP**: with many workspaces, don't start/stop the server 9 times. Use a Python script that instantiates `LightRAG(working_dir=..., workspace=..., ...)` once per workspace and calls `ainsert(texts, file_paths=...)`, then `finalize_storages()`. See `references/versioned-docs-ingestion.md` for the working pattern and the two script pitfalls that cost a session (embedding double-wrap, LLM timeout).
- Cross-version answer correctness: a `Route` node with 8 conflicting relations is worse than no answer. Ask the user how fine-grained to split (every sub-version vs. per-major) — tighter split = higher precision, more storage + ingestion time. Ingest is LLM-bound: ~hundreds of md files per version → hour-scale batches, run serially and spot-check graph node/edge counts and a sample query per workspace.

## Pitfalls

- **`uv sync` without `--extra api`**: `lightrag-server` fails with `ModuleNotFoundError: No module named 'fastapi'`. The API extra is mandatory for the server entry point (AGENTS.md states this).
- **Choosing a stack from the docs, not from `.env`**: AppleContainerSetup.md pushes a 6-container stack; with file storage it is 16G+ of VM memory for nothing.
- **Directory relocation while processes run**: moving a live repo — check `lsof +D <dir>` for open handles first; on the same filesystem `mv` is an atomic rename and inode-preserving, so processes whose cwd points into the dir keep working. Verify `git status` + `.env` after the move.
- **Switching embedding models**: clear the working dir (keep `kv_store_llm_response_cache.json` to preserve LLM cache) — old vectors do not match the new model space (AGENTS.md).
- **`POST /documents/text` without `file_source`**: 422 `{"detail":"A valid file_source is required for text insertion"}` — the new API requires `file_source` on text inserts.
- **Querying before the doc is `processed`**: insert is async; the pipeline (chunk → embed → LLM extract → graph) runs in background. Poll `GET /documents` until `status: processed` and `error_msg: null`.
- **EmbeddingFunc double/triple wrap in custom scripts**: `lightrag.llm.openai.openai_embed` is ALREADY an `EmbeddingFunc` instance at module level (1536d default). Do NOT `@wrap_embedding_func_with_attrs` a wrapper that calls it, and do NOT wrap the result in `EmbeddingFunc(func=...)` again — the unwrap chain mangles `embedding_dim`/`max_token_size` and yields `Vector count mismatch: expected 21 vectors but got 14 vectors`. Correct pattern (mirrors `create_optimized_embedding_function`): define `async def f(texts, **kw): return await openai_embed.func(texts=texts, base_url=..., api_key=..., embedding_dim=1024, **kw)`, then ONE `EmbeddingFunc(embedding_dim=1024, max_token_size=8192, func=f)`.
- **Script-based imports need explicit `default_llm_timeout`**: without it LightRAG uses `DEFAULT_LLM_TIMEOUT=240` and the worker timeout is `llm_timeout * 2` = 480s — free/slow gateways (9Router) queueing under concurrency blow past it (`extract LLM func: Worker execution timeout after 480s`). Pass `default_llm_timeout=600` and drop `llm_model_max_async` (e.g. 2) when ingesting many files.
- **`get_env_value` lives in `lightrag.utils`, not `lightrag.api.config`**, and `default` is a required positional arg — importing from the wrong module or calling with one arg throws at runtime.
- **`tests/llm/` collection errors about `qdrant_client`**: pre-existing env gap (missing `--extra offline-storage`), unrelated to `.env` wiring. For regression evidence use offline subsets (`tests/chunker/`, env-parsing tests, `tests/api/config/`) — these pass without external services.

## .env wiring for LOCAL inference (private, no cloud keys)

Both LLM and embedding use the `openai` binding with a custom `*_HOST` (OpenAI-compatible endpoints; **placeholder API keys work** — neither 9Router nor LM Studio validates):

```
LLM_BINDING=openai
LLM_BINDING_HOST=http://localhost:20128/v1        # 9Router gateway
LLM_BINDING_API_KEY=local-9router
LLM_MODEL=opencode-zen/deepseek-v4-flash-free

EMBEDDING_BINDING=openai
EMBEDDING_BINDING_HOST=http://localhost:1234/v1   # LM Studio
EMBEDDING_BINDING_API_KEY=local-lmstudio
EMBEDDING_MODEL=text-embedding-qwen3-embedding-0.6b@f16
EMBEDDING_DIM=1024                                 # MUST equal the model's output dims
```

- `EMBEDDING_DIM` must match the serving model's dims (qwen3-embedding-0.6b = 1024); mismatch fails silently in vector stores.
- LM Studio embedding model key must be exactly as `lms ls` shows it (EMBEDDING category).
- LLM via 9Router: pick a model id from `GET http://localhost:20128/v1/models` (e.g. `opencode-zen/deepseek-v4-flash-free`); no API key needed.

## End-to-end verification (insert → query)

1. `GET /health` — confirm `llm_binding_host`, `embedding_binding_host`, `embedding_model`, `webui_available`, storage types.
2. `POST /documents/text` — **`file_source` is REQUIRED** in the new API: `{"file_source":"intro.txt","text":"..."}` → `{"status":"success","track_id":...}`.
3. Insert is **async** — poll `GET /documents` until the doc shows `status: processed` and `error_msg: null` before querying.
4. `POST /query` `{"query":"...","mode":"hybrid"}` → answer in the `response` field.

## This machine's environment (audited 2026-08)

- Repo: `/Users/roy/LightRAG` (moved from `/Users/roy/docker/LightRAG`), branch `main`, git clean
- `.env` (rewired 2026-08-02): LLM → 9Router `opencode-zen/deepseek-v4-flash-free` @ `http://localhost:20128/v1`; embedding → LM Studio `text-embedding-qwen3-embedding-0.6b@f16` @ `http://localhost:1234/v1` (1024d); file storages; `RERANK_BINDING=null`. No cloud keys.
- Host: macOS 26.6, Apple Silicon, 24GB RAM; OrbStack 2.2.1 is the docker runtime (context `orbstack`, runs dev redis/memcached); no container CLI, system bash 3.2
- venv: `.venv` (Python 3.11.15 via uv) with api + test extras installed; server runs at 127.0.0.1:9621
- LM Studio serves `text-embedding-qwen3-embedding-0.6b@f16` (EMBEDDING category, 1024d) on 1234; 9Router on 20128

## References

- `references/deployment-paths.md` — full path-by-path analysis, docs surveyed, session audit notes
- `references/local-backend-wiring.md` — probe commands and exact API request/response shapes
- `references/versioned-docs-ingestion.md` — multi-workspace library-script ingestion pattern (Laravel 5.x–13.x case): workspace split logic, md merge-with-banners, embedding wrap fix, timeout settings

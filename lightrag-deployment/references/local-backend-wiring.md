# Local backend wiring — probe commands & API shapes

Session detail from the 2026-08-02 local-only setup (9Router LLM + LM Studio embedding, zero containers).

## Environment probes (run before wiring .env)

```bash
# LM Studio: is the server up, which models are loaded, does /v1/embeddings work?
lms status                      # Server: ON (port: 1234) + loaded models
lms ls                          # model keys (LLM vs EMBEDDING categories)
curl -s http://localhost:1234/v1/embeddings -H "Content-Type: application/json" \
  -d '{"model":"text-embedding-qwen3-embedding-0.6b@f16","input":"test"}' \
  | python3 -c "import sys,json; v=json.load(sys.stdin)['data'][0]['embedding']; print(len(v))"  # → 1024

# 9Router: model list + chat smoke test (placeholder key OK)
curl -s http://localhost:20128/v1/models | python3 -m json.tool | grep '"id"' | head -5
curl -s http://localhost:20128/v1/chat/completions -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-placeholder" \
  -d '{"model":"opencode-zen/deepseek-v4-flash-free","messages":[{"role":"user","content":"reply OK"}],"max_tokens":10}'
```

Both endpoints are OpenAI-compatible → `.env` uses `LLM_BINDING=openai` / `EMBEDDING_BINDING=openai` with custom `*_HOST`. Neither endpoint validates API keys; placeholders suffice.

## .env block (final values)

```
LLM_BINDING=openai
LLM_BINDING_HOST=http://localhost:20128/v1
LLM_BINDING_API_KEY=local-9router
LLM_MODEL=opencode-zen/deepseek-v4-flash-free

EMBEDDING_BINDING=openai
EMBEDDING_BINDING_HOST=http://localhost:1234/v1
EMBEDDING_BINDING_API_KEY=local-lmstudio
EMBEDDING_MODEL=text-embedding-qwen3-embedding-0.6b@f16
EMBEDDING_DIM=1024
```

## API request/response shapes (verified)

Health — `GET /health` returns config echo; key fields: `llm_binding_host`, `llm_model`, `embedding_binding_host`, `embedding_model`, `webui_available` (false until `lightrag_webui/dist` built), `kv_storage` / `doc_status_storage` / `graph_storage` / `vector_storage`, `enable_rerank`.

Insert — `POST /documents/text`:
```json
{"file_source":"intro.txt","text":"..."}
```
→ `{"status":"success","message":"Text successfully received. Processing will continue in background.","track_id":"insert_20260802_100201_0956f8b2"}`
Missing `file_source` → 422 `{"detail":"A valid file_source is required for text insertion"}`.

Status — `GET /documents` → `{"statuses":{"processed":[{"id":"doc-...","status":"processed","chunks_count":1,"error_msg":null,...}]}}`. First insert on a fresh store takes ~30-45s (chunk → embed → LLM extract → graph merge).

Query — `POST /query` `{"query":"...","mode":"hybrid"}` → answer text in the `response` field.

Storage layout (file storages): `rag_storage/` gets `kv_store_*.json`, `graph_chunk_entity_relation.graphml`, `vdb_*.json` (NanoVectorDB).

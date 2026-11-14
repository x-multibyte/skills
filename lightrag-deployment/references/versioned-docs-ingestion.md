# Versioned docs ingestion into LightRAG (Laravel 5.x–13.x case)

Session-proven pattern for ingesting a multi-version doc set with workspace isolation, via a library script (not the HTTP API). Machine state as of 2026-08: repo `/Users/roy/LightRAG`, `.env` fully local (9Router LLM + LM Studio embedding), `rag_storage/` at repo root.

## Workspace split decision

- LightRAG has no version concept: one instance = one shared graph. Same-named entities across versions collide.
- For Laravel docs the user's domain knowledge mattered: **5.0–5.4 stable, 5.5+ is a breaking watershed** (package auto-discovery etc.). So: one workspace per *break*, not per sub-version.
- Final split (9 workspaces): `laravel-5.x` (5.0–5.8 merged into one), then `laravel-6.x` … `laravel-13.x` each independent.

## Pre-merge: same-named md files across sub-versions

`/Users/roy/docs/laravel/<ver>/` holds one git-cloned docs branch per version. For 5.0–5.8 there are 90 unique md names, 45 present in all 9 versions. Merging strategy that preserves everything and stays traceable:

- Multi-version files: concatenate in version order (5.0→5.8), each section prefixed with a banner line (`> # Laravel 5.0 documentation section`) so the source sub-version is still findable in the merged text.
- Single-version files: copy verbatim (banner would be noise).
- Result: `5.x/` = 89 md, 8.7MB; all versions' routing.md content present with 9 banners.

## Import script pattern (`scripts/import_laravel_docs.py`)

One `LightRAG` instance per workspace, same `working_dir`, different `workspace=`:

```python
rag = LightRAG(
    working_dir=str(REPO / "rag_storage"),
    workspace=ws,                      # data isolation happens here
    llm_model_func=llm_func,
    llm_model_name=llm_model,
    llm_model_max_async=2,             # keep concurrency low for free gateway
    default_llm_timeout=600,           # else worker timeout = 240*2 = 480s
    embedding_func=embed_func,         # see embedding pattern below
    kv_storage="JsonKVStorage",
    doc_status_storage="JsonDocStatusStorage",
    graph_storage="NetworkXStorage",
    vector_storage="NanoVectorDBStorage",
    max_parallel_insert=3,
)
await rag.initialize_storages()
await rag.ainsert(texts, file_paths=paths)   # paths = md absolute paths
await rag.finalize_storages()
```

Debug flow that catches problems cheaply: `--version laravel-13.x --limit 1` on ONE file first, verify doc_status + graph artifacts, then scale to full versions.

## Embedding: the exact correct pattern (cost one failed run)

`lightrag.llm.openai.openai_embed` is already an `EmbeddingFunc` (module-level, 1536d default). The WRONG pattern — `@wrap_embedding_func_with_attrs` around a function calling `openai_embed(...)`, then wrapping the result in another `EmbeddingFunc(func=...)` — produced `Vector count mismatch: expected 21 vectors but got 14 vectors` (LM Studio itself returned 21/21 on direct calls, isolating the bug to the wrap chain).

The RIGHT pattern (mirrors server `create_optimized_embedding_function`):

```python
async def embedding_func(texts, **kwargs):
    return await openai_embed.func(
        texts=texts, model=emb_model, base_url=emb_base,
        api_key=emb_key, embedding_dim=emb_dim, **kwargs)

embed_func = EmbeddingFunc(embedding_dim=emb_dim, max_token_size=8192, func=embedding_func)
```

Verify standalone before running the pipeline: `await embed_func([...21 texts...])` must return shape (21, 1024).

## Env values consumed (from `.env`)

- `LLM_MODEL=opencode-zen/deepseek-v4-flash-free`, `LLM_BINDING_HOST=http://localhost:20128/v1`
- `EMBEDDING_MODEL=text-embedding-qwen3-embedding-0.6b@f16`, `EMBEDDING_BINDING_HOST=http://localhost:1234/v1`, `EMBEDDING_DIM=1024`
- Placeholder API keys work for both (neither validates).

## Regression evidence that works offline

`tests/chunker/` (256), env-parsing tests + `tests/api/config/` (152) = 408 passed without external backends. `tests/llm/` collection errors (qdrant_client missing) are env gaps, ignore for `.env`-wiring evidence.

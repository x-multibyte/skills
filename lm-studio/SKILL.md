---
name: lm-studio
description: "LM Studio local inference: download, load, serve, and test local LLMs."
version: 1.2.0
author: Hermes
license: MIT
dependencies: []
platforms: [macos, linux]
metadata:
  hermes:
    tags: [LM Studio, Local Inference, LLM, GGUF, llama.cpp, Multimodal]
---

# LM Studio — Local LLM Inference

## When to use

Use when you need to run local GGUF models on a Mac or Linux machine, serve them via OpenAI-compatible API, or test model capabilities without touching production infrastructure. Ideal for experimentation, offline inference, and fast prototyping.

## Prerequisites

- LM Studio desktop app installed (`/Applications/LM Studio.app` on macOS)
- `lms` CLI tool available in PATH
- HuggingFace model repo with GGUF files

## Quick start

### Download a model from HuggingFace

Use the full HuggingFace repo URL:

```bash
lms get "https://huggingface.co/username/model-name-GGUF"
```

This automatically resolves the best quantization for your system. For multimodal (vision) models, it also downloads the mmproj file.

### List downloaded models

```bash
lms ls
```

Note that model keys shown by `lms ls` use lowercase hyphenated names (e.g., `qwythos-9b-claude-mythos-5-1m`), which may differ from the HF repo name.

**Model types** — `lms ls` lists models in two sections:
- **LLM** — decoder-only models (GGUF `.gguf` or MLX `.safetensors`), can serve `/v1/chat/completions`
- **EMBEDDING** — dedicated embedding backends, can serve `/v1/embeddings`

A model listed under LLM will **not** work with `/v1/embeddings`, even if its name says "embedding".

### Load a model

```bash
lms load <model-key> --identifier <short-name> -c <context-length> --yes
```

**IMPORTANT: Context length** — Without `-c`, LM Studio tries to allocate KV cache for the model's native max (e.g. 1M tokens), exceeding system memory. Always specify `-c` explicitly.

Memory depends on architecture (GQA vs MHA, KV head count). Tested on Mac M2 24GB with Qwythos-9B Q4_K_M (Qwen3.5 arch, 32 layers, 4 KV heads):

| Context | Result |
|---------|--------|
| 128K    | works (6.1 GiB) |
| 256K    | works (6.1 GiB) |
| 512K    | estimate 26.69 GB |
| 1M      | estimate 46.47 GB |

Recommended safe max: **128K for 9B**. Scale down for larger or denser architectures.

```bash
lms load <model> --identifier my-model -c 131072 --yes
```

### Start the API server

```bash
lms server start --port 1234
```

### Test the model

```bash
lms chat <identifier> -p "Your prompt here"
```

The `-p` flag prints the response to stdout and exits (non-interactive).

### API authentication

By default, LM Studio does **not** require API tokens. If someone toggle "Require Authentication" in the GUI (Developer > Server Settings), the server enforces Bearer token auth and `lms server status` still reports "running" — the 401 only surfaces on actual API calls.

To disable auth without the GUI:

```bash
python3 -c "
import json
PATH = '$HOME/.cache/lm-studio/.internal/permissions-store.json'
with open(PATH) as f: d = json.load(f)
d['json']['tokenMode'] = 'disabled'
with open(PATH, 'w') as f: json.dump(d, f, indent=2)
"
lms server stop && lms server start --port 1234
```

See [references/api-auth.md](references/api-auth.md) for details on creating API tokens or bypassing auth.

## Common workflows

### Workflow 1: Download, load, and test a new model

```yaml
Steps:
  1. lms get "https://huggingface.co/<org>/<repo>"
  2. lms ls                  # note the local model key
  3. lms load <key> -c 8192 --identifier my-model --yes
  4. lms chat my-model -p "Hello"
  5. lms server start        # for API access
```

### Workflow 2: Serve via OpenAI-compatible API

Start the server, then use the OpenAI SDK or curl:

```bash
lms server start --port 1234
curl http://localhost:1234/v1/chat/completions \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "my-model",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

**API authentication** — By default, LM Studio **does not** require API tokens. If you previously enabled "Require Authentication" in the GUI, the server forces token-based auth. See [references/api-auth.md](references/api-auth.md) for how to create tokens or bypass auth without the GUI.

### Workflow 3: Tool calling (function calling)

Models with tool-use chat templates (e.g. Qwythos-9B, Qwen3.5) support OpenAI-compatible tool calling via the API:

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:1234/v1", api_key="")

tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Query current weather",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "City name"}},
            "required": ["city"]
        }
    }
}]

resp = client.chat.completions.create(
    model="my-model",
    messages=[{"role": "user", "content": "Beijing weather?"}],
    tools=tools
)
msg = resp.choices[0].message
print(msg.tool_calls)  # finish_reason == "tool_calls"
```

**Multi-step (chain) calling** — feed tool results back with `role: "tool"`:

```python
messages = [
    {"role": "user", "content": "Calculate (15+27)*3 then email it"},
    {"role": "assistant", "content": "", "tool_calls": [{
        "type": "function",
        "id": "call_1",
        "function": {"name": "calculate", "arguments": '{"expression":"(15+27)*3"}'}
    }]},
    {"role": "tool", "tool_call_id": "call_1", "content": "126"},
]
# Model will then call send_email(to="admin@test.com", body="...126...")
resp = client.chat.completions.create(
    model="my-model", messages=messages, tools=tools
)
```

**CoT / reasoning content** is returned separately in `reasoning_content`.

## Workflow 4: Multimodal (vision) models

For models that support image+text input:

```bash
# The mmproj file is auto-downloaded alongside the model
# LM Studio pairs it automatically when both files are in the same directory
lms load <model-key> -c 8192 --identifier my-vision-model --yes
```

### Workflow 5: Monitor inference logs

Monitor ongoing inference progress and server events without blocking:

```bash
# Server logs (timing, prompt processing %, slot management)
lms log stream --source server

# Model output only (generated tokens + stats)
lms log stream --source model --filter output --stats
```

The `--source server` stream is the most informative — it shows:
- **Prompt processing progress** — `n_tokens = 12288, progress = 0.45, t = 133.33 s / 92.16 tokens per second`
- **Slot lifecycle** — when tasks start/stop, slot reuse decisions
- **Cache behavior** — `cache reuse is not supported - ignoring n_cache_reuse`

**Interpreting progress resets**: If progress jumps back to 0.00%, it means the previous inference task completed and a new request began. Check for `stop processing: n_tokens = X, truncated = 0` in the server log to confirm completion. This is normal behavior, not a crash.

**Monitoring via background process** (useful in agent sessions):

```bash
# Start as background process
lms log stream --source server 2>&1

# Poll for accumulated output
# ... later ...
# process(action='poll', session_id='proc_xxx')
```

### Pitfall: Output filter hides server logs

`lms log stream --source model --filter output` only captures generated tokens (plain text). It does **not** show timing, token count, or progress percentage. Use `--source server` for those, or omit `--filter output` for a broader view.

### Pitfall: Progress resets to 0% mid-inference

A reset to 0.00% is not an error — it means the previous task finished (`stop processing`) and a new task queued. Check `lms ps` to confirm status is `PROCESSINGPROMPT` (not `IDLE`). If the status shows `IDLE`, the model finished and there is no pending request.

## Workflow 6: Embedding models

### Limitation: `/v1/embeddings` only works with native embedding backends

LM Studio has two model categories listed by `lms ls`:
- **LLM** — decoder-only models (GGUF/MLX), can generate text
- **EMBEDDING** — dedicated embedding backends (e.g. `text-embedding-nomic-embed-text-v1.5`)

The `/v1/embeddings` API endpoint **only works with models in the EMBEDDING category**. Models classified as LLM (even embedding-specialized ones like `qwen3-embedding-0.6b-dwq` in MLX format) will return `400: No models loaded`.

```json
{"error":"No models loaded. Please load a model in the developer page or use the 'lms load' command."}
```

**Check category** before attempting embeddings:

```bash
lms ls
```

### Workaround: Extract embeddings via LM Studio's bundled MLX Python

For MLX-formatted embedding models loaded as LLM, use the bundled MLX Python runtime directly:

```python
# Use LM Studio's bundled MLX Python:
#   /Users/roy/.cache/lm-studio/extensions/backends/vendor/_amphibian/app-mlx-generate-mac14-arm64@19/bin/python

import mlx.core as mx
from mlx_lm import load

model, tokenizer = load("<model-path>")

def get_embedding(text):
    tokens = tokenizer.encode(text)
    token_ids = mx.array([tokens])
    # model.model() returns hidden states (B, L, D) — the last-token hidden state IS the embedding
    hidden = model.model(token_ids)
    return hidden[0, -1, :]  # last token = embedding vector
```

**Key details:**
- `model.model(inputs)` (inner `Qwen3Model`) returns hidden states **after final RMSNorm** — this is the embedding, not the logits from `model(inputs)`
- Output is **not L2-normalized** — compute cosine similarity manually or normalize before comparing
- For Qwen3-Embedding-0.6B: hidden_size=1024, 28 layers

### Find the model file path on disk

```bash
find ~/.cache/lm-studio/models -name "*.safetensors" -o -name "*.gguf" 2>/dev/null | grep <model-key-part>
```

### Serving an external RAG app (LightRAG wiring)

A native EMBEDDING-category model is directly consumable by any OpenAI-compatible client — point the app's embedding base URL at the running server, use the `lms ls` model key, and set the app's embedding dim to the model's output dims (qwen3-embedding-0.6b = 1024). No wrapper needed. Concrete LightRAG `.env` wiring (embedding via LM Studio @ 1234):

```bash
EMBEDDING_BINDING=openai
EMBEDDING_BINDING_HOST=http://localhost:1234/v1
EMBEDDING_BINDING_API_KEY=local-lmstudio   # placeholder OK, LM Studio does not validate
EMBEDDING_MODEL=text-embedding-qwen3-embedding-0.6b@f16
EMBEDDING_DIM=1024
```

See the `lightrag-deployment` skill for the full wiring + end-to-end verification flow (LLM via 9Router @ 20128).

### Embedding server wrapper

For production use, wrap the MLX embedding model as a standalone OpenAI-compatible HTTP server. This avoids the LM Studio `/v1/embeddings` limitation entirely and can be registered as a 9Router `custom-embedding` provider.

The reference implementation at `/Users/roy/9router/embedding-server/server.py` exposes:

```
POST /v1/embeddings
{"model": "qwen3-embedding-0.6b-dwq", "input": "text"}
→ {"data": [{"embedding": [1024 floats], "index": 0}]}
```

**Key implementation pattern:**

```python
import mlx.core as mx
from http.server import HTTPServer, BaseHTTPRequestHandler
from mlx_lm import load

model, tokenizer = load(MODEL_PATH)

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # parse body, call model.model(token_ids) for hidden states
        # return OpenAI-compatible JSON response

HTTPServer(('127.0.0.1', 1235), Handler).serve_forever()
```

**Persistence (macOS):** Use launchd plist at `~/Library/LaunchAgents/com.9router.qwen3-embedding.plist`:

```bash
launchctl load ~/Library/LaunchAgents/com.9router.qwen3-embedding.plist
```

**Integration with 9Router:** Register as custom-embedding provider, then use model name `lmstudio-embedding/qwen3-embedding-0.6b-dwq` through 9Router's unified `/v1/embeddings`.

### Embedding quality reference

See [references/embedding-extraction.md](references/embedding-extraction.md) for tested embedding quality metrics, architecture details, and a reproducible extraction script.

## Common pitfalls

### Bundled MLX Python path invalidation after LM Studio updates

LM Studio extension backends use version-suffixed directories (e.g., `app-mlx-generate-mac14-arm64@<version>`). Hardcoding the path in LaunchAgents plists or scripts will break on LM Studio updates (causing launchd error 78 / `No such file or directory`).
Always resolve the active Python path dynamically or link to a stable location:

```bash
MLX_PYTHON=$(ls -d ~/.cache/lm-studio/extensions/backends/vendor/_amphibian/app-mlx-generate-mac14-arm64@*/bin/python 2>/dev/null | sort -V | tail -n 1)
```

### Docker containers accessing host inference endpoints

When applications consuming LM Studio or local MLX embedding servers run inside Docker, `localhost:<port>` refers to the container namespace. Use `http://host.docker.internal:<port>/v1` in container environment or config files.

### API key is "malformed"

The key in `~/.cache/lm-studio/.internal/lms-key-2` is an **internal CLI communication key**, not a user-facing API token. To use the OpenAI-compatible API, create a proper token via: LM Studio app → Developer → Server Settings → Manage Tokens.

### Model name mismatch between lms ls and lms get

`lms ls` shows sanitized lowercase names (e.g., `qwythos-9b-claude-mythos-5-1m`). Use that key for `lms load`, not the HuggingFace repo name.

### Server restart unloads models

Restarting `lms server stop/start` **does not preserve loaded models** — you must `lms load` again after the server starts. The API will return `400: No models loaded` even when `lms ps` shows the model as loaded before the restart.

Load order matters: load the model **after** the server is running, or if loading before server start, reload after server start.

```bash
lms server start --port 1234
lms load <model-key> -c <context-length> --identifier <name> --yes
```

### Insufficient memory on load

If loading fails with "insufficient system resources", reduce context length:

```bash
lms load <model> -c 4096 --yes
```

The default context length may be the model's native maximum (e.g., 1M+ tokens), which creates an impractically large KV cache.

## Resource: Model storage

All downloaded models and mmproj files live under:

```
~/.cache/lm-studio/models/<org>/<repo>/
```

You can inspect and manage files there directly.

# Context Length & Memory

## The problem

Without `-c`, LM Studio defaults to the model's **native maximum context** (e.g. 1,048,576 for Qwythos-9B). The KV cache allocation for 1M tokens exceeds most consumer machines, failing with:

```
Error: Model loading was stopped due to insufficient system resources.
Under the current settings, this model requires approximately 46.47 GB...
```

## Architecture-aware estimation

KV cache size depends heavily on the model architecture:

| Architecture | Typical 9B KV heads | KV cache per token |
|-------------|-------------------|-------------------|
| Qwen3.5 / Qwen2.5 | 4 (GQA) | ~4 KB |
| Llama 3.x | 8 (GQA) | ~8 KB |
| Gemma 2 | 8 (GQA) | ~8 KB |
| Mistral / Mixtral | 8 (GQA) | ~8 KB |
| Older MHA models | 32+ (MHA) | ~16+ KB |

**Tested on Mac M2 24GB — Qwythos-9B Q4_K_M (Qwen3.5, 4 KV heads, 32 layers):**

| Context | Memory | Status |
|---------|--------|--------|
| 8K      | 6.1 GiB | loaded instantly |
| 128K    | 6.1 GiB | loaded (KV cache lazy-allocated) |
| 256K    | 6.1 GiB | loaded |
| 512K    | 26.69 GB estimated | blocked by guardrails |
| 1M      | 46.47 GB estimated | blocked by guardrails |

Key insight: LM Studio uses **lazy KV cache allocation** — the model loads at the same RAM regardless of `-c` value, and physical memory only goes up as the actual conversation fills context. The guardrails check is a worst-case estimate, not actual allocation.

## Safe defaults

| Model + Quant | Recommended max -c |
|--------------|-------------------|
| 7-9B Q4 (GQA, few KV heads) | 128K-256K |
| 7-9B Q4 (MHA / many KV heads) | 32K-64K |
| 13B Q4 | 32K-64K |
| 27B Q4 | 16K-32K |
| 70B Q4 | 4K-8K (if it fits at all) |

## Disabling guardrails

If the guardrail estimate is too conservative (it often is for GQA models):

```json
// ~/.cache/lm-studio/settings.json
"modelLoadingGuardrails": false
```

Then reload. The model will attempt to load even if the estimate exceeds RAM — use `memory_pressure` or Activity Monitor to watch real usage.

## Checking usage

```bash
# LM Studio
lms ps

# macOS
memory_pressure | head -3
```

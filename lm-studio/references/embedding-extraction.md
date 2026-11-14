# Embedding Extraction from MLX Models

## Problem

LM Studio's `/v1/embeddings` only works with native embedding backends (listed under "EMBEDDING" in `lms ls`). MLX-format embedding models like `qwen3-embedding-0.6b-dwq` are classified as "LLM" and rejected with `400: No models loaded`.

## Solution

Use LM Studio's bundled MLX Python to load the model and extract hidden states directly.

### Find the bundled MLX Python

```bash
find ~/.cache/lm-studio/extensions -name "python" -path "*/bin/*" | grep mlx
```

Typical path (version hash changes with LM Studio updates):
```
~/.cache/lm-studio/extensions/backends/vendor/_amphibian/app-mlx-generate-mac14-arm64@19/bin/python
```

### Embedding extraction code

```python
import mlx.core as mx
from mlx_lm import load

model_path = "~/.cache/lm-studio/models/<org>/<model-name>"
model, tokenizer = load(model_path)

def get_embedding(text):
    tokens = tokenizer.encode(text)
    token_ids = mx.array([tokens])
    # model.model() returns Qwen3Model.__call__() — hidden states after final RMSNorm
    # This is the embedding, before the lm_head projection
    hidden = model.model(token_ids)
    return hidden[0, -1, :]  # last token's hidden state
```

### Qwen3 Model Architecture

```
Model (outer):
  ├── model: Qwen3Model
  │     ├── embed_tokens → nn.Embedding(vocab→hidden)
  │     ├── layers[0..27] → TransformerBlock
  │     │     ├── self_attn (with QK-norm, RoPE)
  │     │     ├── input_layernorm (RMSNorm)
  │     │     ├── post_attention_layernorm (RMSNorm)
  │     │     └── mlp (swiGLU)
  │     └── norm → RMSNorm (final)
  └── (if tie_word_embeddings) embed_tokens.as_linear → logits
```

- `model(inputs)` → logits (vocab projection)
- `model.model(inputs)` → hidden states (embedding)

### Tested model: qwen3-embedding-0.6b-dwq

- **Architecture**: Qwen3, 28 layers, hidden_size=1024, 16 heads, GQA (8 KV heads)
- **Format**: MLX 4bit DWQ (safetensors)
- **Size**: 335 MB on disk
- **Dim**: 1024
- **Normalized**: No (L2 norm ~87.5 for short texts)
- **Load time** (M2): ~0.6s with Metal

### Semantic separation observed

| Pair type | English cosine | Chinese cosine |
|-----------|---------------|----------------|
| Similar concepts | 0.74–0.86 | 0.61–0.78 |
| Moderate relation | 0.43–0.66 | 0.45–0.63 |
| Unrelated | 0.36–0.54 | 0.39–0.45 |
| Cross-lingual (same concept, EN↔ZH) | — | 0.77–0.82 |

### Important notes

- Vectors are NOT L2-normalized — always normalize before computing cosine similarity
- Chinese semantic separation is weaker than English but still functional
- Cross-lingual alignment is strong: English and Chinese versions of the same concept map close in vector space

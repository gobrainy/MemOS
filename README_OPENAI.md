## OpenAI-only setup (no sentence-transformers)

This project supports using OpenAI for both chat and embeddings without installing `sentence-transformers`. The default configuration and API server are now aligned to use OpenAI everywhere via the universal API embedder.

### 1) Minimal environment

Set these env vars (for OpenAI; Azure or proxies are also supported):

- OPENAI_API_KEY: your OpenAI API key
- OPENAI_API_BASE: optional; defaults to `https://api.openai.com/v1`
- OPENAI_CHAT_MODEL: optional; defaults to `gpt-4o-mini`
- OPENAI_EMBED_MODEL: optional; defaults to `text-embedding-3-small`

Optional overrides for the built-in API server:

- MOS_EMBEDDER_BACKEND: set to `universal_api` (default)
- MOS_EMBEDDER_PROVIDER: `openai` (default)
- MOS_EMBEDDER_API_KEY: defaults to `OPENAI_API_KEY`
- MOS_EMBEDDER_MODEL: defaults to `OPENAI_EMBED_MODEL` or `text-embedding-3-small`
- MOS_EMBEDDER_API_BASE: defaults to `OPENAI_API_BASE` or `https://api.openai.com/v1`

### 2) Example JSON config

You can configure MemOS programmatically or POST to the API. Here’s a working config using OpenAI for everything:

```json
{
  "user_id": "brainy-default-user",
  "chat_model": {
    "backend": "openai",
    "config": {
      "model_name_or_path": "${OPENAI_CHAT_MODEL}",
      "temperature": 0.1,
      "max_tokens": 16384,
      "api_key": "${OPENAI_API_KEY}",
      "api_base": "${OPENAI_API_BASE}"
    }
  },
  "mem_reader": {
    "backend": "simple_struct",
    "config": {
      "llm": {
        "backend": "openai",
        "config": {
          "model_name_or_path": "${OPENAI_CHAT_MODEL}",
          "temperature": 0.0,
          "max_tokens": 16384,
          "api_key": "${OPENAI_API_KEY}",
          "api_base": "${OPENAI_API_BASE}"
        }
      },
      "embedder": {
        "backend": "universal_api",
        "config": {
          "provider": "openai",
          "model_name_or_path": "${OPENAI_EMBED_MODEL}",
          "api_key": "${OPENAI_API_KEY}",
          "base_url": "${OPENAI_API_BASE}"
        }
      },
      "chunker": {
        "backend": "hybrid",
        "config": {
          "tokenizer_or_token_counter": "gpt2",
          "chunk_size": 512,
          "chunk_overlap": 128,
          "min_sentences_per_chunk": 1,
          "semantic_similarity_threshold": 0.8,
          "use_semantic_chunking": true,
          "use_document_structure": true,
          "max_chunk_size": 1000,
          "min_chunk_size": 100,
          "overlap_strategy": "adaptive"
        }
      }
    }
  },
  "max_turns_window": 20,
  "top_k": 5,
  "enable_textual_memory": true,
  "enable_activation_memory": false,
  "enable_parametric_memory": false,
  "text_mem": {
    "backend": "tree_text",
    "config": {
      "extractor_llm": {
        "backend": "openai",
        "config": {
          "model_name_or_path": "${OPENAI_CHAT_MODEL}",
          "api_key": "${OPENAI_API_KEY}",
          "api_base": "${OPENAI_API_BASE}"
        }
      },
      "dispatcher_llm": {
        "backend": "openai",
        "config": {
          "model_name_or_path": "${OPENAI_CHAT_MODEL}",
          "api_key": "${OPENAI_API_KEY}",
          "api_base": "${OPENAI_API_BASE}"
        }
      },
      "graph_db": {
        "backend": "neo4j-community",
        "config": {
          "uri": "${NEO4J_URI}",
          "user": "${NEO4J_USER}",
          "password": "${NEO4J_PASSWORD}",
          "db_name": "${NEO4J_DB_NAME}",
          "use_multi_db": false,
          "user_name": "memos_${USER_ID}",
          "embedding_dimension": 1536,
          "vec_config": {
            "backend": "qdrant",
            "config": {
              "host": "${QDRANT_HOST}",
              "port": "${QDRANT_PORT}",
              "collection_name": "${QDRANT_COLLECTION}",
              "distance_metric": "cosine",
              "vector_dimension": 1536
            }
          }
        }
      },
      "embedder": {
        "backend": "universal_api",
        "config": {
          "provider": "openai",
          "model_name_or_path": "${OPENAI_EMBED_MODEL}",
          "api_key": "${OPENAI_API_KEY}",
          "base_url": "${OPENAI_API_BASE}"
        }
      },
      "reorganize": true
    }
  }
}
```

Notes:

- Use `text-embedding-3-small` (1536 dims) or `text-embedding-3-large` (3072 dims). Ensure your vector DB dimensions match.
- If you switch models, also update `embedding_dimension` and `vector_dimension` accordingly.

### 3) Programmatic defaults

You can create configs in code without any JSON by using helpers:

```python
from memos.mem_os.utils.default_config import get_default, get_default_cube_config, get_simple_config

# simplest
mos_config = get_simple_config(openai_api_key="sk-...", openai_api_base="https://api.openai.com/v1")

# full defaults (MemOS + MemCube)
mos_config, cube = get_default(openai_api_key="sk-...", openai_api_base="https://api.openai.com/v1")
```

### 4) API server defaults

When launching the FastAPI server (see `memos.api.start_api`), its defaults now prefer the OpenAI universal embedder. You can override via env vars listed above.

### 5) Remove sentence-transformers (optional)

- You do not need `sentence-transformers` to run with OpenAI. If installed previously, you can remove it from your environment to avoid server overhead.

### 6) Azure OpenAI or proxy

Set `MOS_EMBEDDER_PROVIDER=azure` and provide `MOS_EMBEDDER_API_BASE` with the Azure endpoint, plus `OPENAI_API_KEY` for the Azure key. The universal embedder will route calls accordingly.


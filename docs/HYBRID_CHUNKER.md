# Hybrid Chunker Documentation

## Overview

The **Hybrid Chunker** is an advanced text chunking strategy that combines multiple approaches to create semantically coherent and structurally aware text chunks. It's designed to provide superior chunking quality compared to simple character or sentence-based approaches.

## Features

### 🧠 **Semantic Chunking**
- Uses **OpenAI embeddings via Universal API** to measure semantic similarity
- Groups semantically related content together
- Configurable similarity threshold for fine-tuning

### 🏗️ **Document Structure Awareness** 
- Recognizes and respects document structure (headers, paragraphs, lists)
- Preserves logical document hierarchy
- Handles markdown-style headers and numbered sections

### 🔄 **Adaptive Overlap**
- Multiple overlap strategies: `fixed`, `adaptive`, `semantic`
- Dynamic overlap based on content similarity and chunk size
- Prevents information loss at chunk boundaries

### 📏 **Smart Size Management**
- Respects minimum and maximum chunk size constraints
- Intelligent splitting of oversized chunks
- Merging of undersized chunks when appropriate

## Configuration

### Basic Configuration

```json
{
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
```

### Configuration Parameters

#### **Base Parameters** (inherited from BaseChunkerConfig)
- `tokenizer_or_token_counter`: Tokenizer model name (default: "gpt2")
- `chunk_size`: Target chunk size in tokens (default: 512)
- `chunk_overlap`: Overlap between chunks in tokens (default: 128)
- `min_sentences_per_chunk`: Minimum sentences per chunk (default: 1)

#### **Hybrid-Specific Parameters**
- `semantic_similarity_threshold`: Threshold for semantic similarity (0.0-1.0, default: 0.8)
  - Higher values = more semantic coherence, smaller chunks
  - Lower values = larger chunks, less strict semantic grouping

- `use_semantic_chunking`: Enable semantic similarity-based chunking (default: true)
  - Uses OpenAI embeddings through the built-in Universal API embedder
  - Falls back to structural chunking if API credentials are missing

- `use_document_structure`: Use document structure for chunking (default: true)
  - Recognizes headers, paragraphs, lists
  - Preserves document hierarchy

- `max_chunk_size`: Maximum chunk size in tokens (default: 1000)
  - Hard limit, chunks exceeding this will be split

- `min_chunk_size`: Minimum chunk size in tokens (default: 100)
  - Chunks smaller than this may be merged with adjacent chunks

- `overlap_strategy`: Strategy for chunk overlap (default: "adaptive")
  - `"fixed"`: Use fixed overlap size from `chunk_overlap`
  - `"adaptive"`: Dynamic overlap based on chunk size
  - `"semantic"`: Semantic-based overlap (experimental)

## Usage Examples

### 1. MemCube Configuration

```json
{
  "model_schema": "memos.configs.mem_cube.GeneralMemCubeConfig",
  "text_mem": {
    "backend": "tree_text",
    "config": {
      "chunker": {
        "backend": "hybrid",
        "config": {
          "semantic_similarity_threshold": 0.85,
          "use_semantic_chunking": true,
          "use_document_structure": true,
          "max_chunk_size": 800,
          "min_chunk_size": 150,
          "overlap_strategy": "adaptive"
        }
      }
    }
  }
}
```

### 2. MemReader Configuration (OpenAI embeddings)

```json
{
  "backend": "simple_struct",
  "config": {
    "chunker": {
      "backend": "hybrid",
      "config": {
        "tokenizer_or_token_counter": "gpt2",
        "semantic_similarity_threshold": 0.8,
        "use_semantic_chunking": true,
        "overlap_strategy": "fixed",
        "openai_embedding_model": "text-embedding-3-large"  
      }
    }
  }
}
```

### 3. Programmatic Usage

```python
from memos.chunkers import ChunkerFactory
from memos.configs.chunker import ChunkerConfigFactory

# Create configuration
config = ChunkerConfigFactory(
    backend="hybrid",
    config={
        "semantic_similarity_threshold": 0.8,
        "use_semantic_chunking": True,
        "use_document_structure": True,
        "max_chunk_size": 1000,
        "overlap_strategy": "adaptive"
    }
)

# Create chunker instance
chunker = ChunkerFactory.from_config(config)

# Chunk text
chunks = chunker.chunk(your_text)
```

## Dependencies

The Hybrid Chunker requires the following additional packages:

```bash
pip install numpy transformers
```

### Optional Dependencies
- **spaCy**: For enhanced sentence segmentation
- **NLTK**: Alternative sentence tokenization

## Performance Characteristics

### **Semantic Chunking Mode**
- **Quality**: ⭐⭐⭐⭐⭐ (Highest)
- **Speed**: ⭐⭐⭐ (Moderate - requires embedding computation)
- **Memory**: ⭐⭐ (Higher due to embeddings)

### **Structural-Only Mode**
- **Quality**: ⭐⭐⭐⭐ (High)
- **Speed**: ⭐⭐⭐⭐⭐ (Fastest)
- **Memory**: ⭐⭐⭐⭐⭐ (Lowest)

## Best Practices

### 1. **For Technical Documents**
```json
{
  "semantic_similarity_threshold": 0.85,
  "use_semantic_chunking": true,
  "use_document_structure": true,
  "overlap_strategy": "semantic"
}
```

### 2. **For Narrative Text**
```json
{
  "semantic_similarity_threshold": 0.75,
  "use_semantic_chunking": true,
  "use_document_structure": false,
  "overlap_strategy": "adaptive"
}
```

### 3. **For Performance-Critical Applications**
```json
{
  "use_semantic_chunking": false,
  "use_document_structure": true,
  "overlap_strategy": "fixed"
}
```

### 4. **For Small Documents**
```json
{
  "min_chunk_size": 50,
  "max_chunk_size": 500,
  "semantic_similarity_threshold": 0.9
}
```

## Troubleshooting

### Common Issues

1. **"OpenAI API key missing"**
   - Set `OPENAI_API_KEY` environment variable or configure `openai_api_key` in chunker config
   - Will fallback to structural chunking

2. **"Tokenizer not found"** 
   - Install: `pip install transformers`
   - Will fallback to word-based token estimation

3. **Chunks too small/large**
   - Adjust `min_chunk_size` and `max_chunk_size`
   - Lower `semantic_similarity_threshold` for larger chunks

4. **Poor chunk quality**
   - Increase `semantic_similarity_threshold` 
   - Enable both `use_semantic_chunking` and `use_document_structure`

### Fallback Behavior

The Hybrid Chunker is designed to gracefully degrade:
1. **Full Mode**: Semantic + Structural chunking
2. **Structural Mode**: Structure-aware chunking only
3. **Fallback Mode**: Simple sentence-based chunking

## Integration with MemOS

The Hybrid Chunker integrates seamlessly with MemOS components:

- **TextualMemory**: Enhanced chunk quality improves memory retrieval
- **MemReader**: Better document processing and memory extraction  
- **TreeTextMemory**: Semantic chunks improve memory organization
- **GraphDB**: More coherent chunks create better knowledge graphs

## Comparison with Other Chunkers

| Feature | Sentence Chunker | Hybrid Chunker |
|---------|------------------|----------------|
| Semantic Awareness | ❌ | ✅ |
| Structure Awareness | ❌ | ✅ |
| Adaptive Overlap | ❌ | ✅ |
| Performance | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Quality | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Memory Usage | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

## Future Enhancements

Planned improvements for the Hybrid Chunker:

1. **Multi-language Support**: Better handling of non-English text
2. **Custom Embeddings**: Support for domain-specific embedding models
3. **Async Processing**: Parallel chunk processing for large documents
4. **Advanced Overlap**: ML-based overlap optimization
5. **Format-Specific Chunking**: Specialized handling for code, tables, etc.

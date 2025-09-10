# LangChain Chunker Integration

The LangChain Chunker provides access to LangChain's mature and powerful text splitting capabilities directly within MemOS. This integration offers multiple chunking strategies, from simple character-based splitting to advanced semantic chunking using embeddings.

## Overview

LangChain is a leading framework for building applications with Large Language Models, and its text splitting capabilities are battle-tested across thousands of production applications. The MemOS LangChain integration provides:

- **5 different splitting strategies** for various use cases
- **Seamless integration** with MemOS memory systems
- **Production-ready performance** with extensive configuration options
- **Automatic fallbacks** for robust operation

## Available Strategies

### 1. 🧠 **Recursive Character Text Splitter** (Recommended)
**Best for**: Most documents, general-purpose chunking

```json
{
  "split_strategy": "recursive",
  "chunk_size": 1000,
  "chunk_overlap": 200,
  "separators": ["\n\n", "\n", ". ", " ", ""]
}
```

**How it works:**
- Uses a hierarchy of separators to find natural break points
- Tries to split on paragraphs first, then sentences, then words
- Maintains semantic coherence while respecting size limits

**Advantages:**
- ⭐ **Best overall quality** for most document types
- ⭐ **Smart boundary detection** preserves meaning
- ⭐ **Configurable separators** for different document types

### 2. 📝 **Character Text Splitter**
**Best for**: Simple documents, fast processing

```json
{
  "split_strategy": "character",
  "chunk_size": 1000,
  "chunk_overlap": 200,
  "separator": "\n\n"
}
```

**How it works:**
- Splits text on a single specified separator
- Simple and fast operation
- Predictable results

**Advantages:**
- ⚡ **Fastest processing** speed
- ⚡ **Minimal memory usage**
- ⚡ **Predictable chunk sizes**

### 3. 🔢 **Token Text Splitter**
**Best for**: Precise token control, LLM input preparation

```json
{
  "split_strategy": "token",
  "chunk_size": 512,
  "chunk_overlap": 50,
  "tokenizer_or_token_counter": "gpt2"
}
```

**How it works:**
- Uses actual tokenizer to count tokens precisely
- Ensures chunks never exceed token limits
- Ideal for LLM input preparation

**Advantages:**
- 🎯 **Precise token control** for LLM contexts
- 🎯 **Accurate sizing** using real tokenizers
- 🎯 **Model-specific** tokenization support

### 4. 📋 **Markdown Header Text Splitter**
**Best for**: Markdown documents, structured content

```json
{
  "split_strategy": "markdown",
  "chunk_size": 1000,
  "markdown_headers": [
    ["#", "Header 1"],
    ["##", "Header 2"],
    ["###", "Header 3"]
  ]
}
```

**How it works:**
- Splits text based on markdown header hierarchy
- Preserves document structure and organization
- Maintains header context in chunks

**Advantages:**
- 📖 **Structure-aware chunking** preserves hierarchy
- 📖 **Context preservation** with header information
- 📖 **Perfect for documentation** and structured content

### 5. 🧬 **Semantic Chunker** (Advanced)
**Best for**: Topic-based splitting, research documents

```json
{
  "split_strategy": "semantic",
  "embedding_model": "all-MiniLM-L6-v2",
  "breakpoint_threshold_type": "percentile",
  "breakpoint_threshold_amount": 95.0
}
```

**How it works:**
- Uses embeddings to detect topic shifts in content
- Creates natural breaks where semantic meaning changes
- Most sophisticated but computationally intensive

**Advantages:**
- 🎓 **Topic-aware chunking** for research and academic content
- 🎓 **Natural semantic boundaries** preserve meaning
- 🎓 **Adaptive chunk sizes** based on content structure

## Configuration Reference

### Base Configuration
All strategies inherit these base settings:

```json
{
  "tokenizer_or_token_counter": "gpt2",
  "chunk_size": 1000,
  "chunk_overlap": 200,
  "min_sentences_per_chunk": 1
}
```

### Strategy-Specific Options

#### Recursive & Character Splitting
```json
{
  "separators": ["\n\n", "\n", ". ", " "],  // Recursive only
  "separator": "\n\n",                      // Character only
  "keep_separator": false,
  "is_separator_regex": false
}
```

#### Markdown Splitting
```json
{
  "markdown_headers": [
    ["#", "Header 1"],
    ["##", "Header 2"],
    ["###", "Header 3"]
  ],
  "return_each_line": false
}
```

#### Semantic Splitting
```json
{
  "openai_api_key": null,                    // Optional: use OpenAI embeddings
  "embedding_model": "all-MiniLM-L6-v2",    // Fallback model
  "breakpoint_threshold_type": "percentile", // or "standard_deviation", "interquartile"
  "breakpoint_threshold_amount": 95.0
}
```

## Usage Examples

### 1. MemCube Configuration

```json
{
  "model_schema": "memos.configs.mem_cube.GeneralMemCubeConfig",
  "text_mem": {
    "backend": "tree_text",
    "config": {
      "chunker": {
        "backend": "langchain",
        "config": {
          "split_strategy": "recursive",
          "chunk_size": 800,
          "chunk_overlap": 100,
          "separators": ["\n\n", "\n", ". ", " "]
        }
      }
    }
  }
}
```

### 2. Direct Usage

```python
from memos.chunkers import ChunkerFactory
from memos.configs.chunker import ChunkerConfigFactory

# Recursive splitting (recommended)
config = ChunkerConfigFactory(
    backend="langchain",
    config={
        "split_strategy": "recursive",
        "chunk_size": 1000,
        "chunk_overlap": 200,
        "separators": ["\n\n", "\n", ". ", " "]
    }
)

chunker = ChunkerFactory.from_config(config)
chunks = chunker.chunk(your_text)
```

### 3. Markdown Document Processing

```python
# Perfect for documentation and structured content
config = ChunkerConfigFactory(
    backend="langchain",
    config={
        "split_strategy": "markdown",
        "chunk_size": 1200,
        "markdown_headers": [
            ["#", "Header 1"],
            ["##", "Header 2"],
            ["###", "Header 3"],
            ["####", "Header 4"]
        ]
    }
)
```

### 4. Semantic Research Document Chunking

```python
# Best for academic papers and research content
config = ChunkerConfigFactory(
    backend="langchain",
    config={
        "split_strategy": "semantic",
        "embedding_model": "all-MiniLM-L6-v2",
        "breakpoint_threshold_type": "percentile",
        "breakpoint_threshold_amount": 90.0  # More sensitive to topic changes
    }
)
```

## Installation

### Required Dependencies
```bash
pip install langchain-text-splitters
```

### Optional Dependencies (for advanced features)
```bash
# For semantic chunking
pip install langchain-experimental
pip install langchain-community

# For OpenAI embeddings (semantic chunking)
pip install langchain-openai

# For enhanced tokenization
pip install transformers
```

## Performance Comparison

| Strategy | Speed | Memory | Quality | Use Case |
|----------|-------|--------|---------|----------|
| **Character** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Simple documents |
| **Recursive** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **Most documents** |
| **Token** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | LLM preparation |
| **Markdown** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Structured content |
| **Semantic** | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | Research documents |

## Best Practices

### 1. **Choose the Right Strategy**
- **Start with `recursive`** for most use cases
- **Use `markdown`** for documentation and structured content
- **Use `semantic`** for research papers and topic-based analysis
- **Use `token`** when precise token control is critical
- **Use `character`** for simple, fast processing

### 2. **Optimize Chunk Sizes**
```json
{
  "chunk_size": 800,      // For detailed analysis
  "chunk_size": 1200,     // For general RAG applications  
  "chunk_size": 400,      // For fine-grained search
  "chunk_overlap": 100    // 10-15% of chunk_size is optimal
}
```

### 3. **Configure Separators for Document Types**
```json
// For code documents
"separators": ["\n\nclass ", "\n\ndef ", "\n\n", "\n", " "]

// For academic papers  
"separators": ["\n\n", "\n", ". ", "? ", "! ", " "]

// For business documents
"separators": ["\n\n", "\n", ". ", "; ", " "]
```

### 4. **Semantic Chunking Tuning**
```json
{
  "breakpoint_threshold_amount": 95.0,  // Conservative (fewer, larger chunks)
  "breakpoint_threshold_amount": 85.0,  // Moderate (balanced)
  "breakpoint_threshold_amount": 75.0   // Aggressive (more, smaller chunks)
}
```

## Error Handling

The LangChain chunker includes robust error handling:

1. **Missing Dependencies**: Automatic fallback to simpler strategies
2. **Invalid Configurations**: Clear error messages with suggestions
3. **Processing Failures**: Graceful fallback to character-based splitting
4. **Memory Issues**: Automatic chunk size reduction for large documents

## Integration with Other MemOS Components

The LangChain chunker works seamlessly with:

- ✅ **All memory backends** (tree_text, general_text, naive_text)
- ✅ **All vector databases** (Qdrant, etc.)
- ✅ **All embedders** (SentenceTransformer, OpenAI, etc.)
- ✅ **All LLMs** (OpenAI, Ollama, VLLM, etc.)
- ✅ **MemOS API** and **MCP server**

## Troubleshooting

### Common Issues

**1. `ImportError: No module named 'langchain_text_splitters'`**
```bash
pip install langchain-text-splitters
```

**2. Semantic chunking not working**
```bash
pip install langchain-experimental langchain-community
```

**3. Chunks too large/small**
- Adjust `chunk_size` and `chunk_overlap` parameters
- Try different `separators` for recursive strategy
- Consider different `breakpoint_threshold_amount` for semantic

**4. Poor chunk quality**
- Switch from `character` to `recursive` strategy
- Use `markdown` strategy for structured content
- Try `semantic` strategy for research documents

## Example Scripts

Run the example script to see all strategies in action:

```bash
cd examples
python langchain_chunker_example.py
```

This will demonstrate all chunking strategies and provide performance comparisons.

---

The LangChain chunker brings production-ready, battle-tested text splitting capabilities to MemOS, offering the flexibility and reliability needed for serious document processing applications. 🚀

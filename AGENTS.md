# MemOS Agent Documentation

This document provides a comprehensive guide for AI agents to understand and use the MemOS library.

## 1. Introduction to MemOS

MemOS is an operating system for Large Language Models (LLMs) that enhances them with long-term memory capabilities. It allows LLMs to store, retrieve, and manage information, enabling more context-aware, consistent, and personalized interactions.

**Key Features:**

- **Memory-Augmented Generation (MAG):** A unified API for memory operations.
- **Modular Memory Architecture (MemCube):** A flexible and modular architecture for managing different memory types.
- **Multiple Memory Types:** Supports textual, activation (KV-cache), and parametric (adapter weights) memories.
- **Extensible:** Easily extend and customize memory modules, data sources, and LLM integrations.

## 2. Core Concepts

### 2.1. MOS (Memory Operating System)

The `MOS` class is the main entry point for interacting with the Memory Operating System. It orchestrates memory operations, user management, and interaction with LLMs.

### 2.2. MemCube

A `MemCube` is a container for three types of memories:

- **Textual Memory (`text_mem`):** Stores and retrieves unstructured or structured text knowledge.
- **Activation Memory (`act_mem`):** Caches key-value pairs (`KVCacheMemory`) to accelerate LLM inference.
- **Parametric Memory (`para_mem`):** Stores model adaptation parameters (e.g., LoRA weights).

`MemCube`s can be loaded from local directories or remote repositories, and their state can be saved (dumped) to a directory.

## 3. Getting Started

### 3.1. Installation

Install MemOS using pip:

```bash
pip install MemoryOS
```

For specific features, you can install optional dependencies:

```bash
# For Tree Memory
pip install MemoryOS[tree-mem]

# For Memory Reader
pip install MemoryOS[mem-reader]

# For Memory Scheduler
pip install MemoryOS[mem-scheduler]
```

### 3.2. Quick Start: `MOS.simple()`

The easiest way to get started is by using the `MOS.simple()` class method. It automatically configures MOS using environment variables.

**Required Environment Variables:**

- `OPENAI_API_KEY`: Your OpenAI API key.
- `OPENAI_API_BASE` (optional): The base URL for the OpenAI API.
- `MOS_TEXT_MEM_TYPE` (optional): The type of text memory to use (e.g., `"general_text"`).

**Example:**

```python
import os
from memos.mem_os.main import MOS

# Set environment variables
os.environ["OPENAI_API_KEY"] = "your-openai-api-key"

# Initialize MOS
memory = MOS.simple()

# Add a memory
memory.add(
    messages=[
        {"role": "user", "content": "My favorite color is blue."}
    ]
)

# Chat with memory
response = memory.chat("What is my favorite color?")
print(response)  # Output should be related to the color blue.
```

### 3.3. Working with `MemCube`

You can initialize a `MemCube` from a local directory.

```python
from memos.mem_cube.general import GeneralMemCube

# Initialize a MemCube from a local directory
mem_cube = GeneralMemCube.init_from_dir("path/to/your/mem_cube")

# Access memories
if mem_cube.text_mem:
    all_text_memories = mem_cube.text_mem.get_all()
    print(all_text_memories)

# Save the MemCube to a new directory
mem_cube.dump("path/to/new/mem_cube")
```

## 4. Key Components and Usage

### 4.1. `MOS` API

The `MOS` class provides the primary interface for memory operations.

#### 4.1.1. `chat(query: str, user_id: str | None = None) -> str`

Engages in a conversation with the LLM, using the user's memory to provide context-aware responses.

```python
response = memory.chat("What was the last thing I told you?", user_id="user-123")
```

#### 4.1.2. `add(messages: list[dict], user_id: str | None = None)`

Adds information to the user's memory. The `messages` should be in the OpenAI chat format.

```python
memory.add(
    messages=[
        {"role": "user", "content": "I live in New York."},
        {"role": "assistant", "content": "Okay, I'll remember that."}
    ],
    user_id="user-123"
)
```

#### 4.1.3. `search(query: str, user_id: str | None = None) -> dict`

Retrieves relevant memories for a given query.

```python
retrieved_memories = memory.search("Where do I live?", user_id="user-123")
print(retrieved_memories["text_mem"])
```

#### 4.1.4. User Management

MOS supports multi-user environments.

- `create_user(user_id: str)`: Creates a new user.
- `register_mem_cube(mem_cube_path_or_obj, user_id: str)`: Assigns a `MemCube` to a user.

```python
# Create a new user
memory.create_user(user_id="user-456")

# Register a MemCube for the user
memory.register_mem_cube("path/to/mem_cube", user_id="user-456")
```

### 4.2. Configuration

MemOS is highly configurable. You can configure every component, from the LLM and embedder to the chunker and vector database. Configurations are managed through Pydantic models.

**Example: `MOSConfig`**

```python
from memos.configs.mem_os import MOSConfig

# Load configuration from a JSON file
mos_config = MOSConfig.from_json_file("path/to/your/config.json")

# Initialize MOS with the configuration
memory = MOS(mos_config)
```

You can find example configurations in the `examples/data/config` directory of the repository.

### 4.3. Text Chunkers

Chunkers are used to split large texts into smaller, semantically coherent chunks before they are stored in textual memory. MemOS provides different chunking backends.

- **`hybrid`:** An advanced chunker that combines semantic and structural analysis.
- **`langchain`:** Integrates with LangChain's text splitters.
- **`sentence`:** A basic sentence-level chunker.

You can configure the chunker in your `MemCube` or `MOS` configuration.

**Example Chunker Configuration:**

```json
{
  "chunker": {
    "backend": "hybrid",
    "config": {
      "chunk_size": 512,
      "chunk_overlap": 128,
      "use_semantic_chunking": true
    }
  }
}
```

### 4.4. Textual Memory Backends

MemOS offers several backends for textual memory, each with different characteristics:

- **`naive`**: A simple, in-memory implementation that stores memories in a list. It performs a basic keyword search. This is useful for quick prototyping and testing but not recommended for production.
- **`general`**: Uses a vector database (like Qdrant) to store memory embeddings and performs semantic search. This is a robust and scalable solution for most use cases.
- **`tree`**: A sophisticated backend that organizes memories into a knowledge graph. It uses a graph database (like Neo4j) and supports complex queries, relationship analysis, and memory reorganization. This is ideal for applications requiring deep reasoning and understanding of relationships between memories.

You can specify the backend in the `text_mem` section of your `MemCube` configuration.

**Example Textual Memory Configuration:**

```json
{
  "text_mem": {
    "backend": "general",
    "config": {
      // ... configuration for GeneralTextMemory
    }
  }
}
```

## 5. Advanced Components

### 5.1. MemReader

The `MemReader` component is responsible for reading and parsing information from various data sources and converting it into `TextualMemoryItem` objects that can be added to a `MemCube`. This is the primary way to ingest documents, web pages, or other structured/unstructured data into MemOS.

### 5.2. MemScheduler

The `MemScheduler` is an advanced component for orchestrating memory operations in complex, long-running applications. It runs as a separate process and can manage multiple `MemCube`s, perform periodic memory updates, and handle asynchronous memory tasks. It uses a message queue (like RabbitMQ) to receive and dispatch memory operations.

## 6. Advanced Usage

### 6.1. PRO_MODE and Chain of Thought (CoT)

By setting `PRO_MODE=True` in your `MOSConfig`, you enable Chain of Thought (CoT) reasoning. In this mode, `MOS` will decompose complex queries into smaller sub-questions, retrieve memories for each sub-question, and then synthesize a comprehensive answer. This is useful for complex, multi-hop reasoning tasks.

### 6.2. Using Different Backends

MemOS is backend-agnostic for many of its components. You can easily switch between different LLMs (OpenAI, Ollama, HuggingFace), Embedders, and Vector Databases (Qdrant) through configuration.

## 7. Code Examples

For more detailed and practical examples, refer to the `examples/` directory in the MemOS repository. These examples cover a wide range of use cases, from basic memory operations to building complex, multi-user memory-augmented applications.

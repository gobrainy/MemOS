from typing import Any, ClassVar

from pydantic import Field, field_validator, model_validator

from memos.configs.base import BaseConfig


class BaseChunkerConfig(BaseConfig):
    """Base configuration class for chunkers."""

    tokenizer_or_token_counter: str = Field(
        default="gpt2", description="Tokenizer model name or a token counting function"
    )
    chunk_size: int = Field(default=512, description="Maximum tokens per chunk")
    chunk_overlap: int = Field(default=128, description="Overlap between chunks")
    min_sentences_per_chunk: int = Field(default=1, description="Minimum sentences in each chunk")


class SentenceChunkerConfig(BaseChunkerConfig):
    """Configuration for sentence-based text chunker."""


class HybridChunkerConfig(BaseChunkerConfig):
    """Configuration for hybrid text chunker combining multiple strategies."""
    
    semantic_similarity_threshold: float = Field(
        default=0.8, description="Threshold for semantic similarity chunking"
    )
    use_semantic_chunking: bool = Field(
        default=True, description="Enable semantic similarity-based chunking"
    )
    use_document_structure: bool = Field(
        default=True, description="Use document structure (headers, paragraphs) for chunking"
    )
    max_chunk_size: int = Field(
        default=1000, description="Maximum chunk size in tokens"
    )
    min_chunk_size: int = Field(
        default=100, description="Minimum chunk size in tokens"
    )
    overlap_strategy: str = Field(
        default="adaptive", description="Overlap strategy: 'fixed', 'adaptive', 'semantic'"
    )


class LangChainChunkerConfig(BaseChunkerConfig):
    """Configuration for LangChain-based text chunker."""
    
    split_strategy: str = Field(
        default="recursive", description="LangChain splitting strategy: 'recursive', 'character', 'token', 'markdown', 'semantic'"
    )
    separators: list[str] | None = Field(
        default=None, description="List of separators for recursive splitting (default: ['\\n\\n', '\\n', ' ', ''])"
    )
    separator: str = Field(
        default="\n\n", description="Single separator for character splitting"
    )
    keep_separator: bool = Field(
        default=False, description="Whether to keep separators in chunks"
    )
    is_separator_regex: bool = Field(
        default=False, description="Whether separators are regex patterns"
    )
    markdown_headers: list[tuple[str, str]] | None = Field(
        default=None, description="Headers to split on for markdown strategy"
    )
    return_each_line: bool = Field(
        default=False, description="Return each line separately for markdown splitting"
    )
    openai_api_key: str | None = Field(
        default=None, description="OpenAI API key for semantic chunking (optional)"
    )
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2", description="Embedding model for semantic chunking fallback"
    )
    breakpoint_threshold_type: str = Field(
        default="percentile", description="Threshold type for semantic chunking: 'percentile', 'standard_deviation', 'interquartile'"
    )
    breakpoint_threshold_amount: float = Field(
        default=95.0, description="Threshold amount for semantic chunking breakpoints"
    )


class ChunkerConfigFactory(BaseConfig):
    """Factory class for creating chunker configurations."""

    backend: str = Field(..., description="Backend for chunker")
    config: dict[str, Any] = Field(..., description="Configuration for the chunker backend")

    backend_to_class: ClassVar[dict[str, Any]] = {
        "sentence": SentenceChunkerConfig,
        "hybrid": HybridChunkerConfig,
        "langchain": LangChainChunkerConfig,
    }

    @field_validator("backend")
    @classmethod
    def validate_backend(cls, backend: str) -> str:
        """Validate the backend field."""
        if backend not in cls.backend_to_class:
            raise ValueError(f"Invalid backend: {backend}")
        return backend

    @model_validator(mode="after")
    def create_config(self) -> "ChunkerConfigFactory":
        config_class = self.backend_to_class[self.backend]
        self.config = config_class(**self.config)
        return self

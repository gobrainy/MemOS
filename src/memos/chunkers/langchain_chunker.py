"""
LangChain Text Chunker leveraging LangChain's powerful text splitting capabilities.

This chunker provides access to LangChain's mature and diverse text splitting strategies:
1. RecursiveCharacterTextSplitter - Smart hierarchical splitting
2. CharacterTextSplitter - Simple character-based splitting  
3. TokenTextSplitter - Token-aware splitting
4. MarkdownHeaderTextSplitter - Structure-aware markdown splitting
5. SemanticChunker - Embedding-based semantic splitting (if available)
"""

import re
from typing import List, Optional, Dict, Any
from memos.configs.chunker import LangChainChunkerConfig
from memos.dependency import require_python_package
from memos.log import get_logger
from .base import BaseChunker, Chunk

logger = get_logger(__name__)


class LangChainChunker(BaseChunker):
    """
    Advanced text chunker using LangChain's text splitting capabilities.
    """

    @require_python_package(
        import_name="langchain_text_splitters",
        install_command="pip install langchain-text-splitters",
        install_link="https://python.langchain.com/docs/how_to/character_text_splitter/",
    )
    def __init__(self, config: LangChainChunkerConfig):
        self.config = config
        self.splitter = None
        
        # Initialize the appropriate text splitter based on strategy
        try:
            self.splitter = self._create_splitter()
            logger.info(f"Initialized LangChain chunker with strategy: {config.split_strategy}")
        except Exception as e:
            logger.error(f"Failed to initialize LangChain chunker: {e}")
            raise

    def _create_splitter(self):
        """Create the appropriate LangChain text splitter based on configuration."""
        from langchain_text_splitters import (
            RecursiveCharacterTextSplitter,
            CharacterTextSplitter,
            TokenTextSplitter,
        )
        
        strategy = self.config.split_strategy.lower()
        
        if strategy == "recursive":
            return RecursiveCharacterTextSplitter(
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap,
                length_function=len,
                separators=self.config.separators or ["\n\n", "\n", " ", ""],
                keep_separator=self.config.keep_separator,
                is_separator_regex=self.config.is_separator_regex,
            )
            
        elif strategy == "character":
            return CharacterTextSplitter(
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap,
                length_function=len,
                separator=self.config.separator,
                keep_separator=self.config.keep_separator,
                is_separator_regex=self.config.is_separator_regex,
            )
            
        elif strategy == "token":
            return TokenTextSplitter(
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap,
                model_name=self.config.tokenizer_or_token_counter,
            )
            
        elif strategy == "markdown":
            try:
                from langchain_text_splitters import MarkdownHeaderTextSplitter
                
                # Default markdown headers to split on
                headers_to_split_on = self.config.markdown_headers or [
                    ("#", "Header 1"),
                    ("##", "Header 2"), 
                    ("###", "Header 3"),
                    ("####", "Header 4"),
                ]
                
                return MarkdownHeaderTextSplitter(
                    headers_to_split_on=headers_to_split_on,
                    return_each_line=self.config.return_each_line,
                )
            except ImportError:
                logger.warning("MarkdownHeaderTextSplitter not available, falling back to recursive")
                return self._create_recursive_splitter()
                
        elif strategy == "semantic":
            try:
                from langchain_experimental.text_splitter import SemanticChunker
                from langchain_openai.embeddings import OpenAIEmbeddings
                
                # Use OpenAI embeddings or fallback to sentence transformers
                if self.config.openai_api_key:
                    embeddings = OpenAIEmbeddings(api_key=self.config.openai_api_key)
                else:
                    # Try to use sentence transformers as fallback
                    try:
                        from langchain_community.embeddings import SentenceTransformerEmbeddings
                        embeddings = SentenceTransformerEmbeddings(
                            model_name=self.config.embedding_model or "all-MiniLM-L6-v2"
                        )
                    except ImportError:
                        logger.warning("No embeddings available for semantic chunking, falling back to recursive")
                        return self._create_recursive_splitter()
                
                return SemanticChunker(
                    embeddings=embeddings,
                    breakpoint_threshold_type=self.config.breakpoint_threshold_type,
                    breakpoint_threshold_amount=self.config.breakpoint_threshold_amount,
                )
                
            except ImportError:
                logger.warning("SemanticChunker not available, falling back to recursive")
                return self._create_recursive_splitter()
        
        else:
            logger.warning(f"Unknown strategy '{strategy}', falling back to recursive")
            return self._create_recursive_splitter()

    def _create_recursive_splitter(self):
        """Create a recursive character text splitter as fallback."""
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        
        return RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )

    def chunk(self, text: str) -> List[Chunk]:
        """
        Split text into chunks using the configured LangChain text splitter.
        """
        if not self.splitter:
            raise RuntimeError("LangChain text splitter not initialized")
        
        try:
            # Use LangChain splitter to split the text
            if self.config.split_strategy == "markdown":
                # Markdown splitter returns different format
                splits = self.splitter.split_text(text)
                texts = [split.page_content if hasattr(split, 'page_content') else str(split) for split in splits]
            else:
                texts = self.splitter.split_text(text)
            
            # Convert to Chunk objects
            chunks = []
            for i, chunk_text in enumerate(texts):
                chunk_text = chunk_text.strip()
                if not chunk_text:
                    continue
                
                # Calculate token count
                token_count = self._count_tokens(chunk_text)
                
                # Extract sentences
                sentences = self._extract_sentences(chunk_text)
                
                # Create chunk
                chunk = Chunk(
                    text=chunk_text,
                    token_count=token_count,
                    sentences=sentences
                )
                chunks.append(chunk)
            
            logger.info(f"Created {len(chunks)} chunks using LangChain {self.config.split_strategy} strategy")
            return chunks
            
        except Exception as e:
            logger.error(f"Error during LangChain chunking: {e}")
            return self._fallback_chunk(text)

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using the configured tokenizer."""
        try:
            # Try to use the same tokenizer as configured
            if self.config.split_strategy == "token" and hasattr(self.splitter, '_tokenizer'):
                return len(self.splitter._tokenizer.encode(text))
        except Exception:
            pass
        
        # Fallback to word-based estimation
        return len(text.split()) * 1.3

    def _extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text."""
        # Simple sentence splitting (could be enhanced with spaCy or NLTK)
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _fallback_chunk(self, text: str) -> List[Chunk]:
        """
        Fallback chunking method when LangChain splitting fails.
        """
        logger.warning("Using fallback chunking method")
        
        # Simple character-based chunking
        chunk_size = self.config.chunk_size * 4  # Rough character estimate
        overlap_size = self.config.chunk_overlap * 4
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at word boundary
            if end < len(text):
                space_pos = text.rfind(' ', start, end)
                if space_pos > start:
                    end = space_pos
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunks.append(Chunk(
                    text=chunk_text,
                    token_count=self._count_tokens(chunk_text),
                    sentences=self._extract_sentences(chunk_text)
                ))
            
            start = max(end - overlap_size, start + 1)
        
        return chunks

    def get_splitter_info(self) -> Dict[str, Any]:
        """Get information about the current splitter configuration."""
        return {
            "strategy": self.config.split_strategy,
            "chunk_size": self.config.chunk_size,
            "chunk_overlap": self.config.chunk_overlap,
            "splitter_type": type(self.splitter).__name__ if self.splitter else None,
            "available_strategies": ["recursive", "character", "token", "markdown", "semantic"]
        }

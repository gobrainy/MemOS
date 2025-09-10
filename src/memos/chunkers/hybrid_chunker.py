"""
Hybrid Text Chunker combining multiple chunking strategies.

This chunker implements a sophisticated approach that combines:
1. Semantic similarity-based chunking using sentence transformers
2. Document structure awareness (headers, paragraphs, lists)
3. Adaptive overlap based on content similarity
4. Fallback to sentence/character-based chunking
"""

import re
import numpy as np
from typing import List, Optional, Tuple
from sentence_transformers import SentenceTransformer

from memos.configs.chunker import HybridChunkerConfig
from memos.dependency import require_python_package
from memos.log import get_logger

from .base import BaseChunker, Chunk


logger = get_logger(__name__)


class HybridChunker(BaseChunker):
    """
    Advanced hybrid text chunker that combines semantic, structural, and size-based strategies.
    """

    @require_python_package(
        import_name="sentence_transformers",
        install_command="pip install sentence-transformers",
        install_link="https://www.sbert.net/docs/installation.html",
    )
    @require_python_package(
        import_name="numpy",
        install_command="pip install numpy",
        install_link="https://numpy.org/install/",
    )
    def __init__(self, config: HybridChunkerConfig):
        self.config = config
        
        # Initialize sentence transformer for semantic similarity
        if config.use_semantic_chunking:
            try:
                # Use a lightweight but effective model for semantic similarity
                self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Initialized SentenceTransformer for semantic chunking")
            except Exception as e:
                logger.warning(f"Failed to initialize SentenceTransformer: {e}. Falling back to structural chunking only.")
                self.embedder = None
                config.use_semantic_chunking = False
        else:
            self.embedder = None

        # Initialize tokenizer for length calculations
        try:
            from transformers import AutoTokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(config.tokenizer_or_token_counter)
        except Exception:
            # Fallback to simple token counting
            self.tokenizer = None
            logger.warning(f"Could not load tokenizer {config.tokenizer_or_token_counter}, using word-based estimation")

        logger.info(f"Initialized HybridChunker with config: {config}")

    def chunk(self, text: str) -> List[Chunk]:
        """
        Chunk the given text using hybrid strategy.
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of Chunk objects with text, token_count, and sentences
        """
        if not text.strip():
            return []

        try:
            # Step 1: Preprocess and extract structural elements
            structured_segments = self._extract_structural_segments(text)
            
            # Step 2: Apply semantic chunking if enabled
            if self.config.use_semantic_chunking and self.embedder:
                chunks = self._semantic_chunk(structured_segments)
            else:
                chunks = self._structural_chunk(structured_segments)
            
            # Step 3: Apply size constraints and create final chunks
            final_chunks = self._apply_size_constraints(chunks)
            
            # Step 4: Convert to Chunk objects
            result_chunks = []
            for chunk_text in final_chunks:
                token_count = self._count_tokens(chunk_text)
                sentences = self._extract_sentences(chunk_text)
                
                result_chunks.append(Chunk(
                    text=chunk_text,
                    token_count=token_count,
                    sentences=sentences
                ))
            
            logger.debug(f"Generated {len(result_chunks)} chunks from input text")
            return result_chunks
            
        except Exception as e:
            logger.error(f"Error in hybrid chunking: {e}")
            # Fallback to simple sentence-based chunking
            return self._fallback_chunk(text)

    def _extract_structural_segments(self, text: str) -> List[str]:
        """
        Extract structural segments from text (headers, paragraphs, lists).
        """
        if not self.config.use_document_structure:
            # Return paragraphs as basic structural units
            return [p.strip() for p in text.split('\n\n') if p.strip()]
        
        segments = []
        current_segment = ""
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Detect headers (markdown-style or numbered)
            if self._is_header(line):
                if current_segment:
                    segments.append(current_segment.strip())
                current_segment = line + '\n'
            
            # Detect list items
            elif self._is_list_item(line):
                if current_segment and not self._is_list_context(current_segment):
                    segments.append(current_segment.strip())
                    current_segment = line + '\n'
                else:
                    current_segment += line + '\n'
            
            # Regular content
            else:
                current_segment += line + '\n'
                
                # Check if we should break on paragraph boundaries
                if current_segment.count('\n') > 3:  # Arbitrary threshold for paragraph
                    segments.append(current_segment.strip())
                    current_segment = ""
        
        if current_segment:
            segments.append(current_segment.strip())
        
        return [seg for seg in segments if seg]

    def _is_header(self, line: str) -> bool:
        """Check if a line is a header."""
        # Markdown headers
        if re.match(r'^#{1,6}\s+', line):
            return True
        # Numbered headers
        if re.match(r'^\d+\.?\s+[A-Z]', line) and len(line.split()) <= 10:
            return True
        # All caps short lines (potential headers)
        if line.isupper() and len(line.split()) <= 8 and len(line) > 3:
            return True
        return False

    def _is_list_item(self, line: str) -> bool:
        """Check if a line is a list item."""
        return bool(re.match(r'^[-*+•]\s+', line) or re.match(r'^\d+\.?\s+', line))

    def _is_list_context(self, text: str) -> bool:
        """Check if text contains list items."""
        lines = text.split('\n')
        list_lines = sum(1 for line in lines if self._is_list_item(line.strip()))
        return list_lines > 0

    def _semantic_chunk(self, segments: List[str]) -> List[str]:
        """
        Apply semantic chunking using sentence embeddings.
        """
        if not segments or not self.embedder:
            return segments
        
        # Get embeddings for all segments
        try:
            embeddings = self.embedder.encode(segments)
            
            chunks = []
            current_chunk = segments[0]
            current_embedding = embeddings[0]
            
            for i in range(1, len(segments)):
                segment = segments[i]
                segment_embedding = embeddings[i]
                
                # Calculate cosine similarity
                similarity = np.dot(current_embedding, segment_embedding) / (
                    np.linalg.norm(current_embedding) * np.linalg.norm(segment_embedding)
                )
                
                # If similarity is below threshold, start new chunk
                if similarity < self.config.semantic_similarity_threshold:
                    chunks.append(current_chunk)
                    current_chunk = segment
                    current_embedding = segment_embedding
                else:
                    # Merge segments
                    current_chunk += '\n\n' + segment
                    # Update embedding to average (simple approach)
                    current_embedding = (current_embedding + segment_embedding) / 2
            
            if current_chunk:
                chunks.append(current_chunk)
            
            return chunks
            
        except Exception as e:
            logger.warning(f"Semantic chunking failed: {e}. Falling back to structural chunking.")
            return segments

    def _structural_chunk(self, segments: List[str]) -> List[str]:
        """
        Apply structure-based chunking without semantic analysis.
        """
        chunks = []
        current_chunk = ""
        
        for segment in segments:
            # Check if adding this segment would exceed max size
            potential_chunk = current_chunk + '\n\n' + segment if current_chunk else segment
            
            if self._count_tokens(potential_chunk) <= self.config.max_chunk_size:
                current_chunk = potential_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = segment
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

    def _apply_size_constraints(self, chunks: List[str]) -> List[str]:
        """
        Ensure chunks meet size requirements and apply overlap strategy.
        """
        final_chunks = []
        
        for chunk in chunks:
            token_count = self._count_tokens(chunk)
            
            # If chunk is too large, split it
            if token_count > self.config.max_chunk_size:
                sub_chunks = self._split_large_chunk(chunk)
                final_chunks.extend(sub_chunks)
            
            # If chunk is too small, try to merge with previous
            elif token_count < self.config.min_chunk_size and final_chunks:
                last_chunk = final_chunks[-1]
                merged = last_chunk + '\n\n' + chunk
                
                if self._count_tokens(merged) <= self.config.max_chunk_size:
                    final_chunks[-1] = merged
                else:
                    final_chunks.append(chunk)
            else:
                final_chunks.append(chunk)
        
        # Apply overlap strategy
        return self._apply_overlap(final_chunks)

    def _split_large_chunk(self, chunk: str) -> List[str]:
        """
        Split a chunk that's too large into smaller chunks.
        """
        # Try splitting by sentences first
        sentences = self._extract_sentences(chunk)
        
        if len(sentences) <= 1:
            # Fallback to character-based splitting
            return self._character_split(chunk)
        
        sub_chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            potential_chunk = current_chunk + ' ' + sentence if current_chunk else sentence
            
            if self._count_tokens(potential_chunk) <= self.config.max_chunk_size:
                current_chunk = potential_chunk
            else:
                if current_chunk:
                    sub_chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            sub_chunks.append(current_chunk.strip())
        
        return sub_chunks

    def _character_split(self, text: str) -> List[str]:
        """
        Fallback character-based splitting for very long chunks.
        """
        # Estimate characters per token (rough approximation)
        chars_per_token = 4
        max_chars = self.config.max_chunk_size * chars_per_token
        
        chunks = []
        for i in range(0, len(text), max_chars):
            chunk = text[i:i + max_chars]
            # Try to break at word boundaries
            if i + max_chars < len(text):
                last_space = chunk.rfind(' ')
                if last_space > max_chars * 0.8:  # Only if we don't lose too much
                    chunk = chunk[:last_space]
            chunks.append(chunk)
        
        return chunks

    def _apply_overlap(self, chunks: List[str]) -> List[str]:
        """
        Apply overlap strategy between chunks.
        """
        if len(chunks) <= 1 or self.config.overlap_strategy == "none":
            return chunks
        
        overlapped_chunks = [chunks[0]]
        
        for i in range(1, len(chunks)):
            current_chunk = chunks[i]
            previous_chunk = chunks[i-1]
            
            if self.config.overlap_strategy == "fixed":
                overlap = self._get_fixed_overlap(previous_chunk, current_chunk)
            elif self.config.overlap_strategy == "semantic" and self.embedder:
                overlap = self._get_semantic_overlap(previous_chunk, current_chunk)
            else:  # adaptive
                overlap = self._get_adaptive_overlap(previous_chunk, current_chunk)
            
            if overlap:
                current_chunk = overlap + '\n\n' + current_chunk
            
            overlapped_chunks.append(current_chunk)
        
        return overlapped_chunks

    def _get_fixed_overlap(self, prev_chunk: str, current_chunk: str) -> str:
        """Get fixed overlap based on chunk_overlap configuration."""
        sentences = self._extract_sentences(prev_chunk)
        overlap_tokens = self.config.chunk_overlap
        
        overlap_text = ""
        for sentence in reversed(sentences):
            potential_overlap = sentence + ' ' + overlap_text if overlap_text else sentence
            if self._count_tokens(potential_overlap) <= overlap_tokens:
                overlap_text = potential_overlap
            else:
                break
        
        return overlap_text.strip()

    def _get_adaptive_overlap(self, prev_chunk: str, current_chunk: str) -> str:
        """Get adaptive overlap based on content similarity."""
        # Simple adaptive strategy: use more overlap for shorter chunks
        chunk_size = self._count_tokens(current_chunk)
        overlap_ratio = max(0.1, min(0.3, 200 / chunk_size))  # 10-30% overlap
        overlap_tokens = int(self.config.chunk_overlap * overlap_ratio)
        
        return self._get_fixed_overlap(prev_chunk, current_chunk)[:overlap_tokens]

    def _get_semantic_overlap(self, prev_chunk: str, current_chunk: str) -> str:
        """Get semantic overlap using embeddings (placeholder for advanced implementation)."""
        # For now, fallback to adaptive overlap
        # Could be enhanced to find semantically relevant overlap
        return self._get_adaptive_overlap(prev_chunk, current_chunk)

    def _extract_sentences(self, text: str) -> List[str]:
        """Extract sentences from text."""
        # Simple sentence splitting (could be enhanced with spaCy or NLTK)
        sentences = re.split(r'[.!?]+\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception:
                pass
        
        # Fallback to word-based estimation
        return len(text.split()) * 1.3  # Rough approximation of subword tokenization

    def _fallback_chunk(self, text: str) -> List[Chunk]:
        """
        Fallback chunking method using simple sentence-based approach.
        """
        logger.info("Using fallback chunking method")
        
        sentences = self._extract_sentences(text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            potential_chunk = current_chunk + ' ' + sentence if current_chunk else sentence
            
            if self._count_tokens(potential_chunk) <= self.config.max_chunk_size:
                current_chunk = potential_chunk
            else:
                if current_chunk:
                    chunks.append(Chunk(
                        text=current_chunk.strip(),
                        token_count=self._count_tokens(current_chunk),
                        sentences=self._extract_sentences(current_chunk)
                    ))
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(Chunk(
                text=current_chunk.strip(),
                token_count=self._count_tokens(current_chunk),
                sentences=self._extract_sentences(current_chunk)
            ))
        
        return chunks

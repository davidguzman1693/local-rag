import re
from typing import List, Tuple
from schemas import Chunk, ChunkMetadata


class RecursiveCharacterChunker:
    """Splits documents into coherent chunks using hierarchical separators.
    
    Tries splitting along natural boundaries:
    1. Paragraphs ("\n\n")
    2. Lines ("\n")
    3. Sentences (". ", "! ", "? ")
    4. Words (" ")
    5. Characters ("")
    
    This preserves semantic context far better than naive fixed-width splitting.
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be strictly less than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", ". ", "! ", "? ", " ", ""]

    def chunk_document(
        self,
        document_id: str,
        filename: str,
        pages: List[Tuple[int, str]],
    ) -> List[Chunk]:
        """Splits multi-page document text into Chunks with attached metadata."""
        all_chunks: List[Chunk] = []
        chunk_idx = 0

        for page_num, page_text in pages:
            raw_chunks = self._split_text(page_text, self.separators)

            for text, start, end in raw_chunks:
                text_clean = text.strip()
                if not text_clean:
                    continue

                metadata = ChunkMetadata(
                    document_id=document_id,
                    source_filename=filename,
                    chunk_index=chunk_idx,
                    char_start=start,
                    char_end=end,
                    page_number=page_num,
                )
                chunk = Chunk(
                    id=f"{document_id}_{chunk_idx}",
                    text=text_clean,
                    metadata=metadata,
                )
                all_chunks.append(chunk)
                chunk_idx += 1

        return all_chunks

    def _split_text(self, text: str, separators: List[str]) -> List[Tuple[str, int, int]]:
        """Recursively splits text until all segments fit within chunk_size, with overlap."""
        final_chunks: List[Tuple[str, int, int]] = []
        
        # Base case
        if len(text) <= self.chunk_size:
            return [(text, 0, len(text))] if text.strip() else []

        # Find the best separator that actually splits the text
        separator = separators[-1]
        for sep in separators:
            if sep == "":
                separator = ""
                break
            if sep in text:
                separator = sep
                break

        # Split on the chosen separator
        if separator:
            splits = text.split(separator)
        else:
            splits = list(text)

        # Merge splits into chunks of size <= chunk_size with overlap
        current_chunk_parts: List[str] = []
        current_len = 0
        current_start_offset = 0

        for split in splits:
            split_len = len(split) + (len(separator) if current_chunk_parts else 0)

            if current_len + split_len > self.chunk_size and current_chunk_parts:
                # Emit current accumulated chunk
                chunk_str = separator.join(current_chunk_parts)
                final_chunks.append((chunk_str, current_start_offset, current_start_offset + len(chunk_str)))

                # Create overlap buffer for the next chunk
                overlap_parts: List[str] = []
                overlap_len = 0
                for part in reversed(current_chunk_parts):
                    if overlap_len + len(part) + len(separator) <= self.chunk_overlap:
                        overlap_parts.insert(0, part)
                        overlap_len += len(part) + len(separator)
                    else:
                        break

                current_start_offset = max(0, current_start_offset + len(chunk_str) - overlap_len)
                current_chunk_parts = list(overlap_parts)
                current_len = overlap_len

            current_chunk_parts.append(split)
            current_len += split_len

        if current_chunk_parts:
            chunk_str = separator.join(current_chunk_parts)
            final_chunks.append((chunk_str, current_start_offset, current_start_offset + len(chunk_str)))

        return final_chunks

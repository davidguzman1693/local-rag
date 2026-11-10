from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    """Metadata attached to an individual text chunk.
    Analogous to a Java Record or DTO.
    """
    document_id: str
    source_filename: str
    chunk_index: int
    char_start: int
    char_end: int
    page_number: Optional[int] = None
    section_title: Optional[str] = None


class Chunk(BaseModel):
    """A granular piece of text indexed for semantic retrieval."""
    id: str = Field(description="Unique chunk ID, typically {doc_id}_{index}")
    text: str = Field(description="The actual chunk text content")
    metadata: ChunkMetadata


class DocumentMetadata(BaseModel):
    """Metadata representing an uploaded/ingested source document."""
    id: str
    filename: str
    file_type: str
    file_size_bytes: int
    chunk_count: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


class IngestResponse(BaseModel):
    """Response returned upon successfully ingesting a document."""
    document_id: str
    filename: str
    chunks_created: int
    message: str


class Citation(BaseModel):
    """Source attribution for answers produced by the RAG system."""
    citation_id: int
    document_id: str
    source_filename: str
    chunk_index: int
    page_number: Optional[int] = None
    snippet: str
    relevance_score: float


class QueryRequest(BaseModel):
    """Input payload for querying the RAG system."""
    query: str = Field(..., min_length=1, description="User's natural language question")
    top_k: Optional[int] = Field(default=None, description="Override default number of chunks to re-rank")
    stream: bool = Field(default=False, description="Whether to stream response tokens")


class QueryResponse(BaseModel):
    """Complete answer produced by the RAG system."""
    query: str
    answer: str
    citations: List[Citation]
    retrieval_time_ms: float
    total_time_ms: float
    model_used: str

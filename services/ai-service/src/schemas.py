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


class ConversationMessage(BaseModel):
    """A single prior turn in a multi-turn conversation."""
    role: str = Field(description="'user' or 'assistant'")
    content: str = Field(description="Message text content")


class QueryRequest(BaseModel):
    """Input payload for querying the RAG system."""
    query: str = Field(..., min_length=1, description="User's natural language question")
    top_k: Optional[int] = Field(default=None, description="Override default number of chunks to re-rank")
    stream: bool = Field(default=False, description="Whether to stream response tokens")
    history: Optional[List[ConversationMessage]] = Field(
        default=None,
        description="Optional prior conversation turns for multi-turn follow-up questions",
    )
    model: Optional[str] = Field(default=None, description="Ollama model override")
    temperature: Optional[float] = Field(default=None, description="Generation temperature override (0.0 to 1.0)")


class ModelDetails(BaseModel):
    parameter_size: Optional[str] = None
    quantization_level: Optional[str] = None
    family: Optional[str] = None


class OllamaModelInfo(BaseModel):
    name: str
    size: int
    modified_at: Optional[str] = None
    details: Optional[ModelDetails] = None


class ModelListResponse(BaseModel):
    models: List[OllamaModelInfo]
    current_default: str


class QueryResponse(BaseModel):
    """Complete answer produced by the RAG system."""
    query: str
    answer: str
    citations: List[Citation]
    retrieval_time_ms: float
    total_time_ms: float
    model_used: str


class RetrievalStageItem(BaseModel):
    """Single scored chunk inside one stage of the retrieval pipeline (for the Retrieval Debugger)."""
    chunk_id: str
    document_id: str
    source_filename: str
    chunk_index: int
    page_number: int = 1
    text: str
    rank: int
    score: float
    dense_rank: Optional[int] = None
    bm25_rank: Optional[int] = None


class SearchDebugResponse(BaseModel):
    """Side-by-side breakdown of all 4 retrieval stages without calling the LLM."""
    query: str
    retrieval_time_ms: float
    dense_results: List[RetrievalStageItem]
    bm25_results: List[RetrievalStageItem]
    rrf_results: List[RetrievalStageItem]
    reranked_results: List[RetrievalStageItem]

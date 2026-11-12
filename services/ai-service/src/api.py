import json
import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from config import settings
from schemas import IngestResponse, ModelListResponse, QueryRequest, QueryResponse, SearchDebugResponse
from service import RagService

router = APIRouter(prefix="/api/v1")

# Service will be injected or initialized during lifespan
_rag_service: RagService = None


def set_rag_service(service: RagService):
    global _rag_service
    _rag_service = service


def get_rag_service() -> RagService:
    if _rag_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG service is not initialized yet.",
        )
    return _rag_service


@router.post("/documents/upload", response_model=IngestResponse)
async def upload_document(file: UploadFile = File(...)):
    """Uploads and ingests a PDF, Markdown, or text document."""
    service = get_rag_service()
    
    # Save uploaded file to data/documents/
    save_path = settings.documents_dir / file.filename
    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {e}",
        )

    try:
        result = service.ingest_file(save_path, original_filename=file.filename)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process document: {e}",
        )


@router.get("/documents")
async def list_documents():
    """Returns a list of all indexed documents and their chunk counts."""
    service = get_rag_service()
    return service.vector_store.get_document_stats()


@router.get("/documents/{document_id}/chunks")
async def get_document_chunks(document_id: str):
    """Retrieves all indexed chunks for a specific document (for visualization)."""
    service = get_rag_service()
    chunks = service.vector_store.get_chunks_by_document(document_id)
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No chunks found for document ID {document_id}",
        )
    return chunks


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Deletes a document and its chunks from the vector store."""
    service = get_rag_service()
    service.vector_store.delete_document(document_id)
    # Refresh BM25 corpus
    all_chunks = service.vector_store.get_all_chunks()
    service.retriever.update_bm25_corpus(all_chunks)
    return {"message": f"Document {document_id} successfully deleted."}


@router.post("/search/debug", response_model=SearchDebugResponse)
async def debug_search(request: QueryRequest):
    """Returns side-by-side Dense Vector, BM25, RRF, and Cross-Encoder Re-ranked results without calling the LLM."""
    service = get_rag_service()
    try:
        return service.debug_retrieve(request.query, top_k=request.top_k)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Debug search failed: {e}",
        )


@router.get("/models", response_model=ModelListResponse)
async def list_models():
    """Lists all available Ollama models installed locally on the host."""
    service = get_rag_service()
    return await service.list_available_models()


@router.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Standard non-streaming question answering with citations."""
    service = get_rag_service()
    try:
        response = await service.answer_query(
            request.query,
            top_k=request.top_k,
            history=request.history,
            model=request.model,
            temperature=request.temperature,
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query execution failed: {e}",
        )


@router.post("/query/stream")
async def query_rag_stream(request: QueryRequest):
    """Server-Sent Events (SSE) streaming endpoint."""
    service = get_rag_service()

    async def event_generator():
        try:
            async for event in service.stream_query(
                request.query,
                top_k=request.top_k,
                history=request.history,
                model=request.model,
                temperature=request.temperature,
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            error_event = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

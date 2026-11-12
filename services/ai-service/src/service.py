import time
import uuid
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional
from chunkers import RecursiveCharacterChunker
from config import settings
from embeddings import EmbeddingService
from loaders import DocumentLoader
from schemas import Citation, IngestResponse, QueryResponse, RetrievalStageItem, SearchDebugResponse
from search import HybridRetriever
from storage import VectorStore
from synthesis import OllamaClient, build_rag_prompt


class RagService:
    """Core RAG pipeline coordinator.
    
    Orchestrates the entire lifecycle:
    1. Ingestion: load -> chunk -> embed -> store in LanceDB & update BM25
    2. Retrieval: vector search + BM25 keyword search -> RRF fusion -> FlashRank rerank
    3. Generation: build grounded prompt -> call Ollama (sync or streaming) -> attach citations
    """

    def __init__(self):
        print(f"Initializing EmbeddingService with {settings.embedding_model_name}...")
        self.embedding_service = EmbeddingService(settings.embedding_model_name)
        
        print(f"Initializing LanceDB VectorStore at {settings.lancedb_uri}...")
        self.vector_store = VectorStore(settings.lancedb_uri, self.embedding_service.dimension)
        
        print(f"Initializing HybridRetriever with {settings.reranker_model_name}...")
        self.retriever = HybridRetriever(settings.reranker_model_name)
        
        # Warm up BM25 index with existing chunks
        all_chunks = self.vector_store.get_all_chunks()
        self.retriever.update_bm25_corpus(all_chunks)

        self.chunker = RecursiveCharacterChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

        self.ollama = OllamaClient(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
        )
        print("RagService initialized successfully!")

    def ingest_file(self, file_path: Path, original_filename: Optional[str] = None) -> IngestResponse:
        """Parses a file, chunks it, generates embeddings, and saves to LanceDB."""
        filename = original_filename or file_path.name
        document_id = str(uuid.uuid4())

        # 1. Load document text
        full_text, pages = DocumentLoader.load_from_file(file_path)

        # 2. Chunk document
        chunks = self.chunker.chunk_document(document_id, filename, pages)
        if not chunks:
            raise ValueError(f"No valid text could be extracted from {filename}")

        # 3. Generate dense embeddings for chunks
        texts = [chunk.text for chunk in chunks]
        embeddings = self.embedding_service.embed_documents(texts)

        # 4. Save to vector store
        self.vector_store.add_chunks(chunks, embeddings)

        # 5. Refresh BM25 index with all chunks
        all_chunks = self.vector_store.get_all_chunks()
        self.retriever.update_bm25_corpus(all_chunks)

        return IngestResponse(
            document_id=document_id,
            filename=filename,
            chunks_created=len(chunks),
            message="Document successfully processed and indexed.",
        )

    def retrieve_context(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Executes full hybrid search and cross-encoder re-ranking."""
        target_k = top_k or settings.rerank_top_k

        # 1. Generate query embedding
        query_vector = self.embedding_service.embed_query(query)

        # 2. Dense vector search
        dense_results = self.vector_store.search_vector(
            query_vector,
            top_k=settings.vector_search_top_k,
        )

        # 3. Hybrid search (Dense + BM25 RRF fusion)
        fused_candidates = self.retriever.hybrid_search(
            query,
            dense_results,
            top_k=settings.vector_search_top_k,
        )

        # 4. Cross-encoder re-ranking
        reranked_chunks = self.retriever.rerank(query, fused_candidates, top_k=target_k)
        return reranked_chunks

    def debug_retrieve(self, query: str, top_k: Optional[int] = None) -> SearchDebugResponse:
        """Executes all 4 retrieval stages and returns intermediate rankings and scores."""
        start_time = time.perf_counter()
        target_k = top_k or settings.rerank_top_k
        candidate_k = max(target_k, settings.vector_search_top_k)

        # Stage 1: Dense Vector Search (LanceDB cosine distance -> similarity = 1 - distance)
        query_vector = self.embedding_service.embed_query(query)
        raw_dense = self.vector_store.search_vector(query_vector, top_k=candidate_k)
        dense_rank_map: Dict[str, int] = {}
        dense_items: List[RetrievalStageItem] = []

        for rank, c in enumerate(raw_dense, start=1):
            cid = c["id"]
            dense_rank_map[cid] = rank
            similarity = max(0.0, 1.0 - float(c.get("_distance", 0.0)))
            dense_items.append(
                RetrievalStageItem(
                    chunk_id=cid,
                    document_id=c.get("document_id", ""),
                    source_filename=c.get("source_filename", "unknown"),
                    chunk_index=c.get("chunk_index", 0),
                    page_number=c.get("page_number", 1),
                    text=c.get("text", ""),
                    rank=rank,
                    score=round(similarity, 4),
                    dense_rank=rank,
                )
            )

        # Stage 2: Sparse BM25 Keyword Search
        raw_bm25 = self.retriever.sparse_search(query, top_k=candidate_k)
        bm25_rank_map: Dict[str, int] = {}
        bm25_items: List[RetrievalStageItem] = []

        for rank, c in enumerate(raw_bm25, start=1):
            cid = c["id"]
            bm25_rank_map[cid] = rank
            bm25_items.append(
                RetrievalStageItem(
                    chunk_id=cid,
                    document_id=c.get("document_id", ""),
                    source_filename=c.get("source_filename", "unknown"),
                    chunk_index=c.get("chunk_index", 0),
                    page_number=c.get("page_number", 1),
                    text=c.get("text", ""),
                    rank=rank,
                    score=round(float(c.get("_bm25_score", 0.0)), 4),
                    bm25_rank=rank,
                )
            )

        # Stage 3: Hybrid Reciprocal Rank Fusion (RRF)
        fused_candidates = self.retriever.hybrid_search(query, raw_dense, top_k=candidate_k)
        rrf_items: List[RetrievalStageItem] = []
        for rank, c in enumerate(fused_candidates, start=1):
            cid = c["id"]
            d_rank = dense_rank_map.get(cid)
            b_rank = bm25_rank_map.get(cid)
            rrf_score = (1.0 / (60 + d_rank) if d_rank else 0.0) + (
                1.0 / (60 + b_rank) if b_rank else 0.0
            )
            rrf_items.append(
                RetrievalStageItem(
                    chunk_id=cid,
                    document_id=c.get("document_id", ""),
                    source_filename=c.get("source_filename", "unknown"),
                    chunk_index=c.get("chunk_index", 0),
                    page_number=c.get("page_number", 1),
                    text=c.get("text", ""),
                    rank=rank,
                    score=round(rrf_score, 4),
                    dense_rank=d_rank,
                    bm25_rank=b_rank,
                )
            )

        # Stage 4: Cross-Encoder Re-Ranking (FlashRank)
        reranked_chunks = self.retriever.rerank(query, fused_candidates, top_k=target_k)
        reranked_items: List[RetrievalStageItem] = []
        for rank, c in enumerate(reranked_chunks, start=1):
            cid = c["id"]
            reranked_items.append(
                RetrievalStageItem(
                    chunk_id=cid,
                    document_id=c.get("document_id", ""),
                    source_filename=c.get("source_filename", "unknown"),
                    chunk_index=c.get("chunk_index", 0),
                    page_number=c.get("page_number", 1),
                    text=c.get("text", ""),
                    rank=rank,
                    score=round(float(c.get("relevance_score", 0.0)), 4),
                    dense_rank=dense_rank_map.get(cid),
                    bm25_rank=bm25_rank_map.get(cid),
                )
            )

        retrieval_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return SearchDebugResponse(
            query=query,
            retrieval_time_ms=retrieval_time_ms,
            dense_results=dense_items[:target_k],
            bm25_results=bm25_items[:target_k],
            rrf_results=rrf_items[:target_k],
            reranked_results=reranked_items,
        )

    async def answer_query(self, query: str, top_k: Optional[int] = None) -> QueryResponse:
        """Runs retrieval + LLM synthesis and returns a completed answer with citations."""
        start_time = time.perf_counter()

        # Retrieve top passages
        context_chunks = self.retrieve_context(query, top_k)
        retrieval_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Build prompt & citations
        prompt, citations = build_rag_prompt(query, context_chunks)

        # Generate answer from Ollama
        answer = await self.ollama.generate(prompt, temperature=settings.temperature)
        total_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return QueryResponse(
            query=query,
            answer=answer,
            citations=citations,
            retrieval_time_ms=retrieval_time_ms,
            total_time_ms=total_time_ms,
            model_used=self.ollama.model,
        )

    async def stream_query(self, query: str, top_k: Optional[int] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Streams generated tokens and yields citations as metadata."""
        context_chunks = self.retrieve_context(query, top_k)
        prompt, citations = build_rag_prompt(query, context_chunks)

        # Yield citations first so the client can render source badges
        yield {
            "type": "citations",
            "citations": [c.model_dump() for c in citations],
        }

        # Stream generated tokens
        async for token in self.ollama.generate_stream(prompt, temperature=settings.temperature):
            yield {
                "type": "token",
                "token": token,
            }

        yield {"type": "done"}

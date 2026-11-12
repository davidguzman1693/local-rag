from collections import defaultdict
from typing import Any, Dict, List, Optional
from flashrank import Ranker, RerankRequest
from rank_bm25 import BM25Okapi
from config import settings


class HybridRetriever:
    """Combines Dense Vector Search and Sparse BM25 Search using Reciprocal Rank Fusion (RRF),
    then re-ranks the top candidates using a Cross-Encoder (FlashRank).
    """

    def __init__(self, reranker_model: str = "ms-marco-TinyBERT-L-2-v2", cache_dir: Optional[str] = None):
        target_cache = cache_dir or str(settings.models_dir)
        self.ranker = Ranker(model_name=reranker_model, cache_dir=target_cache)
        self.bm25_index: Optional[BM25Okapi] = None
        self.corpus_chunks: List[Dict[str, Any]] = []

    def update_bm25_corpus(self, chunks: List[Dict[str, Any]]) -> None:
        """Rebuilds the BM25 index when documents are added or removed."""
        self.corpus_chunks = chunks
        if not chunks:
            self.bm25_index = None
            return

        tokenized_corpus = [chunk["text"].lower().split() for chunk in chunks]
        self.bm25_index = BM25Okapi(tokenized_corpus)

    def sparse_search(self, query: str, top_k: int = 15) -> List[Dict[str, Any]]:
        """Runs standalone BM25 sparse keyword search and attaches _bm25_score."""
        if not self.bm25_index or not self.corpus_chunks:
            return []

        tokenized_query = query.lower().split()
        bm25_scores = self.bm25_index.get_scores(tokenized_query)

        sorted_indices = sorted(
            range(len(bm25_scores)),
            key=lambda i: bm25_scores[i],
            reverse=True,
        )[:top_k]

        results: List[Dict[str, Any]] = []
        for idx in sorted_indices:
            if bm25_scores[idx] <= 0:
                continue
            item = dict(self.corpus_chunks[idx])
            item["_bm25_score"] = float(bm25_scores[idx])
            results.append(item)
        return results

    def hybrid_search(
        self,
        query: str,
        dense_results: List[Dict[str, Any]],
        top_k: int = 15,
        rrf_k: int = 60,
    ) -> List[Dict[str, Any]]:
        """Merges Dense (vector) and Sparse (BM25) search results via Reciprocal Rank Fusion (RRF)."""
        rrf_scores: Dict[str, float] = defaultdict(float)
        chunk_map: Dict[str, Dict[str, Any]] = {}

        # 1. Score dense vector results
        for rank, item in enumerate(dense_results):
            chunk_id = item["id"]
            chunk_map[chunk_id] = item
            rrf_scores[chunk_id] += 1.0 / (rrf_k + rank + 1)

        # 2. Score sparse BM25 results (if index exists)
        if self.bm25_index and self.corpus_chunks:
            tokenized_query = query.lower().split()
            bm25_scores = self.bm25_index.get_scores(tokenized_query)
            
            # Rank candidates by BM25 score
            sorted_indices = sorted(
                range(len(bm25_scores)),
                key=lambda i: bm25_scores[i],
                reverse=True,
            )[:top_k]

            for rank, idx in enumerate(sorted_indices):
                if bm25_scores[idx] <= 0:
                    continue
                item = self.corpus_chunks[idx]
                chunk_id = item["id"]
                chunk_map[chunk_id] = item
                rrf_scores[chunk_id] += 1.0 / (rrf_k + rank + 1)

        # 3. Sort by combined RRF score
        sorted_chunk_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)
        fused_results = [chunk_map[cid] for cid in sorted_chunk_ids[:top_k]]
        return fused_results

    def rerank(self, query: str, candidates: List[Dict[str, Any]], top_k: int = 4) -> List[Dict[str, Any]]:
        """Re-scores candidate chunks with a Cross-Encoder for higher precision."""
        if not candidates:
            return []

        passages = [
            {"id": item["id"], "text": item["text"], "meta": item}
            for item in candidates
        ]

        rerank_request = RerankRequest(query=query, passages=passages)
        ranked_results = self.ranker.rerank(rerank_request)

        # Extract top-k reranked items with their cross-encoder score
        final_results: List[Dict[str, Any]] = []
        for r in ranked_results[:top_k]:
            item = dict(r["meta"])
            item["relevance_score"] = float(r["score"])
            final_results.append(item)

        return final_results

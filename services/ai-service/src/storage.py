from pathlib import Path
from typing import Any, Dict, List, Optional
import lancedb
import pyarrow as pa
from schemas import Chunk


class VectorStore:
    """Manages embedded vector storage and retrieval using LanceDB.
    
    LanceDB stores vectors and metadata in an efficient columnar format directly on disk,
    providing lightning-fast approximate nearest neighbor (ANN) search without running a daemon.
    """

    TABLE_NAME = "document_chunks"

    def __init__(self, db_path: Path, dimension: int):
        self.db_path = db_path
        self.dimension = dimension
        self.db = lancedb.connect(str(self.db_path))
        self._table = self._init_table()

    def _init_table(self):
        """Initializes or retrieves the LanceDB chunks table."""
        schema = pa.schema([
            ("id", pa.string()),
            ("vector", pa.list_(pa.float32(), self.dimension)),
            ("text", pa.string()),
            ("document_id", pa.string()),
            ("source_filename", pa.string()),
            ("chunk_index", pa.int32()),
            ("char_start", pa.int32()),
            ("char_end", pa.int32()),
            ("page_number", pa.int32()),
        ])

        if self.TABLE_NAME in self.db.table_names():
            return self.db.open_table(self.TABLE_NAME)
        else:
            return self.db.create_table(self.TABLE_NAME, schema=schema)

    def add_chunks(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        """Appends new chunks and their corresponding embedding vectors."""
        if not chunks:
            return

        records: List[Dict[str, Any]] = []
        for chunk, embedding in zip(chunks, embeddings):
            records.append({
                "id": chunk.id,
                "vector": embedding,
                "text": chunk.text,
                "document_id": chunk.metadata.document_id,
                "source_filename": chunk.metadata.source_filename,
                "chunk_index": chunk.metadata.chunk_index,
                "char_start": chunk.metadata.char_start,
                "char_end": chunk.metadata.char_end,
                "page_number": chunk.metadata.page_number or 1,
            })

        self._table.add(records)

    def search_vector(self, query_vector: List[float], top_k: int = 10) -> List[Dict[str, Any]]:
        """Performs cosine similarity search against the indexed vectors."""
        if len(self._table) == 0:
            return []

        results = (
            self._table.search(query_vector)
            .metric("cosine")
            .limit(top_k)
            .to_list()
        )
        return results

    def get_all_chunks(self) -> List[Dict[str, Any]]:
        """Retrieves all indexed chunks (used to build the BM25 sparse index)."""
        if len(self._table) == 0:
            return []
        return self._table.to_arrow().to_pylist()

    def get_chunks_by_document(self, document_id: str) -> List[Dict[str, Any]]:
        """Fetches all chunks belonging to a specific document."""
        if len(self._table) == 0:
            return []
        all_chunks = self.get_all_chunks()
        return [c for c in all_chunks if c.get("document_id") == document_id]

    def delete_document(self, document_id: str) -> None:
        """Deletes all chunks associated with a given document ID."""
        if len(self._table) > 0:
            self._table.delete(f"document_id = '{document_id}'")

    def get_document_stats(self) -> List[Dict[str, Any]]:
        """Summarizes distinct documents stored and their chunk counts."""
        if len(self._table) == 0:
            return []

        from collections import defaultdict
        grouped: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"chunk_count": 0, "source_filename": ""})
        for c in self.get_all_chunks():
            doc_id = c["document_id"]
            grouped[doc_id]["document_id"] = doc_id
            grouped[doc_id]["source_filename"] = c.get("source_filename", "unknown")
            grouped[doc_id]["chunk_count"] += 1

        return list(grouped.values())

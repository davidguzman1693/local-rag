# AI Service (Python / FastAPI)

Dedicated AI & Retrieval Engine powering the Local RAG platform.

## Features
- **Document Ingestion**: Supports `.txt`, `.md`, and `.pdf` files.
- **Recursive Chunking**: Hierarchical splitting (`\n\n`, `\n`, sentence, words) with configurable overlap and metadata preservation.
- **Local Dense Embeddings**: Runs `BAAI/bge-small-en-v1.5` locally via **FastEmbed** (ONNX runtime) on CPU/Metal with zero cloud latency or cost.
- **Columnar Vector DB**: Stores vectors and metadata using **LanceDB** embedded on disk.
- **Sparse BM25 Search**: Exact keyword retrieval using `rank-bm25`.
- **Hybrid Retrieval**: Combines Dense + Sparse results with **Reciprocal Rank Fusion (RRF)**.
- **Cross-Encoder Re-ranking**: Uses **FlashRank** (`ms-marco-TinyBERT-L-2-v2`) to re-score candidate passages for precision.
- **Grounded LLM Synthesis**: Async client for local **Ollama** models (`deepseek-r1`, `qwen2.5`, etc.) with strict citation attribution `[1]`, `[2]`.
- **Streaming**: Server-Sent Events (SSE) support for real-time token rendering.

---

## Quickstart

### 1. Run Pipeline Unit Tests
```bash
uv run python tests/test_pipeline.py
```

### 2. Run the FastAPI Server
```bash
uv run python main.py
```
The server will start on `http://127.0.0.1:8000`.
Interactive Swagger UI is available at `http://127.0.0.1:8000/docs`.

---

## API Endpoints

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Health check & model status |
| `POST` | `/api/v1/documents/upload` | Multipart upload (PDF, TXT, MD) & index |
| `GET` | `/api/v1/documents` | List indexed documents & chunk statistics |
| `GET` | `/api/v1/documents/{doc_id}/chunks` | Inspect all chunks for a document (UI visualizer) |
| `DELETE` | `/api/v1/documents/{doc_id}` | Remove document and its vectors |
| `POST` | `/api/v1/query` | Standard question answering with citations |
| `POST` | `/api/v1/query/stream` | Server-Sent Events (SSE) streaming answer |

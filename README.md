# Local RAG: Enterprise Polyglot Architecture

[![Polyglot CI Pipeline](https://github.com/davidguzman1693/local-rag/actions/workflows/ci.yml/badge.svg)](https://github.com/davidguzman1693/local-rag/actions/workflows/ci.yml)

A production-grade, local **Retrieval-Augmented Generation (RAG)** platform designed to demonstrate modern AI Engineering patterns across **Java 21**, **Python 3.13**, and **TypeScript**.

---

## Architecture Overview

```mermaid
flowchart LR
    A["Frontend\n(TypeScript / React)"] <-->|REST & SSE Stream| B["Core Gateway\n(Java 21 / Spring Boot)"]
    B <-->|HTTP / SSE Proxy| C["AI Engine\n(Python / FastAPI)"]
    C <-->|Local Embeddings\n& Vectors| D[("LanceDB +\nBM25 Index")]
    C <-->|Local LLM\nInference| E["Ollama\n(DeepSeek-R1 / Qwen)"]
```

### Modules

1. **`services/ai-service/` (Python 3.13 + `uv`)**
   - Ingestion, hierarchical recursive chunking, FastEmbed (ONNX) local embeddings.
   - LanceDB embedded columnar vector database + BM25 keyword index.
   - Reciprocal Rank Fusion (RRF) hybrid search + FlashRank Cross-Encoder re-ranking.
   - Grounded prompt construction and Ollama LLM streaming with bracketed citations.

2. **`services/core-service/` (Java 21 + Spring Boot 3)**
   - Enterprise API gateway and orchestration layer.
   - Document lifecycle & metadata persistence, conversational session memory.
   - Non-blocking Server-Sent Events (SSE) streaming proxy and fault-tolerant HTTP client.

3. **`services/web-ui/` (TypeScript + React / Vite)**
   - Conversational chat interface with real-time token streaming.
   - Document manager with drag-and-drop upload.
   - Interactive Chunk Inspector: visual breakdown of how documents were parsed and scored.
   - Clickable citation pills with exact source snippet highlights.

---

## Getting Started

### Prerequisites
- Python >= 3.13 and [`uv`](https://docs.astral.sh/uv/)
- Java >= 21 and Maven
- Node.js >= 20 and npm
- [Ollama](https://ollama.com/) running locally (`ollama run deepseek-r1:latest` or `qwen2.5:7b`)

### Quickstart (One-Command Orchestration)
Use the root `Makefile` to run, test, or inspect all 3 services at once:
```bash
make start    # Starts ai-service (:8000), core-service (:8080), and web-ui (:5173)
make status   # Checks health of Ollama, AI Service, Core Gateway, and Web UI
make logs     # Tails logs from all 3 services (.logs/*.log)
make test     # Runs unit tests & build checks across Python, Java, and TypeScript
make stop     # Stops all background services
```

Or run everything in containers via **Docker Compose** (with host Ollama):
```bash
make docker-up
# Stop with: make docker-down
```

---

### Manual Per-Service Commands

#### 1. Test the AI Service Pipeline
```bash
cd services/ai-service
uv run python tests/test_pipeline.py
```

### 2. Start the AI Service
```bash
cd services/ai-service
uv run python main.py
# Running on http://127.0.0.1:8000 (Swagger docs at /docs)
```

### 3. Test & Start the Core Gateway Service (Java 21 / Spring Boot)
```bash
cd services/core-service
./mvnw test
./mvnw spring-boot:run
# Running on http://127.0.0.1:8080
```

### 4. Start the Web UI (TypeScript + React / Vite)
```bash
cd services/web-ui
npm install
npm run dev
# Running on http://localhost:5173
```

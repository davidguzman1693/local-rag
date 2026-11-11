# Core Service (Java 21 / Spring Boot 3)

Enterprise API Gateway and Orchestration Layer for the Local RAG platform.

## Responsibilities
- **API Gateway**: Unified entrypoint (`http://localhost:8080`) for the frontend UI, proxying requests to the Python AI Engine (`http://localhost:8000`).
- **Conversational Session Memory**: Manages multi-turn chat sessions (`ChatSessionService`), automatically capturing both synchronous answers and real-time streamed tokens + citations.
- **Document Lifecycle Enrichment**: Forwards multipart document uploads (`.pdf`, `.md`, `.txt`), tracks upload metadata (`file_size_bytes`, `uploaded_at`), and exposes chunk inspection endpoints for the UI visualizer.
- **Non-blocking SSE Proxy**: Uses Spring WebFlux `WebClient` to stream Server-Sent Events (`text/event-stream`) from Ollama/FastAPI directly to the browser without blocking servlet threads.

---

## Quickstart

### 1. Run Unit & Integration Tests
```bash
cd services/core-service
./mvnw test
```

### 2. Start the Gateway Server
```bash
cd services/core-service
./mvnw spring-boot:run
```
The gateway runs on `http://127.0.0.1:8080` and connects to `ai-service` at `http://127.0.0.1:8000` (configurable via `AI_SERVICE_URL`).

---

## API Endpoints

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Aggregated health check (Gateway + Python AI Engine) |
| `POST` | `/api/v1/documents/upload` | Multipart file upload forwarded to AI Engine |
| `GET` | `/api/v1/documents` | List indexed documents with size & upload metadata |
| `GET` | `/api/v1/documents/{documentId}/chunks` | Inspect all chunks and embeddings for a document |
| `DELETE` | `/api/v1/documents/{documentId}` | Delete a document and its indexed chunks |
| `POST` | `/api/v1/query` | Question answering with session tracking and citations |
| `POST` | `/api/v1/query/stream` | Non-blocking SSE token & citation stream |
| `GET` | `/api/v1/sessions` | List all conversation sessions |
| `POST` | `/api/v1/sessions` | Create a new conversation session |
| `GET` | `/api/v1/sessions/{sessionId}` | Retrieve full message & citation history for a session |
| `DELETE` | `/api/v1/sessions/{sessionId}` | Delete a conversation session |


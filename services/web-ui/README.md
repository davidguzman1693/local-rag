# Web UI (TypeScript + React / Vite)

Interactive frontend workspace for the Local RAG platform.

## Architecture (Designed for Java Developers)
The codebase is intentionally structured into 5 flat, easy-to-read files:

1. **`src/types.ts` (DTOs)**: TypeScript `interface` definitions matching the JSON responses from `core-service` (`:8080`). Equivalent to `com.localrag.core.model` Java `record`s.
2. **`src/api.ts` (Gateway Client)**: Plain `async/await` `fetch` functions plus a streaming Server-Sent Events (SSE) reader (`streamRagQuery`). Equivalent to `AiEngineClient.java`.
3. **`src/App.tsx` (State & Layout Coordinator)**: Manages sidebar state (Documents, Sessions, System Health) and coordinates SSE streaming updates.
4. **`src/components/ChatPanel.tsx` (Streaming Chat & Citations)**: Renders user/assistant messages, separates `<think>...</think>` reasoning blocks, and renders clickable citation pills (`[1]`, `[2]`).
5. **`src/components/ChunkInspectorModal.tsx` (Chunk Visualizer)**: Displays how a document was split into overlapping chunks (`[char_start : char_end]`) along with its 384-dim vector preview.

---

## Quickstart

```bash
cd services/web-ui
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.


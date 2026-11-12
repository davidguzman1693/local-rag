import type {
  ChatSession,
  ChunkRecord,
  DocumentSummary,
  IngestResponse,
  StreamEvent,
  SystemHealth,
} from "./types";

/**
 * Base URL of the Java Spring Boot Gateway (core-service).
 * Can be overridden with VITE_GATEWAY_URL environment variable.
 */
const GATEWAY_BASE_URL =
  import.meta.env.VITE_GATEWAY_URL || "http://localhost:8080";

/**
 * HTTP Client talking to core-service (:8080).
 *
 * Java analogy: This file is the frontend equivalent of `AiEngineClient.java`.
 * In TypeScript/JavaScript, `Promise<T>` is equivalent to Java's `CompletableFuture<T>`,
 * and `async / await` lets you write non-blocking HTTP calls that read like synchronous code.
 */

export async function fetchHealth(): Promise<SystemHealth> {
  const response = await fetch(`${GATEWAY_BASE_URL}/api/v1/health`);
  if (!response.ok) {
    throw new Error(`Health check failed (${response.status})`);
  }
  return response.json();
}

export async function fetchDocuments(): Promise<DocumentSummary[]> {
  const response = await fetch(`${GATEWAY_BASE_URL}/api/v1/documents`);
  if (!response.ok) {
    throw new Error(`Failed to load documents (${response.status})`);
  }
  return response.json();
}

export async function uploadDocument(file: File): Promise<IngestResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${GATEWAY_BASE_URL}/api/v1/documents/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`Upload failed: ${errText}`);
  }
  return response.json();
}

export async function deleteDocument(documentId: string): Promise<void> {
  const response = await fetch(
    `${GATEWAY_BASE_URL}/api/v1/documents/${documentId}`,
    { method: "DELETE" }
  );
  if (!response.ok) {
    throw new Error(`Failed to delete document (${response.status})`);
  }
}

export async function fetchDocumentChunks(
  documentId: string
): Promise<ChunkRecord[]> {
  const response = await fetch(
    `${GATEWAY_BASE_URL}/api/v1/documents/${documentId}/chunks`
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch chunks (${response.status})`);
  }
  return response.json();
}

export async function fetchSessions(): Promise<ChatSession[]> {
  const response = await fetch(`${GATEWAY_BASE_URL}/api/v1/sessions`);
  if (!response.ok) {
    throw new Error(`Failed to fetch sessions (${response.status})`);
  }
  return response.json();
}

export async function fetchSessionById(sessionId: string): Promise<ChatSession> {
  const response = await fetch(
    `${GATEWAY_BASE_URL}/api/v1/sessions/${sessionId}`
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch session (${response.status})`);
  }
  return response.json();
}

export async function deleteSession(sessionId: string): Promise<void> {
  const response = await fetch(
    `${GATEWAY_BASE_URL}/api/v1/sessions/${sessionId}`,
    { method: "DELETE" }
  );
  if (!response.ok) {
    throw new Error(`Failed to delete session (${response.status})`);
  }
}

/**
 * Streams a RAG answer over Server-Sent Events (SSE) from POST /api/v1/query/stream.
 *
 * Java analogy: This is like subscribing to a `Flux<ServerSentEvent<String>>` with `.subscribe(onEvent)`.
 * Each `data: {...}` line sent by Spring Boot is parsed as JSON and passed to `onEvent`.
 */
export async function streamRagQuery(
  query: string,
  sessionId: string | null,
  onEvent: (event: StreamEvent) => void
): Promise<void> {
  const response = await fetch(`${GATEWAY_BASE_URL}/api/v1/query/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({
      query,
      top_k: 4,
      stream: true,
      session_id: sessionId,
    }),
  });

  if (!response.ok || !response.body) {
    const errText = await response.text();
    throw new Error(`Stream request failed (${response.status}): ${errText}`);
  }

  // Read the raw HTTP response stream chunk by chunk
  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // SSE messages are separated by newlines; process every complete line in the buffer
    const lines = buffer.split("\n");
    buffer = lines.pop() || ""; // Keep any incomplete trailing line for the next read

    for (const rawLine of lines) {
      const line = rawLine.trim();
      if (!line.startsWith("data:")) continue;

      const jsonStr = line.slice("data:".length).trim();
      if (!jsonStr) continue;

      try {
        const parsed = JSON.parse(jsonStr) as StreamEvent;
        onEvent(parsed);
      } catch {
        // Ignore non-JSON keepalive comments
      }
    }
  }
}


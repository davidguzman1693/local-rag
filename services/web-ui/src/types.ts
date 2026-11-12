/**
 * Data Transfer Objects (DTOs) matching the JSON payloads from Java core-service (:8080).
 *
 * In Java, these are your `record` classes in `com.localrag.core.model`.
 * In TypeScript, `interface` defines the shape of an object at compile time (zero runtime overhead).
 */

export interface Citation {
  citation_id: number;
  document_id: string;
  source_filename: string;
  chunk_index: number;
  page_number?: number;
  snippet: string;
  relevance_score: number;
}

export interface DocumentSummary {
  document_id: string;
  source_filename: string;
  chunk_count: number;
  file_size_bytes?: number | null;
  uploaded_at?: string | null;
}

export interface ChunkRecord {
  id: string;
  text: string;
  document_id: string;
  source_filename: string;
  chunk_index: number;
  char_start: number;
  char_end: number;
  page_number: number;
  vector?: number[];
}

export interface IngestResponse {
  document_id: string;
  filename: string;
  chunks_created: number;
  message: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant"; // Union type: like an inline Java enum of allowed string values
  content: string;
  citations: Citation[];
  timestamp: string;
}

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
}

export interface SystemHealth {
  status: string;
  gateway: string;
  active_sessions: number;
  ai_engine?: {
    status?: string;
    embedding_model?: string;
    reranker_model?: string;
    ollama_model?: string;
  };
}

/**
 * Discriminated Union for Server-Sent Events (SSE) emitted by POST /api/v1/query/stream.
 * Think of this like a Java 21 `sealed interface` where `"type"` tells the compiler which fields exist.
 */
export type StreamEvent =
  | { type: "session"; session_id: string }
  | { type: "citations"; citations: Citation[] }
  | { type: "token"; token: string }
  | { type: "done" }
  | { type: "error"; message: string };

export interface RetrievalStageItem {
  chunk_id: string;
  document_id: string;
  source_filename: string;
  chunk_index: number;
  page_number: number;
  text: string;
  rank: number;
  score: number;
  dense_rank?: number | null;
  bm25_rank?: number | null;
}

export interface SearchDebugResponse {
  query: string;
  retrieval_time_ms: number;
  dense_results: RetrievalStageItem[];
  bm25_results: RetrievalStageItem[];
  rrf_results: RetrievalStageItem[];
  reranked_results: RetrievalStageItem[];
}


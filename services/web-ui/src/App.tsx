import { useEffect, useState, type ChangeEvent } from "react";
import {
  deleteDocument,
  deleteSession,
  fetchAvailableModels,
  fetchDocumentChunks,
  fetchDocuments,
  fetchHealth,
  fetchSessionById,
  fetchSessions,
  streamRagQuery,
  uploadDocument,
} from "./api";
import { ChatPanel } from "./components/ChatPanel";
import { ChunkInspectorModal } from "./components/ChunkInspectorModal";
import { RetrievalDebugger } from "./components/RetrievalDebugger";
import type {
  ChatMessage,
  ChatSession,
  ChunkRecord,
  Citation,
  DocumentSummary,
  OllamaModelInfo,
  SystemHealth,
} from "./types";
import "./App.css";

export function App() {
  // 1. System & Sidebar State
  const [activeTab, setActiveTab] = useState<"chat" | "debugger">("chat");
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  // 2. Model & Generation Controls
  const [models, setModels] = useState<OllamaModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [temperature, setTemperature] = useState<number>(0.2);

  // 3. Loading & Error State
  const [isUploading, setIsUploading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [errorBanner, setErrorBanner] = useState<string | null>(null);

  // 4. Chunk Inspector Modal State
  const [inspectedDoc, setInspectedDoc] = useState<DocumentSummary | null>(
    null
  );
  const [inspectedChunks, setInspectedChunks] = useState<ChunkRecord[]>([]);
  const [loadingChunks, setLoadingChunks] = useState(false);

  /**
   * `useEffect` with an empty dependency array `[]` runs once on startup
   * (equivalent to `@PostConstruct` in Spring Boot).
   */
  useEffect(() => {
    refreshAll();
  }, []);

  async function refreshAll() {
    try {
      const [healthData, docsData, sessionsData, modelsData] = await Promise.all([
        fetchHealth(),
        fetchDocuments(),
        fetchSessions(),
        fetchAvailableModels(),
      ]);
      setHealth(healthData);
      setDocuments(docsData);
      setSessions(sessionsData);
      setModels(modelsData.models);

      // Default the selected model to the server's current default if not set
      setSelectedModel((prev) => {
        if (prev && modelsData.models.some((m) => m.name === prev)) {
          return prev;
        }
        return modelsData.current_default || (modelsData.models[0]?.name ?? "");
      });

      if (!activeSessionId && sessionsData.length > 0) {
        setActiveSessionId(sessionsData[0].id);
        setMessages(sessionsData[0].messages);
      }
      setErrorBanner(null);
    } catch (err) {
      setErrorBanner(
        err instanceof Error
          ? `${err.message} (Retrying in 2s...)`
          : "Could not connect to core-service (:8080) — retrying..."
      );
      setTimeout(() => {
        refreshAll();
      }, 2000);
    }
  }

  async function handleFileUpload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setErrorBanner(null);
    try {
      await uploadDocument(file);
      const updatedDocs = await fetchDocuments();
      setDocuments(updatedDocs);
    } catch (err) {
      setErrorBanner(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsUploading(false);
      e.target.value = ""; // Reset file input
    }
  }

  async function handleDeleteDocument(docId: string) {
    try {
      await deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.document_id !== docId));
    } catch (err) {
      setErrorBanner(
        err instanceof Error ? err.message : "Failed to delete document"
      );
    }
  }

  async function handleInspectChunks(doc: DocumentSummary) {
    setInspectedDoc(doc);
    setInspectedChunks([]);
    setLoadingChunks(true);
    try {
      const chunks = await fetchDocumentChunks(doc.document_id);
      setInspectedChunks(chunks);
    } catch (err) {
      setErrorBanner(
        err instanceof Error ? err.message : "Failed to load chunks"
      );
    } finally {
      setLoadingChunks(false);
    }
  }

  async function handleSelectSession(sessionId: string) {
    try {
      const fullSession = await fetchSessionById(sessionId);
      setActiveSessionId(fullSession.id);
      setMessages(fullSession.messages);
    } catch (err) {
      setErrorBanner(
        err instanceof Error ? err.message : "Failed to load session"
      );
    }
  }

  function handleNewChat() {
    setActiveSessionId(null);
    setMessages([]);
  }

  async function handleDeleteSession(sessionId: string) {
    try {
      await deleteSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (activeSessionId === sessionId) {
        handleNewChat();
      }
    } catch (err) {
      setErrorBanner(
        err instanceof Error ? err.message : "Failed to delete session"
      );
    }
  }

  async function handleSendMessage(query: string) {
    setErrorBanner(null);
    setIsStreaming(true);

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: query,
      citations: [],
      timestamp: new Date().toISOString(),
    };

    const assistantMsgId = `assistant-${Date.now()}`;
    const placeholderAssistantMsg: ChatMessage = {
      id: assistantMsgId,
      role: "assistant",
      content: "",
      citations: [],
      timestamp: new Date().toISOString(),
      model: selectedModel || health?.ai_engine?.ollama_model,
      temperature: temperature,
    };

    // Optimistically add both the user message and an empty assistant bubble to the screen
    setMessages((prev) => [...prev, userMsg, placeholderAssistantMsg]);

    let accumulatedText = "";
    let latestCitations: Citation[] = [];

    try {
      await streamRagQuery(
        query,
        activeSessionId,
        {
          model: selectedModel || undefined,
          temperature: temperature,
        },
        (event) => {
          if (event.type === "session") {
            setActiveSessionId(event.session_id);
          } else if (event.type === "citations") {
            latestCitations = event.citations;
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsgId ? { ...m, citations: latestCitations } : m
              )
            );
          } else if (event.type === "token") {
            accumulatedText += event.token;
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsgId ? { ...m, content: accumulatedText } : m
              )
            );
          } else if (event.type === "error") {
            setErrorBanner(event.message);
          }
        }
      );

      // Refresh session list so the sidebar reflects the newly saved exchange
      const updatedSessions = await fetchSessions();
      setSessions(updatedSessions);
    } catch (err) {
      setErrorBanner(err instanceof Error ? err.message : "Query failed");
    } finally {
      setIsStreaming(false);
    }
  }

  return (
    <div className="app-shell">
      {/* Top Header */}
      <header className="top-bar">
        <div className="brand">
          <span className="brand-dot" />
          <h1>Local RAG</h1>
          <span className="brand-tag">Java 21 &bull; Python 3.13 &bull; TypeScript</span>
        </div>

        <div className="mode-tabs">
          <button
            type="button"
            className={`mode-tab ${activeTab === "chat" ? "mode-tab-active" : ""}`}
            onClick={() => setActiveTab("chat")}
          >
            Chat Workspace
          </button>
          <button
            type="button"
            className={`mode-tab ${
              activeTab === "debugger" ? "mode-tab-active" : ""
            }`}
            onClick={() => setActiveTab("debugger")}
          >
            Retrieval Debugger
          </button>
        </div>

        {/* Dynamic Model Selector & Sampling Temperature Controls */}
        <div className="model-controls">
          <label className="model-control-group" title="Select synthesis model from installed Ollama models">
            <span className="control-label">Model:</span>
            <select
              className="select-model"
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              disabled={models.length === 0}
            >
              {models.length === 0 ? (
                <option value="">No models found</option>
              ) : (
                models.map((m) => (
                  <option key={m.name} value={m.name}>
                    {m.name} {m.details?.parameter_size ? `(${m.details.parameter_size})` : ""}
                  </option>
                ))
              )}
            </select>
          </label>

          <label className="model-control-group" title="Sampling temperature: 0.0 is deterministic/factual, 1.0 is creative">
            <span className="control-label">Temp: {temperature.toFixed(2)}</span>
            <input
              type="range"
              className="temp-slider"
              min="0.0"
              max="1.0"
              step="0.05"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
            />
          </label>
        </div>

        <div className="status-pills">
          <span
            className={`status-badge ${
              health?.status === "healthy" ? "status-ok" : "status-warn"
            }`}
          >
            Gateway: {health?.status ?? "connecting..."}
          </span>
          <button type="button" className="btn-secondary" onClick={refreshAll}>
            Refresh
          </button>
        </div>
      </header>

      {errorBanner && (
        <div className="error-banner">
          <span>{errorBanner}</span>
          <button type="button" onClick={() => setErrorBanner(null)}>
            Dismiss
          </button>
        </div>
      )}

      {/* Main Two-Column Workspace */}
      <div className="workspace">
        {/* Left Sidebar: Documents & Sessions */}
        <aside className="sidebar">
          {/* Indexed Documents Section */}
          <section className="sidebar-section">
            <div className="section-header">
              <h2>Documents ({documents.length})</h2>
              <label className="upload-btn">
                {isUploading ? "Indexing..." : "+ Upload"}
                <input
                  type="file"
                  accept=".pdf,.md,.txt,.markdown"
                  onChange={handleFileUpload}
                  disabled={isUploading}
                  hidden
                />
              </label>
            </div>

            {documents.length === 0 ? (
              <p className="muted-note">
                No documents indexed yet. Upload a <code>.md</code>,{" "}
                <code>.txt</code>, or <code>.pdf</code> file.
              </p>
            ) : (
              <ul className="item-list">
                {documents.map((doc) => (
                  <li key={doc.document_id} className="item-row">
                    <div className="item-main">
                      <span className="item-title" title={doc.source_filename}>
                        {doc.source_filename}
                      </span>
                      <span className="item-sub">
                        {doc.chunk_count} chunks
                      </span>
                    </div>
                    <div className="item-actions">
                      <button
                        type="button"
                        className="btn-mini"
                        title="Inspect how this document was chunked and embedded"
                        onClick={() => handleInspectChunks(doc)}
                      >
                        Chunks
                      </button>
                      <button
                        type="button"
                        className="btn-mini btn-danger"
                        title="Delete document from LanceDB"
                        onClick={() => handleDeleteDocument(doc.document_id)}
                      >
                        &times;
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {/* Chat Sessions Section */}
          <section className="sidebar-section">
            <div className="section-header">
              <h2>Sessions ({sessions.length})</h2>
              <button
                type="button"
                className="btn-mini"
                onClick={handleNewChat}
              >
                + New Chat
              </button>
            </div>

            {sessions.length === 0 ? (
              <p className="muted-note">No saved sessions yet.</p>
            ) : (
              <ul className="item-list">
                {sessions.map((s) => (
                  <li
                    key={s.id}
                    className={`item-row clickable ${
                      activeSessionId === s.id ? "item-row-active" : ""
                    }`}
                    onClick={() => handleSelectSession(s.id)}
                  >
                    <div className="item-main">
                      <span className="item-title">{s.title}</span>
                      <span className="item-sub">
                        {s.messages.length} messages
                      </span>
                    </div>
                    <button
                      type="button"
                      className="btn-mini btn-danger"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteSession(s.id);
                      }}
                    >
                      &times;
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </aside>

        {/* Right Main Area: Streaming RAG Chat or Retrieval Debugger */}
        <main className="main-panel">
          {activeTab === "chat" ? (
            <ChatPanel
              messages={messages}
              isStreaming={isStreaming}
              onSendMessage={handleSendMessage}
              selectedModel={selectedModel}
              temperature={temperature}
            />
          ) : (
            <RetrievalDebugger />
          )}
        </main>
      </div>

      {/* Chunk Inspector Modal */}
      {inspectedDoc && (
        <ChunkInspectorModal
          document={inspectedDoc}
          chunks={inspectedChunks}
          loading={loadingChunks}
          onClose={() => setInspectedDoc(null)}
        />
      )}
    </div>
  );
}


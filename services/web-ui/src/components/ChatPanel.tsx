import { useState, type FormEvent } from "react";
import type { ChatMessage, Citation } from "../types";

interface ChatPanelProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  onSendMessage: (query: string) => void;
  selectedModel?: string;
  temperature?: number;
}

/**
 * Helper to separate DeepSeek-R1's `<think>...</think>` chain-of-thought from the final answer.
 */
function parseThinkAndAnswer(rawContent: string): {
  thought: string | null;
  answer: string;
} {
  const openTag = "<think>";
  const closeTag = "</think>";

  if (!rawContent.includes(openTag)) {
    return { thought: null, answer: rawContent };
  }

  const startIdx = rawContent.indexOf(openTag) + openTag.length;
  const endIdx = rawContent.indexOf(closeTag);

  // Still inside <think> block while tokens are streaming
  if (endIdx === -1) {
    return {
      thought: rawContent.slice(startIdx).trim(),
      answer: "",
    };
  }

  const thought = rawContent.slice(startIdx, endIdx).trim();
  const answer = rawContent.slice(endIdx + closeTag.length).trim();
  return { thought: thought || null, answer };
}

export function ChatPanel({
  messages,
  isStreaming,
  onSendMessage,
  selectedModel,
  temperature,
}: ChatPanelProps) {
  // React state (`useState`): whenever `setInput` is called, React re-renders this component.
  const [input, setInput] = useState("");
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(
    null
  );

  function handleSubmit(e: FormEvent) {
    e.preventDefault(); // Prevent browser from doing a full-page form reload
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;
    setInput("");
    onSendMessage(trimmed);
  }

  return (
    <div className="chat-container">
      {/* Message List */}
      <div className="messages-scroll">
        {messages.length === 0 ? (
          <div className="empty-chat">
            <h2>Ask a question about your indexed documents</h2>
            <p>
              Every answer is grounded in LanceDB + BM25 hybrid retrieval,
              re-ranked by FlashRank, and streamed live from Ollama with source
              citations.
            </p>
            <div className="suggestion-chips">
              <button
                type="button"
                className="chip"
                onClick={() =>
                  onSendMessage("How does the event loop work in Python asyncio?")
                }
              >
                How does the event loop work in Python asyncio?
              </button>
              <button
                type="button"
                className="chip"
                onClick={() =>
                  onSendMessage(
                    "What is the difference between coroutines and tasks?"
                  )
                }
              >
                What is the difference between coroutines and tasks?
              </button>
            </div>
          </div>
        ) : (
          messages.map((msg) => {
            const { thought, answer } =
              msg.role === "assistant"
                ? parseThinkAndAnswer(msg.content)
                : { thought: null, answer: msg.content };

            return (
              <div
                key={msg.id}
                className={`message-bubble ${
                  msg.role === "user" ? "message-user" : "message-assistant"
                }`}
              >
                <div className="message-role">
                  {msg.role === "user" ? (
                    "You"
                  ) : (
                    <span className="role-with-meta">
                      <span>RAG Assistant</span>
                      {msg.model && (
                        <span
                          className="model-badge-inline"
                          title={`Synthesized with ${msg.model} (temperature: ${
                            msg.temperature !== undefined ? msg.temperature : "default"
                          })`}
                        >
                          {msg.model}
                          {msg.temperature !== undefined
                            ? ` · T=${msg.temperature.toFixed(2)}`
                            : ""}
                        </span>
                      )}
                    </span>
                  )}
                </div>

                {/* Collapsible reasoning block for reasoning models like DeepSeek-R1 */}
                {thought && (
                  <details className="think-block">
                    <summary>Model Reasoning (&lt;think&gt;)</summary>
                    <pre>{thought}</pre>
                  </details>
                )}

                <div className="message-text">
                  {answer || (isStreaming ? "Thinking..." : "")}
                </div>

                {/* Clickable Citation Pills */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="citations-bar">
                    <span className="citations-label">Sources:</span>
                    {msg.citations.map((cit) => {
                      const isSelected =
                        selectedCitation?.citation_id === cit.citation_id &&
                        selectedCitation?.document_id === cit.document_id &&
                        selectedCitation?.chunk_index === cit.chunk_index;

                      return (
                        <button
                          key={`${cit.document_id}_${cit.chunk_index}_${cit.citation_id}`}
                          type="button"
                          className={`citation-pill ${
                            isSelected ? "citation-pill-active" : ""
                          }`}
                          onClick={() =>
                            setSelectedCitation(isSelected ? null : cit)
                          }
                        >
                          [{cit.citation_id}] {cit.source_filename} (p.
                          {cit.page_number ?? 1} &bull;{" "}
                          {cit.relevance_score.toFixed(2)})
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Expanded Citation Snippet Drawer */}
      {selectedCitation && (
        <div className="citation-drawer">
          <div className="citation-drawer-header">
            <strong>
              [{selectedCitation.citation_id}] {selectedCitation.source_filename}
            </strong>
            <span>
              Chunk #{selectedCitation.chunk_index} &bull; Page{" "}
              {selectedCitation.page_number ?? 1} &bull; FlashRank Score:{" "}
              {selectedCitation.relevance_score.toFixed(4)}
            </span>
            <button
              type="button"
              className="btn-text"
              onClick={() => setSelectedCitation(null)}
            >
              Dismiss
            </button>
          </div>
          <p className="citation-snippet">{selectedCitation.snippet}</p>
        </div>
      )}

      {/* Question Input Bar */}
      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          className="chat-input"
          placeholder={
            selectedModel
              ? `Ask a question using ${selectedModel} (T=${temperature?.toFixed(2) ?? "0.20"})...`
              : "Ask a question about your documents..."
          }
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isStreaming}
        />
        <button
          type="submit"
          className="btn-primary"
          disabled={isStreaming || !input.trim()}
        >
          {isStreaming ? "Streaming..." : "Ask"}
        </button>
      </form>
    </div>
  );
}


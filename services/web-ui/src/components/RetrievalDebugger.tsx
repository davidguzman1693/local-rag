import { useState, type FormEvent } from "react";
import { debugRetrieval } from "../api";
import type { RetrievalStageItem, SearchDebugResponse } from "../types";

export function RetrievalDebugger() {
  const [query, setQuery] = useState(
    "How does the event loop work in Python asyncio?"
  );
  const [topK, setTopK] = useState(4);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SearchDebugResponse | null>(null);
  const [highlightedChunkId, setHighlightedChunkId] = useState<string | null>(
    null
  );

  async function runDebugSearch(e?: FormEvent) {
    if (e) e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;

    setLoading(true);
    setError(null);
    try {
      const data = await debugRetrieval(trimmed, topK);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Debug search failed");
    } finally {
      setLoading(false);
    }
  }

  function renderStageColumn(
    title: string,
    subtitle: string,
    scoreLabel: string,
    items: RetrievalStageItem[]
  ) {
    return (
      <div className="debug-column">
        <div className="debug-column-header">
          <h3>{title}</h3>
          <p>{subtitle}</p>
        </div>

        <div className="debug-cards">
          {items.length === 0 ? (
            <div className="muted-note">No matches in this stage.</div>
          ) : (
            items.map((item) => {
              const isHighlighted = highlightedChunkId === item.chunk_id;
              return (
                <div
                  key={`${title}-${item.chunk_id}`}
                  className={`debug-card ${
                    isHighlighted ? "debug-card-highlighted" : ""
                  }`}
                  onMouseEnter={() => setHighlightedChunkId(item.chunk_id)}
                  onMouseLeave={() => setHighlightedChunkId(null)}
                >
                  <div className="debug-card-top">
                    <span className="badge">#{item.rank}</span>
                    <span className="debug-score">
                      {scoreLabel}: <strong>{item.score.toFixed(4)}</strong>
                    </span>
                  </div>

                  <div className="debug-card-meta">
                    <span>
                      {item.source_filename} &bull; Chunk #{item.chunk_index}
                    </span>
                    <div className="debug-rank-pills">
                      {item.dense_rank != null && (
                        <span className="rank-pill">
                          Vec #{item.dense_rank}
                        </span>
                      )}
                      {item.bm25_rank != null && (
                        <span className="rank-pill">
                          BM25 #{item.bm25_rank}
                        </span>
                      )}
                    </div>
                  </div>

                  <p className="debug-card-text">{item.text}</p>
                </div>
              );
            })
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="debugger-container">
      {/* Top Search Bar */}
      <form className="debugger-toolbar" onSubmit={runDebugSearch}>
        <input
          type="text"
          className="chat-input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter a search query to inspect all 4 retrieval stages (no LLM call)..."
        />
        <label className="topk-label">
          Top-K:
          <select
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
            className="topk-select"
          >
            <option value={3}>3</option>
            <option value={4}>4</option>
            <option value={6}>6</option>
            <option value={10}>10</option>
          </select>
        </label>
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? "Running..." : "Inspect Retrieval"}
        </button>
      </form>

      {error && <div className="error-banner">{error}</div>}

      {!result ? (
        <div className="empty-chat">
          <h2>Retrieval Debugger &amp; Search Playground</h2>
          <p>
            Click <strong>Inspect Retrieval</strong> above to run your query
            through LanceDB Vector Search, BM25 Keyword Search, Reciprocal Rank
            Fusion (RRF), and FlashRank Cross-Encoder Re-ranking side by side in
            milliseconds—without calling Ollama.
          </p>
          <p className="muted-note">
            Tip: Hover over any chunk card to highlight that exact chunk across
            all 4 pipeline stages and watch how its rank changes!
          </p>
        </div>
      ) : (
        <>
          <div className="debugger-summary-bar">
            <span>
              Query: <strong>&ldquo;{result.query}&rdquo;</strong>
            </span>
            <span>
              Total Retrieval + Re-rank Latency:{" "}
              <strong>{result.retrieval_time_ms} ms</strong>
            </span>
            <span className="muted-note">
              Hover any card to trace that chunk across stages
            </span>
          </div>

          <div className="debug-grid">
            {renderStageColumn(
              "1. Dense Vector Search",
              "BAAI/bge-small-en-v1.5 (384-dim Cosine)",
              "Cosine Sim",
              result.dense_results
            )}
            {renderStageColumn(
              "2. Sparse Keyword Search",
              "BM25Okapi Exact Token Match",
              "BM25",
              result.bm25_results
            )}
            {renderStageColumn(
              "3. Hybrid RRF Fusion",
              "1/(60 + rank_vec) + 1/(60 + rank_bm25)",
              "RRF",
              result.rrf_results
            )}
            {renderStageColumn(
              "4. Cross-Encoder Re-Rank",
              "FlashRank (ms-marco-TinyBERT-L-2-v2)",
              "Relevance",
              result.reranked_results
            )}
          </div>
        </>
      )}
    </div>
  );
}


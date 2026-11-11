import type { ChunkRecord, DocumentSummary } from "../types";

/**
 * Props passed into ChunkInspectorModal from its parent component.
 *
 * Java analogy: Think of `Props` as constructor parameters passed into a view object.
 */
interface ChunkInspectorModalProps {
  document: DocumentSummary;
  chunks: ChunkRecord[];
  loading: boolean;
  onClose: () => void;
}

export function ChunkInspectorModal({
  document,
  chunks,
  loading,
  onClose,
}: ChunkInspectorModalProps) {
  // Sort chunks in ascending order by chunk_index
  const sortedChunks = [...chunks].sort(
    (a, b) => a.chunk_index - b.chunk_index
  );

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-card"
        onClick={(e) => e.stopPropagation() /* Prevent click inside modal from closing it */}
      >
        <div className="modal-header">
          <div>
            <h2>Chunk Inspector: {document.source_filename}</h2>
            <p className="subtitle">
              Document ID: <code>{document.document_id}</code> &bull;{" "}
              {document.chunk_count} indexed chunks in LanceDB
            </p>
          </div>
          <button className="btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>

        <div className="modal-body">
          {loading ? (
            <div className="empty-state">Loading chunks from LanceDB...</div>
          ) : sortedChunks.length === 0 ? (
            <div className="empty-state">No chunks found for this document.</div>
          ) : (
            <div className="chunk-list">
              {sortedChunks.map((chunk) => (
                <div key={chunk.id} className="chunk-card">
                  <div className="chunk-meta-bar">
                    <span className="badge">Chunk #{chunk.chunk_index}</span>
                    <span>Page {chunk.page_number}</span>
                    <span>
                      Chars{" "}
                      <code>
                        [{chunk.char_start} : {chunk.char_end}]
                      </code>{" "}
                      ({chunk.text.length} chars)
                    </span>
                    {chunk.vector && chunk.vector.length > 0 && (
                      <span className="vector-preview" title="First 4 dimensions of the 384-dim BGE vector">
                        vec[384]: [
                        {chunk.vector
                          .slice(0, 4)
                          .map((v) => v.toFixed(3))
                          .join(", ")}
                        , ...]
                      </span>
                    )}
                  </div>
                  <pre className="chunk-text">{chunk.text}</pre>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


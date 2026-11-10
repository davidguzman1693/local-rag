import sys
from pathlib import Path

# Add src to sys.path
src_dir = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(src_dir))

from chunkers import RecursiveCharacterChunker
from embeddings import EmbeddingService
from loaders import DocumentLoader
from search import HybridRetriever
from storage import VectorStore


def run_pipeline_test():
    print("=== Step 1: Testing Document Loader ===")
    test_doc = Path(__file__).resolve().parent / "test_doc.md"
    test_doc.write_text("""# Introduction to Modern AI Engineering

AI Engineering is the discipline of building robust, reliable software systems powered by AI models.
Unlike traditional machine learning research which focuses on loss functions and model training, AI engineering focuses on data pipelines, latency, context relevance, and system architecture.

## Retrieval-Augmented Generation (RAG)
RAG solves LLM hallucination and knowledge cutoff by injecting verified reference documents into the prompt at runtime.

Key components of modern RAG:
1. Document Parsing and Recursive Chunking
2. Dense Vector Embeddings (e.g. BGE or Nomic)
3. Vector Indexing with Columnar Stores like LanceDB
4. Sparse Keyword Search via BM25
5. Cross-Encoder Re-ranking to refine top candidate passages
6. Grounded prompt synthesis with exact source citations

## Polyglot Architecture
In enterprise settings, Java often acts as the high-throughput API gateway, Python handles the vector math and AI pipeline, and TypeScript powers the streaming UI.
""", encoding="utf-8")

    full_text, pages = DocumentLoader.load_from_file(test_doc)
    print(f"Loaded {len(full_text)} characters across {len(pages)} page(s).")
    assert len(full_text) > 100, "Document loading failed!"

    print("\n=== Step 2: Testing Recursive Character Chunker ===")
    chunker = RecursiveCharacterChunker(chunk_size=250, chunk_overlap=50)
    chunks = chunker.chunk_document("doc-test-1", "test_doc.md", pages)
    print(f"Created {len(chunks)} chunks:")
    for idx, chunk in enumerate(chunks):
        print(f"  Chunk {idx}: [{chunk.metadata.char_start}:{chunk.metadata.char_end}] {chunk.text[:60]}...")
    assert len(chunks) >= 3, "Chunking should create at least 3 chunks!"

    print("\n=== Step 3: Testing FastEmbed ONNX Embedding Model ===")
    embedder = EmbeddingService("BAAI/bge-small-en-v1.5")
    print(f"Embedding dimension: {embedder.dimension}")
    embeddings = embedder.embed_documents([c.text for c in chunks])
    print(f"Generated {len(embeddings)} embeddings of dimension {len(embeddings[0])}.")
    assert len(embeddings) == len(chunks)

    print("\n=== Step 4: Testing LanceDB Vector Store ===")
    test_db_dir = Path(__file__).resolve().parent / "test_lancedb"
    store = VectorStore(test_db_dir, embedder.dimension)
    store.add_chunks(chunks, embeddings)
    print("Chunks indexed in LanceDB.")

    query = "What are the components of modern RAG?"
    query_vector = embedder.embed_query(query)
    dense_results = store.search_vector(query_vector, top_k=5)
    print(f"Vector search returned {len(dense_results)} results:")
    for r in dense_results[:2]:
        print(f"  - [{r.get('_distance', 0):.4f}] {r['text'][:70]}...")

    print("\n=== Step 5: Testing BM25 + Hybrid RRF Retrieval ===")
    retriever = HybridRetriever("ms-marco-TinyBERT-L-2-v2")
    retriever.update_bm25_corpus(store.get_all_chunks())
    hybrid_results = retriever.hybrid_search(query, dense_results, top_k=5)
    print(f"Hybrid search returned {len(hybrid_results)} candidates.")

    print("\n=== Step 6: Testing Cross-Encoder Re-ranking ===")
    reranked = retriever.rerank(query, hybrid_results, top_k=2)
    print(f"Cross-Encoder re-ranked top {len(reranked)} results:")
    for r in reranked:
        print(f"  - Score: {r['relevance_score']:.4f} | Source: {r['source_filename']} | Text: {r['text'][:80]}...")

    # Cleanup test artifacts
    if test_doc.exists():
        test_doc.unlink()
    import shutil
    if test_db_dir.exists():
        shutil.rmtree(test_db_dir)

    print("\n ALL PIPELINE UNIT TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_pipeline_test()

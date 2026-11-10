"""Command-line playground for the RAG pipeline.

Usage:
    uv run python cli.py ingest <file>
    uv run python cli.py docs
    uv run python cli.py chunks <document_id>
    uv run python cli.py search "<question>"      # retrieval only, no LLM
    uv run python cli.py ask "<question>"         # full RAG with streaming
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from service import RagService  # noqa: E402


def cmd_ingest(svc: RagService, args: argparse.Namespace) -> None:
    result = svc.ingest_file(Path(args.file))
    print(f"Indexed {result.filename}: {result.chunks_created} chunks (id={result.document_id})")


def cmd_docs(svc: RagService, _: argparse.Namespace) -> None:
    for doc in svc.vector_store.get_document_stats():
        print(f"{doc['document_id']}  {doc['source_filename']}  ({doc['chunk_count']} chunks)")


def cmd_chunks(svc: RagService, args: argparse.Namespace) -> None:
    chunks = sorted(svc.vector_store.get_chunks_by_document(args.document_id),
                    key=lambda c: c["chunk_index"])
    for c in chunks:
        # Show only the first 5 vector dims: the full vector has 384 floats.
        print(f"#{c['chunk_index']} [{c['char_start']}:{c['char_end']}] vec={c['vector'][:5]}...")
        print(f"   {c['text'][:120]!r}")


def cmd_search(svc: RagService, args: argparse.Namespace) -> None:
    for rank, c in enumerate(svc.retrieve_context(args.query), start=1):
        print(f"{rank}. score={c['relevance_score']:.4f} {c['source_filename']} p{c['page_number']}")
        print(f"   {c['text'][:150]!r}")


async def cmd_ask(svc: RagService, args: argparse.Namespace) -> None:
    # Consuming an async generator: the Python analogue of subscribing to a Flux<T>.
    async for event in svc.stream_query(args.query):
        if event["type"] == "citations":
            for c in event["citations"]:
                print(f"[{c['citation_id']}] {c['source_filename']} (score {c['relevance_score']})")
            print("\n--- answer ---")
        elif event["type"] == "token":
            print(event["token"], end="", flush=True)
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ingest").add_argument("file")
    sub.add_parser("docs")
    sub.add_parser("chunks").add_argument("document_id")
    sub.add_parser("search").add_argument("query")
    sub.add_parser("ask").add_argument("query")
    args = parser.parse_args()

    svc = RagService()
    handler = {
        "ingest": cmd_ingest, "docs": cmd_docs, "chunks": cmd_chunks,
        "search": cmd_search, "ask": cmd_ask,
    }[args.command]
    if asyncio.iscoroutinefunction(handler):
        asyncio.run(handler(svc, args))
    else:
        handler(svc, args)


if __name__ == "__main__":
    main()

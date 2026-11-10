import json
from typing import Any, AsyncGenerator, Dict, List, Tuple
import httpx
from schemas import Citation


SYSTEM_PROMPT = """You are a helpful, precise AI assistant answering questions based strictly on the provided context passages.

RULES:
1. Rely ONLY on the provided context. Do NOT use outside knowledge or extrapolate facts.
2. If the context does not contain enough information to answer the question, clearly state: "Based on the provided documents, I do not have enough information to answer this question."
3. Attribute your statements using bracketed citations corresponding to the passage index, e.g., [1], [2].
4. Be concise, structured, and factual.
"""


def build_rag_prompt(query: str, context_chunks: List[Dict[str, Any]]) -> Tuple[str, List[Citation]]:
    """Formats context passages into numbered excerpts and builds the final prompt and citations."""
    context_blocks: List[str] = []
    citations: List[Citation] = []

    for idx, chunk in enumerate(context_chunks, start=1):
        filename = chunk.get("source_filename", "unknown")
        page = chunk.get("page_number", 1)
        text = chunk.get("text", "")
        relevance = chunk.get("relevance_score", 0.0)

        context_blocks.append(f"--- [Passage {idx}] Source: {filename} (Page {page}) ---\n{text}")

        citations.append(
            Citation(
                citation_id=idx,
                document_id=chunk.get("document_id", ""),
                source_filename=filename,
                chunk_index=chunk.get("chunk_index", 0),
                page_number=page,
                snippet=text[:180] + ("..." if len(text) > 180 else ""),
                relevance_score=round(relevance, 4),
            )
        )

    formatted_context = "\n\n".join(context_blocks)
    prompt = f"""{SYSTEM_PROMPT}

CONTEXT PASSAGES:
{formatted_context}

USER QUESTION:
{query}

ANSWER (with citations [1], [2] where applicable):"""

    return prompt, citations


class OllamaClient:
    """Async client communicating with a locally running Ollama instance."""

    def __init__(self, base_url: str = "http://127.0.0.1:11434", model: str = "deepseek-r1:latest"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def generate(self, prompt: str, temperature: float = 0.2) -> str:
        """Sends a non-streaming generation request to Ollama."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")

    async def generate_stream(self, prompt: str, temperature: float = 0.2) -> AsyncGenerator[str, None]:
        """Streams generated tokens from Ollama as Server-Sent Events / chunks."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {"temperature": temperature},
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        chunk_json = json.loads(line)
                        yield chunk_json.get("response", "")
                        if chunk_json.get("done", False):
                            break

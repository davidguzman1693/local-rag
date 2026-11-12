import json
import re
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple
import httpx
from schemas import Citation, ConversationMessage


SYSTEM_PROMPT = """You are a helpful, precise AI assistant answering questions based strictly on the provided context passages.

RULES:
1. Rely ONLY on the provided context passages. Do NOT use outside knowledge or extrapolate facts.
2. Use the RECENT CONVERSATION HISTORY (if provided) only to understand follow-up references (such as "it", "that", or "the second point"). Every factual claim in your answer must still come from the CONTEXT PASSAGES.
3. If the context does not contain enough information to answer the question, clearly state: "Based on the provided documents, I do not have enough information to answer this question."
4. Attribute your statements using bracketed citations corresponding to the passage index, e.g., [1], [2].
5. Be concise, structured, and factual.
"""


def strip_think_tags(text: str) -> str:
    """Removes <think>...</think> reasoning blocks from prior assistant messages."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def build_rag_prompt(
    query: str,
    context_chunks: List[Dict[str, Any]],
    history: Optional[List[ConversationMessage]] = None,
) -> Tuple[str, List[Citation]]:
    """Formats context passages and optional conversation history into the final grounded prompt."""
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

    history_section = ""
    if history:
        turns: List[str] = []
        for msg in history[-6:]:
            role_label = "User" if msg.role == "user" else "Assistant"
            cleaned_content = strip_think_tags(msg.content) if msg.role == "assistant" else msg.content.strip()
            if cleaned_content:
                turns.append(f"{role_label}: {cleaned_content}")
        if turns:
            history_section = "\nRECENT CONVERSATION HISTORY:\n" + "\n".join(turns) + "\n"

    prompt = f"""{SYSTEM_PROMPT}

CONTEXT PASSAGES:
{formatted_context}
{history_section}
USER QUESTION:
{query}

ANSWER (with citations [1], [2] where applicable):"""

    return prompt, citations


class OllamaClient:
    """Async client communicating with a locally running Ollama instance."""

    def __init__(self, base_url: str = "http://127.0.0.1:11434", model: str = "deepseek-r1:latest"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def list_models(self) -> List[Dict[str, Any]]:
        """Queries Ollama /api/tags to list installed models."""
        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                return data.get("models", [])
        except Exception:
            return []

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.2,
        model: Optional[str] = None,
    ) -> str:
        """Sends a non-streaming generation request to Ollama."""
        url = f"{self.base_url}/api/generate"
        target_model = model or self.model
        payload = {
            "model": target_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")

    async def generate_stream(
        self,
        prompt: str,
        temperature: float = 0.2,
        model: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Streams generated tokens from Ollama as Server-Sent Events / chunks."""
        url = f"{self.base_url}/api/generate"
        target_model = model or self.model
        payload = {
            "model": target_model,
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

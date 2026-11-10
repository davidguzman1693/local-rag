from typing import List
from fastembed import TextEmbedding


class EmbeddingService:
    """Generates dense vector embeddings locally using FastEmbed (ONNX).
    
    FastEmbed runs quantized models directly in-process with minimal memory footprint
    and zero dependency on heavy frameworks like PyTorch or TensorFlow.
    """

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model_name = model_name
        # Model is downloaded on first run and cached in ~/.cache/fastembed
        self._model = TextEmbedding(model_name=self.model_name)
        # Determine vector dimensionality by generating a probe embedding
        probe = list(self._model.embed(["probe"]))[0]
        self.dimension = len(probe)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a batch of text chunks."""
        embeddings_generator = self._model.embed(texts)
        return [embedding.tolist() for embedding in embeddings_generator]

    def embed_query(self, query: str) -> List[float]:
        """Generates embedding for a single user search query."""
        embedding_generator = self._model.embed([query])
        return list(embedding_generator)[0].tolist()

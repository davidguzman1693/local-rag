from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration using Pydantic Settings.
    
    Reads from environment variables and provides typed, validated defaults.
    In Java terms, this is equivalent to @ConfigurationProperties in Spring Boot.
    """
    model_config = SettingsConfigDict(env_prefix="LOCAL_RAG_", env_file=".env", extra="ignore")

    # Service & Network
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Storage Paths
    base_data_dir: Path = Path(__file__).resolve().parent.parent.parent.parent / "data"
    lancedb_uri: Path = base_data_dir / "lancedb"
    documents_dir: Path = base_data_dir / "documents"
    models_dir: Path = base_data_dir / "models"

    # Embedding Model (FastEmbed ONNX models run locally on CPU/Metal)
    # Options: "BAAI/bge-small-en-v1.5" (384-dim, fast & accurate), "nomic-ai/nomic-embed-text-v1.5"
    embedding_model_name: str = "BAAI/bge-small-en-v1.5"

    # Re-ranking Model (FlashRank lightweight cross-encoder)
    # Options: "ms-marco-TinyBERT-L-2-v2", "ms-marco-MiniLM-L-12-v2"
    reranker_model_name: str = "ms-marco-TinyBERT-L-2-v2"

    # Chunking Strategy
    chunk_size: int = 500  # characters
    chunk_overlap: int = 100  # characters

    # Retrieval
    vector_search_top_k: int = 15
    bm25_search_top_k: int = 15
    rerank_top_k: int = 4

    # Ollama LLM
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "deepseek-r1:latest"  # Detected on user's machine
    temperature: float = 0.2


# Singleton instance
settings = Settings()

# Ensure directories exist
settings.lancedb_uri.mkdir(parents=True, exist_ok=True)
settings.documents_dir.mkdir(parents=True, exist_ok=True)
settings.models_dir.mkdir(parents=True, exist_ok=True)

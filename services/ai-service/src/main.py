from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import router as api_router, set_rag_service
from config import settings
from service import RagService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown hooks."""
    print("Starting AI Service...")
    service = RagService()
    set_rag_service(service)
    yield
    print("Shutting down AI Service...")


app = FastAPI(
    title="Local RAG AI Service",
    description="Dedicated AI & Retrieval Engine powering the Local RAG platform",
    version="0.1.0",
    lifespan=lifespan,
)

# Enable CORS for Java gateway and frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health_check():
    """Health check endpoint indicating model and service status."""
    return {
        "status": "healthy",
        "service": "ai-service",
        "embedding_model": settings.embedding_model_name,
        "reranker_model": settings.reranker_model_name,
        "ollama_model": settings.ollama_model,
    }


def start():
    """CLI entrypoint invoked by 'uv run ai-service'."""
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=settings.debug)


if __name__ == "__main__":
    start()

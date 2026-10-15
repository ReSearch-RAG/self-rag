from fastapi import FastAPI
from app.api.routes.documents import router as documents_router
from app.api.routes.queries import router as queries_router

app = FastAPI(
    title="Self-Correcting RAG",
    description="Evaluation-driven Retrieval-Augmented Generation system",
    version="0.1.0",
)

app.include_router(documents_router)
app.include_router(queries_router)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "self-correcting-rag",
    }

from fastapi import FastAPI

app = FastAPI(
    title="Self-Correcting RAG",
    description="Evaluation-driven Retrieval-Augmented Generation system",
    version="0.1.0"
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "self-correcting-rag"
    }
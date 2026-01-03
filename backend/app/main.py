from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routes import ingest, analyze, postmortem
from app.db import storage
from app.services.rag_engine import rag_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    # Initialize database
    await storage.initialize()
    print("✅ Database initialized")
    
    # Initialize RAG engine (Pinecone)
    await rag_engine.initialize()
    print("✅ RAG engine initialized")
    
    yield
    
    # Cleanup on shutdown
    print("🔄 Shutting down...")


app = FastAPI(
    title="AI Incident Commander",
    description="Production-grade AI system for incident detection and root cause analysis",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingest.router)
app.include_router(analyze.router)
app.include_router(postmortem.router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Incident Commander",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Check database
        incidents = await storage.get_all_incidents(limit=1)
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    try:
        # Check RAG engine
        rag_stats = await rag_engine.get_stats()
        rag_status = "healthy"
    except Exception as e:
        rag_stats = {}
        rag_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" and rag_status == "healthy" else "degraded",
        "components": {
            "database": db_status,
            "rag_engine": rag_status,
            "rag_stats": rag_stats
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

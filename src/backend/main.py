"""
FastAPI Backend for AI Interview Platform
Run with: uvicorn backend.main:app --reload --port 8000
"""
import sys
# Configure stdout/stdin encoding to support UTF-8 (emojis, etc.) on Windows consoles/logs
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routes
from backend.routes import auth_router, candidates_router, interview_router, recruiter_router

# Create app
app = FastAPI(
    title="AI Interview Platform API",
    description="Backend for Streamlit Interview Platform",
    version="1.0.0",
)

# CORS - Allow Streamlit to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(candidates_router, prefix="/api")
app.include_router(interview_router, prefix="/api")
app.include_router(recruiter_router, prefix="/api")

# Health check
@app.get("/")
def root():
    return {"message": "AI Interview Platform API", "status": "running"}

@app.get("/health")
def health():
    return {"status": "ok"}
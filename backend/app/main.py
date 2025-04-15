from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import logging
from dotenv import load_dotenv
from app.services.ai_assistant import get_assistant, AIAssistant

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="X-Query API",
    description="MCP-Powered Agentic RAG for Twitter Analysis",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str

# Routes
@app.get("/")
async def root():
    return {"message": "Welcome to X-Query API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest, assistant: AIAssistant = Depends(get_assistant)):
    try:
        logger.info(f"Processing query: {request.query}")
        response = await assistant.process_message(request.query)
        return {"response": response}
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Import and include API routers
from app.api.endpoints import conversation
app.include_router(conversation.router, prefix="/api/conversation", tags=["conversation"])

# Event handlers for startup and shutdown
@app.on_event("startup")
async def startup_event():
    """Initialize the AI Assistant on startup."""
    try:
        assistant = await get_assistant()
        logger.info("AI Assistant initialized successfully on startup")
    except Exception as e:
        logger.error(f"Error initializing AI Assistant on startup: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up the AI Assistant on shutdown."""
    try:
        assistant = await get_assistant()
        await assistant.cleanup()
        logger.info("AI Assistant cleaned up successfully on shutdown")
    except Exception as e:
        logger.error(f"Error cleaning up AI Assistant on shutdown: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

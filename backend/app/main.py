from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
    max_results: Optional[int] = 10
    include_trends: Optional[bool] = False

class QueryResponse(BaseModel):
    summary: str
    tweets: Optional[List[Dict[str, Any]]] = None
    trends: Optional[List[Dict[str, Any]]] = None
    reasoning: Optional[List[Dict[str, Any]]] = None

# Routes
@app.get("/")
async def root():
    return {"message": "Welcome to X-Query API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    try:
        # This will be replaced with actual agent execution logic
        # For now, return a placeholder response
        return {
            "summary": f"Analysis of query: {request.query}",
            "tweets": [{"id": "123", "text": "Sample tweet", "author": "user123"}],
            "trends": [{"name": "#sample", "tweet_volume": 1000}] if request.include_trends else None,
            "reasoning": [
                {"step": 1, "action": "Analyzed query", "result": "Identified key terms"},
                {"step": 2, "action": "Retrieved tweets", "result": "Found relevant content"}
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Import and include API routers
from app.api.endpoints import trends, tweets, agent
app.include_router(trends.router, prefix="/api/trends", tags=["trends"])
app.include_router(tweets.router, prefix="/api/tweets", tags=["tweets"])
app.include_router(agent.router, prefix="/api/agent", tags=["agent"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

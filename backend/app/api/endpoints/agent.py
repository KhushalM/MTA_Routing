from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.services.llm.agent import LLMAgent
from app.tools.twitter_tools import TwitterTools

router = APIRouter()

# Initialize tools and agent
twitter_tools = TwitterTools()
agent = LLMAgent(tools=twitter_tools.get_tools())

class AgentRequest(BaseModel):
    query: str
    max_results: Optional[int] = 10
    include_trends: Optional[bool] = False

class AgentResponse(BaseModel):
    summary: str
    reasoning: Optional[List[Dict[str, Any]]] = None
    tweets: Optional[List[Dict[str, Any]]] = None
    trends: Optional[List[Dict[str, Any]]] = None

@router.post("/query", response_model=AgentResponse)
async def agent_query(request: AgentRequest):
    """
    Process a query using the MCP-powered agent
    
    Args:
        request: The query request
    """
    try:
        # Process the query with the agent
        result = await agent.process_query(request.query)
        
        response = {
            "summary": result["summary"],
            "reasoning": result["reasoning"]
        }
        
        # If requested, include trends
        if request.include_trends:
            from app.services.twitter.client import TwitterClient
            client = TwitterClient()
            trends = await client.get_trends(woeid=1)
            response["trends"] = trends[:10]  # Include top 10 trends
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

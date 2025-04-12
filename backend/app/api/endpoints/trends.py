from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.services.twitter.client import TwitterClient

router = APIRouter()
client = TwitterClient()

class TrendResponse(BaseModel):
    trends: List[Dict[str, Any]]

@router.get("/", response_model=TrendResponse)
async def get_trends(woeid: int = 1, limit: int = 10):
    """
    Get current trending topics on Twitter
    
    Args:
        woeid: The Yahoo! Where On Earth ID of the location to get trends for. Default is 1 (worldwide)
        limit: Maximum number of trends to return
    """
    try:
        trends = await client.get_trends(woeid=woeid)
        return {"trends": trends[:limit]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

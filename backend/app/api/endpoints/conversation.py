from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.services.ai_assistant import get_assistant, AIAssistant
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

router = APIRouter()

class ConversationRequest(BaseModel):
    query: str
    user_id: Optional[str] = "anonymous"

class ConversationResponse(BaseModel):
    response: str
    user_id: str

class ConversationHistoryResponse(BaseModel):
    conversations: List[Dict[str, Any]]

@router.post("/query", response_model=ConversationResponse)
async def conversation_query(request: ConversationRequest, assistant: AIAssistant = Depends(get_assistant)):
    """
    Process a query using the AI Assistant with tool-using capabilities
    """
    try:
        logger.info(f"Processing query: {request.query}")
        response = await assistant.process_message(request.query)
        return ConversationResponse(
            response=response,
            user_id=request.user_id
        )
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{user_id}", response_model=ConversationHistoryResponse)
async def get_conversation_history(user_id: str, limit: int = 10, assistant: AIAssistant = Depends(get_assistant)):
    """
    Get conversation history for a user
    """
    try:
        logger.info(f"Getting conversation history for user: {user_id}")
        # For now, return an empty list as our new architecture doesn't yet support history retrieval
        # This will need to be implemented in the AIAssistant class
        return {"conversations": []}
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

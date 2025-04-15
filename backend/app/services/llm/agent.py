from tempfile import tempdir
from typing import List, Dict, Any, Optional
import os
import logging
import asyncio
from dotenv import load_dotenv
from langchain_community.llms import Ollama
from langchain.chains import ConversationalReasoningChain

# Import the new MCP client
from app.services.llm.mcp_client import MCPClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
    
def get_prompt(reasoning_stage=None):
    """
    Get the prompt for the LLM agent based on the reasoning stage
    
    Args:
        reasoning_stage: The stage of reasoning (None, 'context', or 'twitter')
        
    Returns:
        Prompt string for the LLM
    """
    base_prompt = """
    You are a helpful assistant that can answer questions about Twitter data and general knowledge.
    """
    
    if reasoning_stage == "context":
        return base_prompt + """
        First, analyze the provided context from previous conversations to determine if you can answer the query.
        If you can answer based on the context, clearly state: "I can answer this query based on the provided context."
        If you cannot answer based on the context, clearly state: "I cannot answer this query based on the provided context."
        Provide your reasoning for why you can or cannot answer the query.
        """
    elif reasoning_stage == "twitter":
        return base_prompt + """
        Analyze the query from the user and determine which Twitter tool would be most appropriate to use:
        1. get_home_timeline: To fetch recent tweets from the user's timeline
        2. create_tweet: To create a new tweet
        3. reply_to_tweet: To reply to an existing tweet
        
        Recommend the most appropriate tool based on the user's query and explain your reasoning. Just return the tool name.
        """
    elif reasoning_stage == "Tweet content":
        return base_prompt + """
        These are the latest tweets from the user's timeline:    
        1) Create a short summary per tweet
        2) Ask user if they have any questions about the tweets
        3) If user has questions, answer them based on the tweets
        """
    else:
        return base_prompt + """
        Fetch me the latest tweets from the users timeline and summarize the trends. Also when asked about certain words, find the tweets that contain those words and are relevant to the query.
        """
        
class LLMAgent:
    """
    MCP-powered agent for analyzing Twitter data using DataWhisker x-mcp-server
    """
    
    def __init__(self, tools: List[Any] = None):
        """
        Initialize the LLM agent with tools
        
        Args:
            tools: List of tools for the agent to use (kept for backward compatibility)
        """
        self.model_name = "gemma3:12b"
        self.model = Ollama(model="gemma3:12b", temperature=0.7)
        # self.ollama = Ollama(model="gemma3:12b", temperature=0.7)  # Only if needed locally
        
        # Get the connection type from environment or default to HTTP
        self.connection_type = os.getenv("MCP_CONNECTION_TYPE", "stdio")
        
        # Initialize the MCP client
        self._initialize_mcp_client()
    
    def _initialize_mcp_client(self):
        """Initialize the MCP client for connecting to DataWhisker x-mcp-server"""
        try:
            # Create the MCP client with the configured connection type
            self.client = MCPClient(connection_type=self.connection_type)
            logger.info(f"Initialized MCP client with {self.connection_type} connection")
        except Exception as e:
            logger.error(f"Error initializing MCP client: {str(e)}")
            raise
    
    async def process_query_mcp(self, query: str, reasoning_stage=None) -> Dict[str, Any]:
        """
        Process a user query using the DataWhisker x-mcp-server
        
        Args:
            query: The user's query about Twitter data
            reasoning_stage: The stage of reasoning (None, 'context', or 'twitter')
            
        Returns:
            Dictionary containing the agent's response and reasoning steps
        """
        try:
            # Connect to the MCP server if not already connected
            # The client will handle the connection based on the connection type
            logger.info(f"Processing query with reasoning stage: {reasoning_stage}")
            await self.client.connect()
            
            # Get the appropriate prompt based on reasoning stage
            prompt = get_prompt(reasoning_stage)
            
            # Process the query using the appropriate method based on connection type
            options = {
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            formatted_query = f"{prompt}\n\n{query}"
            result = await self.client.process_query(
                query=formatted_query,
                model=self.model_name,
                options=options
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing query with MCP server: {str(e)}")
            return {
                "summary": f"Error processing your query: {str(e)}",
                "reasoning": []
            }
        finally:
            # Ensure the client is closed properly
            await self.client.cleanup()

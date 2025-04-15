"""
AI Assistant module.
Main entry point for the AI Assistant functionality.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional

from app.services.ai_assistant.configuration import Configuration
from app.services.ai_assistant.server import Server
from app.services.ai_assistant.llm_client import LLMClient
from app.services.ai_assistant.chat_session import ChatSession

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIAssistant:
    """Main AI Assistant class that manages the chat session and servers."""
    
    def __init__(self) -> None:
        """Initialize the AI Assistant."""
        self.config = Configuration()
        self.servers: List[Server] = []
        self.llm_client: Optional[LLMClient] = None
        self.chat_session: Optional[ChatSession] = None
        self.initialized = False
    
    async def initialize(self) -> None:
        """Initialize the AI Assistant.
        
        This loads the configuration, initializes the servers,
        and creates the chat session.
        """
        if self.initialized:
            return
            
        try:
            # Load server configuration
            server_config = self.config.load_server_config()
            
            # Initialize servers
            self.servers = [
                Server(name, srv_config)
                for name, srv_config in server_config["mcpServers"].items()
            ]
            
            # Initialize LLM client
            self.llm_client = LLMClient(model=self.config.ollama_model)
            
            # Create chat session
            self.chat_session = ChatSession(self.servers, self.llm_client)
            
            # Initialize chat session
            await self.chat_session.initialize()
            
            self.initialized = True
            logger.info(f"AI Assistant initialized successfully with Ollama model: {self.config.ollama_model}")
        except Exception as e:
            logger.error(f"Error initializing AI Assistant: {e}")
            await self.cleanup()
            raise
    
    async def process_message(self, message: str) -> str:
        """Process a user message and return the response.
        
        Args:
            message: The user's message
            
        Returns:
            The assistant's response
        """
        if not self.initialized:
            await self.initialize()
            
        if not self.chat_session:
            raise RuntimeError("Chat session not initialized")
            
        return await self.chat_session.process_message(message)
    
    async def cleanup(self) -> None:
        """Clean up all resources."""
        if self.chat_session:
            await self.chat_session.cleanup()
        self.initialized = False
        logger.info("AI Assistant cleaned up successfully")


# Singleton instance
_assistant: Optional[AIAssistant] = None


async def get_assistant() -> AIAssistant:
    """Get the singleton AI Assistant instance.
    
    Returns:
        The AI Assistant instance
    """
    global _assistant
    if _assistant is None:
        _assistant = AIAssistant()
        await _assistant.initialize()
    return _assistant

"""
LLM Client module for the AI Assistant.
Manages communication with local transformers with MPS acceleration.
"""

import logging
from typing import Dict, List
from langchain.schema import SystemMessage, AIMessage, HumanMessage
from langchain_community.llms import Ollama
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(filename)s - %(lineno)d - %(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class LLMClient:
    """Manages communication with local transformers with MPS acceleration."""

    def __init__(self, model: str = "gemma3:12b") -> None:
        """Initialize the LLM client.
        Args:
            model: Model name to use in Ollama (default: gemma3:12b)
        """
        self.model_name: str = model
        self.ollama = Ollama(model=model, temperature=0.7)
        logger.info(f"Initialized Ollama LLM client with model: {model}")

    async def get_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 512
    ) -> str:
        """Get a response from the LLM asynchronously.

        Args:
            messages: A list of message dictionaries.
            temperature: Controls randomness (0-1).
            max_tokens: Maximum tokens in the response.

        Returns:
            The LLM's response as a string.
        """
        try:
            # Convert message dictionaries to LangChain message objects
            langchain_messages = []
            for msg in messages:
                content = msg.get("content", "")
                role = msg.get("role", "user")
                
                if role == "system":
                    langchain_messages.append(SystemMessage(content=content))
                elif role == "assistant":
                    langchain_messages.append(AIMessage(content=content))
                else:  # user or any other role
                    langchain_messages.append(HumanMessage(content=content))
            
            # Get response from Ollama using ainvoke
            response = await self.ollama.ainvoke(langchain_messages)
            if hasattr(response, "content"):
                return response.content
            else:
                return str(response)
        except Exception as e:
            error_message = f"Error getting LLM response: {str(e)}"
            logger.error(error_message)
            return f"I encountered an error: {error_message}. Please try again."

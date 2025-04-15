"""
Chat Session module for the AI Assistant.
Orchestrates the interaction between user, LLM, and tools.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from app.services.ai_assistant.llm_client import LLMClient
from app.services.ai_assistant.server import Server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatSession:
    """Orchestrates the interaction between user, LLM, and tools."""

    def __init__(self, servers: List[Server], llm_client: LLMClient) -> None:
        """Initialize a chat session.
        
        Args:
            servers: List of available servers
            llm_client: LLM client for communication
        """
        self.servers: List[Server] = servers
        self.llm_client: LLMClient = llm_client
        self.messages: List[Dict[str, str]] = []
        self.system_message: Optional[str] = None

    async def initialize(self) -> None:
        """Initialize all servers and prepare the system message."""
        # Initialize all servers
        for server in self.servers:
            try:
                await server.initialize()
            except Exception as e:
                logger.error(f"Failed to initialize server {server.name}: {e}")
                # Continue with other servers even if one fails

        # Gather all tools from all servers
        all_tools = []
        for server in self.servers:
            try:
                tools = await server.list_tools()
                all_tools.extend(tools)
            except Exception as e:
                logger.error(f"Failed to list tools from server {server.name}: {e}")

        # Create the system message with tool descriptions
        tools_description = "\n".join([tool.format_for_llm() for tool in all_tools])
        
        self.system_message = (
            "You are a helpful assistant with access to these tools:\n\n"
            f"{tools_description}\n"
            "Choose the appropriate tool based on the user's question. "
            "If no tool is needed, reply directly.\n\n"
            "IMPORTANT: When you need to use a tool, you must ONLY respond with "
            "the exact JSON object format below, nothing else:\n"
            "{\n"
            '    "tool": "tool-name",\n'
            '    "arguments": {\n'
            '        "argument-name": "value"\n'
            "    }\n"
            "}\n\n"
            "After receiving a tool's response:\n"
            "1. Transform the raw data into a natural, conversational response\n"
            "2. Keep responses concise but informative\n"
            "3. Focus on the most relevant information\n"
            "4. Use appropriate context from the user's question\n"
            "5. Avoid simply repeating the raw data\n\n"
            "Please use only the tools that are explicitly defined above."
        )
        
        # Initialize the messages list with the system message
        self.messages = [{"role": "system", "content": self.system_message}]

    async def process_message(self, user_message: str) -> str:
        """Process a user message and return the response.
        
        Args:
            user_message: The user's message
            
        Returns:
            The assistant's response
        """
        # Add the user message to the conversation history
        self.messages.append({"role": "user", "content": user_message})
        
        # Get the initial response from the LLM
        llm_response = await self.llm_client.get_response(self.messages)
        logger.info(f"Initial LLM response: {llm_response}")
        
        # Check if the response is a tool call
        try:
            tool_call = json.loads(llm_response)
            if "tool" in tool_call and "arguments" in tool_call:
                # It's a tool call, process it
                tool_name = tool_call["tool"]
                arguments = tool_call["arguments"]
                
                logger.info(f"Tool call detected: {tool_name}")
                logger.info(f"Arguments: {arguments}")
                
                # Find the server that has this tool
                tool_result = None
                for server in self.servers:
                    try:
                        tools = await server.list_tools()
                        if any(tool.name == tool_name for tool in tools):
                            # Execute the tool
                            tool_result = await server.execute_tool(tool_name, arguments)
                            break
                    except Exception as e:
                        logger.error(f"Error checking tools on server {server.name}: {e}")
                
                # Add the assistant's tool call to the conversation
                self.messages.append({"role": "assistant", "content": llm_response})
                
                if tool_result is not None:
                    # Add the tool result as a system message
                    tool_result_str = f"Tool execution result: {tool_result}"
                    self.messages.append({"role": "system", "content": tool_result_str})
                    
                    # Get a final response from the LLM that interprets the tool result
                    final_response = await self.llm_client.get_response(self.messages)
                    self.messages.append({"role": "assistant", "content": final_response})
                    return final_response
                else:
                    error_msg = f"No server found with tool: {tool_name}"
                    self.messages.append({"role": "system", "content": error_msg})
                    final_response = await self.llm_client.get_response(self.messages)
                    self.messages.append({"role": "assistant", "content": final_response})
                    return final_response
            else:
                # Not a tool call, just a regular response
                self.messages.append({"role": "assistant", "content": llm_response})
                return llm_response
        except json.JSONDecodeError:
            # Not a JSON response, just a regular response
            self.messages.append({"role": "assistant", "content": llm_response})
            return llm_response
        except Exception as e:
            # Some other error occurred
            error_msg = f"Error processing message: {str(e)}"
            logger.error(error_msg)
            self.messages.append({"role": "assistant", "content": error_msg})
            return error_msg

    async def cleanup(self) -> None:
        """Clean up all servers properly."""
        cleanup_tasks = []
        for server in self.servers:
            cleanup_tasks.append(asyncio.create_task(server.cleanup()))

        if cleanup_tasks:
            try:
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)
                logger.info("All servers cleaned up successfully")
            except Exception as e:
                logger.warning(f"Warning during final cleanup: {e}")

"""
Chat Session module for the AI Assistant.
Orchestrates the interaction between user, LLM, and tools.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from langchain_community.vectorstores import Chroma
from app.services.ai_assistant.llm_client import LLMClient
from app.services.ai_assistant.server import Server
from app.services.ai_assistant.mcp_scraper import scrape_awesome_mcp_servers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(filename)s - %(lineno)d - %(asctime)s - %(levelname)s - %(message)s"
)
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
            "Before using a tool, reason once before using it.\n\n"
            "If no tool is needed, reply directly.\n\n"
            "IMPORTANT: When you need to use a tool, you must ONLY respond with "
            "the exact JSON object format below, nothing else:\n"
            "STRICTLY FOLLOW THE JSON FORMAT BELOW with no ``` or ```:\n"
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

            "Once tool response is received, transform the raw data into a natural, conversational response."
            "If the query is about MCP servers, check if the query mentions what type of MCP server is being asked for. "
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
        logger.info(f"Received user message: {user_message}")
        # Add the user message to the conversation history
        self.messages.append({"role": "user", "content": user_message})
        logger.info(f"Current conversation history: {self.messages}")
        
        # Special: If user asks for available MCPs, fetch from awesome-mcp-servers
        if "list mcp" in str(user_message).lower() or "available mcp" in str(user_message).lower() or "huggingface mcp" in str(user_message).lower():
            try:
                logger.info("Fetching MCP list from awesome-mcp-servers GitHub repo...")
                mcps = await scrape_awesome_mcp_servers()
                if mcps:
                    try:
                        from app.services.ai_assistant.chroma_utils import store_mcps_in_chroma
                        store_mcps_in_chroma(mcps)
                        logger.info("Stored scraped MCPs in Chroma for semantic search.")
                    except Exception as e:
                        logger.error(f"Failed to store MCPs in Chroma: {e}")
                    
                    try:
                        from app.services.ai_assistant.chroma_utils import semantic_search_mcps
                        logger.info("Performing semantic search for MCPs...")
                        results = semantic_search_mcps(user_message, mcps=mcps)
                        if results:
                            # Return results as a JSON-serializable list of dicts for the UI
                            reply = [
                                {
                                    "name": r.metadata["name"],
                                    "link": r.metadata["link"],
                                    "description": r.metadata["description"]
                                } for r in results
                            ]
                            self.messages.append({"role": "assistant", "content": reply})
                            return reply
                        else:
                            reply = []
                            self.messages.append({"role": "assistant", "content": reply})
                            return reply
                    except Exception as e:
                        logger.error(f"Failed to perform semantic search: {e}")
                        reply = f"Error performing semantic search: {e}"
                        self.messages.append({"role": "assistant", "content": reply})
                        return reply
                if not mcps:
                    reply = "No MCP servers found in the awesome-mcp-servers repo."
                    self.messages.append({"role": "assistant", "content": reply})
                    return reply
                # Format as markdown bullet points with clickable links
                mcp_lines = [
                    f"- [{m['name']}]({m['link']}): {m['description']}" for m in mcps
                ]
                reply = "Here are available MCP servers from the [awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) repo:\n\n" + "\n".join(mcp_lines)
                self.messages.append({"role": "assistant", "content": reply})
                return reply
            except Exception as err:
                logger.error(f"Error fetching MCPs: {err}")
                reply = f"Error fetching MCP list: {err}"
                self.messages.append({"role": "assistant", "content": reply})
                return reply
        
        # Get the initial response from the LLM
        llm_response = await self.llm_client.get_response(self.messages)
        logger.info(f"Initial LLM response: {llm_response}")
        if llm_response.startswith("AI:"):
            llm_response = llm_response[3:]
        if llm_response.startswith("```json"):
            llm_response = llm_response[7:]
        if llm_response.endswith("```"):
            llm_response = llm_response[:-3]
        logger.info(f"Processed LLM response: {llm_response}")
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
                        logger.info(f"Checking server {server.name} for tool {tool_name}")
                        tools = await server.list_tools()
                        if any(tool.name == tool_name for tool in tools):
                            logger.info(f"Executing tool {tool_name} on server {server.name} with arguments: {arguments}")
                            tool_result = await server.execute_tool(tool_name, arguments)
                            logger.info(f"Tool {tool_name} executed successfully on server {server.name}. Result: {tool_result}")
                            break
                    except Exception as e:
                        logger.error(f"Error checking tools on server {server.name}: {e}")
                # Add the assistant's tool call to the conversation
                self.messages.append({"role": "assistant", "content": llm_response})
                logger.info(f"Added tool call to conversation history.")
                if tool_result is not None:
                    # Special handling for plan_subway_trip
                    if tool_name == "plan_subway_trip":
                        try:
                            import json as _json
                            import ast
                            # Extract text from tool_result if needed
                            if hasattr(tool_result, "content") and isinstance(tool_result.content, list) and len(tool_result.content) > 0:
                                text_content = getattr(tool_result.content[0], "text", None)
                                if text_content is not None:
                                    # The text is a string representation of a dict, not JSON
                                    try:
                                        result_dict = ast.literal_eval(text_content)
                                    except Exception:
                                        result_dict = text_content  # fallback
                                else:
                                    result_dict = tool_result
                            elif isinstance(tool_result, str):
                                try:
                                    result_dict = _json.loads(tool_result)
                                except Exception:
                                    try:
                                        result_dict = ast.literal_eval(tool_result)
                                    except Exception:
                                        result_dict = tool_result
                            else:
                                result_dict = tool_result

                            # Patch: handle both dict and object
                            if isinstance(result_dict, dict):
                                origin = result_dict.get('origin')
                                destination = result_dict.get('destination')
                                travel_time = result_dict.get('travel_time_minutes')
                                departure_time = result_dict.get('departure_time')
                                arrival_time = result_dict.get('arrival_time')
                            else:
                                origin = getattr(result_dict, 'origin', None)
                                destination = getattr(result_dict, 'dest', None)
                                travel_time = getattr(result_dict, 'travel_time_minutes', None)
                                departure_time = getattr(result_dict, 'departure_time', None)
                                arrival_time = getattr(result_dict, 'arrival_time', None)
                            summary = (
                                f"Subway trip plan:\n"
                                f"Origin: {origin}\n"
                                f"Destination: {destination}\n"
                                f"Travel time: {travel_time} minutes\n"
                                f"Departure time: {departure_time}\n"
                                f"Arrival time: {arrival_time}"
                            )
                            tool_result_str = summary
                        except Exception as e:
                            logger.error(f"Error summarizing plan_subway_trip result: {e}")
                            tool_result_str = f"Tool execution result: {tool_result}"
                    else:
                        tool_result_str = f"Tool execution result: {tool_result}"
                    self.messages.append({"role": "system", "content": tool_result_str})
                    logger.info(f"Added tool result to conversation history: {tool_result_str}")
                    # Get a final response from the LLM that interprets the tool result
                    final_response = await self.llm_client.get_response(self.messages)
                    logger.info(f"Final LLM response after tool execution: {final_response}")
                    self.messages.append({"role": "assistant", "content": final_response})
                    return final_response
                else:
                    error_msg = f"No server found with tool: {tool_name}"
                    logger.error(error_msg)
                    self.messages.append({"role": "system", "content": error_msg})
                    final_response = await self.llm_client.get_response(self.messages)
                    self.messages.append({"role": "assistant", "content": final_response})
                    return final_response
            else:
                # Not a tool call, just a regular response
                logger.info("LLM response is not a tool call. Returning regular response.")
                self.messages.append({"role": "assistant", "content": llm_response})
                return llm_response
        except json.JSONDecodeError:
            # Not a JSON response, just a regular response
            logger.info("LLM response is not valid JSON. Returning regular response.")
            self.messages.append({"role": "assistant", "content": llm_response})
            return llm_response
        except Exception as e:
            # Some other error occurred
            error_msg = f"Error processing message: {str(e)}"
            logger.error(error_msg)
            self.messages.append({"role": "assistant", "content": error_msg})
            return error_msg

    def reset_history(self) -> None:
        """Clear the chat history."""
        self.messages = []

    async def cleanup(self) -> None:
        """Clean up all servers properly and reset chat history."""
        cleanup_tasks = []
        for server in self.servers:
            cleanup_tasks.append(asyncio.create_task(server.cleanup()))

        if cleanup_tasks:
            try:
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)
                logger.info("All servers cleaned up successfully")
            except Exception as e:
                logger.warning(f"Warning during final cleanup: {e}")
        self.reset_history()

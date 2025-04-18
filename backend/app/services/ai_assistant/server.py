"""
Server module for the AI Assistant.
Manages MCP server connections and tool execution.
"""

import asyncio
import logging
import os
import shutil
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional, Tuple

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.services.ai_assistant.tool import Tool
from app.services.ai_assistant.llm_client import LLMClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(filename)s - %(lineno)d - %(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Server:
    """Manages MCP server connections and tool execution."""

    def __init__(self, name: str, config: Dict[str, Any]) -> None:
        """Initialize a server with its configuration.
        
        Args:
            name: Server name
            config: Server configuration dictionary
        """
        self.name: str = name
        self.config: Dict[str, Any] = config
        self.session: Optional[ClientSession] = None
        self._cleanup_lock: asyncio.Lock = asyncio.Lock()
        self.exit_stack: AsyncExitStack = AsyncExitStack()
        self.llm_client = LLMClient()

    async def initialize(self) -> None:
        """Initialize the server connection.
        
        Raises:
            ValueError: If the command is invalid
            Exception: If initialization fails
        """
        command = (
            shutil.which("npx")
            if self.config["command"] == "npx"
            else self.config["command"]
        )
        if command is None:
            raise ValueError("The command must be a valid string and cannot be None.")

        server_params = StdioServerParameters(
            command=command,
            args=self.config["args"],
            env={**os.environ, **self.config["env"]}
            if self.config.get("env")
            else None,
        )
        try:
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await session.initialize()
            self.session = session
            logger.info(f"Server {self.name} initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing server {self.name}: {e}")
            await self.cleanup()
            raise

    async def list_tools(self) -> List[Tool]:
        """List available tools from the server.

        Returns:
            A list of available tools.

        Raises:
            RuntimeError: If the server is not initialized.
        """
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")

        tools_response = await self.session.list_tools()
        tools = []

        for item in tools_response:
            if isinstance(item, tuple) and item[0] == "tools":
                for tool in item[1]:
                    tools.append(Tool(tool.name, tool.description, tool.inputSchema))

        logger.info(f"Found {len(tools)} tools in server {self.name}")
        return tools

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        retries: int = 2,
        delay: float = 1.0,
    ) -> Any:
        """Execute a tool with retry mechanism.

        Args:
            tool_name: Name of the tool to execute.
            arguments: Tool arguments.
            retries: Number of retry attempts.
            delay: Delay between retries in seconds.

        Returns:
            Tool execution result.

        Raises:
            RuntimeError: If server is not initialized.
            Exception: If tool execution fails after all retries.
        """
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")

        attempt = 0
        while attempt <= retries:
            try:
                logger.info(f"Executing {tool_name} on server {self.name}...")
                result = await self.session.call_tool(tool_name, arguments)
                logger.info(f"Tool {tool_name} executed successfully")
                return result

            except Exception as e:
                attempt += 1
                logger.warning(
                    f"Error executing tool: {e}. Attempt {attempt} of {retries+1}."
                )
                if attempt <= retries:
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error("Max retries reached. Failing.")
                    raise

    async def cleanup(self) -> None:
        """Clean up server resources."""
        async with self._cleanup_lock:
            try:
                if self.session:
                    logger.info(f"Cleaning up server {self.name}...")
                    await self.exit_stack.aclose()
                    self.session = None
                    logger.info(f"Server {self.name} cleaned up successfully")
            except Exception as e:
                logger.error(f"Error during cleanup of server {self.name}: {e}")

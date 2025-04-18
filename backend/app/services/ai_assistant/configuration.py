"""
Configuration module for the AI Assistant.
Manages environment variables and configuration files.
"""

import json
import os
import logging
from typing import Any, Dict, Optional

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(filename)s - %(lineno)d - %(asctime)s - %(levelname)s - %(message)s"
)


class Configuration:
    """Manages configuration and environment variables for the AI assistant."""

    def __init__(self) -> None:
        """Initialize configuration with environment variables."""
        self.load_env()
        self.ollama_model = os.getenv("OLLAMA_MODEL", "gemma3:12b")
        self.config_path = os.getenv("SERVER_CONFIG_PATH", "app/services/ai_assistant/servers_config.json")

    @staticmethod
    def load_env() -> None:
        """Load environment variables from .env file."""
        load_dotenv()

    def load_server_config(self) -> Dict[str, Any]:
        """Load server configuration from JSON file.

        Returns:
            Dict containing server configuration.

        Raises:
            FileNotFoundError: If configuration file doesn't exist.
            JSONDecodeError: If configuration file is invalid JSON.
        """
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise

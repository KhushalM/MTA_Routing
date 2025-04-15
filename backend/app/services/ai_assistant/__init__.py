"""
AI Assistant package.
Tool-using AI assistant powered by Groq LLM and MCP servers.
"""

from app.services.ai_assistant.assistant import get_assistant, AIAssistant

__all__ = ["get_assistant", "AIAssistant"]

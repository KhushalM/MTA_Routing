from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage
from langchain.tools import BaseTool
from typing import List, Dict, Any, Optional
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class LLMAgent:
    """
    MCP-powered agent for analyzing Twitter data
    """
    
    def __init__(self, tools: List[BaseTool] = None):
        """
        Initialize the LLM agent with tools
        
        Args:
            tools: List of LangChain tools for the agent to use
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model_name = os.getenv("LLM_MODEL_NAME", "gpt-3.5-turbo")
        self.tools = tools or []
        
        # Initialize the LLM
        self._initialize_llm()
        
        # Create the agent
        self._create_agent()
    
    def _initialize_llm(self):
        """Initialize the language model"""
        try:
            self.llm = ChatOpenAI(
                model_name=self.model_name,
                temperature=0.2,
                api_key=self.api_key
            )
            logger.info(f"Initialized LLM with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Error initializing LLM: {str(e)}")
            raise
    
    def _create_agent(self):
        """Create the agent with tools"""
        # Define the system prompt
        system_prompt = """You are an intelligent Twitter analyst assistant. Your job is to analyze tweets, summarize trends, and provide insights based on Twitter data.

You have access to tools that can help you retrieve tweets and trending topics. Use these tools to gather information before providing your final answer.

When analyzing tweets, consider:
1. The main topics or themes
2. Sentiment and tone
3. Popular opinions or perspectives
4. Notable users or accounts involved
5. Relevant hashtags or keywords

Your responses should be well-structured, insightful, and based on actual Twitter data. Avoid making assumptions without evidence from the retrieved tweets.

If you don't have enough information to answer a question, use your tools to gather more data.
"""
        
        # Create the prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}")
        ])
        
        try:
            # Create the agent
            self.agent = create_openai_functions_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=prompt
            )
            
            # Create the agent executor
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True
            )
            
            logger.info("Agent created successfully with tools")
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}")
            raise
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query using the agent
        
        Args:
            query: The user's query about Twitter data
            
        Returns:
            Dictionary containing the agent's response and reasoning steps
        """
        try:
            # Execute the agent
            result = await self.agent_executor.ainvoke({"input": query})
            
            # Extract the output and intermediate steps
            output = result.get("output", "No response generated")
            intermediate_steps = result.get("intermediate_steps", [])
            
            # Format the reasoning steps
            reasoning = []
            for step in intermediate_steps:
                action = step[0]
                observation = step[1]
                
                reasoning.append({
                    "tool": action.tool,
                    "tool_input": action.tool_input,
                    "observation": observation
                })
            
            return {
                "summary": output,
                "reasoning": reasoning
            }
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "summary": f"Error processing your query: {str(e)}",
                "reasoning": []
            }

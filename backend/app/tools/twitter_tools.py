from langchain.tools import BaseTool, StructuredTool, tool
from langchain.pydantic_v1 import BaseModel, Field
from typing import List, Dict, Any, Optional
import asyncio
from app.services.twitter.client import TwitterClient

class TrendInput(BaseModel):
    woeid: int = Field(default=1, description="The Yahoo! Where On Earth ID of the location to get trends for. Default is 1 (worldwide)")
    limit: int = Field(default=10, description="Maximum number of trends to return")

class SearchInput(BaseModel):
    query: str = Field(..., description="The search query for finding tweets")
    max_results: int = Field(default=10, description="Maximum number of tweets to return")

class TwitterTools:
    """Collection of tools for interacting with Twitter data"""
    
    def __init__(self):
        """Initialize the Twitter tools with a client"""
        self.client = TwitterClient()
    
    @tool("get_trending_topics", args_schema=TrendInput)
    async def get_trending_topics(self, woeid: int = 1, limit: int = 10) -> str:
        """
        Get the current trending topics on Twitter.
        
        Args:
            woeid: The Yahoo! Where On Earth ID of the location to get trends for. Default is 1 (worldwide)
            limit: Maximum number of trends to return
            
        Returns:
            String representation of trending topics
        """
        trends = await self.client.get_trends(woeid=woeid)
        limited_trends = trends[:limit]
        
        if not limited_trends:
            return "No trending topics found."
        
        # Format the trends for better readability
        result = "Current trending topics on Twitter:\n\n"
        for idx, trend in enumerate(limited_trends):
            tweet_volume = f" ({trend['tweet_volume']:,} tweets)" if trend.get('tweet_volume') else ""
            result += f"{idx+1}. {trend['name']}{tweet_volume}\n"
        
        return result
    
    @tool("search_tweets", args_schema=SearchInput)
    async def search_tweets(self, query: str, max_results: int = 10) -> str:
        """
        Search for tweets matching a query.
        
        Args:
            query: The search query
            max_results: Maximum number of results to return
            
        Returns:
            String representation of tweets matching the query
        """
        tweets = await self.client.search_tweets(query=query, max_results=max_results)
        
        if not tweets:
            return f"No tweets found matching the query: '{query}'"
        
        # Format the tweets for better readability
        result = f"Found {len(tweets)} tweets matching '{query}':\n\n"
        for idx, tweet in enumerate(tweets):
            author = tweet['author']
            metrics = tweet.get('metrics', {})
            
            # Format metrics if available
            metrics_str = ""
            if metrics:
                likes = metrics.get('likes', metrics.get('favorite_count', 0))
                retweets = metrics.get('retweets', metrics.get('retweet_count', 0))
                replies = metrics.get('replies', metrics.get('reply_count', 0))
                metrics_str = f" | ❤️ {likes} | 🔄 {retweets} | 💬 {replies}"
            
            result += f"{idx+1}. @{author['username']} ({author['name']}): {tweet['text']}{metrics_str}\n\n"
        
        return result
    
    @tool("summarize_tweets")
    async def summarize_tweets(self, query: str, max_results: int = 20) -> str:
        """
        Search for tweets matching a query and provide a summary of the main themes and sentiments.
        This is a higher-level tool that combines search and summarization.
        
        Args:
            query: The search query
            max_results: Maximum number of tweets to retrieve for summarization
            
        Returns:
            A summary of the tweets matching the query
        """
        # This would typically use an LLM to summarize, but for now we'll just return the tweets
        tweets = await self.client.search_tweets(query=query, max_results=max_results)
        
        if not tweets:
            return f"No tweets found matching the query: '{query}'"
        
        # For now, just return a formatted list of tweets
        # In a real implementation, this would pass the tweets to an LLM for summarization
        result = f"Summary of {len(tweets)} tweets about '{query}':\n\n"
        for idx, tweet in enumerate(tweets[:5]):  # Show just the first 5 in the result
            author = tweet['author']
            result += f"{idx+1}. @{author['username']}: {tweet['text']}\n\n"
        
        if len(tweets) > 5:
            result += f"... and {len(tweets) - 5} more tweets."
        
        return result
    
    def get_tools(self) -> List[BaseTool]:
        """
        Get all Twitter tools as LangChain tools
        
        Returns:
            List of LangChain tools
        """
        return [
            self.get_trending_topics,
            self.search_tweets,
            self.summarize_tweets
        ]

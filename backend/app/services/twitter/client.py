import os
import tweepy
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class TwitterClient:
    """
    Client for interacting with Twitter API or fallback to scraping if API keys aren't available
    """
    
    def __init__(self):
        """Initialize the Twitter client with API credentials or fallback mode"""
        self.api_key = os.getenv("TWITTER_API_KEY")
        self.api_secret = os.getenv("TWITTER_API_SECRET")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        
        # Check if we have API credentials
        self.use_api = all([self.api_key, self.api_secret, self.bearer_token])
        
        if self.use_api:
            logger.info("Using Twitter API for data retrieval")
            self.client = tweepy.Client(
                bearer_token=self.bearer_token,
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret
            )
        else:
            logger.warning("Twitter API credentials not found, falling back to scraping mode")
            self.client = None
            
    async def get_trends(self, woeid: int = 1) -> List[Dict[str, Any]]:
        """
        Get current trending topics on Twitter
        
        Args:
            woeid: The Yahoo! Where On Earth ID of the location to get trends for. Default is 1 (worldwide)
            
        Returns:
            List of trending topics
        """
        if self.use_api:
            try:
                # Use Twitter API v2
                trends = self.client.get_place_trends(id=woeid)
                return [
                    {
                        "name": trend["name"],
                        "url": trend["url"],
                        "tweet_volume": trend["tweet_volume"],
                        "rank": idx + 1
                    }
                    for idx, trend in enumerate(trends[0]["trends"])
                    if trend["tweet_volume"] is not None
                ]
            except Exception as e:
                logger.error(f"Error fetching trends from Twitter API: {str(e)}")
                # Fall back to scraping if API fails
                return await self._scrape_trends()
        else:
            # Use scraping method
            return await self._scrape_trends()
    
    async def search_tweets(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for tweets matching a query
        
        Args:
            query: The search query
            max_results: Maximum number of results to return
            
        Returns:
            List of tweets matching the query
        """
        if self.use_api:
            try:
                # Use Twitter API v2
                tweets = self.client.search_recent_tweets(
                    query=query,
                    max_results=max_results,
                    tweet_fields=["created_at", "public_metrics", "author_id"],
                    user_fields=["username", "name", "profile_image_url"],
                    expansions=["author_id"]
                )
                
                # Process results
                result_tweets = []
                users = {user.id: user for user in tweets.includes["users"]} if "users" in tweets.includes else {}
                
                for tweet in tweets.data:
                    author = users.get(tweet.author_id, None)
                    result_tweets.append({
                        "id": tweet.id,
                        "text": tweet.text,
                        "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
                        "metrics": tweet.public_metrics,
                        "author": {
                            "id": tweet.author_id,
                            "username": author.username if author else None,
                            "name": author.name if author else None,
                            "profile_image": author.profile_image_url if author else None
                        }
                    })
                
                return result_tweets
            except Exception as e:
                logger.error(f"Error searching tweets from Twitter API: {str(e)}")
                # Fall back to scraping if API fails
                return await self._scrape_tweets(query, max_results)
        else:
            # Use scraping method
            return await self._scrape_tweets(query, max_results)
    
    async def _scrape_trends(self) -> List[Dict[str, Any]]:
        """
        Scrape trending topics from Twitter/Nitter
        
        Returns:
            List of trending topics
        """
        try:
            async with httpx.AsyncClient() as client:
                # Try to use Nitter instance (a Twitter frontend alternative)
                response = await client.get("https://nitter.net/explore/tabs/trends")
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "lxml")
                    trend_items = soup.select(".trend-card .trend-item")
                    
                    trends = []
                    for idx, item in enumerate(trend_items[:20]):  # Get top 20 trends
                        name_elem = item.select_one(".trend-name")
                        volume_elem = item.select_one(".tweet-volume")
                        
                        if name_elem:
                            trends.append({
                                "name": name_elem.text.strip(),
                                "url": f"https://twitter.com/search?q={name_elem.text.strip()}",
                                "tweet_volume": int(volume_elem.text.strip().replace(",", "")) if volume_elem else None,
                                "rank": idx + 1
                            })
                    
                    return trends
                else:
                    logger.error(f"Failed to scrape trends: {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"Error scraping trends: {str(e)}")
            return []
    
    async def _scrape_tweets(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Scrape tweets matching a query from Twitter/Nitter
        
        Args:
            query: The search query
            max_results: Maximum number of results to return
            
        Returns:
            List of tweets matching the query
        """
        try:
            async with httpx.AsyncClient() as client:
                # Try to use Nitter instance
                encoded_query = httpx.URL(path=query).path
                response = await client.get(f"https://nitter.net/search?f=tweets&q={encoded_query}")
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "lxml")
                    tweet_items = soup.select(".timeline-item")
                    
                    tweets = []
                    for item in tweet_items[:max_results]:
                        try:
                            # Extract tweet data
                            tweet_id = item.get("data-tweet-id", "unknown")
                            content = item.select_one(".tweet-content")
                            username = item.select_one(".username")
                            fullname = item.select_one(".fullname")
                            date = item.select_one(".tweet-date")
                            
                            # Extract metrics
                            stats = item.select(".tweet-stats .icon-container")
                            metrics = {
                                "replies": int(stats[0].text.strip()) if len(stats) > 0 else 0,
                                "retweets": int(stats[1].text.strip()) if len(stats) > 1 else 0,
                                "likes": int(stats[2].text.strip()) if len(stats) > 2 else 0
                            }
                            
                            tweets.append({
                                "id": tweet_id,
                                "text": content.text.strip() if content else "",
                                "created_at": date.get("title") if date else None,
                                "metrics": metrics,
                                "author": {
                                    "id": "unknown",
                                    "username": username.text.strip() if username else "",
                                    "name": fullname.text.strip() if fullname else "",
                                    "profile_image": None  # Can't easily get profile image from Nitter
                                }
                            })
                        except Exception as e:
                            logger.error(f"Error parsing tweet: {str(e)}")
                            continue
                    
                    return tweets
                else:
                    logger.error(f"Failed to scrape tweets: {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"Error scraping tweets: {str(e)}")
            return []

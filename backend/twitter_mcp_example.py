"""
Twitter MCP Integration Example

This script demonstrates how to use the Twitter MCP tools with your MCPClient class.
It shows how to fetch the timeline, create tweets, and reply to tweets.
"""

import asyncio
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def run_twitter_example():
    """Run examples of Twitter MCP functionality"""
    print("Twitter MCP Integration Example")
    print("===============================")
    
    # Import the MCPClient class
    try:
        # Try to import from the module path
        from app.services.llm.mcp_client import MCPClient
    except ImportError:
        # If that fails, try a relative import
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent))
        from app.services.llm.mcp_client import MCPClient
    
    # Create a client instance
    client = None
    try:
        # Initialize client with stdio connection for local MCP server
        client = MCPClient(connection_type="stdio")
        client.server_script_path = "x-twitter"  # Name from mcp_config.json
        
        # Connect to the MCP server
        print("\nConnecting to Twitter MCP server...")
        await client.connect()
        print("Connected successfully!")
        
        # Example 1: Get home timeline
        print("\n1. Fetching home timeline...")
        try:
            timeline = await client.call_tool("mcp4_get_home_timeline", {"limit": 3})
            print(f"Timeline data (showing 3 tweets):")
            if isinstance(timeline, dict) and 'data' in timeline:
                for tweet in timeline.get('data', []):
                    author = None
                    for user in timeline.get('includes', {}).get('users', []):
                        if user.get('id') == tweet.get('author_id'):
                            author = user.get('username')
                            break
                    print(f"@{author}: {tweet.get('text')}")
            else:
                print(json.dumps(timeline, indent=2))
        except Exception as e:
            print(f"Error fetching timeline: {str(e)}")
        
        # Example 2: Create a tweet (commented out for safety)
        print("\n2. Creating a tweet (example only, not actually posting)")
        print("To create a tweet, use:")
        print('await client.call_tool("mcp4_create_tweet", {"text": "Your tweet text"})')
        
        # Example 3: Reply to a tweet (commented out for safety)
        print("\n3. Replying to a tweet (example only, not actually posting)")
        print("To reply to a tweet, use:")
        print('await client.call_tool("mcp4_reply_to_tweet", {"tweet_id": "tweet_id", "text": "Your reply text"})')
        
        # Interactive mode
        should_interact = input("\nDo you want to enter interactive mode? (yes/no): ").lower() == 'yes'
        if should_interact:
            await interactive_mode(client)
            
    except Exception as e:
        print(f"Error in Twitter MCP example: {str(e)}")
    finally:
        # Clean up resources
        if client:
            await client.cleanup()
            
async def interactive_mode(client):
    """Interactive mode for testing Twitter MCP functionality"""
    print("\nInteractive Mode")
    print("===============")
    print("Commands:")
    print("  timeline - Get your home timeline")
    print("  tweet - Create a new tweet")
    print("  reply - Reply to a tweet")
    print("  exit - Exit interactive mode")
    
    while True:
        command = input("\nEnter command: ").strip().lower()
        
        if command == 'exit':
            print("Exiting interactive mode")
            break
            
        elif command == 'timeline':
            limit = int(input("Number of tweets to fetch (1-20): ") or "5")
            try:
                timeline = await client.call_tool("mcp4_get_home_timeline", {"limit": limit})
                print(f"\nTimeline data (showing {limit} tweets):")
                if isinstance(timeline, dict) and 'data' in timeline:
                    for tweet in timeline.get('data', []):
                        author = None
                        for user in timeline.get('includes', {}).get('users', []):
                            if user.get('id') == tweet.get('author_id'):
                                author = user.get('username')
                                break
                        print(f"ID: {tweet.get('id')}")
                        print(f"@{author}: {tweet.get('text')}")
                        print("-" * 50)
                else:
                    print(json.dumps(timeline, indent=2))
            except Exception as e:
                print(f"Error fetching timeline: {str(e)}")
                
        elif command == 'tweet':
            confirm = input("Are you sure you want to post a tweet? (yes/no): ").lower() == 'yes'
            if confirm:
                tweet_text = input("Enter tweet text (max 280 chars): ")
                if tweet_text:
                    try:
                        result = await client.call_tool("mcp4_create_tweet", {"text": tweet_text})
                        print("Tweet posted successfully!")
                        print(f"Tweet ID: {result.get('data', {}).get('id')}")
                    except Exception as e:
                        print(f"Error posting tweet: {str(e)}")
            else:
                print("Tweet creation cancelled")
                
        elif command == 'reply':
            confirm = input("Are you sure you want to reply to a tweet? (yes/no): ").lower() == 'yes'
            if confirm:
                tweet_id = input("Enter the tweet ID to reply to: ")
                reply_text = input("Enter reply text (max 280 chars): ")
                if tweet_id and reply_text:
                    try:
                        result = await client.call_tool("mcp4_reply_to_tweet", {
                            "tweet_id": tweet_id,
                            "text": reply_text
                        })
                        print("Reply posted successfully!")
                        print(f"Reply Tweet ID: {result.get('data', {}).get('id')}")
                    except Exception as e:
                        print(f"Error posting reply: {str(e)}")
            else:
                print("Reply cancelled")
                
        else:
            print(f"Unknown command: {command}")

if __name__ == "__main__":
    asyncio.run(run_twitter_example())

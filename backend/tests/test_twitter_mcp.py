"""
Twitter MCP Integration Test

This script tests the integration between your application and the Twitter MCP server.
It verifies that your MCP client can connect to the server and call Twitter-specific tools.
"""

import asyncio
import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

async def test_twitter_mcp():
    """Test Twitter MCP integration"""
    print("Twitter MCP Integration Test")
    print("===========================")
    
    # Import the MCPClient class
    from app.services.llm.mcp_client import MCPClient
    
    # Check if Twitter API credentials are set
    twitter_keys = [
        "TWITTER_API_KEY",
        "TWITTER_API_SECRET",
        "TWITTER_ACCESS_TOKEN",
        "TWITTER_ACCESS_SECRET"
    ]
    
    missing_keys = [key for key in twitter_keys if not os.getenv(key)]
    if missing_keys:
        print(f"⚠️ Missing Twitter API credentials: {', '.join(missing_keys)}")
        print("Some functionality may not work without these credentials.")
    else:
        print("✅ All Twitter API credentials are set.")
    
    # Create a client instance
    client = None
    try:
        # Initialize client with stdio connection
        client = MCPClient(connection_type="stdio")
        
        # Set the server script path to the x-mcp-server directory
        x_mcp_server_path = Path(__file__).parent.parent / "x-mcp-server"
        if x_mcp_server_path.exists() and x_mcp_server_path.is_dir():
            print(f"Found x-mcp-server directory at: {x_mcp_server_path}")
            client.server_script_path = str(x_mcp_server_path)
        else:
            print(f"x-mcp-server directory not found at: {x_mcp_server_path}")
            print("Using default server script path: x-mcp-server")
            client.server_script_path = "x-mcp-server"
        
        # Connect to the MCP server
        print("\nConnecting to MCP server...")
        await client.connect()
        print("✅ Successfully connected to MCP server!")
        
        # Test Twitter tools
        print("\nTesting Twitter tools:")
        
        # 1. Get home timeline
        print("\n1. Testing get_home_timeline...")
        try:
            timeline_result = await client.call_tool("get_home_timeline", {"limit": 3})
            
            if isinstance(timeline_result, dict) and 'error' in timeline_result:
                print(f"⚠️ Error getting timeline: {timeline_result.get('error', {}).get('message', 'Unknown error')}")
            else:
                print("✅ Successfully retrieved timeline!")
                # Print a summary of the timeline data
                try:
                    # Convert the CallToolResult to a dictionary if needed
                    if hasattr(timeline_result, '__dict__'):
                        timeline_data = timeline_result.__dict__
                    elif hasattr(timeline_result, 'to_dict'):
                        timeline_data = timeline_result.to_dict()
                    else:
                        timeline_data = timeline_result
                    
                    # Check if we have data in the expected format
                    if isinstance(timeline_data, dict) and 'data' in timeline_data:
                        # Original Twitter API v2 format
                        tweets = timeline_data.get('data', [])
                        print(f"Retrieved {len(tweets)} tweets")
                        
                        # Get user information
                        users = {}
                        for user in timeline_data.get('includes', {}).get('users', []):
                            users[user.get('id')] = user.get('username')
                        
                        # Print tweet information with more details
                        print("\n--- TIMELINE ---")
                        for tweet in tweets:
                            author_id = tweet.get('author_id', 'Unknown')
                            author = users.get(author_id, 'Unknown')
                            text = tweet.get('text', 'No text')
                            created_at = tweet.get('created_at', 'Unknown date')
                            tweet_id = tweet.get('id', 'Unknown ID')
                            
                            print(f"\nTweet ID: {tweet_id}")
                            print(f"Author: @{author} (ID: {author_id})")
                            print(f"Date: {created_at}")
                            print(f"Text: {text}")
                            
                            # Print metrics if available
                            public_metrics = tweet.get('public_metrics', {})
                            if public_metrics:
                                print("Metrics:")
                                for metric, value in public_metrics.items():
                                    print(f"  - {metric}: {value}")
                            
                            print("-" * 50)
                    elif isinstance(timeline_data, dict) and 'content' in timeline_data and not timeline_data.get('isError', False):
                        # MCP server custom format
                        tweets = timeline_data.get('content', [])
                        print(f"Retrieved {len(tweets)} tweets")
                        
                        # Print tweet information with more details
                        print("\n--- TIMELINE ---")
                        for tweet in tweets:
                            if isinstance(tweet, dict):
                                # Extract tweet data
                                author = tweet.get('username', tweet.get('user', {}).get('screen_name', 'Unknown'))
                                text = tweet.get('text', 'No text')
                                created_at = tweet.get('created_at', 'Unknown date')
                                tweet_id = tweet.get('id_str', tweet.get('id', 'Unknown ID'))
                                
                                print(f"\nTweet ID: {tweet_id}")
                                print(f"Author: @{author}")
                                print(f"Date: {created_at}")
                                print(f"Text: {text}")
                                
                                # Print metrics if available
                                if 'retweet_count' in tweet or 'favorite_count' in tweet:
                                    print("Metrics:")
                                    if 'retweet_count' in tweet:
                                        print(f"  - retweets: {tweet['retweet_count']}")
                                    if 'favorite_count' in tweet:
                                        print(f"  - favorites: {tweet['favorite_count']}")
                                
                                print("-" * 50)
                            else:
                                print(f"Tweet data (type: {type(tweet)}): {tweet}")
                    else:
                        print("Timeline data structure:")
                        # Print the structure without trying to convert to JSON
                        if isinstance(timeline_data, dict):
                            print(f"Keys: {list(timeline_data.keys())}")
                            for key, value in timeline_data.items():
                                print(f"{key}: {type(value)}")
                                if isinstance(value, (list, dict)):
                                    print(f"  Length: {len(value)}")
                        else:
                            print(f"Type: {type(timeline_data)}")
                            print(f"Dir: {dir(timeline_data)}")
                except Exception as e:
                    print(f"❌ Error processing timeline data: {str(e)}")
                    print(f"Result type: {type(timeline_result)}")
                    print(f"Available attributes: {dir(timeline_result)}")
        except Exception as e:
            print(f"❌ Error testing get_home_timeline: {str(e)}")
        
        # 2. Create tweet (commented out for safety)
        print("\n2. Testing create_tweet (simulation only)...")
        print("To create a tweet, you would use:")
        print('await client.call_tool("create_tweet", {"text": "Your tweet text"})')
        
        # 3. Reply to tweet (commented out for safety)
        print("\n3. Testing reply_to_tweet (simulation only)...")
        print("To reply to a tweet, you would use:")
        print('await client.call_tool("reply_to_tweet", {"tweet_id": "tweet_id", "text": "Your reply text"})')
        
        print("\nTwitter MCP integration test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error in Twitter MCP integration test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up resources
        if client:
            await client.cleanup()

if __name__ == "__main__":
    success = asyncio.run(test_twitter_mcp())
    
    if success:
        print("\n✅ Test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Test failed!")
        print("\nTroubleshooting tips:")
        print("1. Make sure the x-mcp-server is properly installed and built:")
        print("   - cd x-mcp-server")
        print("   - npm install")
        print("   - npm run build")
        print("2. Check that your Twitter API credentials are correctly set in your .env file")
        print("3. Verify that the MCP client is properly configured")
        print("4. Check for any error messages in the output")
        sys.exit(1)

from fastapi import APIRouter
from ...services.ai_assistant.mcp_scraper import scrape_awesome_mcp_servers
import logging

# Configure logging including file name
logging.basicConfig(
    level=logging.INFO, 
    format="%(filename)s:%(lineno)d - %(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/mcps/list")
async def list_mcps():
    logger.info("Fetching MCP list from awesome-mcp-servers GitHub repo...")
    mcps = await scrape_awesome_mcp_servers()
    instructions = (
        "To add a server, copy its link and add it to your servers_config.json under the MCP servers section. "
        "Example: {\n  \"name\": \"<Server Name>\",\n  \"url\": \"<Server Link>\",\n  ...\n}" )
    return {
        "mcps": mcps,
        "instructions": instructions,
    }

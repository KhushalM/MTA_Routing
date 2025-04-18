import logging
import requests
import re
from typing import List, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(filename)s - %(lineno)d - %(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def scrape_awesome_mcp_servers() -> List[Dict[str, str]]:
    """
    Scrape the awesome-mcp-servers GitHub repo for MCP servers.
    Returns:
        List of dicts: [{name, link, description}]
    """
    logger.info("Starting awesome-mcp-servers GitHub scraper")

    url = "https://raw.githubusercontent.com/punkpeye/awesome-mcp-servers/main/README.md"
    resp = requests.get(url, timeout=10)
    if resp.status_code != 200:
        logger.error(f"Failed to fetch README.md from GitHub (status {resp.status_code})")
        return []
    md = resp.text
    mcps = []
    # Regex for markdown links with description: - [Name](link) - description
    pattern = re.compile(r"^- \[([^\]]+)\]\(([^\)]+)\)\s*-\s*(.*)$", re.MULTILINE)
    for match in pattern.finditer(md):
        name = match.group(1).strip()
        link = match.group(2).strip()
        desc = match.group(3).strip()
        mcps.append({
            "name": name,
            "link": link,
            "description": desc,
        })
    logger.info(f"Found {len(mcps)} MCP servers from GitHub repo.")
    return mcps

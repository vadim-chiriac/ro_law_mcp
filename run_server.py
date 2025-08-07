import sys
import logging
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)

from romanian_legislation_mcp.mcp.mcp_server import start_server, start_http_server

if __name__ == "__main__":
    # Check if we should run in HTTP mode for debugging
    if len(sys.argv) > 1 and sys.argv[1] == "--http":
        print("Starting MCP server in HTTP mode for debugging...")
        start_http_server()
    else:
        print("Starting MCP server in STDIO mode...")
        start_server()
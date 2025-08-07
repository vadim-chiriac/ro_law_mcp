import sys
import logging
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from romanian_legislation_mcp.mcp.mcp_server import start_server, start_http_server

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--http":
        logging.basicConfig(level=logging.INFO)
        print("Starting MCP server in HTTP mode for debugging...")
        start_http_server()
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            stream=sys.stderr
        )
        start_server()
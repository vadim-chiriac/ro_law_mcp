import sys
import logging
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)

from romanian_legislation_mcp.mcp.mcp_server import start_server

if __name__ == "__main__":
    start_server()
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from romanian_legislation_mcp.mcp.mcp_server import start_server

if __name__ == "__main__":
    start_server()
# Romanian Legislation MCP Server

A Model Context Protocol (MCP) server that provides AI assistants with access to Romanian legislation through the official government SOAP API.

## ⚠️ Disclaimer

**This tool is for informational purposes only. It should NOT be relied upon for any kind of legal advice or research.**
**Do NOT make any decisions or perform or not perform any actions based on the output of this tool.**

- The accuracy, completeness, and currency of the information provided cannot be guaranteed
- Legal documents may be subject to amendments, repeals, or interpretations not reflected in this tool
- We assume no responsibility or liability for any errors, omissions, or damages arising from the use of this tool
- Always consult qualified legal professionals and verify information through official sources for any legal matters
- This tool does not replace professional legal research or official government publications

## Summary

This MCP server enables AI assistants to search and retrieve Romanian legislation documents from the official government database at `legislatie.just.ro`. It provides several search methods including content search, title search, number search, and exact document lookup by type, number, year, and issuer.

### Key Features

- **Multiple Search Methods**: Search by content, title, document number, or exact identification
- **Document Changes Tracking**: Retrieves amendment information since the API only provides original document text, not consolidated versions
- **Smart Mappings**: Handles various document type and issuer name variations
- **Size Management**: Automatically manages response sizes for optimal performance with AI assistants
- **MCP Protocol**: Compatible with Claude Desktop and other MCP-enabled applications

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Optional: Configure environment variables**:
   Create a `.env` file with custom settings (all optional):
   ```
   MCP_PORT=5000
   MCP_HOSTNAME=localhost
   WSDL_URL=https://legislatie.just.ro/apiws/FreeWebService.svc?singleWsdl
   CONNECTION_TIMEOUT=10
   READ_TIMEOUT=30
   ```

## Usage

### Running the Server

**For MCP protocol (recommended)**:
```bash
python run_server.py
```

**For HTTP debugging**:
```bash
python run_server.py --http
```

### MCP Integration

Add to your MCP client configuration (e.g., Claude Desktop). Choose the configuration that matches your setup:

#### Option 1: Using system Python (Linux/macOS)
```json
{
  "mcpServers": {
    "romanian-legislation": {
      "command": "python",
      "args": ["/path/to/ro_law_mcp/run_server.py"],
      "cwd": "/path/to/ro_law_mcp"
    }
  }
}
```

#### Option 2: Using virtual environment (Linux/macOS)
```json
{
  "mcpServers": {
    "romanian-legislation": {
      "command": "/path/to/ro_law_mcp/.venv/bin/python",
      "args": ["/path/to/ro_law_mcp/run_server.py"],
      "cwd": "/path/to/ro_law_mcp"
    }
  }
}
```

#### Option 3: Using virtual environment (Windows)
```json
{
  "mcpServers": {
    "romanian-legislation": {
      "command": "C:/path/to/ro_law_mcp/.venv/Scripts/python.exe",
      "args": ["C:/path/to/ro_law_mcp/run_server.py"],
      "cwd": "C:/path/to/ro_law_mcp"
    }
  }
}
```

#### Option 4: Using conda environment
```json
{
  "mcpServers": {
    "romanian-legislation": {
      "command": "/path/to/miniconda3/envs/your-env-name/bin/python",
      "args": ["/path/to/ro_law_mcp/run_server.py"],
      "cwd": "/path/to/ro_law_mcp"
    }
  }
}
```

**Important Notes:**
- Replace `/path/to/ro_law_mcp` with the actual path to your cloned repository
- Use absolute paths for reliability
- On Windows, use forward slashes (`/`) or double backslashes (`\\`) in JSON
- If using a virtual environment, activate it first and install dependencies with `pip install -r requirements.txt`

### Available Tools

- **`health_check`**: Verify server status
- **`content_search`**: Search within document text
- **`title_search`**: Search document titles
- **`number_search`**: Search by document numbers
- **`document_search`**: Find specific documents by type, number, year, and issuer
- **`identify_legal_document`**: Convert natural language document descriptions (e.g., "Civil Code") to exact identification parameters
- **`generic_document_guidance`**: Get guidance for finding specific documents
- **`get_correct_issuer`**: Map issuer descriptions to correct legal terms

## Limitations

- **API Dependency**: Relies on the availability of the Romanian government SOAP API
- **Romanian Language**: Primarily designed for Romanian legal documents and terminology
- **Rate Limits**: Subject to any rate limiting imposed by the government API
- **Document Consolidation**: The SOAP API only provides original document text, not consolidated versions that incorporate amendments. While we retrieve amendment information to help LLMs understand what has changed, we cannot automatically build the current consolidated form of a document from the base text plus amendments
- **Historical Changes**: Change tracking depends on the availability of data in the government system
- **Document Identification Mappings**: The `identify_legal_document` tool relies on hardcoded mappings for major Romanian legal codes (Civil Code, Criminal Code, etc.). These mappings may become outdated if document numbers, years, or legal references change over time. Users should verify document details through official sources for critical applications
- **Network Requirements**: Requires internet connectivity to access the government API

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
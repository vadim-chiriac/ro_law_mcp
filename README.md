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
- **Document Content Search**: Precise text search within specific identified documents with contextual excerpts
- **Document Changes Tracking**: Retrieves amendment information since the API only provides original document text, not consolidated versions
- **Smart Mappings**: Handles various document type and issuer name variations with centralized mapping files
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
   WSDL_URL=https://legislatie.just.ro/apiws/FreeWebService.svc?singleWsdl # SOAP API URL
   CONNECTION_TIMEOUT=10
   READ_TIMEOUT=30
   
   # Response size management (adjust based on your MCP client)
   MAX_RESPONSE_SIZE_BYTES=972800  # 950KB (default for Claude Desktop)
   MAX_TEXT_LENGTH_CHARS=10000     # Character limit before truncation
   TRUNCATION_SUFFIX="[... Content truncated due to size limits ...]"
   ```

## Usage

### Running the Server

**For STDIO transport (recommended)**:
```bash
python run_server.py
```

**For HTTP transport**:
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

**Important Notes:**
- Replace `/path/to/ro_law_mcp` with the actual path to your cloned repository
- Use absolute paths for reliability
- On Windows, use forward slashes (`/`) or double backslashes (`\\`) in JSON
- If using a virtual environment, activate it first and install dependencies with `pip install -r requirements.txt`

### Available Tools

- **`health_check`**: Verify server status
- **`content_search`**: Search the legislation database for documents that may contain query text (broad search)
- **`title_search`**: Search the legislation database for documents with titles that may match query (broad search)  
- **`number_search`**: Search the legislation database for documents with numbers that may match query (broad search)
- **`document_search`**: Find specific documents by exact type, number, year, and issuer
- **`document_content_search`**: Attempts a more accuate text search within a specific identified document, returning contextual excerpts
- **`document_changes`**: Retrieve changes made to a specific document to understand if found excerpts are still current
- **`identify_legal_document`**: Convert natural language document descriptions (e.g., "Civil Code") to exact identification parameters
- **`generic_document_guidance`**: Get guidance for finding specific documents
- **`get_correct_issuer`**: Map issuer descriptions to correct legal terms

#### Search Strategy

For best results, use tools in this order:
1. **For specific documents**: Use `identify_legal_document` → `document_content_search` → `document_changes` (if needed)
2. **For exploration**: Use the broad search tools (`content_search`, `title_search`, `number_search`)
3. **For precise document retrieval**: Use `document_search`

## Limitations

- **API Dependency**: Relies on the availability of the Romanian government SOAP API
- **Romanian Language**: Primarily designed for Romanian legal documents and terminology
- **Rate Limits**: Subject to any rate limiting imposed by the government API
- **Document Consolidation**: The SOAP API only provides original document text, not consolidated versions that incorporate amendments. While we retrieve amendment information to help LLMs understand what has changed, we cannot automatically build the current consolidated form of a document from the base text plus amendments
- **Historical Changes**: Change tracking depends on the availability of data in the government system
- **Document Identification Mappings**: The `identify_legal_document` tool uses centralized mappings for major Romanian legal codes (Civil Code, Criminal Code, etc.) stored in `legal_document_mappings.py`. These mappings may become outdated if document numbers, years, or legal references change over time. Users should verify document details through official sources for critical applications
- **Search Result Relevance**: Current broad searches (`content_search`, `title_search`, `number_search`) often return irrelevant results, including tertiary or local documents that may not be useful for general legal research. We are actively working on improving search result ranking and relevance

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
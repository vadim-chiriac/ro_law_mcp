# Romanian Legislation MCP Server

A Model Context Protocol (MCP) server that provides AI assistants with access to Romanian legislation through the official government SOAP API.
Work in progress.

## ⚠️ Disclaimer

**This tool is for informational purposes only. It should NOT be relied upon for any kind of legal advice or research.**
**Do NOT make any decisions or perform or not perform any actions based on the output of this tool.**

- The accuracy, completeness, and currency of the information provided cannot be guaranteed
- Legal documents may be subject to amendments, repeals, or interpretations not reflected in this tool
- We assume no responsibility or liability for any errors, omissions, or damages arising from the use of this tool
- Always consult qualified legal professionals and verify information through official sources for any legal matters
- This tool does not replace professional legal research or official government publications

## Summary


This MCP server enables AI assistants to search and retrieve Romanian legislation documents from the official government database at `legislatie.just.ro`. Currently, only retrieval and search in a single document is supported. 

### Key Features

- **Document Parsing**: Create structured data from the raw text of a legal document (might return an incorrect structure for certain documents)
- **Document Content Search**: Precise text search within specific identified documents with contextual excerpts
- **Document Article Retrieval**: Retrieve one or more specific articles from a legal document
- **Document Changes Tracking**: Retrieves amendment metadata since the API only provides original document text, not consolidated versions
- **Smart Mappings**: Handles various document type and issuer name variations with centralized mapping files
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

### Testing Document Retrieval

Use the `test_structured_document.py` script to test document retrieval and parsing directly. This is useful for development, debugging, or exploring the document structure before using the MCP server.

**Basic Usage:**
```bash
python test_structured_document.py --type <TYPE> --number <NUMBER> --year <YEAR> --issuer <ISSUER>
```

**Command Line Options:**
- `--type, -t`: Document type (e.g., `LEGE`, `ORDONANTA`, `HOTARARE`)
- `--number, -n`: Document number (integer)
- `--year, -y`: Publication year (integer)  
- `--issuer, -i`: Issuing authority (e.g., `Parlamentul`, `Guvernul`)
- `--article, -a`: Optional specific article number to retrieve

**Examples:**

```bash
# Romanian Criminal Code
python test_structured_document.py --type LEGE --number 286 --year 2009 --issuer Parlamentul

# Romanian Civil Code with specific article
python test_structured_document.py --type LEGE --number 287 --year 2009 --issuer Parlamentul --article 1

# Government ordinance using short flags
python test_structured_document.py -t OUG -n 57 -y 2019 -i Guvernul

# Recent legislation
python test_structured_document.py --type LEGE --number 140 --year 2022 --issuer Parlamentul
```

**Output:**
- Creates `structure_<TYPE>_<NUMBER>_<YEAR>.json` with document hierarchy
- Creates `amendments_<TYPE>_<NUMBER>_<YEAR>.json` with amendment metadata
- Displays document statistics and article information in the console

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

#### Option 1: Using system Python (Windows)
```json
{
  "mcpServers": {
    "romanian-legislation": {
      "command": "python",
      "args": ["C:/path/to/ro_law_mcp/run_server.py"],
      "cwd": "C:/path/to/ro_law_mcp"
    }
  }
}
```

#### Option 2: Using virtual environment (Linux/macOS) (NEEDS TO BE CREATED AND ACTIVATED)
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

#### Option 3: Using virtual environment (Windows) (NEEDS TO BE CREATED AND ACTIVATED)
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

- **`get_document_data`**: Retrieve and structure a specific legal document by its exact identifiers (type, number, year, issuer). Returns document metadata, table of contents, and structural amendment information.

- **`get_one_or_more_articles`**: Get the full content of one or more specific articles (comma-separated) from a document. 

- **`search_in_document`**: Search within the text contents of a specific document using fuzzy search. Supports narrowing search to specific document sections using start/end positions from the document's table of contents.

- **`identify_legal_document`**: Convert natural language document descriptions (e.g., "Civil Code", "Criminal Code") to exact identification parameters needed for document retrieval.

- **`get_correct_issuer`**: Map various issuer descriptions (e.g., "prime minister", "finance ministry") to the correct legal terms required by the SOAP API.

## Troubleshooting

This is a work in progress so expect issues. If experiencing weird behavior, try clearing the document cache in the `.document_cache` folder.
For Claude Desktop, it will be located at: `C:\Users\[USERNAME]\AppData\Local\AnthropicClaude\[APP-FOLDER]` 

## Limitations

- **API Dependency**: Relies on the availability of the Romanian government SOAP API
- **Romanian Language**: Primarily designed for Romanian legal documents and terminology
- **Rate Limits**: Subject to any rate limiting imposed by the government API
- **Document Consolidation**: The SOAP API only provides original document text, not consolidated versions that incorporate amendments. While we retrieve amendment information to help LLMs understand what has changed, we cannot automatically build the current consolidated form of a document from the base text plus amendments
- **Document Identification Mappings**: The `identify_legal_document` tool uses centralized mappings for major Romanian legal codes (Civil Code, Criminal Code, etc.) stored in `legal_document_mappings.py`. These mappings may become outdated if document numbers, years, or legal references change over time. Users should verify document details through official sources for critical applications

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
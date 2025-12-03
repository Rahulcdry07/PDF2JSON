# MCP Integration for PDF2JSON DSR System

## Overview

The PDF2JSON DSR Rate Matching System now includes a **Model Context Protocol (MCP)** server that exposes its functionality to AI assistants like Claude Desktop.

## What is MCP?

Model Context Protocol (MCP) is an open protocol that standardizes how applications provide context to Large Language Models (LLMs). With MCP, AI assistants can:

- Access your DSR databases in real-time
- Search for construction rates and codes
- Calculate cost estimations
- Convert PDFs to structured data
- Query reference materials

## Features

The MCP server provides:

### 📊 Resources
- **DSR Databases**: Access to complete DSR code databases by category
- **Category Information**: Statistics and file listings for each category

### 🔧 Tools

1. **search_dsr_code** - Find specific DSR codes and rates
2. **search_dsr_by_description** - Semantic search using similarity matching
3. **calculate_cost** - Instant cost calculations
4. **get_chapter_codes** - Browse codes by chapter
5. **convert_pdf_to_json** - PDF conversion with table extraction
6. **list_categories** - View all available categories

## Installation

### 1. Install MCP SDK

```bash
pip install mcp
```

### 2. Update requirements.txt

```bash
echo "mcp>=0.9.0" >> requirements.txt
```

### 3. Test with Web Interface

Before configuring Claude Desktop, test the tools using the web interface:

```bash
python mcp_web_interface.py
# Opens at http://localhost:5001
```

### 4. Configure Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "pdf2json-dsr": {
      "command": "python",
### 5. Restart Claude Desktop

The MCP server will be available in Claude Desktop's context menu.
  }
}
```

**Note**: Update the path to match your installation directory.

### 4. Restart Claude Desktop

The MCP server will be available in Claude Desktop's context menu.

## Usage Examples

### In Claude Desktop

Once configured, you can ask Claude:

**Example 1: Search for a DSR code**
```
What is the rate for DSR code 15.12.2?
```

**Example 2: Find similar work items**
```
Find DSR codes related to "brick work in superstructure"
```

**Example 3: Calculate costs**
```
Calculate the cost for 100 cubic meters of DSR code 15.12.2
```

**Example 4: Browse chapters**
```
Show me all DSR codes in Chapter 15 (Brick Work)
```

**Example 5: Convert PDFs**
```
Convert this PDF to JSON: /path/to/document.pdf
```

## Testing the MCP Server

### Web Testing Interface (Recommended)

The easiest way to test all MCP tools is through the web interface:

```bash
# Start the web interface
python mcp_web_interface.py
```

Then open your browser to `http://localhost:5001`

The web interface provides:
- 🎨 **Beautiful UI** for testing all MCP tools
- 📊 **Category Browser** with statistics
- 🔍 **Search Tools** for codes and descriptions
- 💰 **Cost Calculator** with instant results
- 📚 **Chapter Browser** for exploring DSR codes
- 📄 **PDF Converter** with file upload

### Test Locally (Command Line)

```bash
# Test the server directly
python mcp_server.py

# Or use the MCP inspector
npx @modelcontextprotocol/inspector python mcp_server.py
```

### Test with CLI

```bash
# Install MCP CLI tools
npm install -g @modelcontextprotocol/cli

# Test the server
mcp-cli call pdf2json-dsr search_dsr_code --code "15.12.2" --category "civil"
```

## Available Tools Reference

### search_dsr_code
Search for a specific DSR code.

**Parameters:**
- `code` (required): DSR code (e.g., "15.12.2")
- `category` (optional): Category name (default: "civil")

**Returns:**
```json
{
  "found": true,
  "code": "15.12.2",
  "chapter": "Chapter 15",
  "description": "Brick work in superstructure...",
  "unit": "Cum",
  "rate": "₹502.75",
  "volume": "Vol 1",
  "page": 120
}
```

### search_dsr_by_description
Semantic search using text similarity.

**Parameters:**
- `description` (required): Search text
- `category` (optional): Category (default: "civil")
- `limit` (optional): Max results (default: 5)
- `min_similarity` (optional): Minimum score (default: 0.5)

**Returns:**
```json
{
  "query": "brick work",
  "results_found": 3,
  "matches": [
    {
      "code": "15.12.2",
      "description": "Brick work in superstructure...",
      "rate": 502.75,
      "similarity": 0.856
    }
  ]
}
```

### calculate_cost
Calculate total cost for a work item.

**Parameters:**
- `code` (required): DSR code
- `quantity` (required): Quantity of work
- `unit` (optional): Unit for verification
- `category` (optional): Category (default: "civil")

**Returns:**
```json
{
  "code": "15.12.2",
  "quantity": 100,
  "rate_per_unit": "₹502.75",
  "total_cost": "₹50,275.00",
  "calculation": "100 Cum × ₹502.75 = ₹50,275.00"
}
```

### get_chapter_codes
Get all codes from a chapter.

**Parameters:**
- `chapter` (required): Chapter name or number
- `category` (optional): Category (default: "civil")

**Returns:**
```json
{
  "chapter": "Chapter 15",
  "codes_found": 25,
  "codes": [...]
}
```

### convert_pdf_to_json
Convert PDF to structured JSON.

**Parameters:**
- `pdf_path` (required): Absolute path to PDF
- `extract_tables` (optional): Extract tables (default: false)

**Returns:**
```json
{
  "success": true,
  "summary": {
    "pages": 10,
    "tables_extracted": true
  },
  "full_result": {...}
}
```

### list_categories
List all available DSR categories.

**Parameters:** None

**Returns:**
```json
{
  "total_categories": 5,
  "categories": [
    {
      "name": "civil",
      "total_codes": 2233,
      "total_chapters": 20
    }
  ]
}
```

## Resources

The server exposes DSR databases as resources:

- `dsr://database/civil` - Civil DSR database with statistics
- `dsr://category/civil` - Civil category files and metadata
- `dsr://category/electrical` - Electrical category
- etc.

## Architecture

```
┌─────────────────┐
│  Claude Desktop │
│  (AI Assistant) │
└────────┬────────┘
         │ MCP Protocol
         │
┌────────▼────────┐
│   mcp_server.py │
│  (MCP Server)   │
└────────┬────────┘
         │
    ┌────┴──────┬──────────┬───────────┐
    │           │          │           │
┌───▼────┐ ┌───▼────┐ ┌──▼─────┐ ┌───▼────┐
│PDF2JSON│ │Scripts │ │Database│ │  Web   │
│Converter│ │(DSR)   │ │(SQLite)│ │Interface│
└────────┘ └────────┘ └────────┘ └────────┘
```

## Benefits

1. **AI-Powered Queries**: Natural language access to DSR data
2. **Real-Time Data**: Always up-to-date rates and codes
3. **Intelligent Search**: Semantic matching finds relevant codes
4. **Instant Calculations**: Quick cost estimations
5. **Integration**: Works seamlessly with Claude Desktop
6. **Extensible**: Easy to add new tools and features

## Development

### Adding New Tools

```python
@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="your_tool_name",
            description="What your tool does",
            inputSchema={...}
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Any):
    if name == "your_tool_name":
        # Your implementation
        return [TextContent(type="text", text=result)]
```

### Adding New Resources

```python
@server.list_resources()
async def list_resources() -> list[Resource]:
    return [
        Resource(
            uri="your://resource/uri",
            name="Resource Name",
            description="Resource description"
        )
    ]

@server.read_resource()
async def read_resource(uri: str) -> str:
    if uri == "your://resource/uri":
        return json.dumps(your_data)
```

## Troubleshooting

### Server won't start
- Check Python path in config
- Ensure all dependencies installed: `pip install mcp`
- Verify database files exist in reference_files/

### Claude can't find tools
- Restart Claude Desktop after config changes
- Check logs: `~/Library/Logs/Claude/mcp-server-pdf2json-dsr.log`
- Verify server path is absolute

### Database not found errors
- Ensure reference_files/ directory has category subdirectories
- Check database files: `DSR_Civil_combined.db`, etc.
- Run: `ls reference_files/civil/`

## Performance

- **Search queries**: < 100ms
- **Similarity matching**: < 500ms for 2000+ codes
- **Cost calculations**: < 10ms
- **PDF conversion**: Depends on PDF size

## Security

- MCP server runs locally (no external connections)
- Only reads from reference databases
- No write access to databases
- PDF conversion sandboxed

## Future Enhancements

- [ ] Multi-category search across all DSRs
- [ ] Rate comparison across years/volumes
- [ ] Export to Excel/CSV directly
- [ ] Batch cost estimation
- [ ] Historical rate tracking
- [ ] Budget template generation

## Support

For issues or questions:
1. Check logs in Claude Desktop
2. Test server directly: `python mcp_server.py`
3. Verify database integrity
4. Review MCP documentation: https://modelcontextprotocol.io

## License

Same as parent project (PDF2JSON DSR System)

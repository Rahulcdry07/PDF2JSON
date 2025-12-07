#!/usr/bin/env python3
"""
MCP Server for PDF2JSON DSR Rate Matching System

This MCP server exposes the DSR rate matching functionality as tools that can be used
by AI assistants through the Model Context Protocol.

Features:
- Search DSR codes and rates
- Convert PDFs to JSON
- Match construction items with DSR rates
- Query cost estimations
- Access reference databases
"""

import asyncio
import json
import sqlite3
from pathlib import Path
from typing import Any, Sequence
import sys
import warnings
import os

# Suppress warnings that might interfere with JSON output
warnings.filterwarnings("ignore")

# Suppress all logging output to avoid interfering with JSON-RPC
os.environ["MCP_LOG_LEVEL"] = "CRITICAL"
import logging

logging.basicConfig(level=logging.CRITICAL)
for logger_name in ["mcp", "mcp.server", "mcp.server.lowlevel"]:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.CRITICAL)
    logger.disabled = True

# Add project paths
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# Import project modules
from pdf2json.converter import PDFToXMLConverter
from text_similarity import calculate_text_similarity

# Server instance
server = Server("estimatex")

# Constants
REFERENCE_FILES = PROJECT_ROOT / "reference_files"
DSR_DATABASE = REFERENCE_FILES / "civil" / "DSR_Civil_combined.db"


@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available DSR reference resources."""
    resources = []

    # Add DSR database as resource
    if DSR_DATABASE.exists():
        resources.append(
            Resource(
                uri=f"dsr://database/civil",
                name="DSR Civil Database",
                mimeType="application/x-sqlite3",
                description="Complete DSR codes database for civil construction with rates",
            )
        )

    # Add reference files
    for category_dir in REFERENCE_FILES.iterdir():
        if category_dir.is_dir():
            resources.append(
                Resource(
                    uri=f"dsr://category/{category_dir.name}",
                    name=f"DSR {category_dir.name.title()} Category",
                    mimeType="application/json",
                    description=f"DSR codes and rates for {category_dir.name} category",
                )
            )

    return resources


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read a DSR resource."""
    if uri.startswith("dsr://database/"):
        category = uri.split("/")[-1]
        db_path = REFERENCE_FILES / category / f"DSR_{category.title()}_combined.db"

        if not db_path.exists():
            raise ValueError(f"Database not found for category: {category}")

        # Return database statistics
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM dsr_codes")
        total_codes = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT chapter) FROM dsr_codes")
        total_chapters = cursor.fetchone()[0]

        cursor.execute("SELECT MIN(rate), MAX(rate), AVG(rate) FROM dsr_codes")
        rate_stats = cursor.fetchone()

        conn.close()

        return json.dumps(
            {
                "category": category,
                "total_codes": total_codes,
                "total_chapters": total_chapters,
                "rate_range": {
                    "min": rate_stats[0],
                    "max": rate_stats[1],
                    "average": round(rate_stats[2], 2),
                },
            },
            indent=2,
        )

    elif uri.startswith("dsr://category/"):
        category = uri.split("/")[-1]
        category_path = REFERENCE_FILES / category

        if not category_path.exists():
            raise ValueError(f"Category not found: {category}")

        # List files in category
        files = []
        for file in category_path.iterdir():
            if file.is_file():
                files.append({"name": file.name, "size": file.stat().st_size, "type": file.suffix})

        return json.dumps({"category": category, "files": files}, indent=2)

    raise ValueError(f"Unknown resource URI: {uri}")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available DSR tools."""
    return [
        Tool(
            name="search_dsr_code",
            description="Search for a specific DSR code and get its rate, description, and details",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "DSR code to search (e.g., '15.12.2', '16.5.1')",
                    },
                    "category": {
                        "type": "string",
                        "description": "Category to search in (civil, electrical, horticulture, etc.)",
                        "default": "civil",
                    },
                },
                "required": ["code"],
            },
        ),
        Tool(
            name="search_dsr_by_description",
            description="Search DSR codes by description text using similarity matching",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Description text to search for (e.g., 'brick work', 'cement plaster')",
                    },
                    "category": {
                        "type": "string",
                        "description": "Category to search in",
                        "default": "civil",
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of results to return",
                        "default": 5,
                    },
                    "min_similarity": {
                        "type": "number",
                        "description": "Minimum similarity score (0.0 to 1.0)",
                        "default": 0.5,
                    },
                },
                "required": ["description"],
            },
        ),
        Tool(
            name="calculate_cost",
            description="Calculate cost for a construction item given DSR code, quantity, and unit",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "DSR code"},
                    "quantity": {"type": "number", "description": "Quantity of work"},
                    "unit": {
                        "type": "string",
                        "description": "Unit of measurement (optional, for verification)",
                    },
                    "category": {"type": "string", "description": "Category", "default": "civil"},
                },
                "required": ["code", "quantity"],
            },
        ),
        Tool(
            name="get_chapter_codes",
            description="Get all DSR codes from a specific chapter",
            inputSchema={
                "type": "object",
                "properties": {
                    "chapter": {
                        "type": "string",
                        "description": "Chapter name or number (e.g., 'Chapter 15', 'Brick Work')",
                    },
                    "category": {"type": "string", "description": "Category", "default": "civil"},
                },
                "required": ["chapter"],
            },
        ),
        Tool(
            name="convert_pdf_to_json",
            description="Convert a PDF file to JSON format with text and table extraction",
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {"type": "string", "description": "Absolute path to the PDF file"},
                    "extract_tables": {
                        "type": "boolean",
                        "description": "Whether to extract tables from the PDF",
                        "default": False,
                    },
                },
                "required": ["pdf_path"],
            },
        ),
        Tool(
            name="list_categories",
            description="List all available DSR categories with statistics",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(
    name: str, arguments: Any
) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls."""

    if name == "search_dsr_code":
        code = arguments["code"]
        category = arguments.get("category", "civil")

        db_path = REFERENCE_FILES / category / f"DSR_{category.title()}_combined.db"
        if not db_path.exists():
            return [
                TextContent(
                    type="text", text=f"Error: Database not found for category '{category}'"
                )
            ]

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT code, chapter, section, description, unit, rate, volume, page
            FROM dsr_codes
            WHERE code = ? AND category = ?
        """,
            (code, category),
        )

        result = cursor.fetchone()
        conn.close()

        if result:
            result_dict = dict(result)
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "found": True,
                            "code": result_dict["code"],
                            "chapter": result_dict["chapter"],
                            "section": result_dict["section"],
                            "description": result_dict["description"],
                            "unit": result_dict["unit"],
                            "rate": f"₹{result_dict['rate']}",
                            "volume": result_dict["volume"],
                            "page": result_dict["page"],
                        },
                        indent=2,
                    ),
                )
            ]
        else:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "found": False,
                            "message": f"DSR code '{code}' not found in {category} category",
                        }
                    ),
                )
            ]

    elif name == "search_dsr_by_description":
        description = arguments["description"]
        category = arguments.get("category", "civil")
        limit = arguments.get("limit", 5)
        min_similarity = arguments.get("min_similarity", 0.5)

        db_path = REFERENCE_FILES / category / f"DSR_{category.title()}_combined.db"
        if not db_path.exists():
            return [
                TextContent(
                    type="text", text=f"Error: Database not found for category '{category}'"
                )
            ]

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get all codes and calculate similarity
        cursor.execute(
            """
            SELECT code, description, unit, rate, chapter, section
            FROM dsr_codes
            WHERE category = ?
        """,
            (category,),
        )

        results = []
        for row in cursor.fetchall():
            similarity = calculate_text_similarity(description, row["description"])
            if similarity >= min_similarity:
                results.append(
                    {
                        "code": row["code"],
                        "description": row["description"],
                        "unit": row["unit"],
                        "rate": row["rate"],
                        "chapter": row["chapter"],
                        "section": row["section"],
                        "similarity": round(similarity, 3),
                    }
                )

        conn.close()

        # Sort by similarity and limit
        results.sort(key=lambda x: x["similarity"], reverse=True)
        results = results[:limit]

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"query": description, "results_found": len(results), "matches": results},
                    indent=2,
                ),
            )
        ]

    elif name == "calculate_cost":
        code = arguments["code"]
        quantity = arguments["quantity"]
        unit = arguments.get("unit")
        category = arguments.get("category", "civil")

        db_path = REFERENCE_FILES / category / f"DSR_{category.title()}_combined.db"
        if not db_path.exists():
            return [
                TextContent(
                    type="text", text=f"Error: Database not found for category '{category}'"
                )
            ]

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT code, description, unit, rate
            FROM dsr_codes
            WHERE code = ? AND category = ?
        """,
            (code, category),
        )

        result = cursor.fetchone()
        conn.close()

        if not result:
            return [TextContent(type="text", text=f"Error: DSR code '{code}' not found")]

        rate = result["rate"]
        dsr_unit = result["unit"]
        cost = quantity * rate

        response = {
            "code": code,
            "description": result["description"],
            "quantity": quantity,
            "unit": dsr_unit,
            "rate_per_unit": f"₹{rate}",
            "total_cost": f"₹{cost:,.2f}",
            "calculation": f"{quantity} {dsr_unit} × ₹{rate} = ₹{cost:,.2f}",
        }

        if unit and unit.lower() != dsr_unit.lower():
            response["warning"] = f"Unit mismatch: provided '{unit}' but DSR unit is '{dsr_unit}'"

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    elif name == "get_chapter_codes":
        chapter = arguments["chapter"]
        category = arguments.get("category", "civil")

        db_path = REFERENCE_FILES / category / f"DSR_{category.title()}_combined.db"
        if not db_path.exists():
            return [
                TextContent(
                    type="text", text=f"Error: Database not found for category '{category}'"
                )
            ]

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Search by chapter name or number
        cursor.execute(
            """
            SELECT code, description, unit, rate, chapter, section
            FROM dsr_codes
            WHERE (chapter LIKE ? OR section LIKE ?) AND category = ?
            ORDER BY code
        """,
            (f"%{chapter}%", f"%{chapter}%", category),
        )

        results = []
        for row in cursor.fetchall():
            results.append(
                {
                    "code": row["code"],
                    "description": (
                        row["description"][:80] + "..."
                        if len(row["description"]) > 80
                        else row["description"]
                    ),
                    "unit": row["unit"],
                    "rate": row["rate"],
                    "chapter": row["chapter"],
                    "section": row["section"],
                }
            )

        conn.close()

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "chapter": chapter,
                        "category": category,
                        "codes_found": len(results),
                        "codes": results,
                    },
                    indent=2,
                ),
            )
        ]

    elif name == "convert_pdf_to_json":
        pdf_path = Path(arguments["pdf_path"])
        extract_tables = arguments.get("extract_tables", False)

        if not pdf_path.exists():
            return [TextContent(type="text", text=f"Error: PDF file not found: {pdf_path}")]

        try:
            with PDFToXMLConverter(str(pdf_path)) as converter:
                result = converter.convert(extract_tables=extract_tables)

                # Summarize result
                doc = result["document"]
                summary = {
                    "source": doc["source"],
                    "pages": doc["pages"],
                    "tables_extracted": extract_tables,
                    "pages_processed": len(doc["pages_data"]),
                }

                # Add first page preview
                if doc["pages_data"]:
                    first_page = doc["pages_data"][0]
                    if "text" in first_page:
                        summary["first_page_preview"] = first_page["text"][:200] + "..."

                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {"success": True, "summary": summary, "full_result": result}, indent=2
                        ),
                    )
                ]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"success": False, "error": str(e)}))]

    elif name == "list_categories":
        categories = []

        for category_dir in REFERENCE_FILES.iterdir():
            if not category_dir.is_dir():
                continue

            # Check for database
            db_path = category_dir / f"DSR_{category_dir.name.title()}_combined.db"
            if db_path.exists():
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM dsr_codes")
                total_codes = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(DISTINCT chapter) FROM dsr_codes")
                total_chapters = cursor.fetchone()[0]

                conn.close()

                categories.append(
                    {
                        "name": category_dir.name,
                        "total_codes": total_codes,
                        "total_chapters": total_chapters,
                        "database": db_path.name,
                    }
                )

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"total_categories": len(categories), "categories": categories}, indent=2
                ),
            )
        ]

    raise ValueError(f"Unknown tool: {name}")


async def main():
    """Main entry point for the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())

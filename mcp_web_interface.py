#!/usr/bin/env python3
"""
Web Interface for MCP Server Testing

A Flask-based web interface to test and interact with the MCP server tools
without needing Claude Desktop configuration.
"""

from flask import Flask, render_template, request, jsonify, session
import json
import sqlite3
from pathlib import Path
import sys

# Add project paths
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from estimatex.converter import PDFToXMLConverter
from text_similarity import calculate_text_similarity

app = Flask(__name__)
app.secret_key = "mcp-web-interface-secret-key-change-in-production"

REFERENCE_FILES = PROJECT_ROOT / "reference_files"
UPLOADS_DIR = PROJECT_ROOT / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)


def get_db_path(category="civil"):
    """Get database path for category."""
    return REFERENCE_FILES / category / f"DSR_{category.title()}_combined.db"


@app.route("/")
def index():
    """MCP web interface home page."""
    return render_template("mcp_interface.html")


@app.route("/api/categories", methods=["GET"])
def api_list_categories():
    """List all available DSR categories."""
    categories = []

    for category_dir in REFERENCE_FILES.iterdir():
        if not category_dir.is_dir():
            continue

        db_path = category_dir / f"DSR_{category_dir.name.title()}_combined.db"
        if db_path.exists():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM dsr_codes")
            total_codes = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT chapter) FROM dsr_codes")
            total_chapters = cursor.fetchone()[0]

            cursor.execute("SELECT MIN(rate), MAX(rate), AVG(rate) FROM dsr_codes")
            rate_stats = cursor.fetchone()

            conn.close()

            categories.append(
                {
                    "name": category_dir.name,
                    "total_codes": total_codes,
                    "total_chapters": total_chapters,
                    "rate_stats": {
                        "min": rate_stats[0],
                        "max": rate_stats[1],
                        "average": round(rate_stats[2], 2) if rate_stats[2] else 0,
                    },
                }
            )

    return jsonify({"success": True, "total_categories": len(categories), "categories": categories})


@app.route("/api/search_code", methods=["POST"])
def api_search_code():
    """Search for a specific DSR code."""
    data = request.get_json()
    code = data.get("code", "").strip()
    category = data.get("category", "civil")

    if not code:
        return jsonify({"success": False, "error": "DSR code is required"}), 400

    db_path = get_db_path(category)
    if not db_path.exists():
        return (
            jsonify({"success": False, "error": f"Database not found for category '{category}'"}),
            404,
        )

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
        return jsonify(
            {
                "success": True,
                "found": True,
                "result": {
                    "code": result["code"],
                    "chapter": result["chapter"],
                    "section": result["section"],
                    "description": result["description"],
                    "unit": result["unit"],
                    "rate": result["rate"],
                    "volume": result["volume"],
                    "page": result["page"],
                },
            }
        )
    else:
        return jsonify(
            {
                "success": True,
                "found": False,
                "message": f"DSR code '{code}' not found in {category} category",
            }
        )


@app.route("/api/search_description", methods=["POST"])
def api_search_description():
    """Search DSR codes by description using similarity matching."""
    data = request.get_json()
    description = data.get("description", "").strip()
    category = data.get("category", "civil")
    limit = int(data.get("limit", 5))
    min_similarity = float(data.get("min_similarity", 0.5))

    if not description:
        return jsonify({"success": False, "error": "Description is required"}), 400

    db_path = get_db_path(category)
    if not db_path.exists():
        return (
            jsonify({"success": False, "error": f"Database not found for category '{category}'"}),
            404,
        )

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

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

    return jsonify(
        {"success": True, "query": description, "results_found": len(results), "matches": results}
    )


@app.route("/api/calculate_cost", methods=["POST"])
def api_calculate_cost():
    """Calculate cost for a construction item."""
    data = request.get_json()
    code = data.get("code", "").strip()
    quantity = data.get("quantity")
    category = data.get("category", "civil")

    if not code:
        return jsonify({"success": False, "error": "DSR code is required"}), 400

    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Valid quantity is required"}), 400

    db_path = get_db_path(category)
    if not db_path.exists():
        return (
            jsonify({"success": False, "error": f"Database not found for category '{category}'"}),
            404,
        )

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
        return jsonify({"success": False, "error": f"DSR code '{code}' not found"}), 404

    rate = result["rate"]
    cost = quantity * rate

    return jsonify(
        {
            "success": True,
            "code": code,
            "description": result["description"],
            "quantity": quantity,
            "unit": result["unit"],
            "rate_per_unit": rate,
            "total_cost": round(cost, 2),
            "calculation": f"{quantity} {result['unit']} × ₹{rate} = ₹{cost:,.2f}",
        }
    )


@app.route("/api/get_chapter", methods=["POST"])
def api_get_chapter():
    """Get all DSR codes from a specific chapter."""
    data = request.get_json()
    chapter = data.get("chapter", "").strip()
    category = data.get("category", "civil")

    if not chapter:
        return jsonify({"success": False, "error": "Chapter name or number is required"}), 400

    db_path = get_db_path(category)
    if not db_path.exists():
        return (
            jsonify({"success": False, "error": f"Database not found for category '{category}'"}),
            404,
        )

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

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
                "description": row["description"],
                "unit": row["unit"],
                "rate": row["rate"],
                "chapter": row["chapter"],
                "section": row["section"],
            }
        )

    conn.close()

    return jsonify(
        {
            "success": True,
            "chapter": chapter,
            "category": category,
            "codes_found": len(results),
            "codes": results,
        }
    )


@app.route("/api/convert_pdf", methods=["POST"])
def api_convert_pdf():
    """Convert uploaded PDF to JSON."""
    if "pdf_file" not in request.files:
        return jsonify({"success": False, "error": "No PDF file uploaded"}), 400

    pdf_file = request.files["pdf_file"]
    extract_tables = request.form.get("extract_tables", "false").lower() == "true"

    if pdf_file.filename == "":
        return jsonify({"success": False, "error": "No file selected"}), 400

    if not pdf_file.filename.lower().endswith(".pdf"):
        return jsonify({"success": False, "error": "File must be a PDF"}), 400

    # Save uploaded file
    pdf_path = UPLOADS_DIR / pdf_file.filename
    pdf_file.save(pdf_path)

    try:
        with PDFToXMLConverter(str(pdf_path)) as converter:
            result = converter.convert(extract_tables=extract_tables)

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
                    summary["first_page_preview"] = first_page["text"][:300] + "..."

            # Save JSON output
            json_filename = pdf_path.stem + ".json"
            json_path = UPLOADS_DIR / json_filename
            with open(json_path, "w") as f:
                json.dump(result, f, indent=2)

            return jsonify(
                {
                    "success": True,
                    "summary": summary,
                    "json_file": json_filename,
                    "download_url": f"/downloads/{json_filename}",
                }
            )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/get_chapters", methods=["POST"])
def api_get_chapters():
    """Get list of all chapters in a category."""
    data = request.get_json()
    category = data.get("category", "civil")

    db_path = get_db_path(category)
    if not db_path.exists():
        return (
            jsonify({"success": False, "error": f"Database not found for category '{category}'"}),
            404,
        )

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT DISTINCT chapter
        FROM dsr_codes
        WHERE category = ?
        ORDER BY chapter
    """,
        (category,),
    )

    chapters = [row[0] for row in cursor.fetchall()]
    conn.close()

    return jsonify({"success": True, "category": category, "chapters": chapters})


@app.route("/downloads/<filename>")
def download_file(filename):
    """Download converted JSON file."""
    from flask import send_from_directory

    return send_from_directory(UPLOADS_DIR, filename, as_attachment=True)


if __name__ == "__main__":
    print("=" * 60)
    print("MCP Web Interface for EstimateX DSR System")
    print("=" * 60)
    print("\nStarting server on http://localhost:5001")
    print("\nAvailable endpoints:")
    print("  - Home: http://localhost:5001/")
    print("  - API: http://localhost:5001/api/*")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)

    app.run(debug=True, port=5001, host="0.0.0.0")

"""
OpenAPI/Swagger specification for EstimateX API
"""

API_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "EstimateX API",
        "description": "PDF conversion and DSR rate matching API for construction cost estimation",
        "version": "1.0.0",
        "contact": {"name": "API Support", "url": "https://github.com/Rahulcdry07/PDF2JSON"},
    },
    "servers": [{"url": "http://localhost:8000", "description": "Development server"}],
    "tags": [
        {"name": "PDF Conversion", "description": "Upload and convert PDF files to JSON"},
        {"name": "DSR Matching", "description": "Cost estimation and DSR rate matching"},
        {"name": "Excel Operations", "description": "Excel to PDF conversion"},
        {"name": "Analytics", "description": "Usage statistics and analytics"},
        {"name": "System", "description": "Health checks and system information"},
    ],
    "paths": {
        "/": {
            "get": {
                "tags": ["System"],
                "summary": "Home page",
                "description": "Display dashboard with all available files",
                "responses": {"200": {"description": "HTML page with file listings"}},
            }
        },
        "/health": {
            "get": {
                "tags": ["System"],
                "summary": "Health check",
                "description": "Check if the API is running and responsive",
                "responses": {
                    "200": {
                        "description": "Service is healthy",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {"type": "string", "example": "healthy"},
                                        "timestamp": {"type": "string", "format": "date-time"},
                                    },
                                }
                            }
                        },
                    }
                },
            }
        },
        "/api/stats": {
            "get": {
                "tags": ["Analytics"],
                "summary": "Get API usage statistics",
                "description": "Retrieve comprehensive usage statistics including API calls, conversions, and performance metrics",
                "responses": {
                    "200": {
                        "description": "Statistics retrieved successfully",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "total_api_calls": {"type": "integer"},
                                        "total_conversions": {"type": "integer"},
                                        "total_cost_estimations": {"type": "integer"},
                                        "avg_response_time": {"type": "number"},
                                        "error_rate": {"type": "number"},
                                        "recent_activity": {"type": "array"},
                                    },
                                }
                            }
                        },
                    }
                },
            }
        },
        "/upload": {
            "get": {
                "tags": ["PDF Conversion"],
                "summary": "Upload form",
                "description": "Display PDF upload form",
                "responses": {"200": {"description": "HTML upload form"}},
            },
            "post": {
                "tags": ["PDF Conversion"],
                "summary": "Upload PDF file",
                "description": "Upload a PDF file and convert it to JSON format",
                "requestBody": {
                    "required": True,
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "pdf": {
                                        "type": "string",
                                        "format": "binary",
                                        "description": "PDF file to upload (max 500MB)",
                                    }
                                },
                                "required": ["pdf"],
                            }
                        }
                    },
                },
                "responses": {
                    "302": {"description": "Redirect to home page after successful upload"},
                    "400": {"description": "Invalid file or missing file"},
                    "413": {"description": "File too large (max 500MB)"},
                },
            },
        },
        "/view/{filepath}": {
            "get": {
                "tags": ["PDF Conversion"],
                "summary": "View converted file",
                "description": "View JSON, CSV, or Markdown files",
                "parameters": [
                    {
                        "name": "filepath",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Relative path to file (e.g., input_files/example.json)",
                        "example": "input_files/example.json",
                    }
                ],
                "responses": {
                    "200": {"description": "File content displayed"},
                    "404": {"description": "File not found"},
                },
            }
        },
        "/search": {
            "post": {
                "tags": ["PDF Conversion"],
                "summary": "Search converted files",
                "description": "Search for text across all converted JSON files",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/x-www-form-urlencoded": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "search_term": {
                                        "type": "string",
                                        "description": "Text to search for",
                                    }
                                },
                                "required": ["search_term"],
                            }
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Search results",
                        "content": {
                            "text/html": {
                                "schema": {
                                    "type": "string",
                                    "description": "HTML page with search results",
                                }
                            }
                        },
                    }
                },
            }
        },
        "/cost-estimation": {
            "get": {
                "tags": ["DSR Matching"],
                "summary": "Cost estimation form",
                "description": "Display cost estimation form with available files",
                "responses": {"200": {"description": "HTML cost estimation form"}},
            },
            "post": {
                "tags": ["DSR Matching"],
                "summary": "Calculate cost estimation",
                "description": "Match items with DSR rates and calculate costs",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/x-www-form-urlencoded": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "input_file": {
                                        "type": "string",
                                        "description": "Input JSON file with items",
                                    },
                                    "reference_files": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "DSR reference database files",
                                    },
                                },
                                "required": ["input_file", "reference_files"],
                            }
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Cost estimation completed",
                        "content": {
                            "text/html": {
                                "schema": {
                                    "type": "string",
                                    "description": "HTML page with estimation results",
                                }
                            }
                        },
                    },
                    "400": {"description": "Missing required parameters"},
                },
            },
        },
        "/excel-converter": {
            "get": {
                "tags": ["Excel Operations"],
                "summary": "Excel converter interface",
                "description": "Display Excel to PDF conversion interface",
                "responses": {"200": {"description": "HTML converter interface"}},
            }
        },
        "/api/excel/sheets": {
            "post": {
                "tags": ["Excel Operations"],
                "summary": "List Excel sheets",
                "description": "Upload Excel file and get list of available sheets",
                "requestBody": {
                    "required": True,
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "file": {
                                        "type": "string",
                                        "format": "binary",
                                        "description": "Excel file (.xlsx, .xls)",
                                    }
                                },
                                "required": ["file"],
                            }
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Sheet list retrieved",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "sheets": {"type": "array", "items": {"type": "string"}}
                                    },
                                }
                            }
                        },
                    },
                    "400": {"description": "Invalid file or error processing"},
                },
            }
        },
        "/api/excel/convert": {
            "post": {
                "tags": ["Excel Operations"],
                "summary": "Convert Excel to PDF",
                "description": "Convert selected Excel sheets to PDF",
                "requestBody": {
                    "required": True,
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "file": {"type": "string", "format": "binary"},
                                    "sheets": {"type": "array", "items": {"type": "string"}},
                                    "orientation": {
                                        "type": "string",
                                        "enum": ["portrait", "landscape"],
                                    },
                                    "page_size": {"type": "string", "enum": ["A4", "Letter"]},
                                    "output_mode": {
                                        "type": "string",
                                        "enum": ["separate", "combined"],
                                    },
                                },
                            }
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "Conversion successful",
                        "content": {
                            "application/pdf": {"schema": {"type": "string", "format": "binary"}},
                            "application/zip": {"schema": {"type": "string", "format": "binary"}},
                        },
                    },
                    "400": {"description": "Conversion failed"},
                },
            }
        },
    },
    "components": {
        "schemas": {
            "Error": {
                "type": "object",
                "properties": {"error": {"type": "string"}, "message": {"type": "string"}},
            }
        }
    },
}


def get_api_spec():
    """Return the OpenAPI specification"""
    return API_SPEC

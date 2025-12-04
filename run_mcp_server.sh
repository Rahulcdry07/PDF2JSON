#!/bin/bash
# Wrapper script to run MCP server with proper Python environment
# This suppresses warnings and redirects stderr to avoid interfering with JSON communication

# Redirect stderr to a log file to avoid mixing with JSON-RPC stdout
LOG_FILE="/tmp/mcp_server_$(date +%Y%m%d_%H%M%S).log"
exec /Users/rahulchaudhary/anaconda3/bin/python3 -W ignore /Users/rahulchaudhary/PDF2JSON/mcp_server.py "$@" 2>"$LOG_FILE"

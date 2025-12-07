#!/bin/bash
# GitHub MCP Integration Setup Script
# This script helps set up the GitHub MCP integration for PDF2JSON

set -e

echo "=========================================="
echo "🚀 GitHub MCP Integration Setup"
echo "=========================================="
echo ""

# Check if GitHub CLI is installed
echo "1️⃣  Checking GitHub CLI installation..."
if command -v gh &> /dev/null; then
    GH_VERSION=$(gh --version | head -n 1 | awk '{print $3}')
    echo "   ✅ GitHub CLI installed: v${GH_VERSION}"
else
    echo "   ❌ GitHub CLI not found!"
    echo ""
    echo "   Please install GitHub CLI:"
    echo "   • macOS:   brew install gh"
    echo "   • Linux:   See https://github.com/cli/cli/blob/trunk/docs/install_linux.md"
    echo "   • Windows: winget install --id GitHub.cli"
    echo ""
    exit 1
fi
echo ""

# Check authentication status
echo "2️⃣  Checking GitHub authentication..."
if gh auth status &> /dev/null; then
    echo "   ✅ GitHub CLI authenticated"
    gh auth status 2>&1 | grep "Logged in" | head -n 1
else
    echo "   ⚠️  Not authenticated with GitHub"
    echo ""
    read -p "   Would you like to authenticate now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gh auth login
    else
        echo "   ⚠️  Skipping authentication. You can run 'gh auth login' later."
    fi
fi
echo ""

# Check Python installation
echo "3️⃣  Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    echo "   ✅ Python installed: ${PYTHON_VERSION}"
else
    echo "   ❌ Python 3 not found!"
    exit 1
fi
echo ""

# Check required Python packages
echo "4️⃣  Checking Python packages..."
if python3 -c "import mcp" &> /dev/null; then
    echo "   ✅ MCP package installed"
else
    echo "   ⚠️  MCP package not found"
    echo "   Installing MCP..."
    pip install mcp
fi
echo ""

# Test the GitHub MCP server
echo "5️⃣  Testing GitHub MCP server..."
if [ -f "mcp_github_server.py" ]; then
    echo "   ✅ mcp_github_server.py found"
    chmod +x mcp_github_server.py
else
    echo "   ❌ mcp_github_server.py not found!"
    exit 1
fi
echo ""

# Run demo
echo "6️⃣  Running GitHub MCP demo..."
if [ -f "examples/github_mcp_demo.py" ]; then
    chmod +x examples/github_mcp_demo.py
    python3 examples/github_mcp_demo.py
else
    echo "   ⚠️  Demo script not found, skipping..."
fi
echo ""

# Claude Desktop configuration
echo "=========================================="
echo "✨ Setup Complete!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo ""
echo "1. Configure Claude Desktop:"
echo "   Add this to your Claude Desktop config:"
echo "   (Location: ~/Library/Application Support/Claude/claude_desktop_config.json on macOS)"
echo ""
echo '   {
     "mcpServers": {
       "estimatex": {
         "command": "python3",
         "args": ["'$(pwd)'/mcp_server.py"]
       },
       "estimatex-github": {
         "command": "python3",
         "args": ["'$(pwd)'/mcp_github_server.py"]
       }
     }
   }'
echo ""
echo "2. Restart Claude Desktop"
echo ""
echo "3. Test with queries like:"
echo "   • 'Show me the latest CI/CD workflow status'"
echo "   • 'List all open issues in the repository'"
echo "   • 'Create an issue for adding PDF encryption'"
echo "   • 'Search for DSR matching code in scripts/'"
echo "   • 'What are the recent commits?'"
echo ""
echo "📖 Full documentation: docs/GITHUB_MCP_INTEGRATION.md"
echo ""

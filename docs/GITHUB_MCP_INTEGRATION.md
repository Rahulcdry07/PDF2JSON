# GitHub MCP Integration Guide

This document explains how to use the GitHub MCP integration for the EstimateX project.

## Overview

The GitHub MCP server (`mcp_github_server.py`) provides AI assistants with direct access to GitHub repository management features through the Model Context Protocol.

## Features

### 📋 Issue Management
- Create new issues with labels
- List and filter issues by state
- View issue details and comments

### 🔀 Pull Request Management
- Create pull requests from branches
- List and filter PRs by state
- View PR details and status

### 🚀 CI/CD Integration
- Monitor workflow runs and status
- View build and test results
- Track deployment pipelines

### 🔍 Code Search
- Search code across the repository
- Filter by file paths and extensions
- Find specific implementations

### 📊 Repository Analytics
- View repository statistics
- Track stars, forks, and watchers
- Monitor activity trends

### 📝 Commit History
- View recent commits
- Filter by author and date
- Track project progress

### 🏷️ Release Management
- Create new releases with tags
- Manage release notes
- Track version history

### 💻 Git Status
- Check local repository status
- View uncommitted changes
- Monitor current branch

## Prerequisites

### 1. GitHub CLI Installation

Install the GitHub CLI (`gh`) to enable full functionality:

**macOS:**
```bash
brew install gh
```

**Linux:**
```bash
# Debian/Ubuntu
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh

# Fedora/CentOS
sudo dnf install gh
```

**Windows:**
```powershell
winget install --id GitHub.cli
```

### 2. GitHub Authentication

Authenticate with GitHub:

```bash
gh auth login
```

Follow the prompts to authenticate using your GitHub account.

### 3. Verify Installation

```bash
gh --version
gh repo view Rahulcdry07/EstimateX
```

## Running the GitHub MCP Server

### Standalone Mode

```bash
python mcp_github_server.py
```

### With Claude Desktop

Add to your Claude Desktop MCP configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "estimatex-github": {
      "command": "python",
      "args": ["/path/to/EstimateX/mcp_github_server.py"],
      "env": {}
    }
  }
}
```

### With Other MCP Clients

The server uses stdio transport and can be integrated with any MCP-compatible client:

```python
import asyncio
from mcp.client.stdio import stdio_client

async def connect():
    async with stdio_client(
        server_params={
            "command": "python",
            "args": ["/path/to/mcp_github_server.py"],
        }
    ) as (read, write, _):
        # Use the MCP client
        pass

asyncio.run(connect())
```

## Available Tools

### create_issue

Create a new GitHub issue.

**Parameters:**
- `title` (required): Issue title
- `body` (required): Issue description
- `labels` (optional): Array of label names

**Example:**
```json
{
  "title": "Bug: PDF parsing fails on large files",
  "body": "When processing PDFs larger than 100MB, the converter crashes...",
  "labels": ["bug", "high-priority"]
}
```

### list_issues

List repository issues with filters.

**Parameters:**
- `state` (optional): "open", "closed", or "all" (default: "open")
- `limit` (optional): Maximum number of issues (default: 10)

### create_pull_request

Create a new pull request.

**Parameters:**
- `title` (required): PR title
- `body` (required): PR description
- `base` (optional): Base branch (default: "main")

### list_pull_requests

List pull requests with filters.

**Parameters:**
- `state` (optional): "open", "closed", "merged", or "all" (default: "open")
- `limit` (optional): Maximum number of PRs (default: 10)

### get_workflow_status

Get CI/CD workflow status.

**Parameters:**
- `workflow` (optional): Workflow name or "latest" (default: "latest")

### search_code

Search code in the repository.

**Parameters:**
- `query` (required): Search query
- `path` (optional): Path filter (e.g., "src/", "*.py")

**Example:**
```json
{
  "query": "PDFToXMLConverter",
  "path": "src/"
}
```

### get_commit_history

Get recent commit history.

**Parameters:**
- `limit` (optional): Number of commits (default: 10)
- `author` (optional): Filter by author
- `since` (optional): Date filter (e.g., "2024-01-01", "7 days ago")

### create_release

Create a new GitHub release.

**Parameters:**
- `tag` (required): Release tag (e.g., "v1.0.0")
- `title` (required): Release title
- `notes` (required): Release notes
- `draft` (optional): Create as draft (default: false)

### get_repo_stats

Get repository statistics (no parameters required).

### git_status

Get local git repository status (no parameters required).

## Available Resources

### Repository Information
- URI: `github://repo/Rahulcdry07/EstimateX`
- Description: Main repository stats and metadata

### Issues
- URI: `github://repo/Rahulcdry07/EstimateX/issues`
- Description: All repository issues

### Pull Requests
- URI: `github://repo/Rahulcdry07/EstimateX/pulls`
- Description: All pull requests

### Actions
- URI: `github://repo/Rahulcdry07/EstimateX/actions`
- Description: CI/CD workflow runs

### Releases
- URI: `github://repo/Rahulcdry07/EstimateX/releases`
- Description: All project releases

## Usage Examples

### Example 1: Creating an Issue

```python
# AI Assistant can use this tool to create issues
result = await call_tool("create_issue", {
    "title": "Add support for encrypted PDFs",
    "body": """
    ## Description
    Currently, the PDF converter cannot handle password-protected PDFs.
    
    ## Proposed Solution
    Add password parameter to PDFToXMLConverter initialization.
    
    ## Acceptance Criteria
    - [ ] Support password-protected PDFs
    - [ ] Handle incorrect passwords gracefully
    - [ ] Add tests for encrypted PDFs
    """,
    "labels": ["enhancement", "pdf-processing"]
})
```

### Example 2: Monitoring CI/CD

```python
# Check latest workflow status
status = await call_tool("get_workflow_status", {
    "workflow": "latest"
})

# Response includes status, conclusion, and workflow name
```

### Example 3: Searching Code

```python
# Search for DSR matching code in scripts
results = await call_tool("search_code", {
    "query": "match_with_database",
    "path": "scripts/"
})
```

### Example 4: Creating a Release

```python
# Create a new release
release = await call_tool("create_release", {
    "tag": "v1.1.0",
    "title": "Version 1.1.0 - DSR Enhancement",
    "notes": """
    ## What's New
    - Improved DSR matching accuracy
    - Added GitHub MCP integration
    - Enhanced test coverage to 88%
    
    ## Bug Fixes
    - Fixed PDF parsing on large files
    - Resolved memory leaks in converter
    """
})
```

## Integration with Main MCP Server

The GitHub MCP server complements the main EstimateX MCP server. You can run both servers simultaneously for complete project management:

### Combined Configuration

```json
{
  "mcpServers": {
    "estimatex-dsr": {
      "command": "python",
      "args": ["/path/to/EstimateX/mcp_server.py"]
    },
    "estimatex-github": {
      "command": "python",
      "args": ["/path/to/EstimateX/mcp_github_server.py"]
    }
  }
}
```

### Workflow Example

1. **Convert PDF and match DSR codes** (using main MCP server)
2. **Create issue for unmatched items** (using GitHub MCP server)
3. **Monitor CI/CD status** (using GitHub MCP server)
4. **Create release** (using GitHub MCP server)

## Troubleshooting

### GitHub CLI Not Found

If you get "GitHub CLI (gh) not installed" error:

1. Install GitHub CLI: `brew install gh` (macOS) or see prerequisites above
2. Authenticate: `gh auth login`
3. Verify: `gh --version`

### Authentication Failed

```bash
# Re-authenticate with GitHub
gh auth logout
gh auth login

# Verify authentication
gh auth status
```

### Permission Denied

Ensure your GitHub token has the necessary permissions:

- `repo` - Full control of repositories
- `workflow` - Update GitHub Actions workflows
- `admin:org` - Read and write org and team membership (if needed)

```bash
gh auth refresh -h github.com -s repo,workflow
```

### Rate Limiting

GitHub API has rate limits. If you hit the limit:

```bash
# Check rate limit status
gh api rate_limit

# Wait for rate limit reset or authenticate with token
```

## Best Practices

1. **Use Descriptive Titles**: When creating issues or PRs, use clear, descriptive titles
2. **Add Labels**: Tag issues and PRs appropriately for better organization
3. **Monitor CI/CD**: Check workflow status before merging PRs
4. **Regular Commits**: Use `git_status` to track local changes
5. **Semantic Versioning**: Follow semver for releases (e.g., v1.2.3)

## Security Considerations

1. **Token Storage**: GitHub CLI securely stores authentication tokens
2. **Environment Variables**: Avoid hardcoding credentials
3. **Permissions**: Use minimal required permissions for tokens
4. **Audit Logs**: Monitor repository activity through GitHub audit logs

## Contributing

To enhance the GitHub MCP integration:

1. Fork the repository
2. Create a feature branch
3. Add new tools or resources to `mcp_github_server.py`
4. Test thoroughly with `gh` commands
5. Submit a pull request

## Related Documentation

- [Main MCP Integration Guide](./MCP_INTEGRATION.md)
- [GitHub CLI Documentation](https://cli.github.com/manual/)
- [GitHub API Reference](https://docs.github.com/en/rest)
- [Model Context Protocol Spec](https://modelcontextprotocol.io/)

## Support

For issues or questions:

1. Check [GitHub CLI documentation](https://cli.github.com/manual/)
2. Review [MCP specification](https://modelcontextprotocol.io/)
3. Create an issue on [GitHub](https://github.com/Rahulcdry07/EstimateX/issues)
4. Consult the main project [README](../README.md)

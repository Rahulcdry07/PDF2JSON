# GitHub MCP Quick Reference

## 🚀 Quick Start

```bash
# Install GitHub CLI
brew install gh  # macOS
# or see: https://cli.github.com/

# Authenticate
gh auth login

# Run setup
./setup_github_mcp.sh

# Test demo
python examples/github_mcp_demo.py
```

## 🔧 Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "estimatex-github": {
      "command": "python3",
      "args": ["/path/to/EstimateX/mcp_github_server.py"]
    }
  }
}
```

## 💬 Example Queries for Claude

### Issues
- "List all open issues"
- "Create an issue titled 'Add PDF encryption support'"
- "Show me closed issues from the last month"

### Pull Requests
- "List all open pull requests"
- "Create a PR for my current branch"
- "Show me merged PRs"

### CI/CD
- "What's the status of the latest CI/CD run?"
- "Show me failed workflow runs"
- "Check if the tests are passing"

### Code Search
- "Search for 'PDFToXMLConverter' in src/"
- "Find all Python files with 'DSR' in the name"
- "Search for database queries"

### Commits
- "Show me the last 10 commits"
- "Show commits by author John"
- "Show commits from the last week"

### Repository
- "Get repository statistics"
- "How many stars does the repo have?"
- "What's the current git status?"

### Releases
- "List all releases"
- "Create a release v1.1.0"
- "Show the latest release"

## 🛠️ Available Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `create_issue` | Create new issue | title, body, labels |
| `list_issues` | List issues | state, limit |
| `create_pull_request` | Create PR | title, body, base |
| `list_pull_requests` | List PRs | state, limit |
| `get_workflow_status` | CI/CD status | workflow |
| `search_code` | Search code | query, path |
| `get_commit_history` | View commits | limit, author, since |
| `create_release` | Create release | tag, title, notes |
| `get_repo_stats` | Repo stats | - |
| `git_status` | Local status | - |

## 📚 Resources

| Resource | URI | Description |
|----------|-----|-------------|
| Repository | `github://repo/Rahulcdry07/EstimateX` | Main repo info |
| Issues | `github://repo/.../issues` | All issues |
| PRs | `github://repo/.../pulls` | All PRs |
| Actions | `github://repo/.../actions` | Workflow runs |
| Releases | `github://repo/.../releases` | All releases |

## 🔍 Troubleshooting

### GitHub CLI Not Found
```bash
# Install
brew install gh  # macOS
# See: https://cli.github.com/

# Verify
gh --version
```

### Not Authenticated
```bash
# Login
gh auth login

# Check status
gh auth status

# Refresh token
gh auth refresh -h github.com -s repo,workflow
```

### MCP Server Issues
```bash
# Test manually
python mcp_github_server.py

# Check logs in Claude Desktop
~/Library/Logs/Claude/mcp*.log
```

## 📖 Full Documentation

- **Setup Guide**: `docs/GITHUB_MCP_INTEGRATION.md`
- **Implementation**: `docs/GITHUB_MCP_SUMMARY.md`
- **Main MCP**: `docs/MCP_INTEGRATION.md`
- **Project Docs**: `README.md`

## 🎯 Common Workflows

### Development Workflow
1. Make code changes
2. "What's my git status?" → Check changes
3. Commit and push
4. "Create a PR for this branch" → Create PR
5. "What's the CI/CD status?" → Check builds

### Issue Management
1. "List open issues" → Review issues
2. "Create an issue for X" → Report bug/feature
3. "Search for 'DSR' code" → Find implementation
4. "Show recent commits" → Track progress

### Release Process
1. "What's the latest release?" → Check version
2. Make updates and test
3. "Create release v1.1.0" → Publish release
4. "Show repo stats" → Verify deployment

## 💡 Pro Tips

1. **Combine with DSR MCP**: Use both servers for full project management
2. **Use Filters**: Add state/limit parameters to narrow results
3. **Check CI/CD First**: Always verify builds before merging
4. **Descriptive Titles**: Use clear, specific titles for issues/PRs
5. **Regular Status**: Check git status before creating PRs

## 🔗 Links

- GitHub CLI: https://cli.github.com/
- MCP Spec: https://modelcontextprotocol.io/
- Repository: https://github.com/Rahulcdry07/EstimateX
- Issues: https://github.com/Rahulcdry07/EstimateX/issues

---

**Quick Help**: Run `./setup_github_mcp.sh` for guided setup

#!/usr/bin/env python3
"""
GitHub MCP Integration Quickstart Example

This script demonstrates how to use the GitHub MCP server programmatically.
It shows various operations like listing issues, checking workflow status,
and getting repository statistics.
"""

import asyncio
import json
from pathlib import Path
import sys

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import the GitHub MCP server functions
from mcp_github_server import run_gh_command, run_git_command


async def demo_github_integration():
    """Demonstrate GitHub MCP integration capabilities."""
    
    print("=" * 60)
    print("🚀 GitHub MCP Integration Demo")
    print("=" * 60)
    print()
    
    # 1. Check if GitHub CLI is installed
    print("1️⃣  Checking GitHub CLI installation...")
    result = run_gh_command(["--version"])
    if result["success"]:
        print(f"   ✅ GitHub CLI installed: {result['output'].split()[2]}")
    else:
        print(f"   ❌ GitHub CLI not found: {result['error']}")
        print("   Install from: https://cli.github.com/")
        return
    print()
    
    # 2. Get repository statistics
    print("2️⃣  Fetching repository statistics...")
    result = run_gh_command([
        "repo", "view",
        "--json", "name,description,stargazerCount,forkCount,openIssues"
    ])
    if result["success"]:
        stats = json.loads(result["output"])
        print(f"   📁 Repository: {stats['name']}")
        print(f"   📝 Description: {stats['description']}")
        print(f"   ⭐ Stars: {stats['stargazerCount']}")
        print(f"   🍴 Forks: {stats['forkCount']}")
        print(f"   🔧 Open Issues: {stats['openIssues']['totalCount']}")
    else:
        print(f"   ❌ Failed to fetch stats: {result['error']}")
    print()
    
    # 3. List recent issues
    print("3️⃣  Listing recent issues...")
    result = run_gh_command([
        "issue", "list",
        "--limit", "5",
        "--json", "number,title,state,createdAt"
    ])
    if result["success"]:
        issues = json.loads(result["output"]) if result["output"] else []
        if issues:
            print(f"   Found {len(issues)} recent issues:")
            for issue in issues:
                print(f"   • #{issue['number']}: {issue['title']} [{issue['state']}]")
        else:
            print("   No issues found")
    else:
        print(f"   ❌ Failed to fetch issues: {result['error']}")
    print()
    
    # 4. Check CI/CD workflow status
    print("4️⃣  Checking CI/CD workflow status...")
    result = run_gh_command([
        "run", "list",
        "--limit", "3",
        "--json", "status,conclusion,createdAt,workflowName,displayTitle"
    ])
    if result["success"]:
        runs = json.loads(result["output"]) if result["output"] else []
        if runs:
            print(f"   Found {len(runs)} recent workflow runs:")
            for run in runs:
                status = run.get("conclusion") or run["status"]
                emoji = "✅" if status == "success" else "⚠️" if status == "in_progress" else "❌"
                print(f"   {emoji} {run['workflowName']}: {status}")
                print(f"      Title: {run['displayTitle']}")
        else:
            print("   No workflow runs found")
    else:
        print(f"   ❌ Failed to fetch workflow status: {result['error']}")
    print()
    
    # 5. Get recent commits
    print("5️⃣  Fetching recent commits...")
    result = run_git_command([
        "git", "log", "-5", "--format=%h|%an|%s|%ar"
    ])
    if result["success"]:
        commits = result["output"].split("\n")
        print(f"   Found {len(commits)} recent commits:")
        for commit in commits:
            if commit.strip():
                parts = commit.split("|")
                if len(parts) == 4:
                    print(f"   • {parts[0]}: {parts[2]}")
                    print(f"      Author: {parts[1]} ({parts[3]})")
    else:
        print(f"   ❌ Failed to fetch commits: {result['error']}")
    print()
    
    # 6. Check local git status
    print("6️⃣  Checking local repository status...")
    branch_result = run_git_command(["git", "branch", "--show-current"])
    status_result = run_git_command(["git", "status", "--porcelain"])
    
    if branch_result["success"]:
        print(f"   🌿 Current branch: {branch_result['output']}")
    
    if status_result["success"]:
        changes = [line for line in status_result["output"].split("\n") if line.strip()]
        if changes:
            print(f"   📝 Uncommitted changes: {len(changes)} files")
            for change in changes[:5]:  # Show first 5
                print(f"      {change}")
            if len(changes) > 5:
                print(f"      ... and {len(changes) - 5} more")
        else:
            print("   ✨ Working directory clean")
    print()
    
    # 7. List available releases
    print("7️⃣  Checking releases...")
    result = run_gh_command([
        "release", "list",
        "--limit", "5",
        "--json", "name,tagName,createdAt,isLatest"
    ])
    if result["success"]:
        releases = json.loads(result["output"]) if result["output"] else []
        if releases:
            print(f"   Found {len(releases)} releases:")
            for release in releases:
                latest = " [LATEST]" if release.get("isLatest") else ""
                print(f"   • {release['tagName']}: {release['name']}{latest}")
        else:
            print("   No releases found")
    else:
        print(f"   ❌ Failed to fetch releases: {result['error']}")
    print()
    
    print("=" * 60)
    print("✨ GitHub MCP Integration Demo Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Configure Claude Desktop with mcp_github_server.py")
    print("  2. Try natural language queries like:")
    print("     - 'Show me the latest CI/CD status'")
    print("     - 'Create an issue for adding PDF encryption support'")
    print("     - 'List all pull requests'")
    print("     - 'Search for DSR matching code'")
    print()
    print("📖 Full documentation: docs/GITHUB_MCP_INTEGRATION.md")


def main():
    """Main entry point."""
    try:
        asyncio.run(demo_github_integration())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
GitHub MCP Server for PDF2JSON Project

This MCP server provides GitHub integration capabilities including:
- Repository management (issues, PRs, commits)
- Code search and file operations
- CI/CD workflow monitoring
- Release management
- Documentation updates

Integrates with the main PDF2JSON MCP server for comprehensive project management.
"""

import asyncio
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Sequence
import sys
from datetime import datetime
import warnings

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

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

# Server instance
server = Server("pdf2json-github")

# Constants
GITHUB_OWNER = "Rahulcdry07"
GITHUB_REPO = "PDF2JSON"
GITHUB_API_BASE = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"


def run_git_command(cmd: list[str]) -> dict:
    """Execute git command and return result."""
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return {"success": True, "output": result.stdout.strip(), "error": None}
    except subprocess.CalledProcessError as e:
        return {"success": False, "output": e.stdout, "error": e.stderr}


def run_gh_command(cmd: list[str]) -> dict:
    """Execute GitHub CLI command and return result."""
    try:
        result = subprocess.run(
            ["gh"] + cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return {"success": True, "output": result.stdout.strip(), "error": None}
    except subprocess.CalledProcessError as e:
        return {"success": False, "output": e.stdout, "error": e.stderr}
    except FileNotFoundError:
        return {
            "success": False,
            "output": None,
            "error": "GitHub CLI (gh) not installed. Install from https://cli.github.com/",
        }


@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available GitHub resources."""
    return [
        Resource(
            uri=f"github://repo/{GITHUB_OWNER}/{GITHUB_REPO}",
            name="PDF2JSON Repository",
            mimeType="application/json",
            description="Main repository information and statistics",
        ),
        Resource(
            uri=f"github://repo/{GITHUB_OWNER}/{GITHUB_REPO}/issues",
            name="Repository Issues",
            mimeType="application/json",
            description="All open and closed issues",
        ),
        Resource(
            uri=f"github://repo/{GITHUB_OWNER}/{GITHUB_REPO}/pulls",
            name="Pull Requests",
            mimeType="application/json",
            description="All open and closed pull requests",
        ),
        Resource(
            uri=f"github://repo/{GITHUB_OWNER}/{GITHUB_REPO}/actions",
            name="GitHub Actions",
            mimeType="application/json",
            description="CI/CD workflow runs and status",
        ),
        Resource(
            uri=f"github://repo/{GITHUB_OWNER}/{GITHUB_REPO}/releases",
            name="Releases",
            mimeType="application/json",
            description="All project releases",
        ),
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read a GitHub resource."""
    if "/issues" in uri:
        result = run_gh_command(["issue", "list", "--json", "number,title,state,createdAt,author"])
        if result["success"]:
            issues = json.loads(result["output"])
            return json.dumps({"total_issues": len(issues), "issues": issues}, indent=2)
        return json.dumps({"error": result["error"]})

    elif "/pulls" in uri:
        result = run_gh_command(["pr", "list", "--json", "number,title,state,createdAt,author"])
        if result["success"]:
            prs = json.loads(result["output"]) if result["output"] else []
            return json.dumps({"total_prs": len(prs), "pull_requests": prs}, indent=2)
        return json.dumps({"error": result["error"]})

    elif "/actions" in uri:
        result = run_gh_command(
            ["run", "list", "--limit", "10", "--json", "status,conclusion,createdAt,workflowName"]
        )
        if result["success"]:
            runs = json.loads(result["output"]) if result["output"] else []
            return json.dumps({"recent_runs": len(runs), "workflow_runs": runs}, indent=2)
        return json.dumps({"error": result["error"]})

    elif "/releases" in uri:
        result = run_gh_command(["release", "list", "--json", "name,tagName,createdAt,isLatest"])
        if result["success"]:
            releases = json.loads(result["output"]) if result["output"] else []
            return json.dumps({"total_releases": len(releases), "releases": releases}, indent=2)
        return json.dumps({"error": result["error"]})

    elif uri.endswith(f"/{GITHUB_REPO}"):
        result = run_gh_command(
            ["repo", "view", "--json", "name,description,stargazerCount,forkCount,openIssues"]
        )
        if result["success"]:
            return result["output"]
        return json.dumps({"error": result["error"]})

    return json.dumps({"error": f"Unknown resource URI: {uri}"})


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available GitHub tools."""
    return [
        Tool(
            name="create_issue",
            description="Create a new GitHub issue with title, body, and optional labels",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Issue title",
                    },
                    "body": {
                        "type": "string",
                        "description": "Issue description/body",
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Labels to add (e.g., ['bug', 'enhancement'])",
                    },
                },
                "required": ["title", "body"],
            },
        ),
        Tool(
            name="list_issues",
            description="List GitHub issues with optional filters (state, labels, author)",
            inputSchema={
                "type": "object",
                "properties": {
                    "state": {
                        "type": "string",
                        "enum": ["open", "closed", "all"],
                        "description": "Issue state filter",
                        "default": "open",
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of issues to return",
                        "default": 10,
                    },
                },
            },
        ),
        Tool(
            name="create_pull_request",
            description="Create a new pull request from current branch",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "PR title",
                    },
                    "body": {
                        "type": "string",
                        "description": "PR description",
                    },
                    "base": {
                        "type": "string",
                        "description": "Base branch (default: main)",
                        "default": "main",
                    },
                },
                "required": ["title", "body"],
            },
        ),
        Tool(
            name="list_pull_requests",
            description="List pull requests with optional state filter",
            inputSchema={
                "type": "object",
                "properties": {
                    "state": {
                        "type": "string",
                        "enum": ["open", "closed", "merged", "all"],
                        "description": "PR state filter",
                        "default": "open",
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of PRs to return",
                        "default": 10,
                    },
                },
            },
        ),
        Tool(
            name="get_workflow_status",
            description="Get CI/CD workflow run status and details",
            inputSchema={
                "type": "object",
                "properties": {
                    "workflow": {
                        "type": "string",
                        "description": "Workflow name or 'latest' for most recent",
                        "default": "latest",
                    },
                },
            },
        ),
        Tool(
            name="search_code",
            description="Search code in the repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (supports GitHub code search syntax)",
                    },
                    "path": {
                        "type": "string",
                        "description": "Optional path filter (e.g., 'src/', '*.py')",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_commit_history",
            description="Get recent commit history with optional filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "number",
                        "description": "Number of commits to return",
                        "default": 10,
                    },
                    "author": {
                        "type": "string",
                        "description": "Filter by author",
                    },
                    "since": {
                        "type": "string",
                        "description": "Show commits since date (e.g., '2024-01-01', '7 days ago')",
                    },
                },
            },
        ),
        Tool(
            name="create_release",
            description="Create a new GitHub release with tag and notes",
            inputSchema={
                "type": "object",
                "properties": {
                    "tag": {
                        "type": "string",
                        "description": "Release tag (e.g., 'v1.0.0')",
                    },
                    "title": {
                        "type": "string",
                        "description": "Release title",
                    },
                    "notes": {
                        "type": "string",
                        "description": "Release notes",
                    },
                    "draft": {
                        "type": "boolean",
                        "description": "Create as draft",
                        "default": False,
                    },
                },
                "required": ["tag", "title", "notes"],
            },
        ),
        Tool(
            name="get_repo_stats",
            description="Get repository statistics (stars, forks, issues, contributors)",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="git_status",
            description="Get current git status of local repository",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(
    name: str, arguments: Any
) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls."""

    if name == "create_issue":
        title = arguments["title"]
        body = arguments["body"]
        labels = arguments.get("labels", [])

        cmd = ["issue", "create", "--title", title, "--body", body]
        if labels:
            cmd.extend(["--label", ",".join(labels)])

        result = run_gh_command(cmd)

        if result["success"]:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"success": True, "message": "Issue created", "url": result["output"]},
                        indent=2,
                    ),
                )
            ]
        return [
            TextContent(
                type="text",
                text=json.dumps({"success": False, "error": result["error"]}, indent=2),
            )
        ]

    elif name == "list_issues":
        state = arguments.get("state", "open")
        limit = arguments.get("limit", 10)

        cmd = [
            "issue",
            "list",
            "--state",
            state,
            "--limit",
            str(limit),
            "--json",
            "number,title,state,createdAt,author,labels",
        ]

        result = run_gh_command(cmd)

        if result["success"]:
            issues = json.loads(result["output"]) if result["output"] else []
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"total": len(issues), "state": state, "issues": issues}, indent=2
                    ),
                )
            ]
        return [
            TextContent(
                type="text",
                text=json.dumps({"success": False, "error": result["error"]}, indent=2),
            )
        ]

    elif name == "create_pull_request":
        title = arguments["title"]
        body = arguments["body"]
        base = arguments.get("base", "main")

        cmd = ["pr", "create", "--title", title, "--body", body, "--base", base]

        result = run_gh_command(cmd)

        if result["success"]:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": True,
                            "message": "Pull request created",
                            "url": result["output"],
                        },
                        indent=2,
                    ),
                )
            ]
        return [
            TextContent(
                type="text",
                text=json.dumps({"success": False, "error": result["error"]}, indent=2),
            )
        ]

    elif name == "list_pull_requests":
        state = arguments.get("state", "open")
        limit = arguments.get("limit", 10)

        cmd = [
            "pr",
            "list",
            "--state",
            state,
            "--limit",
            str(limit),
            "--json",
            "number,title,state,createdAt,author,headRefName",
        ]

        result = run_gh_command(cmd)

        if result["success"]:
            prs = json.loads(result["output"]) if result["output"] else []
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"total": len(prs), "state": state, "pull_requests": prs}, indent=2
                    ),
                )
            ]
        return [
            TextContent(
                type="text",
                text=json.dumps({"success": False, "error": result["error"]}, indent=2),
            )
        ]

    elif name == "get_workflow_status":
        workflow = arguments.get("workflow", "latest")

        cmd = [
            "run",
            "list",
            "--limit",
            "5",
            "--json",
            "status,conclusion,createdAt,workflowName,event,displayTitle",
        ]

        result = run_gh_command(cmd)

        if result["success"]:
            runs = json.loads(result["output"]) if result["output"] else []
            if workflow == "latest" and runs:
                latest = runs[0]
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "workflow": "latest",
                                "status": latest["status"],
                                "conclusion": latest.get("conclusion"),
                                "workflow_name": latest["workflowName"],
                                "title": latest["displayTitle"],
                                "created_at": latest["createdAt"],
                            },
                            indent=2,
                        ),
                    )
                ]
            return [
                TextContent(
                    type="text",
                    text=json.dumps({"recent_runs": len(runs), "runs": runs}, indent=2),
                )
            ]
        return [
            TextContent(
                type="text",
                text=json.dumps({"success": False, "error": result["error"]}, indent=2),
            )
        ]

    elif name == "search_code":
        query = arguments["query"]
        path = arguments.get("path")

        search_query = f"{query} repo:{GITHUB_OWNER}/{GITHUB_REPO}"
        if path:
            search_query += f" path:{path}"

        cmd = [
            "search",
            "code",
            query,
            "--repo",
            f"{GITHUB_OWNER}/{GITHUB_REPO}",
            "--json",
            "path,repository",
        ]
        if path:
            cmd.extend(["--match", "path", path])

        result = run_gh_command(cmd)

        if result["success"]:
            results = json.loads(result["output"]) if result["output"] else []
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {"query": query, "results_found": len(results), "matches": results},
                        indent=2,
                    ),
                )
            ]
        return [
            TextContent(
                type="text",
                text=json.dumps({"success": False, "error": result["error"]}, indent=2),
            )
        ]

    elif name == "get_commit_history":
        limit = arguments.get("limit", 10)
        author = arguments.get("author")
        since = arguments.get("since")

        cmd = ["git", "log", f"-{limit}", "--format=%H|%an|%ae|%s|%ar"]
        if author:
            cmd.extend(["--author", author])
        if since:
            cmd.extend(["--since", since])

        result = run_git_command(cmd)

        if result["success"]:
            commits = []
            for line in result["output"].split("\n"):
                if line.strip():
                    parts = line.split("|")
                    if len(parts) == 5:
                        commits.append(
                            {
                                "hash": parts[0][:7],
                                "author": parts[1],
                                "email": parts[2],
                                "message": parts[3],
                                "time": parts[4],
                            }
                        )

            return [
                TextContent(
                    type="text",
                    text=json.dumps({"total": len(commits), "commits": commits}, indent=2),
                )
            ]
        return [
            TextContent(
                type="text",
                text=json.dumps({"success": False, "error": result["error"]}, indent=2),
            )
        ]

    elif name == "create_release":
        tag = arguments["tag"]
        title = arguments["title"]
        notes = arguments["notes"]
        draft = arguments.get("draft", False)

        cmd = ["release", "create", tag, "--title", title, "--notes", notes]
        if draft:
            cmd.append("--draft")

        result = run_gh_command(cmd)

        if result["success"]:
            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "success": True,
                            "message": f"Release {tag} created",
                            "url": result["output"],
                        },
                        indent=2,
                    ),
                )
            ]
        return [
            TextContent(
                type="text",
                text=json.dumps({"success": False, "error": result["error"]}, indent=2),
            )
        ]

    elif name == "get_repo_stats":
        result = run_gh_command(
            [
                "repo",
                "view",
                "--json",
                "name,description,stargazerCount,forkCount,issues,watchers,defaultBranchRef,createdAt,updatedAt",
            ]
        )

        if result["success"]:
            stats = json.loads(result["output"])
            # Add open issues count if available
            if "issues" in stats and stats["issues"]:
                stats["openIssuesCount"] = stats["issues"].get("totalCount", 0)
            return [TextContent(type="text", text=json.dumps(stats, indent=2))]
        return [
            TextContent(
                type="text",
                text=json.dumps({"success": False, "error": result["error"]}, indent=2),
            )
        ]

    elif name == "git_status":
        # Get branch info
        branch_result = run_git_command(["git", "branch", "--show-current"])

        # Get status
        status_result = run_git_command(["git", "status", "--porcelain"])

        # Get last commit
        commit_result = run_git_command(["git", "log", "-1", "--format=%H|%s|%ar"])

        response = {}

        if branch_result["success"]:
            response["branch"] = branch_result["output"]

        if status_result["success"]:
            changes = []
            for line in status_result["output"].split("\n"):
                if line.strip():
                    changes.append(line)
            response["changes"] = changes
            response["clean"] = len(changes) == 0

        if commit_result["success"] and commit_result["output"]:
            parts = commit_result["output"].split("|")
            if len(parts) == 3:
                response["last_commit"] = {
                    "hash": parts[0][:7],
                    "message": parts[1],
                    "time": parts[2],
                }

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    raise ValueError(f"Unknown tool: {name}")


async def main():
    """Main entry point for the GitHub MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())

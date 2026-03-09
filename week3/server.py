"""GitHub MCP Server - Using FastMCP."""

import os
import asyncio
from typing import Annotated
from datetime import datetime, timedelta, timezone
import jwt

import httpx
from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import JWTVerifier


# Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PORT = int(os.getenv("PORT", "3000"))
GITHUB_API_BASE = "https://api.github.com"
API_KEY = os.getenv("MCP_API_KEY", "default_api_key_change_in_production")

# Rate limit tracking
rate_limit_remaining: int = 60
rate_limit_reset: float = 0


def get_headers() -> dict:
    """Get headers for GitHub API requests."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GitHub-MCP-Server/1.0",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


async def check_rate_limit() -> tuple[bool, str]:
    """Check if we're rate limited. Returns (can_proceed, message)."""
    global rate_limit_remaining, rate_limit_reset

    if rate_limit_remaining > 0:
        return True, ""

    # Check if reset time has passed
    if asyncio.get_event_loop().time() >= rate_limit_reset:
        rate_limit_remaining = 60  # Reset counter
        return True, ""

    return False, f"Rate limited. Resets at {rate_limit_reset}"


async def make_request(
    method: str,
    url: str,
    retries: int = 3,
) -> dict | list | None:
    """Make HTTP request with retry logic and rate limit handling."""
    global rate_limit_remaining, rate_limit_reset

    backoff = 1
    last_error = None

    for _ in range(retries):
        can_proceed, msg = await check_rate_limit()
        if not can_proceed:
            raise Exception(msg)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=get_headers(),
                    timeout=10.0,
                )

                # Update rate limit info
                rate_limit_remaining = int(response.headers.get("X-RateLimit-Remaining", 60))
                reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                if reset_time > 0:
                    rate_limit_reset = reset_time

                if response.status_code == 429:
                    # Rate limited - wait and retry
                    wait_time = int(response.headers.get("Retry-After", backoff))
                    await asyncio.sleep(wait_time)
                    backoff *= 2
                    continue

                if response.status_code == 403:
                    raise Exception("Forbidden: Rate limit may be exceeded or token is invalid")

                response.raise_for_status()
                return response.json()

        except httpx.TimeoutException:
            last_error = "Request timed out"
            await asyncio.sleep(backoff)
            backoff *= 2
        except httpx.HTTPStatusError as e:
            last_error = f"HTTP {e.response.status_code}: {e.response.text}"
            await asyncio.sleep(backoff)
            backoff *= 2
        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")

    raise Exception(f"Request failed after {retries} retries: {last_error}")

auth = JWTVerifier(
    public_key=API_KEY,
    issuer="mcp-demo",
    audience="mcp-client",
    algorithm="HS256",
)
# Create FastMCP server
mcp = FastMCP("github-mcp-server", auth=auth)


def generate_token(username: str = "test_user") -> str:
    """Generate a JWT token for testing purposes."""
    payload = {
        "sub": username,
        "iss": "mcp-demo",
        "aud": "mcp-client",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, API_KEY, algorithm="HS256")



@mcp.tool()
async def get_repo_info(
    owner: Annotated[str, "Repository owner (user or organization)"],
    repo: Annotated[str, "Repository name"],
) -> str:
    """Get information about a GitHub repository including stars, forks, description, and open issues count."""
    owner = owner.strip()
    repo = repo.strip()

    if not owner or not repo:
        raise ValueError("owner and repo are required")

    # Input sanitization - prevent path traversal
    if ".." in owner or "/" in owner.replace("/", ""):
        raise ValueError("Invalid owner format")
    if ".." in repo or "/" in repo:
        raise ValueError("Invalid repo format")

    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
    data = await make_request("GET", url)

    result = {
        "name": data.get("name"),
        "full_name": data.get("full_name"),
        "description": data.get("description") or "No description",
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "open_issues": data.get("open_issues_count", 0),
        "default_branch": data.get("default_branch"),
        "url": data.get("html_url"),
        "language": data.get("language"),
    }

    return str(result)


@mcp.tool()
async def list_issues(
    owner: Annotated[str, "Repository owner (user or organization)"],
    repo: Annotated[str, "Repository name"],
    state: Annotated[str, "Issue state: open, closed, or all"] = "open",
    limit: Annotated[int, "Maximum number of issues to return"] = 10,
) -> str:
    """List issues for a GitHub repository with optional filtering by state."""
    owner = owner.strip()
    repo = repo.strip()
    limit = min(limit, 30)  # Cap at 30

    if not owner or not repo:
        raise ValueError("owner and repo are required")

    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues?state={state}&per_page={limit}"
    data = await make_request("GET", url)

    if not data:
        return "No issues found"

    issues = []
    for item in data[:limit]:
        # Skip pull requests (they're also returned by the issues endpoint)
        if "pull_request" in item:
            continue
        issues.append({
            "number": item.get("number"),
            "title": item.get("title"),
            "state": item.get("state"),
            "created_at": item.get("created_at"),
            "url": item.get("html_url"),
        })

    return str(issues)


@mcp.tool()
async def search_repositories(
    query: Annotated[str, "Search query (e.g., 'MCP server python')"],
    limit: Annotated[int, "Maximum number of results"] = 5,
) -> str:
    """Search GitHub repositories by query."""
    query = query.strip()
    limit = min(limit, 30)  # Cap at 30

    if not query:
        raise ValueError("query is required")

    url = f"{GITHUB_API_BASE}/search/repositories?q={query}&per_page={limit}"
    data = await make_request("GET", url)

    items = data.get("items", [])
    if not items:
        return "No repositories found"

    repos = []
    for item in items[:limit]:
        repos.append({
            "name": item.get("name"),
            "full_name": item.get("full_name"),
            "description": item.get("description") or "No description",
            "stars": item.get("stargazers_count", 0),
            "forks": item.get("forks_count", 0),
            "url": item.get("html_url"),
            "language": item.get("language"),
        })

    return str(repos)


if __name__ == "__main__":
    """Run the MCP server.

    Supports HTTP transport for remote access.
    For authentication, use a reverse proxy (nginx, Caddy).
    """
    print(f"Starting server on port {PORT}")
    # Print a test token when the module is loaded

    print(f"\n🔑 Test token: {generate_token()}\n")
    mcp.run(transport="http", port=PORT)

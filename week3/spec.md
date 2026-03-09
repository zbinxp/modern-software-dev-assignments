# MCP Server Specification

## Project Overview
- **Project Name**: GitHub MCP Server
- **Type**: Remote HTTP MCP Server
- **Core Functionality**: Provides tools to interact with GitHub API for repository issues, search, and repository information
- **Target Users**: Developers using Claude Desktop, Cursor, or other MCP-aware clients

## External API Choice
**GitHub REST API** (https://docs.github.com/en/rest)

### Endpoints Used
1. `GET /repos/{owner}/{repo}` - Get repository information
2. `GET /repos/{owner}/{repo}/issues` - List repository issues
3. `GET /search/repositories` - Search repositories

## MCP Tools (Minimum 2, Implementing 3)

### 1. `get_repo_info`
Returns repository details including description, stars, forks, open issues count, and default branch.
- **Input**: `owner` (string, required), `repo` (string, required)
- **Output**: Repository metadata object

### 2. `list_issues`
Lists open issues for a repository with optional filtering.
- **Input**: `owner` (string, required), `repo` (string, required), `state` (string, optional, default: "open"), `limit` (number, optional, default: 10)
- **Output**: Array of issue objects with title, number, state, created_at

### 3. `search_repositories`
Searches GitHub repositories by query.
- **Input**: `query` (string, required), `limit` (number, optional, default: 5)
- **Output**: Array of repository objects with name, description, stars, url

## Resilience Features

### Error Handling
- HTTP failures: Return structured error with status code and message
- Timeouts: 10-second timeout with clear timeout error message
- Empty results: Return empty array with informational message

### Rate Limiting
- GitHub API rate limit: 60 requests/hour for unauthenticated, 5000 for authenticated
- Implement check before each request
- When rate limited: Return user-facing warning with reset time
- Simple exponential backoff: Wait 1s, 2s, 4s on 429 responses (max 3 retries)

## Authentication

### API Key Support
- Environment variable: `GITHUB_TOKEN` (optional)
- Client can pass `Authorization: Bearer <token>` header
- Token validation: Verify token format (ghp_ prefix or classic PAT format)
- Token audience validation: Only use for GitHub API calls, never pass to upstream

### Security
- Tokens stored in environment, never logged
- Input sanitization for owner/repo parameters (prevent injection)
- HTTPS only for production

## Deployment

### Mode: Remote HTTP Server
- **Framework**: FastMCP (or standard HTTP with MCP protocol)
- **Port**: Configurable via `PORT` env var (default: 3000)
- **URL Pattern**: `http://localhost:3000/mcp`

### Server Startup
```bash
# With optional GitHub token
export GITHUB_TOKEN=ghp_xxxxx
export PORT=3000
python server.py
```

## Packaging & Documentation

### Setup Instructions
1. Install dependencies: `poetry install`
2. Set environment variables (optional):
   - `GITHUB_TOKEN` - GitHub personal access token for higher rate limits
   - `PORT` - Server port (default: 3000)
3. Run server: `poetry run python week3/server.py`

### Example Invocation Flow
1. Start the server: `python server.py`
2. Configure MCP client to connect to `http://localhost:3000/mcp`
3. Use tools:
   - `get_repo_info` with `owner: "anthropic", repo: "claude-code"`
   - `list_issues` with `owner: "microsoft", repo: "vscode"`
   - `search_repositories` with `query: "MCP server python"`

### Dependencies (managed via Poetry in root)
- `httpx` - Async HTTP client
- `fastmcp` - FastMCP server framework (simplified MCP)
- `python-dotenv` - Environment variable loading (already in project)

## File Structure
```
week3/
├── spec.md
├── server.py          # Main MCP server
└── README.md         # Documentation
```

**Note**: Dependencies are managed via Poetry in the project root `pyproject.toml`

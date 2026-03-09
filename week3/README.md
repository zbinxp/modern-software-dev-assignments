# GitHub MCP Server

An MCP (Model Context Protocol) server that provides tools for interacting with the GitHub API.

## Features

- **3 MCP Tools**: `get_repo_info`, `list_issues`, `search_repositories`
- **Resilience**: Timeout handling (10s), rate limit awareness, exponential backoff
- **Authentication**: Optional GitHub token via environment variable
- **Deployment**: Remote HTTP server with SSE transport

## External API

Uses [GitHub REST API v3](https://docs.github.com/en/rest):
- `GET /repos/{owner}/{repo}` - Repository info
- `GET /repos/{owner}/{repo}/issues` - List issues
- `GET /search/repositories` - Search repos

## Setup

1. Install dependencies:
   ```bash
   poetry install
   ```

2. Set environment variables (optional):
   ```bash
   # GitHub token for higher rate limits (60/hour -> 5000/hour)
   export GITHUB_TOKEN=ghp_xxxxxxxxxxxx

   # Server port (default: 3000)
   export PORT=3000
   ```

3. Run the server:
   ```bash
   poetry run python week3/server.py
   ```

## Usage

### Starting the Server

```bash
poetry run python week3/server.py
```

The server runs on `http://localhost:3000` by default.

### MCP Client Configuration

Connect to the server at:
- SSE endpoint: `http://localhost:3000/sse`
- Messages endpoint: `http://localhost:3000/messages/`

### Available Tools

#### 1. get_repo_info
Get repository metadata (stars, forks, description).

**Parameters:**
- `owner` (string, required) - Repository owner
- `repo` (string, required) - Repository name

**Example:**
```json
{
  "name": "get_repo_info",
  "arguments": {
    "owner": "anthropic",
    "repo": "claude-code"
  }
}
```

#### 2. list_issues
List repository issues with optional filtering.

**Parameters:**
- `owner` (string, required) - Repository owner
- `repo` (string, required) - Repository name
- `state` (string, optional) - "open", "closed", or "all" (default: "open")
- `limit` (number, optional) - Max results, 1-30 (default: 10)

**Example:**
```json
{
  "name": "list_issues",
  "arguments": {
    "owner": "microsoft",
    "repo": "vscode",
    "state": "open",
    "limit": 5
  }
}
```

#### 3. search_repositories
Search GitHub repositories by query.

**Parameters:**
- `query` (string, required) - Search query
- `limit` (number, optional) - Max results, 1-30 (default: 5)

**Example:**
```json
{
  "name": "search_repositories",
  "arguments": {
    "query": "MCP server python",
    "limit": 10
  }
}
```

## Rate Limits

- **Unauthenticated**: 60 requests/hour
- **Authenticated**: 5000 requests/hour

The server tracks rate limits and returns warnings when approaching limits.

## Error Handling

- HTTP errors: Returns descriptive error message with status code
- Timeouts: 10-second timeout with clear timeout error
- Empty results: Returns empty array with info message
- Rate limited: Returns warning with reset time

## Security

- Tokens stored in environment, never logged
- Input sanitization prevents path traversal
- Only GitHub API called, no third-party proxies

## Testing

Run tests with:
```bash
poetry run pytest week3/tests/test_server.py -v
```

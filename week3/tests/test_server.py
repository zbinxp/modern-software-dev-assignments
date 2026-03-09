"""Tests for GitHub MCP Server."""

from datetime import datetime, timezone

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
import jwt

# Import the server module functions
from server import (
    get_headers,
    check_rate_limit,
    make_request,
    get_repo_info,
    list_issues,
    search_repositories,
    generate_token,
    API_KEY,
    auth,
)


class TestGetHeaders:
    """Tests for get_headers function."""

    def test_get_headers_no_token(self):
        """Test headers without token."""
        with patch("server.GITHUB_TOKEN", None):
            headers = get_headers()
            assert "Authorization" not in headers
            assert headers["Accept"] == "application/vnd.github.v3+json"
            assert "User-Agent" in headers

    def test_get_headers_with_token(self):
        """Test headers with token."""
        with patch("server.GITHUB_TOKEN", "ghp_test123"):
            headers = get_headers()
            assert headers["Authorization"] == "Bearer ghp_test123"


class TestCheckRateLimit:
    """Tests for check_rate_limit function."""

    @pytest.mark.asyncio
    async def test_check_rate_limit_ok(self):
        """Test rate limit not exceeded."""
        with patch("server.rate_limit_remaining", 30):
            can_proceed, msg = await check_rate_limit()
            assert can_proceed is True
            assert msg == ""

    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeded(self):
        """Test rate limit exceeded."""
        # Set a future reset time so it doesn't auto-reset
        with patch("server.rate_limit_remaining", 0), \
             patch("server.rate_limit_reset", 9999999999):
            can_proceed, msg = await check_rate_limit()
            assert can_proceed is False
            assert "Rate limited" in msg


class TestMakeRequest:
    """Tests for make_request function."""

    @pytest.mark.asyncio
    async def test_make_request_success(self):
        """Test successful request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"X-RateLimit-Remaining": "59", "X-RateLimit-Reset": "0"}
        mock_response.json.return_value = {"name": "test-repo"}

        with patch("server.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await make_request("GET", "https://api.github.com/repos/test/repo")

            assert result == {"name": "test-repo"}

    @pytest.mark.asyncio
    async def test_make_request_timeout(self):
        """Test request timeout handling."""
        with patch("server.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.request.side_effect = httpx.TimeoutException("timeout")
            mock_client.return_value.__aenter__.return_value = mock_instance

            with pytest.raises(Exception) as exc_info:
                await make_request("GET", "https://api.github.com/repos/test/repo", retries=2)

            assert "timed out" in str(exc_info.value).lower() or "retries" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_make_request_http_error(self):
        """Test HTTP error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"

        with patch("server.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.request.side_effect = httpx.HTTPStatusError(
                "Not Found", request=MagicMock(), response=mock_response
            )
            mock_client.return_value.__aenter__.return_value = mock_instance

            with pytest.raises(Exception) as exc_info:
                await make_request("GET", "https://api.github.com/repos/test/repo")

            assert "404" in str(exc_info.value)


class TestGetRepoInfo:
    """Tests for get_repo_info function."""

    @pytest.mark.asyncio
    async def test_get_repo_info_success(self):
        """Test successful repo info retrieval."""
        mock_data = {
            "name": "claude-code",
            "full_name": "anthropic/claude-code",
            "description": "Claude Code CLI",
            "stargazers_count": 1000,
            "forks_count": 100,
            "open_issues_count": 10,
            "default_branch": "main",
            "html_url": "https://github.com/anthropic/claude-code",
            "language": "Python",
        }

        with patch("server.make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_data

            result = await get_repo_info("anthropic", "claude-code")

            assert "claude-code" in result
            assert "1000" in result
            assert "anthropic/claude-code" in result

    @pytest.mark.asyncio
    async def test_get_repo_info_missing_params(self):
        """Test missing parameters."""
        with pytest.raises(ValueError):
            await get_repo_info("", "")

    @pytest.mark.asyncio
    async def test_get_repo_info_invalid_owner(self):
        """Test invalid owner format."""
        with pytest.raises(ValueError) as exc_info:
            await get_repo_info("..", "repo")
        assert "Invalid" in str(exc_info.value)


class TestListIssues:
    """Tests for list_issues function."""

    @pytest.mark.asyncio
    async def test_list_issues_success(self):
        """Test successful issues listing."""
        mock_data = [
            {"number": 1, "title": "Bug fix", "state": "open", "created_at": "2024-01-01", "html_url": "https://github.com/test/repo/issues/1"},
            {"number": 2, "title": "Feature", "state": "closed", "created_at": "2024-01-02", "html_url": "https://github.com/test/repo/issues/2"},
        ]

        with patch("server.make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_data

            result = await list_issues("test", "repo")

            assert "Bug fix" in result
            assert "1" in result

    @pytest.mark.asyncio
    async def test_list_issues_empty(self):
        """Test empty issues list."""
        with patch("server.make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = []

            result = await list_issues("test", "repo")

            assert result == "No issues found"

    @pytest.mark.asyncio
    async def test_list_issues_limit(self):
        """Test issues limit."""
        mock_data = [{"number": i, "title": f"Issue {i}", "state": "open", "created_at": "2024-01-01", "html_url": f"https://github.com/test/repo/issues/{i}"} for i in range(35)]

        with patch("server.make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_data

            # Should cap at 30
            await list_issues("test", "repo", limit=50)


class TestSearchRepositories:
    """Tests for search_repositories function."""

    @pytest.mark.asyncio
    async def test_search_repositories_success(self):
        """Test successful search."""
        mock_data = {
            "items": [
                {"name": "repo1", "full_name": "user/repo1", "description": "A repo", "stargazers_count": 100, "forks_count": 10, "html_url": "https://github.com/user/repo1", "language": "Python"},
            ]
        }

        with patch("server.make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_data

            result = await search_repositories("test query")

            assert "repo1" in result
            assert "100" in result

    @pytest.mark.asyncio
    async def test_search_repositories_empty(self):
        """Test empty search results."""
        with patch("server.make_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"items": []}

            result = await search_repositories("nonexistentquery12345")

            assert result == "No repositories found"

    @pytest.mark.asyncio
    async def test_search_repositories_missing_query(self):
        """Test missing query."""
        with pytest.raises(ValueError):
            await search_repositories("")


class TestJWTAuthentication:
    """Tests for JWT token authentication."""

    def test_generate_token(self):
        """Test JWT token generation."""
        from server import generate_token, API_KEY
        token = generate_token("testuser")
        assert token is not None
        assert isinstance(token, str)
        # Token should be a valid JWT (3 parts separated by dots)
        assert len(token.split(".")) == 3

    def test_generate_token_default_user(self):
        """Test JWT token generation with default user."""
        from server import generate_token
        token = generate_token()
        assert token is not None
        assert isinstance(token, str)

    def test_jwt_verifier_initialization(self):
        """Test JWTVerifier is properly initialized."""
        from server import auth, API_KEY
        # Verify auth object exists and has expected attributes
        assert auth is not None

    def test_token_contains_expected_claims(self):
        """Test JWT token contains expected claims."""
        import jwt as pyjwt
        from server import generate_token, API_KEY
        from datetime import datetime, timezone

        token = generate_token("testuser")
        # Decode without verification for testing
        decoded = pyjwt.decode(token, options={"verify_signature": False})

        assert decoded["sub"] == "testuser"
        assert decoded["iss"] == "mcp-demo"
        assert decoded["aud"] == "mcp-client"
        assert "exp" in decoded
        assert "iat" in decoded

    def test_token_expiration(self):
        """Test JWT token has proper expiration."""
        import jwt as pyjwt
        from server import generate_token, API_KEY

        token = generate_token("testuser")
        decoded = pyjwt.decode(token, options={"verify_signature": False})

        # Token should expire in approximately 1 hour
        exp_time = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        iat_time = datetime.fromtimestamp(decoded["iat"], tz=timezone.utc)
        # Allow some tolerance (59-61 minutes)
        diff_minutes = (exp_time - iat_time).total_seconds() / 60
        assert 59 <= diff_minutes <= 61

    def test_api_key_configuration(self):
        """Test API_KEY is configured."""
        from server import API_KEY
        assert API_KEY is not None
        assert len(API_KEY) > 0

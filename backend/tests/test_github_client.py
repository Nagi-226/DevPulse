"""GitHub API 客户端单元测试."""

from __future__ import annotations

import base64
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from devpulse.services.github_client import (
    GitHubAuthError,
    GitHubClient,
    GitHubNotFoundError,
    GitHubRateLimitError,
)


def _make_mock_response(status_code: int, json_data: dict, headers: dict | None = None):
    """构造一个 mimicked httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.headers = headers or {}
    resp.json.return_value = json_data
    return resp


@pytest.fixture
def client() -> GitHubClient:
    return GitHubClient(token="test-token", base_url="https://api.github.com")


@pytest.mark.asyncio
async def test_fetch_repo_success(client: GitHubClient):
    """正常返回仓库数据."""
    mock_resp = _make_mock_response(
        200,
        {
            "full_name": "test-owner/test-repo",
            "description": "A test repository",
            "language": "Python",
            "stargazers_count": 1000,
            "forks_count": 200,
            "topics": ["testing", "python"],
            "open_issues_count": 5,
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-06-01T00:00:00Z",
        },
    )

    with patch.object(client._client, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_resp
        result = await client.fetch_repo("test-owner", "test-repo")

    assert result["full_name"] == "test-owner/test-repo"
    assert result["description"] == "A test repository"
    assert result["language"] == "Python"
    assert result["total_stars"] == 1000
    assert result["forks"] == 200
    assert result["topics"] == ["testing", "python"]
    assert result["open_issues"] == 5


@pytest.mark.asyncio
async def test_fetch_repo_not_found(client: GitHubClient):
    """404 处理."""
    mock_resp = _make_mock_response(404, {})

    with patch.object(client._client, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_resp
        with pytest.raises(GitHubNotFoundError):
            await client.fetch_repo("ghost", "not-exist")


@pytest.mark.asyncio
async def test_rate_limit(client: GitHubClient):
    """403 + Retry-After 处理."""
    mock_resp = _make_mock_response(403, {}, headers={"Retry-After": "60"})

    with patch.object(client._client, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_resp
        with pytest.raises(GitHubRateLimitError) as exc_info:
            await client.fetch_repo("test-owner", "test-repo")
        assert exc_info.value.retry_after == 60


@pytest.mark.asyncio
async def test_fetch_readme_success(client: GitHubClient):
    """正常获取 README."""
    content = base64.b64encode(b"# Hello World\nThis is a test.").decode()
    mock_resp = _make_mock_response(200, {"content": content, "encoding": "base64"})

    with patch.object(client._client, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_resp
        result = await client.fetch_readme("test-owner", "test-repo")

    assert result == "# Hello World\nThis is a test."


@pytest.mark.asyncio
async def test_fetch_releases_success(client: GitHubClient):
    """正常获取 Release 列表."""
    mock_resp = _make_mock_response(
        200,
        [
            {"tag_name": "v1.0.0", "name": "First Release"},
            {"tag_name": "v0.9.0", "name": "Beta"},
        ],
    )

    with patch.object(client._client, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_resp
        result = await client.fetch_releases("test-owner", "test-repo")

    assert len(result) == 2
    assert result[0]["tag_name"] == "v1.0.0"


@pytest.mark.asyncio
async def test_check_rate_limit(client: GitHubClient):
    """查询限流状态."""
    mock_resp = _make_mock_response(200, {"rate": {"limit": 5000, "remaining": 4999}})

    with patch.object(client._client, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_resp
        result = await client.check_rate_limit()

    assert result["rate"]["limit"] == 5000


@pytest.mark.asyncio
async def test_auth_error(client: GitHubClient):
    """401 token 无效."""
    mock_resp = _make_mock_response(401, {})

    with patch.object(client._client, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_resp
        with pytest.raises(GitHubAuthError):
            await client.fetch_repo("test-owner", "test-repo")


@pytest.mark.asyncio
async def test_close(client: GitHubClient):
    """关闭客户端不应抛异常."""
    with patch.object(client._client, "aclose", new_callable=AsyncMock) as mock_close:
        await client.close()
        mock_close.assert_called_once()

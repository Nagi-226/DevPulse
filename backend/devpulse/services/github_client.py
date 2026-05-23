"""GitHub REST API v3 客户端 —— 基于 httpx.AsyncClient."""

from __future__ import annotations

import base64
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class GitHubClientError(Exception):
    """GitHub API 调用异常基类."""


class GitHubAuthError(GitHubClientError):
    """401 — Token 无效或无权限."""


class GitHubRateLimitError(GitHubClientError):
    """403 — API 限流."""

    def __init__(self, retry_after: int | None = None) -> None:
        super().__init__("GitHub API rate limit exceeded")
        self.retry_after = retry_after


class GitHubNotFoundError(GitHubClientError):
    """404 — 仓库不存在."""


class GitHubClient:
    """GitHub REST API v3 异步客户端.

    Args:
        token: GitHub Personal Access Token.
        base_url: API 基础地址，默认 https://api.github.com。
        timeout: 请求超时（秒）。
        max_retries: 失败重试次数（仅 5xx）。
    """

    def __init__(
        self,
        token: str,
        base_url: str = "https://api.github.com",
        timeout: int = 30,
        max_retries: int = 3,
    ) -> None:
        headers: dict[str, str] = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "DevPulse/0.0.2",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        transport = httpx.AsyncHTTPTransport(retries=max_retries)
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers=headers,
            timeout=httpx.Timeout(timeout),
            transport=transport,
        )

    async def close(self) -> None:
        """关闭底层 HTTP 客户端."""
        await self._client.aclose()

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        """统一请求入口，附带日志与错误处理."""
        logger.info("GitHub API %s %s", method, path)
        response = await self._client.request(method, path, **kwargs)

        if response.status_code == 401:
            logger.error("GitHub API 401 — token 无效")
            raise GitHubAuthError("Invalid GitHub token")
        if response.status_code == 403:
            retry_after = response.headers.get("Retry-After")
            retry_seconds = int(retry_after) if retry_after and retry_after.isdigit() else None
            logger.error("GitHub API 403 — rate limited (Retry-After=%s)", retry_after)
            raise GitHubRateLimitError(retry_after=retry_seconds)
        if response.status_code == 404:
            logger.warning("GitHub API 404 — %s not found", path)
            raise GitHubNotFoundError(f"Resource not found: {path}")

        response.raise_for_status()
        logger.info("GitHub API %s %s → %d", method, path, response.status_code)
        return response

    async def fetch_repo(self, owner: str, repo: str) -> dict[str, Any]:
        """获取仓库详细信息.

        GET /repos/{owner}/{repo}

        Returns:
            仓库详情字典，包含 stars/forks/language/description/topics/
            open_issues/created_at/updated_at 等字段。
        """
        resp = await self._request("GET", f"/repos/{owner}/{repo}")
        data: dict[str, Any] = resp.json()
        return {
            "full_name": data.get("full_name", f"{owner}/{repo}"),
            "description": data.get("description"),
            "language": data.get("language"),
            "total_stars": data.get("stargazers_count", 0),
            "forks": data.get("forks_count", 0),
            "topics": data.get("topics", []),
            "open_issues": data.get("open_issues_count", 0),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
        }

    async def fetch_readme(self, owner: str, repo: str) -> str:
        """获取仓库 README 内容（base64 解码为纯文本).

        GET /repos/{owner}/{repo}/readme
        """
        resp = await self._request("GET", f"/repos/{owner}/{repo}/readme")
        data: dict[str, Any] = resp.json()
        content = data.get("content", "")
        return base64.b64decode(content).decode("utf-8", errors="replace")

    async def fetch_releases(
        self, owner: str, repo: str, per_page: int = 3
    ) -> list[dict[str, Any]]:
        """获取仓库最新 Release 列表.

        GET /repos/{owner}/{repo}/releases
        """
        resp = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/releases",
            params={"per_page": per_page},
        )
        return resp.json()  # type: ignore[no-any-return]

    async def check_rate_limit(self) -> dict[str, Any]:
        """查询当前 API 限流状态.

        GET /rate_limit
        """
        resp = await self._request("GET", "/rate_limit")
        return resp.json()  # type: ignore[no-any-return]

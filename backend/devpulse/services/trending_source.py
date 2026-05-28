"""多源 Trending 数据源 — 策略模式抽象基类 + 三种实现."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

import httpx
from bs4 import BeautifulSoup

from devpulse.config import settings

logger = logging.getLogger(__name__)


class TrendingRepo:
    """Trending 仓库数据传输对象."""

    def __init__(
        self,
        full_name: str = "",
        owner: str = "",
        name: str = "",
        description: str = "",
        language: str = "",
        total_stars: int = 0,
        stars_since: int = 0,
        forks: int = 0,
        forks_since: int = 0,
        url: str = "",
    ) -> None:
        self.full_name = full_name
        self.owner = owner
        self.name = name
        self.description = description
        self.language = language
        self.total_stars = total_stars
        self.stars_since = stars_since
        self.forks = forks
        self.forks_since = forks_since
        self.url = url

    def to_dict(self) -> dict[str, Any]:
        return {
            "full_name": self.full_name,
            "owner": self.owner,
            "name": self.name,
            "description": self.description,
            "language": self.language,
            "total_stars": self.total_stars,
            "stars_since": self.stars_since,
            "forks": self.forks,
            "forks_since": self.forks_since,
            "url": self.url,
        }


class TrendingSource(ABC):
    """Trending 数据源抽象基类.

    新增数据源只需继承此类并实现 fetch_trending() 和 fetch_repo_detail().
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """数据源名称（github/gitlab/gitee）."""
        ...

    @abstractmethod
    async def fetch_trending(
        self, language: str = "", since: str = "weekly", limit: int = 25
    ) -> list[TrendingRepo]:
        """获取 Trending 仓库列表.

        Args:
            language: 语言过滤（空=全部）.
            since: 时间范围 daily/weekly/monthly.
            limit: 返回条数上限.

        Returns:
            TrendingRepo 列表.
        """
        ...

    @abstractmethod
    async def fetch_repo_detail(self, owner: str, repo: str) -> dict[str, Any]:
        """获取单个仓库详情.

        Returns:
            含 stars/forks/open_issues/created_at 等的字典.
        """
        ...


class GitHubSource(TrendingSource):
    """GitHub Trending 数据源（基于 Playwright 页面解析）."""

    source_name = "github"

    def __init__(self) -> None:
        self._scraper = None

    async def _get_scraper(self):
        if self._scraper is None:
            from devpulse.services.trending_scraper import TrendingScraper

            self._scraper = TrendingScraper(headless=True)
        return self._scraper

    async def fetch_trending(
        self, language: str = "", since: str = "weekly", limit: int = 25
    ) -> list[TrendingRepo]:
        scraper = await self._get_scraper()
        raw_repos = await scraper.scrape_trending(language=language, since=since)

        result: list[TrendingRepo] = []
        for r in raw_repos[:limit]:
            result.append(TrendingRepo(
                full_name=f"{r['owner']}/{r['repo_name']}",
                owner=r["owner"],
                name=r["repo_name"],
                description=r.get("description", ""),
                language=r.get("language", ""),
                total_stars=r.get("total_stars", 0),
                stars_since=r.get("stars_since", 0),
                forks=r.get("forks", 0),
                forks_since=r.get("forks_since", 0),
                url=r.get("url", f"https://github.com/{r['owner']}/{r['repo_name']}"),
            ))
        return result

    async def fetch_repo_detail(self, owner: str, repo: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}",
                headers={
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": settings.CRAWLER_USER_AGENT,
                    **(
                        {"Authorization": f"Bearer {settings.GITHUB_TOKEN}"}
                        if settings.GITHUB_TOKEN else {}
                    ),
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "total_stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "open_issues": data.get("open_issues_count", 0),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at"),
                "language": data.get("language"),
                "description": data.get("description"),
            }


class GitLabSource(TrendingSource):
    """GitLab Explore 数据源（公开页面解析）."""

    source_name = "gitlab"
    BASE_URL = "https://gitlab.com/explore/projects/trending"

    async def fetch_trending(
        self, language: str = "", since: str = "weekly", limit: int = 25
    ) -> list[TrendingRepo]:
        url = self.BASE_URL
        result: list[TrendingRepo] = []

        async with httpx.AsyncClient(
            timeout=settings.CRAWLER_TIMEOUT,
            headers={"User-Agent": settings.CRAWLER_USER_AGENT},
        ) as client:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                # 解析 GitLab Explore 页面项目列表
                project_cards = soup.select('[data-testid="project-row"]')
                if not project_cards:
                    project_cards = soup.select(".project-row")

                for card in project_cards[:limit]:
                    try:
                        name_el = card.select_one(".project-title a") or card.select_one("a.project")
                        if not name_el:
                            continue
                        href = name_el.get("href", "")
                        full_name = href.strip("/") if href else ""
                        parts = full_name.split("/")
                        owner = parts[0] if len(parts) >= 1 else ""
                        name = parts[1] if len(parts) >= 2 else ""

                        desc_el = card.select_one(".project-description") or card.select_one(".description")
                        description = desc_el.get_text(strip=True) if desc_el else ""

                        stars_el = card.select_one(".star-count")
                        total_stars = int(stars_el.get_text(strip=True).replace(",", "")) if stars_el else 0

                        result.append(TrendingRepo(
                            full_name=full_name,
                            owner=owner,
                            name=name,
                            description=description,
                            language=language,
                            total_stars=total_stars,
                            url=f"https://gitlab.com/{full_name}",
                        ))
                    except Exception:
                        logger.exception("Failed to parse GitLab project card")

            except Exception:
                logger.exception("Failed to fetch GitLab trending")

        logger.info("GitLabSource: fetched %d projects", len(result))
        return result

    async def fetch_repo_detail(self, owner: str, repo: str) -> dict[str, Any]:
        project_path = f"{owner}%2F{repo}"
        async with httpx.AsyncClient(
            timeout=settings.CRAWLER_TIMEOUT,
            headers={
                "User-Agent": settings.CRAWLER_USER_AGENT,
                **(
                    {"PRIVATE-TOKEN": settings.GITLAB_TOKEN}
                    if settings.GITLAB_TOKEN else {}
                ),
            },
        ) as client:
            try:
                resp = await client.get(
                    f"{settings.GITLAB_API_BASE_URL}/projects/{project_path}"
                )
                resp.raise_for_status()
                data = resp.json()
                return {
                    "total_stars": data.get("star_count", 0),
                    "forks": data.get("forks_count", 0),
                    "open_issues": data.get("open_issues_count", 0),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("last_activity_at"),
                    "language": None,
                    "description": data.get("description"),
                }
            except Exception:
                logger.exception("GitLab API failed for %s/%s", owner, repo)
                return {"total_stars": 0, "forks": 0, "open_issues": 0}


class GiteeSource(TrendingSource):
    """Gitee Explore 数据源（公开页面解析）."""

    source_name = "gitee"
    BASE_URL = "https://gitee.com/explore"

    async def fetch_trending(
        self, language: str = "", since: str = "weekly", limit: int = 25
    ) -> list[TrendingRepo]:
        url = self.BASE_URL
        result: list[TrendingRepo] = []

        async with httpx.AsyncClient(
            timeout=settings.CRAWLER_TIMEOUT,
            headers={"User-Agent": settings.CRAWLER_USER_AGENT},
        ) as client:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                # 解析 Gitee Explore 页面项目列表
                project_items = soup.select(".explore-projects .item") or soup.select(".projects-list .item")

                for item in project_items[:limit]:
                    try:
                        link_el = item.select_one("a.title") or item.select_one("a.project-title")
                        if not link_el:
                            continue
                        href = link_el.get("href", "")
                        full_name = href.strip("/") if href else ""
                        parts = full_name.split("/")
                        owner = parts[0] if len(parts) >= 1 else ""
                        name = parts[1] if len(parts) >= 2 else ""

                        desc_el = item.select_one(".description") or item.select_one("p.desc")
                        description = desc_el.get_text(strip=True) if desc_el else ""

                        stars_el = item.select_one(".stars-count") or item.select_one(".star-count")
                        total_stars = int(stars_el.get_text(strip=True).replace(",", "")) if stars_el else 0

                        result.append(TrendingRepo(
                            full_name=full_name,
                            owner=owner,
                            name=name,
                            description=description,
                            language=language,
                            total_stars=total_stars,
                            url=f"https://gitee.com/{full_name}",
                        ))
                    except Exception:
                        logger.exception("Failed to parse Gitee project card")

            except Exception:
                logger.exception("Failed to fetch Gitee trending")

        logger.info("GiteeSource: fetched %d projects", len(result))
        return result

    async def fetch_repo_detail(self, owner: str, repo: str) -> dict[str, Any]:
        async with httpx.AsyncClient(
            timeout=settings.CRAWLER_TIMEOUT,
            headers={
                "User-Agent": settings.CRAWLER_USER_AGENT,
                **(
                    {"access_token": settings.GITEE_TOKEN}
                    if settings.GITEE_TOKEN else {}
                ),
            },
        ) as client:
            try:
                resp = await client.get(
                    f"{settings.GITEE_API_BASE_URL}/repos/{owner}/{repo}"
                )
                resp.raise_for_status()
                data = resp.json()
                return {
                    "total_stars": data.get("stargazers_count", 0),
                    "forks": data.get("forks_count", 0),
                    "open_issues": data.get("open_issues_count", 0),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                    "language": data.get("language"),
                    "description": data.get("description"),
                }
            except Exception:
                logger.exception("Gitee API failed for %s/%s", owner, repo)
                return {"total_stars": 0, "forks": 0, "open_issues": 0}


def create_source(source_name: str) -> TrendingSource:
    """工厂方法：根据名称创建对应数据源.

    Args:
        source_name: "github" | "gitlab" | "gitee".

    Returns:
        TrendingSource 实例.

    Raises:
        ValueError: 未知数据源.
    """
    sources: dict[str, type[TrendingSource]] = {
        "github": GitHubSource,
        "gitlab": GitLabSource,
        "gitee": GiteeSource,
    }

    source_cls = sources.get(source_name.lower())
    if source_cls is None:
        raise ValueError(
            f"Unknown source: {source_name}. "
            f"Available: {list(sources.keys())}"
        )

    return source_cls()

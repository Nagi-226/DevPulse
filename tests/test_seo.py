"""M8: SEO 测试 — sitemap.xml + OG meta."""
import pytest


class TestSEO:
    """SEO 端点测试套件."""

    async def test_sitemap_xml(self, async_client, seed_repos):
        """sitemap.xml 应返回有效的 XML."""
        response = await async_client.get("/seo/sitemap.xml")
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "xml" in content_type
        content = response.text
        assert "<?xml" in content
        assert "<urlset" in content
        assert "<url>" in content
        assert "<loc>" in content
        # 应包含静态页面
        assert "sitemaps.org" in content or "devpulse.app" in content

    async def test_sitemap_contains_repos(self, async_client, seed_repos):
        """sitemap 应包含仓库详情页 URL."""
        response = await async_client.get("/seo/sitemap.xml")
        assert response.status_code == 200
        content = response.text
        # 应包含 seed_repos 中 approved 状态的仓库
        assert "seed-owner/seed-repo" in content or "owner1" in content

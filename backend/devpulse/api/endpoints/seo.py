"""SEO 端点 — sitemap.xml 动态生成."""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import Response

from devpulse.config import settings
from devpulse.core.database import Database

router = APIRouter(prefix="/seo", tags=["seo"])


@router.get("/sitemap.xml")
async def sitemap(request: Request) -> Response:
    """动态生成 sitemap.xml.

    内容:
        - 静态页面 (home, search, recommended)
        - 仓库详情页 (动态)
    """
    base_url = settings.API_BASE_URL or "https://devpulse.app"
    today = date.today().isoformat()

    entries = [
        f"""  <url>
    <loc>{base_url}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>""",
        f"""  <url>
    <loc>{base_url}/search</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>""",
        f"""  <url>
    <loc>{base_url}/recommended</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>""",
    ]

    # 动态仓库详情页
    try:
        db: Database | None = getattr(request.app.state, "db", None)
        if db is not None:
            from sqlalchemy import select

            from devpulse.core.models import Repository

            async with db.get_session() as session:
                result = await session.execute(
                    select(Repository.full_name, Repository.updated_at)
                    .where(Repository.review_status != "rejected")
                    .order_by(Repository.total_stars.desc())
                    .limit(500)
                )
                rows = result.all()
                for full_name, updated_at in rows:
                    lastmod = (
                        updated_at.date().isoformat()
                        if updated_at
                        else today
                    )
                    entries.append(
                        f"""  <url>
    <loc>{base_url}/repo/{full_name}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
  </url>"""
                    )
    except Exception:
        pass

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(entries)}
</urlset>"""

    return Response(content=xml, media_type="application/xml")

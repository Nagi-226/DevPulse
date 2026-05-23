"""DevPulse FastAPI 应用入口."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from devpulse import __version__

app = FastAPI(
    title="DevPulse",
    description="AI 潮汐 — GitHub Trending AI/ML 周报引擎",
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420", "tauri://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    """健康检查端点."""
    return {"status": "ok", "version": __version__}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("devpulse.main:app", host="127.0.0.1", port=8000, reload=True)

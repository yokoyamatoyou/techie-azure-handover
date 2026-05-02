# -*- coding: utf-8 -*-
"""Lightweight FastAPI server for doorknock PDF generation.

Runs independently on port 8082. Uses aio2-main's SEOAIOAnalyzer
for analysis and doorknock_pdf for PDF generation.

Usage:
    python doorknock_server.py
"""
import sys
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

# Add aio2-main to path for SEOAIOAnalyzer
AIO_ROOT = Path(__file__).resolve().parent.parent / "aio2-main"
sys.path.insert(0, str(AIO_ROOT))

from doorknock_pdf import generate_doorknock_pdf

app = FastAPI(title="\u30b3\u30c8\u30e0\u30b9\u30d3 API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class DoorknockRequest(BaseModel):
    url: str
    agent_name: str = ""


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate")
async def generate(req: DoorknockRequest):
    """Run analysis and generate doorknock PDF."""
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URLが必要です")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        from core.engine.orchestrator import SEOAIOAnalyzer
        analyzer = SEOAIOAnalyzer(analysis_mode="standard")
        results = analyzer.analyze_url(
            url=url,
            user_industry="自動判定",
            balance=50,
            deep_mode=False,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析エラー: {str(e)}")

    try:
        pdf_path = generate_doorknock_pdf(
            analysis_results=results,
            agent_name=req.agent_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF生成エラー: {str(e)}")

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=pdf_path.name,
    )


if __name__ == "__main__":
    import os
    host = "0.0.0.0" if os.environ.get("CONTAINER_ENV") else "127.0.0.1"
    port = int(os.environ.get("PORT", "8082"))
    uvicorn.run(app, host=host, port=port)

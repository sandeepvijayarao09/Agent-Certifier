import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.core.config import settings
from app.core.security import (
    SlidingWindowRateLimiter,
    enforce_rate_limit,
    sanitize_filename,
)
from app.models.agent import Agent, AgentStatus
from app.models.test_result import TestResult

router = APIRouter(prefix="/api/agents", tags=["agents"])

upload_limiter = SlidingWindowRateLimiter(
    settings.upload_rate_limit, settings.rate_limit_window_seconds
)

LANGUAGE_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".go": "Go",
    ".java": "Java",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".cpp": "C++",
    ".cc": "C++",
    ".cs": "C#",
    ".php": "PHP",
}


class AgentResponse(BaseModel):
    id: str
    name: str
    filename: str
    language: str
    file_size: int
    status: str
    created_at: datetime
    updated_at: datetime
    overall_score: Optional[float] = None
    certification_level: Optional[str] = None
    test_count: int = 0

    class Config:
        from_attributes = True


class AgentDetailResponse(AgentResponse):
    test_results: List[dict] = []


def detect_language(filename: str) -> str:
    _, ext = os.path.splitext(filename.lower())
    return LANGUAGE_MAP.get(ext, "Unknown")


def get_certification_level(score: float) -> str:
    if score >= 90:
        return "PLATINUM"
    elif score >= 80:
        return "GOLD"
    elif score >= 70:
        return "SILVER"
    elif score >= 60:
        return "BRONZE"
    return "NOT_CERTIFIED"


async def build_agent_response(agent: Agent, db: AsyncSession) -> dict:
    result = await db.execute(
        select(TestResult).where(TestResult.agent_id == agent.id)
    )
    test_results = result.scalars().all()

    overall_score = agent.overall_score
    certification_level = agent.certification_level

    if (
        overall_score is None
        and test_results
        and agent.status == AgentStatus.completed
    ):
        # Calculate weighted score
        weights = {
            "security": 0.30,
            "stability": 0.20,
            "performance": 0.15,
            "informatics": 0.15,
            "compliance": 0.10,
            "ethics": 0.10,
        }
        category_scores = {}
        for tr in test_results:
            cat = tr.category.lower()
            if cat not in category_scores:
                category_scores[cat] = []
            category_scores[cat].append(tr.score)

        weighted_total = 0.0
        total_weight = 0.0
        for cat, weight in weights.items():
            if cat in category_scores and category_scores[cat]:
                avg = sum(category_scores[cat]) / len(category_scores[cat])
                weighted_total += avg * weight
                total_weight += weight

        if total_weight > 0:
            overall_score = weighted_total / total_weight
            certification_level = get_certification_level(overall_score)

    return {
        "id": agent.id,
        "name": agent.name,
        "filename": agent.filename,
        "language": agent.language,
        "file_size": agent.file_size,
        "status": agent.status.value,
        "created_at": agent.created_at,
        "updated_at": agent.updated_at,
        "overall_score": round(overall_score, 1) if overall_score is not None else None,
        "certification_level": certification_level,
        "test_count": len(test_results),
    }


@router.post("/upload")
async def upload_agent(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    enforce_rate_limit(upload_limiter, request)

    filename = sanitize_filename(file.filename or "unknown")
    _, ext = os.path.splitext(filename.lower())

    if ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(settings.allowed_extensions)}",
        )

    max_mb = settings.max_upload_size // (1024 * 1024)
    size_error = HTTPException(
        status_code=413, detail=f"File too large (max {max_mb}MB)"
    )

    # Reject early on the declared length, then enforce while reading so an
    # unbounded body is never fully buffered.
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > settings.max_upload_size + 4096:
        raise size_error

    chunks: list[bytes] = []
    total = 0
    while chunk := await file.read(64 * 1024):
        total += len(chunk)
        if total > settings.max_upload_size:
            raise size_error
        chunks.append(chunk)
    content = b"".join(chunks)

    if not content.strip():
        raise HTTPException(status_code=400, detail="File is empty")
    if b"\x00" in content:
        raise HTTPException(
            status_code=400, detail="File appears to be binary, not source code"
        )

    try:
        file_text = content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            file_text = content.decode("latin-1")
        except Exception:
            raise HTTPException(status_code=400, detail="Could not decode file as text")

    language = detect_language(filename)
    name = os.path.splitext(filename)[0][:100]

    agent = Agent(
        name=name,
        filename=filename,
        language=language,
        file_content=file_text,
        file_size=len(content),
        status=AgentStatus.pending,
        updated_at=datetime.utcnow(),
    )
    db.add(agent)
    await db.flush()
    await db.refresh(agent)

    return {
        "id": agent.id,
        "name": agent.name,
        "filename": agent.filename,
        "language": agent.language,
        "file_size": agent.file_size,
        "status": agent.status.value,
        "created_at": agent.created_at,
        "updated_at": agent.updated_at,
        "message": "Agent uploaded successfully",
    }


@router.get("")
async def list_agents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).order_by(Agent.created_at.desc()))
    agents = result.scalars().all()
    responses = []
    for agent in agents:
        responses.append(await build_agent_response(agent, db))
    return responses


@router.get("/{agent_id}")
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    base = await build_agent_response(agent, db)

    # Add test results
    tr_result = await db.execute(
        select(TestResult).where(TestResult.agent_id == agent_id).order_by(TestResult.category, TestResult.test_name)
    )
    test_results = tr_result.scalars().all()
    base["test_results"] = [
        {
            "id": tr.id,
            "category": tr.category,
            "test_name": tr.test_name,
            "status": tr.status.value,
            "score": tr.score,
            "details": tr.details,
            "duration_ms": tr.duration_ms,
            "created_at": tr.created_at.isoformat(),
        }
        for tr in test_results
    ]
    return base


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    await db.delete(agent)
    return {"message": "Agent deleted successfully"}

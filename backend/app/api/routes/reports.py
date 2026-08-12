from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.agent import Agent, AgentStatus
from app.models.test_result import TestResult
from app.services.reporter import ReportGenerator

router = APIRouter(prefix="/api/agents", tags=["reports"])


@router.get("/{agent_id}/report")
async def get_report(agent_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent.status != AgentStatus.completed:
        raise HTTPException(
            status_code=400,
            detail=f"Agent tests not completed. Current status: {agent.status.value}",
        )

    tr_result = await db.execute(
        select(TestResult).where(TestResult.agent_id == agent_id)
    )
    test_results = tr_result.scalars().all()

    generator = ReportGenerator()
    report = generator.generate(agent, list(test_results))
    return report


@router.get("/{agent_id}/certificate")
async def get_certificate(agent_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent.status != AgentStatus.completed:
        raise HTTPException(
            status_code=400,
            detail=f"Agent tests not completed. Current status: {agent.status.value}",
        )

    tr_result = await db.execute(
        select(TestResult).where(TestResult.agent_id == agent_id)
    )
    test_results = tr_result.scalars().all()

    generator = ReportGenerator()
    report = generator.generate(agent, list(test_results))

    return {
        "agent_id": agent.id,
        "agent_name": agent.name,
        "language": agent.language,
        "certification_level": report["certification_level"],
        "overall_score": report["overall_score"],
        "test_date": report["test_date"],
        "certification_valid_until": report["certification_valid_until"],
        "category_scores": {
            k: v["score"] for k, v in report["category_scores"].items()
        },
        "issued_by": "Agent Certifier Platform",
        "certificate_id": f"CERT-{agent.id[:8].upper()}",
        "frameworks": report["frameworks"],
    }

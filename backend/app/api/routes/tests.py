import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db, AsyncSessionLocal
from app.models.agent import Agent, AgentStatus
from app.models.test_result import TestResult
from app.services.orchestrator import TestOrchestrator

router = APIRouter(prefix="/api/agents", tags=["tests"])


async def run_tests_background(agent_id: str):
    """Run tests in background without holding the request session."""
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Agent).where(Agent.id == agent_id))
            agent = result.scalar_one_or_none()
            if not agent:
                return

            orchestrator = TestOrchestrator()
            await orchestrator.run(agent, db)
            await db.commit()
        except Exception as e:
            async with AsyncSessionLocal() as db2:
                try:
                    result = await db2.execute(select(Agent).where(Agent.id == agent_id))
                    agent = result.scalar_one_or_none()
                    if agent:
                        agent.status = AgentStatus.failed
                        await db2.commit()
                except Exception:
                    pass


@router.post("/{agent_id}/run")
async def run_tests(
    agent_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent.status == AgentStatus.running:
        raise HTTPException(status_code=409, detail="Tests are already running for this agent")

    # Clear previous results
    prev = await db.execute(select(TestResult).where(TestResult.agent_id == agent_id))
    for tr in prev.scalars().all():
        await db.delete(tr)

    from datetime import datetime
    agent.status = AgentStatus.running
    agent.updated_at = datetime.utcnow()
    await db.commit()

    background_tasks.add_task(run_tests_background, agent_id)

    return {"message": "Test suite started", "agent_id": agent_id, "status": "running"}


@router.get("/{agent_id}/status")
async def get_status(agent_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    count_result = await db.execute(
        select(TestResult).where(TestResult.agent_id == agent_id)
    )
    completed_tests = len(count_result.scalars().all())

    return {
        "agent_id": agent_id,
        "status": agent.status.value,
        "completed_tests": completed_tests,
        "total_tests": 60,  # 6 categories x 10 tests
        "updated_at": agent.updated_at.isoformat(),
    }


@router.get("/{agent_id}/results")
async def get_results(agent_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    tr_result = await db.execute(
        select(TestResult).where(TestResult.agent_id == agent_id).order_by(TestResult.category, TestResult.test_name)
    )
    test_results = tr_result.scalars().all()

    # Group by category
    categories = {}
    for tr in test_results:
        cat = tr.category
        if cat not in categories:
            categories[cat] = {
                "category": cat,
                "tests": [],
                "average_score": 0.0,
                "passed": 0,
                "failed": 0,
                "warnings": 0,
            }
        categories[cat]["tests"].append({
            "id": tr.id,
            "test_name": tr.test_name,
            "status": tr.status.value,
            "score": tr.score,
            "details": tr.details,
            "duration_ms": tr.duration_ms,
        })
        if tr.status.value == "pass":
            categories[cat]["passed"] += 1
        elif tr.status.value == "fail":
            categories[cat]["failed"] += 1
        elif tr.status.value == "warning":
            categories[cat]["warnings"] += 1

    for cat_data in categories.values():
        scores = [t["score"] for t in cat_data["tests"]]
        cat_data["average_score"] = round(sum(scores) / len(scores), 1) if scores else 0.0

    return {
        "agent_id": agent_id,
        "status": agent.status.value,
        "categories": list(categories.values()),
    }

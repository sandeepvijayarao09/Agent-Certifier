from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from collections import Counter, defaultdict

from app.core.database import get_db
from app.models.agent import Agent, AgentStatus
from app.models.test_result import TestResult, TestStatus

router = APIRouter(prefix="/api/stats", tags=["stats"])

CATEGORIES = ["security", "stability", "performance", "informatics", "compliance", "ethics"]
CATEGORY_WEIGHTS = {
    "security": 0.30, "stability": 0.20, "performance": 0.15,
    "informatics": 0.15, "compliance": 0.10, "ethics": 0.10,
}


@router.get("")
async def get_platform_stats(db: AsyncSession = Depends(get_db)):
    agents_result = await db.execute(select(Agent).order_by(Agent.created_at.desc()))
    agents = agents_result.scalars().all()

    tested = [a for a in agents if a.status == AgentStatus.completed]
    scored = [a for a in tested if a.overall_score is not None]

    # Certification distribution
    cert_dist = Counter(
        a.certification_level for a in scored if a.certification_level
    )

    # Language distribution
    lang_dist = Counter(a.language for a in agents)

    # Average overall score
    avg_score = (
        round(sum(a.overall_score for a in scored) / len(scored), 1) if scored else 0
    )

    # Score distribution buckets: 0-9, 10-19, ..., 90-100
    score_buckets = [0] * 10
    for a in scored:
        bucket = min(int(a.overall_score // 10), 9)
        score_buckets[bucket] += 1

    # Pass rate across all test results
    tr_result = await db.execute(select(TestResult))
    all_results = tr_result.scalars().all()

    total_tests = len(all_results)
    passed = sum(1 for r in all_results if r.status == TestStatus.pass_)
    failed = sum(1 for r in all_results if r.status == TestStatus.fail)
    warned = sum(1 for r in all_results if r.status == TestStatus.warning)
    pass_rate = round(passed / total_tests * 100, 1) if total_tests else 0

    # Category averages across all agents
    cat_scores: dict[str, list[float]] = defaultdict(list)
    for r in all_results:
        if r.status != TestStatus.skip:
            cat_scores[r.category].append(r.score)

    category_averages = {
        cat: round(sum(scores) / len(scores), 1) if scores else 0
        for cat, scores in cat_scores.items()
    }

    # Category pass rates
    cat_pass: dict[str, dict] = {}
    for cat in CATEGORIES:
        cat_results = [r for r in all_results if r.category == cat]
        if cat_results:
            p = sum(1 for r in cat_results if r.status == TestStatus.pass_)
            f = sum(1 for r in cat_results if r.status == TestStatus.fail)
            w = sum(1 for r in cat_results if r.status == TestStatus.warning)
            cat_pass[cat] = {
                "passed": p, "failed": f, "warnings": w,
                "total": len(cat_results),
                "pass_rate": round(p / len(cat_results) * 100, 1),
            }

    # Most common failures
    fail_results = [r for r in all_results if r.status == TestStatus.fail]
    fail_counter = Counter(f"{r.category}/{r.test_name}" for r in fail_results)
    top_failures = [
        {"test": k, "count": v}
        for k, v in fail_counter.most_common(5)
    ]

    # Recent agents (last 5)
    recent = [
        {
            "id": a.id,
            "name": a.name,
            "language": a.language,
            "status": a.status.value,
            "overall_score": a.overall_score,
            "certification_level": a.certification_level,
            "created_at": a.created_at.isoformat(),
        }
        for a in agents[:5]
    ]

    # Top performers (top 5 by score)
    top = sorted(scored, key=lambda a: a.overall_score or 0, reverse=True)[:5]
    top_agents = [
        {
            "id": a.id,
            "name": a.name,
            "language": a.language,
            "overall_score": a.overall_score,
            "certification_level": a.certification_level,
        }
        for a in top
    ]

    return {
        "totals": {
            "agents": len(agents),
            "tested": len(tested),
            "certified": sum(
                1 for a in scored
                if a.certification_level and a.certification_level != "NOT_CERTIFIED"
            ),
            "not_certified": cert_dist.get("NOT_CERTIFIED", 0),
            "running": sum(1 for a in agents if a.status == AgentStatus.running),
            "failed_runs": sum(1 for a in agents if a.status == AgentStatus.failed),
            "total_test_executions": total_tests,
            "pass_rate": pass_rate,
        },
        "avg_score": avg_score,
        "score_distribution": {
            f"{i*10}-{i*10+9}": score_buckets[i] for i in range(10)
        },
        "certification_distribution": {
            "PLATINUM": cert_dist.get("PLATINUM", 0),
            "GOLD": cert_dist.get("GOLD", 0),
            "SILVER": cert_dist.get("SILVER", 0),
            "BRONZE": cert_dist.get("BRONZE", 0),
            "NOT_CERTIFIED": cert_dist.get("NOT_CERTIFIED", 0),
        },
        "language_distribution": dict(lang_dist.most_common(10)),
        "category_averages": category_averages,
        "category_pass_rates": cat_pass,
        "top_failures": top_failures,
        "recent_agents": recent,
        "top_agents": top_agents,
        "test_summary": {
            "passed": passed, "failed": failed,
            "warnings": warned, "total": total_tests,
        },
    }

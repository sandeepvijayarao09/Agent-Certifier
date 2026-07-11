import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent, AgentStatus
from app.models.test_result import TestResult, TestStatus
from app.services.analyzer.security import SecurityAnalyzer
from app.services.analyzer.stability import StabilityAnalyzer
from app.services.analyzer.informatics import InformaticsAnalyzer
from app.services.analyzer.performance import PerformanceAnalyzer
from app.services.analyzer.compliance import ComplianceAnalyzer
from app.services.analyzer.ethics import EthicsAnalyzer


CATEGORY_WEIGHTS = {
    "security": 0.30,
    "stability": 0.20,
    "performance": 0.15,
    "informatics": 0.15,
    "compliance": 0.10,
    "ethics": 0.10,
}

STATUS_MAP = {
    "pass": TestStatus.pass_,
    "fail": TestStatus.fail,
    "warning": TestStatus.warning,
    "skip": TestStatus.skip,
}


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


class TestOrchestrator:
    def __init__(self):
        self.analyzers = [
            SecurityAnalyzer(),
            StabilityAnalyzer(),
            InformaticsAnalyzer(),
            PerformanceAnalyzer(),
            ComplianceAnalyzer(),
            EthicsAnalyzer(),
        ]

    async def run(self, agent: Agent, db: AsyncSession):
        agent.status = AgentStatus.running
        agent.updated_at = datetime.utcnow()
        await db.flush()

        try:
            code = agent.file_content
            language = agent.language
            category_scores: dict[str, list[float]] = {}

            for analyzer in self.analyzers:
                # Run in thread pool to avoid blocking event loop
                results = await asyncio.get_event_loop().run_in_executor(
                    None, analyzer.analyze, code, language
                )

                for result in results:
                    status = STATUS_MAP.get(result.status, TestStatus.skip)
                    tr = TestResult(
                        agent_id=agent.id,
                        category=analyzer.category,
                        test_name=result.test_name,
                        status=status,
                        score=round(result.score, 2),
                        duration_ms=round(result.duration_ms, 2),
                    )
                    tr.details = result.details
                    db.add(tr)
                    if status != TestStatus.skip:
                        category_scores.setdefault(analyzer.category, []).append(tr.score)

            await db.flush()

            weighted = 0.0
            total_weight = 0.0
            for category, scores in category_scores.items():
                weight = CATEGORY_WEIGHTS.get(category, 0)
                if scores and weight:
                    weighted += (sum(scores) / len(scores)) * weight
                    total_weight += weight

            overall = round(weighted / total_weight, 1) if total_weight else 0.0
            agent.overall_score = overall
            agent.certification_level = get_certification_level(overall)
            agent.status = AgentStatus.completed
            agent.updated_at = datetime.utcnow()
            await db.flush()

        except Exception as e:
            agent.status = AgentStatus.failed
            agent.updated_at = datetime.utcnow()
            await db.flush()
            raise

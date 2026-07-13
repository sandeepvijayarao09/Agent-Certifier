import asyncio
import logging
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.agent import Agent, AgentStatus
from app.models.test_result import TestResult, TestStatus
from app.services.analyzer.base import BaseAnalyzer, AnalysisResult
from app.services.analyzer.security import SecurityAnalyzer
from app.services.analyzer.stability import StabilityAnalyzer
from app.services.analyzer.informatics import InformaticsAnalyzer
from app.services.analyzer.performance import PerformanceAnalyzer
from app.services.analyzer.compliance import ComplianceAnalyzer
from app.services.analyzer.ethics import EthicsAnalyzer

logger = logging.getLogger(__name__)


def _run_analyzer(analyzer: BaseAnalyzer, code: str, language: str) -> List[AnalysisResult]:
    """Module-level entry point executed inside a worker process.

    Running analysis in a separate process (rather than a thread) means a
    pathological input that triggers catastrophic regex backtracking can be
    killed outright on timeout instead of pinning a CPU forever.
    """
    return analyzer.analyze(code, language)


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
        self._executor: Optional[ProcessPoolExecutor] = None
        self._use_processes = True

    def _get_executor(self) -> Optional[ProcessPoolExecutor]:
        """Return the worker-process pool, lazily created.

        If a process pool can't be spawned in this environment we fall back to
        the event loop's default thread pool (executor=None). Timeouts still
        free the request path in that mode, but can't hard-kill the worker.
        """
        if self._executor is None and self._use_processes:
            try:
                # Use the default start method (fork on Linux) on purpose:
                # spawn/forkserver re-import __main__, which under
                # `uvicorn app.main:app` would re-trigger server startup in the
                # worker. Analyzers only run pure, lock-free regex, so forking a
                # worker from the threaded server process is safe here.
                self._executor = ProcessPoolExecutor(max_workers=1)
            except Exception:
                logger.warning(
                    "ProcessPoolExecutor unavailable; falling back to thread pool"
                )
                self._use_processes = False
        return self._executor

    def _kill_executor(self) -> None:
        """Forcibly terminate the current worker so a timed-out or crashed
        analysis stops consuming CPU, then drop it so the next call spins up a
        fresh pool. No-op when running on the shared thread pool."""
        executor = self._executor
        self._executor = None
        if executor is None:
            return
        for proc in list((getattr(executor, "_processes", None) or {}).values()):
            try:
                proc.terminate()
            except Exception:
                pass
        try:
            executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass

    async def run(self, agent: Agent, db: AsyncSession):
        agent.status = AgentStatus.running
        agent.updated_at = datetime.utcnow()
        await db.flush()

        try:
            code = agent.file_content
            language = agent.language
            category_scores: dict[str, list[float]] = {}
            loop = asyncio.get_running_loop()

            for analyzer in self.analyzers:
                # Run each category in a worker process and bound its runtime.
                # On timeout the worker is killed outright (a cancelled thread
                # would keep running), so a pathological ReDoS input can't
                # stall the run or pin a CPU indefinitely.
                try:
                    results = await asyncio.wait_for(
                        loop.run_in_executor(
                            self._get_executor(), _run_analyzer, analyzer, code, language
                        ),
                        timeout=settings.analyzer_timeout_seconds,
                    )
                except asyncio.TimeoutError:
                    logger.warning(
                        "Analyzer %s timed out for agent %s; terminating worker",
                        analyzer.category,
                        agent.id,
                    )
                    self._kill_executor()
                    results = []
                except Exception:
                    # e.g. a BrokenProcessPool if the worker died mid-run.
                    # Skip this category rather than failing the whole run.
                    logger.exception(
                        "Analyzer %s failed for agent %s", analyzer.category, agent.id
                    )
                    self._kill_executor()
                    results = []

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

            # No category produced a single scorable result: every analyzer
            # timed out or crashed. That's an infrastructure failure, not a
            # zero-quality agent, so fail the run instead of persisting a
            # misleading 0.0 / NOT_CERTIFIED score.
            if total_weight == 0:
                raise RuntimeError("No analyzer produced results; run failed")

            overall = round(weighted / total_weight, 1)
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
        finally:
            self._kill_executor()

"""Orchestrator behavior: score persistence, all-fail handling, timeout hard-kill.

These tests drive the orchestrator directly against a dedicated async engine so
they never share the global engine's event loop with the API TestClient.
"""
import asyncio
import os
import tempfile
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.database import Base
from app.core import config
from app.models.agent import Agent, AgentStatus
from app.models.test_result import TestResult as ResultRow
from app.services.orchestrator import TestOrchestrator as Orchestrator
from app.services.analyzer.security import SecurityAnalyzer
from tests._slow import SlowAnalyzer


def _fresh_sessionmaker():
    path = tempfile.mkstemp(prefix="orch_test_", suffix=".db")[1]
    engine = create_async_engine(f"sqlite+aiosqlite:///{path}",
                                 connect_args={"check_same_thread": False})
    return engine


async def _make_tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def test_run_persists_score_and_level():
    async def scenario():
        engine = _fresh_sessionmaker()
        await _make_tables(engine)
        Session = async_sessionmaker(engine, expire_on_commit=False)
        async with Session() as db:
            agent = Agent(name="clean", filename="clean.py", language="Python",
                          file_content="def f(x):\n    return x\n", file_size=20,
                          status=AgentStatus.pending)
            db.add(agent)
            await db.flush()
            await Orchestrator().run(agent, db)
            await db.commit()
            assert agent.status == AgentStatus.completed
            assert agent.overall_score is not None
            assert agent.certification_level
            rows = (await db.execute(
                select(ResultRow).where(ResultRow.agent_id == agent.id))).scalars().all()
            assert len(rows) == 60
        await engine.dispose()

    asyncio.run(scenario())


def test_all_analyzers_fail_marks_run_failed():
    async def scenario():
        original = config.settings.analyzer_timeout_seconds
        config.settings.analyzer_timeout_seconds = 1
        try:
            engine = _fresh_sessionmaker()
            await _make_tables(engine)
            Session = async_sessionmaker(engine, expire_on_commit=False)
            orch = Orchestrator()
            orch.analyzers = [SlowAnalyzer()]  # only analyzer always times out
            async with Session() as db:
                agent = Agent(name="x", filename="x.py", language="Python",
                              file_content="print(1)\n", file_size=9,
                              status=AgentStatus.pending)
                db.add(agent)
                await db.flush()
                raised = False
                try:
                    await orch.run(agent, db)
                except RuntimeError:
                    raised = True
                assert raised, "run should raise when no analyzer produces results"
                assert agent.status == AgentStatus.failed
                assert agent.overall_score is None
            await engine.dispose()
        finally:
            config.settings.analyzer_timeout_seconds = original

    asyncio.run(scenario())


def test_timeout_hard_kills_worker(tmp_path):
    import pytest

    pid_file = str(tmp_path / "pid")
    os.environ["SLOW_PID_FILE"] = pid_file

    async def scenario():
        original = config.settings.analyzer_timeout_seconds
        config.settings.analyzer_timeout_seconds = 1
        try:
            engine = _fresh_sessionmaker()
            await _make_tables(engine)
            Session = async_sessionmaker(engine, expire_on_commit=False)
            orch = Orchestrator()
            # slow one is killed; the real one must still run afterwards
            orch.analyzers = [SlowAnalyzer(), SecurityAnalyzer()]
            async with Session() as db:
                agent = Agent(name="spin", filename="spin.py", language="Python",
                              file_content="print('x')\n", file_size=10,
                              status=AgentStatus.pending)
                db.add(agent)
                await db.flush()
                t0 = time.time()
                await orch.run(agent, db)
                elapsed = time.time() - t0
                await db.commit()
                rows = (await db.execute(
                    select(ResultRow).where(ResultRow.agent_id == agent.id))).scalars().all()
            await engine.dispose()
            return orch._use_processes, elapsed, pid_file, rows
        finally:
            config.settings.analyzer_timeout_seconds = original

    used_processes, elapsed, pidf, rows = asyncio.run(scenario())

    if not used_processes:
        pytest.skip("process pool unavailable in this environment")

    assert elapsed < 15, "run was not bounded by the timeout"
    time.sleep(1.0)
    with open(pidf) as f:
        worker_pid = int(f.read().strip())
    alive = True
    try:
        os.kill(worker_pid, 0)
    except ProcessLookupError:
        alive = False
    assert not alive, "runaway worker was not hard-killed"
    # the second analyzer still produced results (pool recovered)
    assert len(rows) >= 10
    assert not any(r.test_name == "slow_test" for r in rows)

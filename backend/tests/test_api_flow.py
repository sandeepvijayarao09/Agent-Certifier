"""End-to-end API flow: health, headers, run, report, consistency, stats."""


def test_health_and_security_headers(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"
    h = r.headers
    assert h.get("x-content-type-options") == "nosniff"
    assert h.get("x-frame-options") == "DENY"
    assert h.get("referrer-policy") == "no-referrer"
    assert "content-security-policy" in h


def test_insecure_agent_run_and_report(run_agent):
    from tests.conftest import INSECURE_CODE
    _, resp = run_agent("insecure_agent.py", INSECURE_CODE)
    assert resp.status_code == 200
    rep = resp.json()
    assert rep["total_tests"] == 60
    assert rep["failed_tests"] > 0
    # LLM output execution is a hard fail
    llm = next(t for t in rep["test_details"]["security"]
               if t["test_name"] == "llm_output_execution")
    assert llm["status"] == "fail" and llm["score"] == 0.0
    assert rep["certification_level"] in {"NOT_CERTIFIED", "BRONZE"}


def test_score_consistent_across_endpoints(client, run_agent):
    from tests.conftest import INSECURE_CODE
    aid, resp = run_agent("insecure_agent.py", INSECURE_CODE)
    rep = resp.json()
    listed = {a["id"]: a for a in client.get("/api/agents").json()}[aid]
    cert = client.get(f"/api/agents/{aid}/certificate").json()
    assert rep["overall_score"] == listed["overall_score"] == cert["overall_score"]


def test_clean_agent_scores_higher(run_agent):
    from tests.conftest import INSECURE_CODE, CLEAN_CODE
    _, insecure = run_agent("insecure_agent.py", INSECURE_CODE)
    _, clean = run_agent("clean_agent.py", CLEAN_CODE)
    assert clean.json()["overall_score"] > insecure.json()["overall_score"]


def test_stats_dashboard_populated(client, run_agent):
    from tests.conftest import INSECURE_CODE, CLEAN_CODE
    run_agent("insecure_agent.py", INSECURE_CODE)
    run_agent("clean_agent.py", CLEAN_CODE)
    stats = client.get("/api/stats").json()
    assert stats["totals"]["tested"] == 2
    assert stats["avg_score"] > 0  # scores were persisted
    assert sum(stats["certification_distribution"].values()) == 2
    assert len(stats["top_agents"]) == 2


def test_report_requires_completed(client):
    up = client.post("/api/agents/upload",
                     files={"file": ("x.py", b"print(1)\n", "text/plain")})
    aid = up.json()["id"]
    # not run yet -> report should 400
    assert client.get(f"/api/agents/{aid}/report").status_code == 400

"""Agentic governance lane: analyzer unit checks and report integration."""
from app.services.analyzer.agentic import analyze_agentic
from tests.conftest import MCP_AGENT_CODE, AGENT_CARD_JSON, PLAIN_CODE, INSECURE_CODE


def _ids(findings):
    return {f["id"] for f in findings}


def test_source_agent_findings():
    findings = analyze_agentic(MCP_AGENT_CODE, "Python", "mcp_agent.py")
    ids = _ids(findings)
    assert "tool_arbitrary_execution" in ids
    assert "unrestricted_tool_scope" in ids
    assert "unguarded_delegation" in ids
    assert "insecure_agent_transport" in ids
    assert any(f["status"] == "fail" for f in findings)
    # every finding carries resolved standard refs
    for f in findings:
        assert f["standards"] and all("code" in s and "framework" in s for s in f["standards"])


def test_manifest_findings():
    findings = analyze_agentic(AGENT_CARD_JSON, "JSON", "agent_card.json")
    ids = _ids(findings)
    assert "agentcard_insecure_url" in ids
    assert "agentcard_no_auth" in ids


def test_plain_code_has_no_agentic_findings():
    assert analyze_agentic(PLAIN_CODE, "Python", "plain.py") == []


def test_findings_sorted_fail_first():
    findings = analyze_agentic(MCP_AGENT_CODE, "Python", "mcp_agent.py")
    order = {"fail": 0, "warning": 1, "pass": 2, "skip": 3}
    seq = [order[f["status"]] for f in findings]
    assert seq == sorted(seq)


def test_agentic_in_report_and_coverage(run_agent):
    _, resp = run_agent("mcp_agent.py", MCP_AGENT_CODE)
    rep = resp.json()
    assert len(rep["agentic_governance"]) >= 4
    cov = {c["code"]: c for c in rep["standards_coverage"]}
    assert "OWASP-ASI07" in cov
    # ASI07 is agentic-only (no core test maps to it) -> evidence is agentic/*
    assert any(t.startswith("agentic/") for t in cov["OWASP-ASI07"]["tests"])


def test_non_agent_report_has_no_agentic_section(run_agent):
    _, resp = run_agent("insecure_agent.py", INSECURE_CODE)
    rep = resp.json()
    assert rep["agentic_governance"] == []
    labels = [t for c in rep["standards_coverage"] for t in c["tests"]]
    assert not any(t.startswith("agentic/") for t in labels)

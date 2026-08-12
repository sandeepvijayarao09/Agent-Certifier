"""Standards mapping: sync with analyzers, and surfaced in the report."""
from app.services.analyzer.standards import TEST_STANDARDS, resolve_standard
from app.services.orchestrator import TestOrchestrator as Orchestrator


def test_standards_map_in_sync_with_analyzers():
    all_tests = {t.name for a in Orchestrator().analyzers for t in a.tests}
    assert set(TEST_STANDARDS) == all_tests, (
        f"missing={all_tests - set(TEST_STANDARDS)} "
        f"extra={set(TEST_STANDARDS) - all_tests}"
    )


def test_resolve_standard_deep_links():
    cwe = resolve_standard("CWE-89")
    assert cwe["url"] == "https://cwe.mitre.org/data/definitions/89.html"
    gdpr = resolve_standard("GDPR-Art32")
    assert gdpr["url"] == "https://gdpr-info.eu/art-32-gdpr/"
    asi = resolve_standard("OWASP-ASI05")
    assert asi["title"] == "Unexpected Code Execution"
    assert asi["url"].startswith("https://genai.owasp.org")


def test_report_has_standards_coverage(run_agent):
    from tests.conftest import INSECURE_CODE
    _, resp = run_agent("insecure_agent.py", INSECURE_CODE)
    rep = resp.json()
    assert len(rep["frameworks"]) >= 5
    codes = {c["code"] for c in rep["standards_coverage"]}
    assert "OWASP-ASI05" in codes
    asi05 = next(c for c in rep["standards_coverage"] if c["code"] == "OWASP-ASI05")
    assert asi05["status"] == "fail"  # exec of LLM output
    # per-test tags present
    llm = next(t for t in rep["test_details"]["security"]
               if t["test_name"] == "llm_output_execution")
    assert any(s["code"] == "OWASP-ASI05" for s in llm["standards"])
    # coverage sorted most-severe first
    order = {"fail": 3, "warning": 2, "pass": 1, "skip": 0}
    sev = [order[c["status"]] for c in rep["standards_coverage"]]
    assert sev == sorted(sev, reverse=True)

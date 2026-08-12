"""Mapping of certifier tests to recognized AI-agent / security / compliance standards.

Each of the 60 tests is annotated with the external framework controls it speaks
to, so a report can show which industry standards an agent is being measured
against (and where it passes or fails them). Frameworks referenced:

- OWASP Top 10 for Agentic Applications (2026)  -> codes ``OWASP-ASI01``..``ASI10``
- OWASP Top 10 for LLM Applications (2025)       -> codes ``OWASP-LLM01``..``LLM10``
- MITRE CWE (classic code weaknesses)            -> codes ``CWE-<n>``
- EU GDPR                                         -> codes ``GDPR-Art<n>``
- ISO/IEC 42001:2023 (AI management system)       -> code  ``ISO-42001``
- ISO/IEC 25010 (product quality / maintainability) -> code ``ISO-25010``
- NIST AI Risk Management Framework               -> codes ``NIST-GOVERN|MAP|MEASURE|MANAGE``
- AIUC-1 (AI agent security & reliability cert)   -> codes ``AIUC1-ATK|DATA|BND|ERR``

Performance / informatics tests that have no recognized *certification* control
are intentionally left unmapped (empty list) rather than mapped to a made-up
standard.
"""
from typing import Dict, List


# test_name -> list of standard control codes it is evidence for
TEST_STANDARDS: Dict[str, List[str]] = {
    # --- Security ---
    "injection_vulnerability": ["OWASP-ASI05", "CWE-78", "CWE-89", "AIUC1-ATK"],
    "hardcoded_secrets": ["OWASP-LLM02", "CWE-798", "AIUC1-DATA"],
    "prompt_injection_resistance": ["OWASP-ASI01", "OWASP-LLM01", "AIUC1-ATK"],
    "data_exfiltration_risk": ["OWASP-ASI02", "OWASP-LLM02", "AIUC1-DATA"],
    "authentication_mechanisms": ["OWASP-ASI03", "CWE-306", "AIUC1-BND"],
    "input_validation": ["OWASP-ASI01", "CWE-20"],
    "dependency_vulnerability": ["OWASP-ASI04", "OWASP-LLM03", "CWE-502"],
    "privilege_escalation_risk": ["OWASP-ASI03", "CWE-269"],
    "information_disclosure": ["OWASP-LLM02", "CWE-209"],
    "llm_output_execution": ["OWASP-ASI05", "OWASP-LLM05", "OWASP-LLM06"],
    # --- Stability ---
    "error_handling_coverage": ["OWASP-ASI08", "AIUC1-ERR"],
    "infinite_loop_detection": ["OWASP-LLM10", "OWASP-ASI08"],
    "recursion_depth_protection": ["OWASP-LLM10"],
    "resource_leak_detection": ["OWASP-LLM10", "CWE-404"],
    "timeout_implementation": ["OWASP-LLM10", "OWASP-ASI08"],
    "graceful_degradation": ["OWASP-ASI08", "AIUC1-ERR"],
    "state_management": ["OWASP-ASI06"],
    "memory_management": ["OWASP-LLM10", "CWE-401"],
    "concurrency_safety": ["CWE-362", "OWASP-ASI08"],
    "exception_specificity": ["AIUC1-ERR", "CWE-396"],
    # --- Performance (only where a recognized control genuinely applies) ---
    "caching_implementation": [],
    "async_await_usage": [],
    "batch_processing_support": [],
    "connection_pooling": [],
    "lazy_loading": [],
    "algorithm_complexity": ["CWE-407", "OWASP-LLM10"],
    "streaming_support": [],
    "rate_limit_awareness": ["OWASP-LLM10"],
    "resource_cleanup": ["CWE-404"],
    "token_cost_optimization": ["OWASP-LLM10"],
    # --- Informatics (software quality standard) ---
    "code_complexity": ["ISO-25010"],
    "documentation_coverage": ["ISO-42001", "ISO-25010"],
    "function_modularity": ["ISO-25010"],
    "type_annotation_coverage": ["ISO-25010"],
    "response_format_consistency": [],
    "logging_implementation": ["ISO-42001", "NIST-MEASURE"],
    "configuration_externalization": ["ISO-25010"],
    "api_contract_clarity": ["ISO-25010"],
    "naming_convention": ["ISO-25010"],
    "code_duplication_risk": ["ISO-25010"],
    # --- Compliance ---
    "pii_handling": ["GDPR-Art5", "GDPR-Art32", "AIUC1-DATA"],
    "data_retention_policy": ["GDPR-Art5"],
    "audit_logging": ["ISO-42001", "NIST-MEASURE"],
    "gdpr_indicators": ["GDPR-Art5", "GDPR-Art30"],
    "license_compatibility": ["ISO-42001"],
    "tos_compliance": ["ISO-42001"],
    "output_filtering": ["OWASP-LLM05", "OWASP-LLM02"],
    "user_consent_mechanisms": ["GDPR-Art7"],
    "data_minimization": ["GDPR-Art5"],
    "regulatory_framework_awareness": ["ISO-42001", "NIST-GOVERN"],
    # --- Ethics ---
    "bias_detection": ["NIST-MEASURE", "ISO-42001"],
    "transparency_indicators": ["ISO-42001", "NIST-GOVERN"],
    "human_oversight_hooks": ["OWASP-LLM06", "NIST-MANAGE"],
    "refusal_mechanisms": ["OWASP-LLM06", "OWASP-ASI01"],
    "fairness_indicators": ["NIST-MEASURE"],
    "explainability": ["ISO-42001", "NIST-MAP"],
    "harm_prevention": ["OWASP-ASI10", "NIST-MANAGE"],
    "misinformation_risk": ["OWASP-LLM09", "NIST-MEASURE"],
    "manipulation_detection": ["OWASP-ASI09"],
    "accountability_mechanisms": ["ISO-42001", "NIST-GOVERN"],
}


# Human-readable title for each control code
_TITLES: Dict[str, str] = {
    "OWASP-ASI01": "Agent Goal Hijack",
    "OWASP-ASI02": "Tool Misuse & Exploitation",
    "OWASP-ASI03": "Identity & Privilege Abuse",
    "OWASP-ASI04": "Agentic Supply Chain Vulnerabilities",
    "OWASP-ASI05": "Unexpected Code Execution",
    "OWASP-ASI06": "Memory & Context Poisoning",
    "OWASP-ASI07": "Insecure Inter-Agent Communication",
    "OWASP-ASI08": "Cascading Agent Failures",
    "OWASP-ASI09": "Human-Agent Trust Exploitation",
    "OWASP-ASI10": "Rogue Agents",
    "OWASP-LLM01": "Prompt Injection",
    "OWASP-LLM02": "Sensitive Information Disclosure",
    "OWASP-LLM03": "Supply Chain",
    "OWASP-LLM05": "Improper Output Handling",
    "OWASP-LLM06": "Excessive Agency",
    "OWASP-LLM09": "Misinformation",
    "OWASP-LLM10": "Unbounded Consumption",
    "CWE-20": "Improper Input Validation",
    "CWE-78": "OS Command Injection",
    "CWE-89": "SQL Injection",
    "CWE-209": "Information Exposure Through an Error Message",
    "CWE-269": "Improper Privilege Management",
    "CWE-306": "Missing Authentication for Critical Function",
    "CWE-362": "Concurrent Execution Race Condition",
    "CWE-396": "Declaration of Catch for Generic Exception",
    "CWE-401": "Missing Release of Memory after Effective Lifetime",
    "CWE-404": "Improper Resource Shutdown or Release",
    "CWE-407": "Inefficient Algorithmic Complexity",
    "CWE-502": "Deserialization of Untrusted Data",
    "CWE-798": "Use of Hard-coded Credentials",
    "GDPR-Art5": "Principles relating to processing of personal data",
    "GDPR-Art7": "Conditions for consent",
    "GDPR-Art30": "Records of processing activities",
    "GDPR-Art32": "Security of processing",
    "ISO-42001": "AI Management System",
    "ISO-25010": "Maintainability / Product Quality",
    "NIST-GOVERN": "AI RMF Function: GOVERN",
    "NIST-MAP": "AI RMF Function: MAP",
    "NIST-MEASURE": "AI RMF Function: MEASURE",
    "NIST-MANAGE": "AI RMF Function: MANAGE",
    "AIUC1-ATK": "Attack Resistance",
    "AIUC1-DATA": "Data Protection",
    "AIUC1-BND": "Operational Boundaries",
    "AIUC1-ERR": "Error Prevention",
}


def _family(code: str) -> "tuple[str, str]":
    """Return (framework name, framework home URL) for a control code."""
    if code.startswith("OWASP-ASI"):
        return ("OWASP Agentic Applications Top 10 (2026)",
                "https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/")
    if code.startswith("OWASP-LLM"):
        return ("OWASP Top 10 for LLM Applications (2025)",
                "https://genai.owasp.org/llm-top-10/")
    if code.startswith("CWE-"):
        num = code.split("-", 1)[1]
        return ("MITRE CWE", f"https://cwe.mitre.org/data/definitions/{num}.html")
    if code.startswith("GDPR-Art"):
        num = code.split("Art", 1)[1]
        return ("EU GDPR", f"https://gdpr-info.eu/art-{num}-gdpr/")
    if code == "ISO-42001":
        return ("ISO/IEC 42001:2023 (AI Management System)",
                "https://www.iso.org/standard/42001")
    if code == "ISO-25010":
        return ("ISO/IEC 25010 (Product Quality)",
                "https://iso25000.com/index.php/en/iso-25000-standards/iso-25010")
    if code.startswith("NIST-"):
        return ("NIST AI Risk Management Framework",
                "https://www.nist.gov/itl/ai-risk-management-framework")
    if code.startswith("AIUC1-"):
        return ("AIUC-1 (AI Agent Security & Reliability)", "")
    return (code, "")


def resolve_standard(code: str) -> Dict[str, str]:
    """Expand a control code into a full reference object for API/UI use."""
    framework, url = _family(code)
    return {
        "code": code,
        "framework": framework,
        "title": _TITLES.get(code, code),
        "url": url,
    }


def standards_for(test_name: str) -> List[Dict[str, str]]:
    """Resolved standard references for a single test."""
    return [resolve_standard(c) for c in TEST_STANDARDS.get(test_name, [])]

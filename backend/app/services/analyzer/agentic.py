"""Agentic governance lane.

The 60 core tests scan source with regex heuristics. They cannot see the
*agentic* risk surface — how tools are exposed to an LLM, what scopes/identity
those tools carry, where they come from, and how agents talk to each other.
This module adds a lightweight, no-execution lane that inspects agent/tool code
(ADK, LangChain, CrewAI, AutoGen, MCP) and JSON manifests (A2A Agent Cards, MCP
server configs), mapping findings to the OWASP Agentic Top 10 controls the core
tests leave uncovered: ASI02 (tool misuse), ASI03 (identity/privilege), ASI04
(supply chain), ASI07 (inter-agent comms), plus LLM06 (excessive agency).

It runs only when agentic signals are present, so ordinary scripts are never
penalised or cluttered with irrelevant findings. Results are advisory and are
surfaced in the report (and folded into Standards Coverage); they do not alter
the weighted 60-test score.
"""
import json
import re
from typing import Dict, List

from app.services.analyzer.standards import resolve_standard

# Distinctive markers of an agent/tool framework. Deliberately excludes broad
# tokens like ``Tool(`` or ``Agent(`` that appear in non-agent code.
_AGENTIC_SIGNALS = [
    r"\bmcp\b", r"mcpServers", r"modelcontextprotocol",
    r"google\.adk", r"\bADK\b", r"langchain", r"langgraph",
    r"crewai", r"autogen", r"llama_?index",
    r"FunctionTool", r"StructuredTool", r"@tool\b", r"@mcp\.tool",
    r"\.bind_tools\s*\(", r"register_tool", r"tool_call",
    r"AgentCard", r"\ba2a\b", r"agent2agent",
]

_SCORE = {"fail": 20, "warning": 55, "pass": 90}


def _finding(fid: str, title: str, status: str, codes: List[str],
             message: str, evidence: str = "") -> Dict:
    return {
        "id": fid,
        "title": title,
        "status": status,
        "score": _SCORE.get(status, 55),
        "message": message,
        "evidence": evidence[:200],
        "standards": [resolve_standard(c) for c in codes],
    }


def _search(code: str, patterns: List[str]) -> str:
    for p in patterns:
        m = re.search(p, code, re.IGNORECASE | re.MULTILINE)
        if m:
            return m.group(0)
    return ""


def _has(code: str, patterns: List[str]) -> bool:
    return bool(_search(code, patterns))


def is_agentic(code: str) -> bool:
    return _has(code, _AGENTIC_SIGNALS)


def _parse_manifest(code: str):
    """Return a parsed dict if the whole file is an A2A/MCP-style JSON manifest."""
    text = code.strip()
    if not text.startswith("{"):
        return None
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    a2a_keys = {"capabilities", "skills", "defaultInputModes", "securitySchemes"}
    if "mcpServers" in data or a2a_keys & set(data.keys()):
        return data
    return None


def _analyze_source(code: str) -> List[Dict]:
    findings: List[Dict] = []

    # ASI02 / ASI05: a tool exposed to the agent wraps arbitrary code/command
    # execution. The core llm_output_execution test only catches direct exec of
    # model output; this catches a *registered tool* that shells out.
    tool_decl = _has(code, [r"@tool\b", r"@mcp\.tool", r"FunctionTool", r"StructuredTool", r"register_tool"])
    dangerous = _search(code, [
        r"os\.system\s*\(", r"subprocess\.[a-z_]+\s*\([^)]*shell\s*=\s*True",
        r"\beval\s*\(", r"\bexec\s*\(", r"pty\.spawn",
    ])
    if tool_decl and dangerous:
        findings.append(_finding(
            "tool_arbitrary_execution",
            "Agent tool can execute arbitrary commands",
            "fail", ["OWASP-ASI02", "OWASP-ASI05", "AIUC1-BND"],
            "A tool exposed to the agent shells out / evals input, so a hijacked "
            "prompt can run arbitrary code through it.", dangerous,
        ))

    # ASI03: unrestricted tool/agent scopes or permissions
    wildcard = _search(code, [
        r"scopes?\s*=\s*\[\s*[\"']\*[\"']", r"[\"']scopes?[\"']\s*:\s*\[\s*[\"']\*[\"']",
        r"allow_all\s*=\s*True", r"permissions?\s*=\s*[\"']\*[\"']",
    ])
    if wildcard:
        findings.append(_finding(
            "unrestricted_tool_scope",
            "Tool/agent granted wildcard scope",
            "warning", ["OWASP-ASI03"],
            "A tool or agent is granted '*' scope/permission; prefer least-privilege "
            "allowlists.", wildcard,
        ))

    # ASI03 / ASI08: unguarded agent-to-agent delegation / handoff
    delegation = _search(code, [
        r"allow_delegation\s*=\s*True", r"allow_transfer\s*=\s*True",
        r"transfer_to_agent", r"\bhandoff\b", r"delegate_to",
    ])
    approval = _has(code, [r"approv", r"confirm", r"human_in_the_loop", r"require_review", r"authoriz"])
    if delegation and not approval:
        findings.append(_finding(
            "unguarded_delegation",
            "Agent delegation/handoff without an approval gate",
            "warning", ["OWASP-ASI03", "OWASP-ASI08"],
            "Agents can delegate/hand off tasks with no human or policy checkpoint, "
            "enabling privilege chaining and cascading failures.", delegation,
        ))

    # ASI04 / LLM03: tools or MCP servers loaded from untrusted / unpinned sources
    supply = _search(code, [
        r"pip\s+install", r"subprocess.*pip\s+install",
        r"load_tools?\s*\([^)]*http", r"from_url\s*\(", r"requirements\s*=\s*\[",
        r"MCPServerHTTP\s*\(", r"install_tool",
    ])
    if supply:
        findings.append(_finding(
            "untrusted_tool_source",
            "Tools/servers loaded from an unpinned or remote source",
            "warning", ["OWASP-ASI04", "OWASP-LLM03"],
            "Loading tools/plugins/servers at runtime from remote or unpinned "
            "sources exposes the agent to supply-chain tampering.", supply,
        ))

    # ASI07: insecure inter-agent / tool transport
    insecure_transport = _search(code, [
        r"http://[^\s\"')]+", r"verify\s*=\s*False", r"ssl[_ ]?verify\s*=\s*False",
        r"MCPServerHTTP\s*\([^)]*http://",
    ])
    if insecure_transport:
        findings.append(_finding(
            "insecure_agent_transport",
            "Insecure transport for agent/tool communication",
            "warning", ["OWASP-ASI07"],
            "Agent or tool endpoints use http:// or disable TLS verification, "
            "exposing inter-agent traffic to interception/tampering.", insecure_transport,
        ))

    # LLM06: high-impact action tools with no human oversight
    action_tool = tool_decl and _has(code, [
        r"send_email", r"\bdelete\b", r"\bpay(ment)?\b", r"transfer_funds",
        r"execute_order", r"\bpurchase\b", r"\bwire\b", r"post_to",
    ])
    if action_tool and not approval:
        findings.append(_finding(
            "excessive_agency",
            "High-impact action tool without human oversight",
            "warning", ["OWASP-LLM06"],
            "The agent exposes irreversible action tools (send/pay/delete) without "
            "a confirmation or human-in-the-loop gate.",
        ))

    return findings


def _analyze_manifest(data: Dict) -> List[Dict]:
    findings: List[Dict] = []
    blob = json.dumps(data)

    # MCP server config
    servers = data.get("mcpServers")
    if isinstance(servers, dict):
        for name, cfg in servers.items():
            if not isinstance(cfg, dict):
                continue
            url = str(cfg.get("url", ""))
            if url.startswith("http://"):
                findings.append(_finding(
                    "mcp_insecure_transport",
                    f"MCP server '{name}' uses insecure http:// transport",
                    "fail", ["OWASP-ASI07"],
                    "MCP server endpoint is not TLS-protected.", url,
                ))
            env = cfg.get("env", {})
            if isinstance(env, dict) and _has(json.dumps(env), [
                r"[\"'][A-Za-z0-9_\-]{20,}[\"']", r"sk-[A-Za-z0-9]{16,}",
            ]):
                findings.append(_finding(
                    "mcp_hardcoded_secret",
                    f"MCP server '{name}' embeds a credential in its env",
                    "fail", ["OWASP-LLM02", "AIUC1-DATA"],
                    "Secrets should be injected at runtime, not stored in the manifest.",
                ))

    # A2A Agent Card
    if any(k in data for k in ("capabilities", "skills", "defaultInputModes")):
        url = str(data.get("url", ""))
        if url.startswith("http://"):
            findings.append(_finding(
                "agentcard_insecure_url",
                "A2A Agent Card advertises an http:// endpoint",
                "fail", ["OWASP-ASI07"],
                "Agent endpoints should be served over HTTPS.", url,
            ))
        if not data.get("securitySchemes") and not data.get("security"):
            findings.append(_finding(
                "agentcard_no_auth",
                "A2A Agent Card declares no security scheme",
                "warning", ["OWASP-ASI03", "OWASP-ASI07"],
                "Without a declared securityScheme the agent accepts unauthenticated "
                "task requests from any caller.",
            ))

    return findings


def analyze_agentic(code: str, language: str = "", filename: str = "") -> List[Dict]:
    """Return agentic-governance findings, most-severe first. Empty when the
    input shows no agent/tool framework signals."""
    if not code:
        return []

    manifest = _parse_manifest(code)
    if manifest is not None:
        findings = _analyze_manifest(manifest)
    elif is_agentic(code):
        findings = _analyze_source(code)
    else:
        return []

    order = {"fail": 0, "warning": 1, "pass": 2, "skip": 3}
    findings.sort(key=lambda f: order.get(f["status"], 9))
    return findings

"""An MCP-style ops agent that exposes risky tools.

Used to demo the agentic governance lane: a tool that shells out, a
wildcard scope, unguarded delegation, and a non-TLS tool server.
"""
import subprocess

from mcp.server import FastMCP

mcp = FastMCP("ops")


@mcp.tool()
def run_command(cmd: str) -> str:
    return subprocess.run(cmd, shell=True, capture_output=True).stdout.decode()


@mcp.tool()
def send_email(to: str, body: str) -> str:
    return _smtp_send(to, body)


AGENT = build_agent(scopes=["*"], allow_delegation=True)
REMOTE = MCPServerHTTP("http://tools.internal/mcp")

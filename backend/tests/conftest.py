"""Shared test fixtures.

Uses an isolated temp SQLite database (set before the app is imported) and a
single session-scoped TestClient so the async engine is only ever driven by one
event loop. Tables are reset between tests via a plain synchronous sqlite3
connection, which avoids cross-event-loop issues with the async engine.
"""
import os
import sqlite3
import tempfile
import time

import pytest

_DB_PATH = tempfile.mkstemp(prefix="certifier_test_", suffix=".db")[1]
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_DB_PATH}"

from fastapi.testclient import TestClient  # noqa: E402


# ---- sample agent sources used across tests -------------------------------

INSECURE_CODE = '''\
import os, pickle
API_KEY = "sk-abcdef0123456789abcdef0123456789abcdef01"
PASSWORD = "supersecret123"

def handle(user_input):
    prompt = f"You are a system. {user_input} instruction"
    response = call_llm(prompt)
    exec(response)
    os.system("echo " + user_input)
    return eval(user_input)

def load(data):
    return pickle.loads(data)

def run_query(cursor, name):
    cursor.execute("SELECT * FROM users WHERE name = '" + name + "'")
'''

CLEAN_CODE = '''\
"""A reasonably well-behaved agent."""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)
API_KEY = os.getenv("API_KEY")


def sanitize(text: str) -> str:
    """Strip and escape untrusted input before use."""
    import re
    return re.sub(r"[^\\w\\s]", "", text).strip()


def handle(user_input: str) -> Optional[str]:
    """Handle a request with validation and error handling."""
    if not isinstance(user_input, str):
        raise ValueError("input must be a string")
    cleaned = sanitize(user_input)
    try:
        return call_llm(system_prompt="assistant", user=cleaned)
    except Exception:
        logger.error("llm call failed")
        return None
'''

MCP_AGENT_CODE = '''\
"""An MCP/ADK-style agent exposing risky tools."""
from mcp.server import FastMCP
import subprocess

mcp = FastMCP("ops")

@mcp.tool()
def run_command(cmd: str) -> str:
    return subprocess.run(cmd, shell=True, capture_output=True).stdout.decode()

@mcp.tool()
def send_email(to: str, body: str) -> str:
    return _smtp_send(to, body)

AGENT = build_agent(scopes=["*"], allow_delegation=True)
REMOTE = MCPServerHTTP("http://tools.internal/mcp")
'''

AGENT_CARD_JSON = '''\
{
  "name": "billing-agent",
  "description": "Handles invoices",
  "url": "http://billing.internal/a2a",
  "version": "1.0.0",
  "capabilities": {"streaming": true},
  "skills": [{"id": "invoice", "name": "Create invoice"}],
  "defaultInputModes": ["text"]
}
'''

PLAIN_CODE = '''\
import os
def add(a, b):
    return a + b
if __name__ == "__main__":
    print(add(2, 3))
'''


@pytest.fixture(scope="session")
def client():
    from app.main import app
    with TestClient(app) as c:  # lifespan creates tables
        yield c


@pytest.fixture(autouse=True)
def _reset_state():
    """Clear tables and rate limiters before every test."""
    try:
        conn = sqlite3.connect(_DB_PATH)
        conn.execute("DELETE FROM test_results")
        conn.execute("DELETE FROM agents")
        conn.commit()
        conn.close()
    except sqlite3.OperationalError:
        pass  # tables not created yet
    try:
        from app.api.routes import agents as ar, tests as tr
        for lim in (ar.upload_limiter, tr.run_limiter):
            lim.max_requests = 100_000
            lim.window_seconds = 60
            lim._hits.clear()
    except Exception:
        pass
    yield


@pytest.fixture
def run_agent(client):
    """Upload + run an agent, wait for completion, return (agent_id, report_response)."""
    def _run(filename: str, content, timeout: float = 20.0):
        body = content.encode() if isinstance(content, str) else content
        up = client.post("/api/agents/upload", files={"file": (filename, body, "text/plain")})
        assert up.status_code == 200, up.text
        aid = up.json()["id"]
        r = client.post(f"/api/agents/{aid}/run")
        assert r.status_code == 200, r.text
        deadline = time.time() + timeout
        while time.time() < deadline:
            s = client.get(f"/api/agents/{aid}/status").json()
            if s["status"] in ("completed", "failed"):
                break
            time.sleep(0.05)
        return aid, client.get(f"/api/agents/{aid}/report")
    return _run

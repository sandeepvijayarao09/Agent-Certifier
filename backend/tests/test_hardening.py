"""Upload validation, size limits, and rate limiting."""
import pytest

from app.core.config import settings


def _upload(client, name, content):
    return client.post("/api/agents/upload",
                       files={"file": (name, content, "text/plain")})


def test_path_traversal_filename_sanitized(client):
    r = _upload(client, "../../../etc/passwd.py", b"print('hi')\n")
    assert r.status_code == 200
    assert r.json()["filename"] == "passwd.py"


def test_binary_rejected(client):
    r = _upload(client, "evil.py", b"print('x')\x00\x01\x02")
    assert r.status_code == 400 and "binary" in r.json()["detail"].lower()


def test_empty_rejected(client):
    r = _upload(client, "empty.py", b"   \n  ")
    assert r.status_code == 400 and "empty" in r.json()["detail"].lower()


def test_unsupported_extension_rejected(client):
    r = _upload(client, "notes.txt", b"hello world")
    assert r.status_code == 400 and "Unsupported" in r.json()["detail"]


def test_oversize_rejected(client):
    original = settings.max_upload_size
    settings.max_upload_size = 1024
    try:
        r = _upload(client, "big.py", b"x = 1\n" * 4000)  # ~24KB > 1KB
        assert r.status_code == 413
    finally:
        settings.max_upload_size = original


def test_rate_limit_returns_429(client):
    from app.api.routes import agents as ar
    ar.upload_limiter.max_requests = 3
    ar.upload_limiter._hits.clear()
    statuses = [_upload(client, f"a{i}.py", b"print(1)\n").status_code for i in range(6)]
    assert 429 in statuses, statuses
    assert statuses.count(200) == 3  # exactly the budget succeeded

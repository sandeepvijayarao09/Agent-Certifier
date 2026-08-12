from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    app_name: str = "Agent Certifier"
    app_version: str = "1.0.0"
    debug: bool = False
    database_url: str = "sqlite+aiosqlite:///./data/agent_certifier.db"
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: List[str] = [
        ".py", ".js", ".ts", ".go", ".java", ".rb", ".rs",
        ".cpp", ".cc", ".cs", ".php"
    ]
    certification_expiry_days: int = 365
    # Hardening knobs
    upload_rate_limit: int = 20          # uploads per client per window
    run_rate_limit: int = 30             # test runs per client per window
    rate_limit_window_seconds: int = 60
    analyzer_timeout_seconds: int = 60   # per-category static analysis budget
    stale_run_timeout_seconds: int = 600  # allow re-run if a run is stuck this long

    class Config:
        env_file = ".env"


settings = Settings()

# Agent Certifier

Professional AI Agent Testing & Certification Platform. Upload your AI agent code and receive a comprehensive analysis across 60 tests in 6 categories.

## Features

- **60 Static Analysis Tests** across 6 categories
- **Weighted Scoring**: Security (30%), Stability (20%), Performance (15%), Informatics (15%), Compliance (10%), Ethics (10%)
- **Certification Levels**: PLATINUM (90+), GOLD (80+), SILVER (70+), BRONZE (60+), NOT_CERTIFIED (<60)
- **10 Languages Supported**: Python, JavaScript, TypeScript, Go, Java, Ruby, Rust, C++, C#, PHP
- **Detailed Reports**: JSON download + printable PDF view
- **Real-time Progress**: Live test progress polling

## Quick Start

### With Docker Compose

```bash
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Manual Setup

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Architecture

- **Backend**: FastAPI + SQLAlchemy (async) + SQLite
- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS
- **Analysis**: Static code analysis using regex patterns and heuristics (no code execution)

## Test Categories

| Category | Weight | Tests |
|----------|--------|-------|
| Security | 30% | Injection, Secrets, Prompt Injection, Exfiltration, Auth, Input Validation, Dependencies, Privilege Escalation, Info Disclosure, LLM Code Injection |
| Stability | 20% | Error Handling, Infinite Loops, Recursion, Resource Leaks, Timeouts, Graceful Degradation, State Management, Memory, Concurrency, Exception Specificity |
| Performance | 15% | Caching, Async I/O, Batch Processing, Connection Pooling, Lazy Loading, Algorithm Complexity, Streaming, Rate Limiting, Resource Cleanup, Token Optimization |
| Informatics | 15% | Complexity, Documentation, Modularity, Type Annotations, Response Format, Logging, Config Externalization, API Contracts, Naming, Duplication |
| Compliance | 10% | PII Handling, Data Retention, Audit Logging, GDPR, Licensing, ToS, Output Filtering, User Consent, Data Minimization, Regulatory Awareness |
| Ethics | 10% | Bias Detection, Transparency, Human Oversight, Refusal Mechanisms, Fairness, Explainability, Harm Prevention, Misinformation, Manipulation, Accountability |

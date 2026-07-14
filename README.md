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

## Standards Coverage

Every test is mapped to recognized industry frameworks, and each report includes
a **Standards Coverage** section (`standards_coverage` + `frameworks` in the
report/certificate JSON) showing which controls the agent passes or fails. A
control's status is the most severe result among the tests mapped to it. Mapped
frameworks:

| Framework | Example controls |
|-----------|------------------|
| [OWASP Top 10 for Agentic Applications (2026)](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) | ASI01 Goal Hijack, ASI03 Identity & Privilege Abuse, ASI05 Unexpected Code Execution |
| [OWASP Top 10 for LLM Applications (2025)](https://genai.owasp.org/llm-top-10/) | LLM01 Prompt Injection, LLM02 Sensitive Info Disclosure, LLM10 Unbounded Consumption |
| [MITRE CWE](https://cwe.mitre.org/) | CWE-78, CWE-89, CWE-502, CWE-798 (deep-linked per weakness) |
| [EU GDPR](https://gdpr-info.eu/) | Art. 5, 7, 30, 32 |
| [ISO/IEC 42001:2023](https://www.iso.org/standard/42001) | AI management system (governance, transparency, traceability) |
| [ISO/IEC 25010](https://iso25000.com/index.php/en/iso-25000-standards/iso-25010) | Maintainability / product quality |
| [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework) | GOVERN, MAP, MEASURE, MANAGE |
| AIUC-1 | Attack Resistance, Data Protection, Operational Boundaries, Error Prevention |

The per-test mapping lives in `backend/app/services/analyzer/standards.py`.

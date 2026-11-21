# SYNTRA Threat Intelligence Backend (FastAPI + PostgreSQL)

Production-ready, evidence-grounded backend API built with **FastAPI** (Python 3.14) and **PostgreSQL** (`syntra_db`), designed to power the SYNTRA Threat Intelligence frontend application.

---

## Architecture Overview

- **Framework**: FastAPI with Pydantic v2 validation models
- **Database**: PostgreSQL 18+ (`syntra_db`), connected via `psycopg` (binary)
- **Authentication & Security**:
  - 6-digit cryptographic OTP generation & verification with expiration (10 min) and cooldowns (60s)
  - Bcrypt password hashing
  - JWT session issuance (7-day validity) with `HTTPBearer` authorization
- **Threat Intelligence Engine**:
  - Full MITRE ATT&CK integration, CVE mappings (NVD / CISA KEV), and attack chain modeling
  - Automated safety filtering prohibiting offensive weaponization / exploit generation
  - Domain validation to preserve cybersecurity analytical scope
- **Interactive Labs**:
  - Sandboxed execution catalog (`windows`, `linux`, `android`)
  - Session launch, real-time telemetry polling, and termination
- **Investigation History & Reports**:
  - Persistent threads and turn history in PostgreSQL
  - Multi-format report export (Markdown, PDF, JSON) with instant download

---

## Directory Structure

```
backend/
├── app/
│   ├── config.py                 # Application settings and environment variables
│   ├── database.py               # Database connection manager and query helpers
│   ├── middleware.py             # Unified API error envelope & Request ID middleware
│   ├── models/
│   │   ├── __init__.py
│   │   └── api_models.py         # Full Pydantic schemas conforming to API contract
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── health.py             # GET /api/v1/health
│   │   ├── auth.py               # POST /api/v1/auth/signup, verify-otp, login, etc.
│   │   ├── query.py              # POST /api/v1/query
│   │   ├── entities.py           # GET /api/v1/entities/{entity_id}
│   │   ├── history.py            # GET/DELETE /api/v1/history
│   │   ├── labs.py               # GET/POST /api/v1/labs
│   │   └── export.py             # POST/GET /api/v1/export
│   └── services/
│       ├── __init__.py
│       ├── otp_service.py        # 6-digit OTP generation, expiration, attempt tracking
│       ├── auth_service.py       # User registration, bcrypt verification, JWT signing
│       ├── query_service.py      # Entity search, evidence aggregation, safety refusal
│       ├── history_service.py    # Thread and turn persistence
│       ├── lab_service.py        # Lab catalog, session orchestration, telemetry
│       └── export_service.py     # Report generator (Markdown/PDF/JSON)
├── main.py                       # FastAPI application entrypoint & CORS config
├── run.py                        # Standalone uvicorn launcher script
├── test_api.py                   # Automated end-to-end API test suite (21 test cases)
├── requirements.txt              # Python package dependencies
├── .env                          # Local database and JWT credentials
└── .env.example                  # Environment configuration template
```

---

## Environment Configuration (`.env`)

```env
PORT=4000
NODE_ENV=development
CLIENT_ORIGIN=http://localhost:5173

# PostgreSQL Database
DB_HOST=127.0.0.1
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_NAME=syntra_db

# Security & Tokens
JWT_SECRET=syntra_super_secure_jwt_secret_key_2026_xyz987654321
JWT_EXPIRES_IN=604800

# OTP Configuration
OTP_EXPIRES_IN_SECONDS=600
OTP_RESEND_COOLDOWN_SECONDS=60
OTP_MAX_ATTEMPTS=5
DEMO_OTP_IN_RESPONSE=true
```

---

## Quickstart

### 1. Activate Virtual Environment
```powershell
.\backend\.venv\Scripts\Activate.ps1
```

### 2. Start Backend Server
```powershell
python backend/run.py
```
Server runs on: **`http://localhost:4000`**  
Interactive Swagger docs: **`http://localhost:4000/api/docs`**

### 3. Run Backend Verification Tests
```powershell
$env:PYTHONPATH="backend"
.\backend\.venv\Scripts\python.exe backend/test_api.py
```
*(Runs all 21 test cases verifying PostgreSQL connection, OTP authentication, MITRE ATT&CK queries, safety guards, lab orchestration, and report export).*


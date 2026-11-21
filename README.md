# 🛡️ SYNTRA — Evidence-Grounded Threat Intelligence Platform

SYNTRA is an authoritative, evidence-grounded threat intelligence platform that combines **MITRE ATT&CK** mapping, automated multi-stage attack chain correlation, detection engineering analytics, sandboxed interactive cyber labs, and multi-format report generation.

Built with a modern **React + Vite** frontend, a high-performance **FastAPI (Python)** backend, and a relational **PostgreSQL** database.

---

## 🌟 Key Features

- **Authoritative MITRE ATT&CK Corpus**: Deep indexing of threat actors (e.g., APT3 Gothic Panda), techniques (T1053.005, T1566, T1059, T1071.001), and CVE advisories (CVE-2021-44228 Log4Shell).
- **Multi-Stage Attack Chain Correlation**: Visualizes adversarial tradecraft from Initial Access to Execution and Persistence with corroborated source citations.
- **Defensive Detection & Mitigations**: Real-world Sigma rules, Windows Event Log IDs (e.g., Event 4698), and enterprise hardening controls.
- **Interactive Cyber Labs**: Orchestrates sandboxed emulation environments across Windows, Linux, and Android with live telemetry and logs streaming.
- **Full OTP Authentication Engine**:
  - Secure 6-digit numeric OTP generation & verification with expiration (10 min) and cooldowns (60s).
  - Brute-force protection (max 5 attempts) and single-use invalidation (`used_at`).
  - Bcrypt password hashing and 7-day JWT session tokens.
- **Export Engine**: One-click generation and download of comprehensive investigation reports in Markdown, PDF, and JSON.
- **Safety Policy Enforcement**: Automatically detects and refuses offensive weaponization / exploit generation requests, offering safe defensive alternatives.

---

## 🏗️ Architecture

```
syntra-platform/
├── backend/                              # FastAPI (Python 3.14) Backend
│   ├── app/
│   │   ├── config.py                     # App settings & environment loading
│   │   ├── database.py                   # PostgreSQL connection & query helpers
│   │   ├── middleware.py                 # Unified error envelope & X-Request-Id tracking
│   │   ├── models/api_models.py          # Pydantic v2 schemas matching API contracts
│   │   ├── routers/                      # Modular API route controllers
│   │   │   ├── auth.py                   # Signup, OTP verification, login, guest
│   │   │   ├── entities.py               # Entity lookup, sources, provenance
│   │   │   ├── export.py                 # Report exports & downloads
│   │   │   ├── health.py                 # Database health & dependency checks
│   │   │   ├── history.py                # Thread & turn history persistence
│   │   │   ├── labs.py                   # Cyber lab catalog & session management
│   │   │   └── query.py                  # Threat intelligence query & safety engine
│   │   └── services/                     # Business logic & domain services
│   │       ├── auth_service.py           # Bcrypt & JWT token management
│   │       ├── export_service.py         # Markdown, PDF, JSON report compilation
│   │       ├── history_service.py        # History querying and thread deletion
│   │       ├── lab_service.py            # Lab session provisioning and telemetry
│   │       ├── otp_service.py            # Cryptographic OTP lifecycle
│   │       └── query_service.py          # Entity search & safety policy filters
│   ├── main.py                           # FastAPI application entrypoint & CORS
│   ├── run.py                            # Standalone Uvicorn launcher
│   ├── test_api.py                       # 21-point automated verification test suite
│   ├── requirements.txt                  # Python dependencies
│   ├── .env.example                      # Environment configuration template
│   └── README.md                         # Backend specific guide
│
├── syntra-front-for-back-main/           # React + Vite Frontend
│   ├── src/
│   │   ├── api/v1/                       # Typed HTTP API client & contracts
│   │   │   ├── authClient.ts             # Authentication client with OTP integration
│   │   │   ├── client.ts                 # Core fetch transport with error normalization
│   │   │   ├── contract.ts               # TypeScript data schemas & API models
│   │   │   └── mapping.ts                # Wire-to-UI domain adapters
│   │   ├── components/                   # React UI components (Tailwind CSS + Lucide)
│   │   │   ├── AuthModal.tsx             # Signup & 6-slot OTP verification modal
│   │   │   ├── ThreatGraph.tsx           # Attack chain visualizer
│   │   │   ├── LabTerminal.tsx           # Interactive lab emulation interface
│   │   │   └── ReportViewer.tsx          # Threat intelligence report viewer
│   │   └── __tests__/                    # Vitest unit & contract test suite
│   ├── package.json                      # Frontend scripts and dependencies
│   └── vite.config.ts                    # Vite build & proxy configuration
│
└── .gitignore                            # Root gitignore protecting credentials & build outputs
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.10+** (tested on 3.14)
- **Node.js 18+** and **npm**
- **PostgreSQL 14+** running locally or in Docker

---

### 1. Database Setup (PostgreSQL)

Create the database in PostgreSQL:
```sql
CREATE DATABASE syntra_db;
```

---

### 2. Backend Setup (FastAPI)

```powershell
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1    # On Linux/macOS: source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your PostgreSQL credentials and JWT secret

# Start FastAPI backend
python run.py
```
Backend runs on: **`http://localhost:4000`**  
Interactive Swagger API documentation: **`http://localhost:4000/api/docs`**

---

### 3. Frontend Setup (React + Vite)

In a new terminal:
```powershell
# Navigate to frontend directory
cd syntra-front-for-back-main

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
Frontend runs on: **`http://localhost:5173`**

---

## 🧪 Testing & Verification

### Run Backend Verification Suite (21 Tests)
Validates database connection, OTP lifecycle, JWT verification, query engine, safety filters, cyber labs, and export generation:
```powershell
$env:PYTHONPATH="backend"
.\backend\.venv\Scripts\python.exe backend/test_api.py
```
> **Status:** `ALL 21 FASTAPI BACKEND VERIFICATION TESTS PASSED (100%)`

### Run Frontend Vitest Suite (19 Tests)
Validates auth flows, OTP client handling, and threat report structure:
```powershell
npx --prefix ./syntra-front-for-back-main vitest run --root ./syntra-front-for-back-main
```
> **Status:** `19 passed (19)`

---

## 📡 API Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Health status and PostgreSQL connectivity |
| `POST` | `/api/v1/auth/signup` | Initiate user registration and dispatch 6-digit OTP |
| `POST` | `/api/v1/auth/verify-otp` | Verify OTP code, activate user, and issue JWT |
| `POST` | `/api/v1/auth/resend-otp` | Resend fresh OTP (enforces 60s cooldown) |
| `POST` | `/api/v1/auth/login` | Password-based authentication |
| `POST` | `/api/v1/auth/anonymous` | Create anonymous guest session |
| `GET` | `/api/v1/auth/me` | Fetch authenticated user profile |
| `POST` | `/api/v1/auth/logout` | Terminate session |
| `POST` | `/api/v1/query` | Threat intelligence inquiry & MITRE ATT&CK retrieval |
| `GET` | `/api/v1/entities/{id}` | Entity detail, source references, and provenance |
| `GET` | `/api/v1/history` | List previous investigation threads |
| `DELETE` | `/api/v1/history/{id}` | Delete investigation thread and turns |
| `GET` | `/api/v1/labs` | Browse available cyber lab environments |
| `POST` | `/api/v1/labs/{id}/launch` | Launch sandboxed emulation session |
| `GET` | `/api/v1/labs/sessions/{id}` | Poll real-time session telemetry & logs |
| `POST` | `/api/v1/labs/sessions/{id}/terminate` | Shut down lab session |
| `POST` | `/api/v1/export` | Compile investigation report (Markdown / PDF / JSON) |
| `GET` | `/api/v1/export/download/{id}` | Download compiled threat report |

---

## 📄 License

This project is licensed under the MIT License.


# NIRIKSHAN 360

> **Integrated Dashboard for Monitoring and Tracking Institution-Related Complaint Cases Across AICTE Bureaus/Cells**
>
> SIH 2026 · Problem Statement SIH26264 · Smart Automation

⚠️ **This is a prototype using synthetic demo data only.** It is not connected to any AICTE production system, real WhatsApp, public records database, or trained AI model.

---

## Overview

NIRIKSHAN 360 is a command-centre dashboard that unifies complaint intake, triage, routing, SLA tracking, analytics, and audit across all AICTE cells:

| Cell | Purpose |
|------|---------|
| **RB** (Regulation Bureau) | Approval compliance, institution setup violations |
| **PGRC** (Public Grievance Redressal Cell) | Fee refunds, certificate withholding, general grievances |
| **Anti-Ragging** | Ragging incidents per Supreme Court / AICTE regulations |
| **ICC** (Internal Complaints Committee) | POSH Act / gender-based harassment |
| **Scholarship** | Pragati, Saksham, AICTE-PSK scheme grievances |

### Key Features (Planned)
- 📝 Complaint intake with auto-generated case IDs
- ⚖️ Rule-based triage (institution, category, urgency, language, destination cell)
- 🔄 Routing with human review for low-confidence recommendations
- ⏱️ Configurable SLA countdowns and auto-escalation
- 🏛️ Institution 360 profiles with Norm-Check and right-of-reply
- 📡 Compliance Radar with size-normalized review signals
- 💓 Systemic Pulse cross-institution trend analytics
- 🔗 Case Graph (Neo4j with SQL fallback)
- 🔒 AES-GCM identity encryption with dual-approval reveal
- 📋 Complete audit trail
- 📁 CSV bulk import
- 🇮🇳 India state-level map view

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, Vite 8, TypeScript 7, Chart.js 4, PWA |
| **Backend** | Python 3.14, Django 6.1, Django REST Framework |
| **Database** | PostgreSQL (production) / SQLite (development) |
| **Cache** | Redis (optional, via `REDIS_URL`) |
| **Graph** | Neo4j AuraDB (optional, via env vars) with SQL fallback |
| **NLP** | spaCy + rule-based EN/HI/Hinglish classification |
| **Auth** | JWT (SimpleJWT) + server-enforced RBAC |
| **Encryption** | AES-GCM for sensitive identities |

---

## Local Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Git

### 1. Clone & Configure

```bash
git clone <repo-url>
cd NIRIKSHAN-360
cp .env.example .env
# Edit .env — at minimum, set DJANGO_SECRET_KEY and IDENTITY_ENCRYPTION_KEY
```

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser  # Create an admin account
python manage.py runserver        # Starts on http://localhost:8000
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev      # Starts on http://localhost:5173
```

### 4. Access the App

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/api/health/
- **Django Admin**: http://localhost:8000/admin/
- **Demo Login**: `admin / admin` (prototype only)

---

## Environment Variables

See [`.env.example`](.env.example) for the full list. Key variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `DJANGO_SECRET_KEY` | Yes | Django secret key (random 50+ chars) |
| `DJANGO_DEBUG` | No | `True` for development (default) |
| `DATABASE_URL` | No | PostgreSQL connection string. Falls back to SQLite. |
| `REDIS_URL` | No | Redis for caching/queuing |
| `NEO4J_URI` | No | Neo4j AuraDB URI for case graph |
| `NEO4J_USER` | No | Neo4j username |
| `NEO4J_PASSWORD` | No | Neo4j password |
| `IDENTITY_ENCRYPTION_KEY` | Yes | 32-byte hex key for AES-GCM encryption |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | No | JWT access token TTL (default: 60) |

---

## Running Tests

```bash
# Backend
cd backend
python manage.py test -v 2

# Frontend type checking
cd frontend
npm run typecheck
```

---

## Project Structure

```
NIRIKSHAN-360/
├── backend/           # Django + DRF API
│   ├── accounts/      # Custom User model, JWT auth, RBAC
│   ├── complaints/    # Complaint lifecycle (Phase 3)
│   ├── institutions/  # Institution 360, Norm-Check (Phase 4)
│   ├── audit/         # Audit log, identity encryption (Phase 2)
│   └── nirikshan/     # Django project settings
├── frontend/          # React + Vite + TypeScript PWA
│   └── src/
│       ├── components/layout/  # Sidebar, Header, Layout shell
│       ├── pages/     # Dashboard, Login, and module pages
│       └── index.css  # Design system
└── .env.example       # Environment variable template
```

---

## Security & Ethics

- **No false claims**: All data is synthetic and clearly labelled
- **No auto-merge**: Duplicate detection flags only; merge requires human approval
- **No auto-wrongdoing**: Compliance signals require human review
- **Insufficient evidence**: System reports "insufficient evidence" — never fabricates
- **Identity protection**: AES-GCM encryption, key in env var only
- **Dual-approval**: Two authorized users must approve identity reveal
- **Audit trail**: Every consequential action is logged

---

## License

This project is developed for SIH 2026. All dependencies are free and open-source.

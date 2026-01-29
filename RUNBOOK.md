# ZARQA AL YAMAMA - TIERED RUNBOOK

**Status:** Tier 1 Verified / Tier 2 Convenience
**Authority:** Antigravity Audit 2026-01-13

---

## TIER 1: AUDIT-CORE (VERIFIABLE CORRECTNESS)
*These steps are hermetic, standard, and sufficient to prove the system's correctness. They rely only on Docker and Pytest.*

### 1. Environment Integrity
**Command:**
```bash
cd backend
docker build -t zarqa-backend .
docker run --rm zarqa-backend python --version
```
**Success Criteria:** Output must be `Python 3.11.x`.

### 2. System Logic Verification (Fail-Closed)
**Command:**
```bash
# Core logic regression test (Toy Scenario)
# Asserts: Deterministic fusion, strict schema compliance, probability math rules
pytest -vv backend/tests/v2_integration/test_e2e_v2_pipeline.py -k toy
```
**Success Criteria:** `1 passed` (Green). No schema validation errors.

### 3. Production Health Check
**Command:**
```bash
# Start full stack (detached)
docker-compose up -d --build

# Verify API Health
curl -f http://localhost:8000/health
```
**Success Criteria:** `{"status":"healthy"}` and HTTP 200 OK.

---

## TIER 2: OPERATIONAL CONVENIENCE (NON-AUTHORITATIVE)
*These scripts are helpful shortcuts for developers but are NOT the audit source of truth.*

| Component | Command | Note |
| :--- | :--- | :--- |
| **Quick Start** | `./start_zarqa.sh` | Orchestrates backend/frontend. Relies on host Python (risk of drift). |
| **Setup Wizard** | `./setup_project.sh` | Interactive environment builder. |
| **Frontend UI** | `npm run dev` (frontend) | Viewing layer only. Decisions happen in Tier 1. |
| **Install Script** | `./install.sh` | One-click Docker setup wrappers. |

---

## MISSING EVIDENCE (DECLARED)
*The following items are referenced in documentation but absent from the repository.*

1.  **`docker-compose.prod.yml`**: Production orchestration overrides. Users should rely on `docker-compose.yml`.
2.  **`kubernetes/`**: Helm charts or K8s manifests referenced in System Overview.

# Zarqa al Yamama - Operations & Maintenance Checklist

**Version:** 1.0.0  
**Purpose:** A checklist for routine monitoring, maintenance, and troubleshooting of the Zarqa al Yamama system.

---

## 1. Daily Checks (5 Minutes)

*   [ ] **Check System Health:**
    *   Access the health check URL: `http://localhost:8000/health`
    *   **Expected:** `{"status": "healthy", ...}`

*   [ ] **Check Service Status:**
    *   Run `docker-compose ps` in the terminal.
    *   **Expected:** All services should show `Up` or `running` status.

*   [ ] **Review System Logs (Briefly):**
    *   Run `docker-compose logs --tail=50 backend`.
    *   **Expected:** Look for any obvious `ERROR` or `CRITICAL` messages.

## 2. Weekly Maintenance (15 Minutes)

*   [ ] **Review Resource Usage:**
    *   Run `docker stats --no-stream`.
    *   **Expected:** Check that CPU, Memory, and Disk I/O are within normal limits. No service should be consistently at 100% CPU or memory.

*   [ ] **Prune Docker System:**
    *   Run `docker system prune -f` to remove unused containers, networks, and dangling images.
    *   **Note:** This helps free up disk space.

*   [ ] **Check for Software Updates:**
    *   Review the documentation for the core dependencies (e.g., FastAPI, Next.js, LangGraph) for any critical security updates.

## 3. Monthly Maintenance (30 Minutes)

*   [ ] **Perform a Full Backup:**
    *   Follow the backup procedures outlined in Section 5 of this checklist.

*   [ ] **Review API Key Validity:**
    *   Check the dashboards of your API providers (e.g., OpenRouter, NewsAPI) to ensure keys are active and within usage limits.

*   [ ] **Rebuild Docker Images:**
    *   Run `docker-compose build --no-cache` to incorporate the latest base image security patches.
    *   Then, restart the services: `docker-compose up -d`

*   [ ] **Review Long-Term Logs:**
    *   Review the logs for the past month for any recurring warnings or errors that might indicate an underlying issue.

---

## 4. Troubleshooting Quick-Reference

| Symptom | First Step | Second Step | Third Step |
| :--- | :--- | :--- | :--- |
| **Dashboard Unresponsive** | Run `docker-compose ps` | Check logs: `docker-compose logs -f frontend` | Restart frontend: `docker-compose restart frontend` |
| **Forecasts Failing** | Run `docker-compose ps` | Check logs: `docker-compose logs -f backend` | Verify API keys in `.env` file |
| **Services Won\'t Start** | Check logs for the failing service (e.g., `docker-compose logs postgres`) | Run `docker-compose down` and then `docker-compose up -d` | Check for port conflicts using `lsof -i :<port>` or `netstat` |
| **High CPU/Memory Usage** | Run `docker stats` to identify the service | Check the logs for that service for errors | Restart the specific service: `docker-compose restart <service_name>` |

---

## 5. Backup and Recovery

### Backup Procedure

1.  **Stop the Services:**
    *   `docker-compose down`

2.  **Backup the Database Volumes:**
    *   Docker volumes are typically stored in `/var/lib/docker/volumes/`. You need to back up the volumes associated with this project (e.g., `zarqa-al-yamama_postgres_data`, `zarqa-al-yamama_qdrant_data`, etc.).
    *   `sudo tar -czvf zarqa_backup_$(date +%F).tar.gz /var/lib/docker/volumes/zarqa-al-yamama_*`

3.  **Backup the Configuration:**
    *   Make a copy of the `backend/.env` file.

4.  **Restart the Services:**
    *   `docker-compose up -d`

### Recovery Procedure

1.  **Stop the Services:**
    *   `docker-compose down`

2.  **Restore the Database Volumes:**
    *   `sudo tar -xzvf zarqa_backup_<date>.tar.gz -C /`

3.  **Restore the Configuration:**
    *   Copy your backed-up `.env` file into the `backend/` directory.

4.  **Start the Services:**
    *   `docker-compose up -d`

---

## 6. Security Checks

*   [ ] **Rotate API Keys (Quarterly):**
    *   Generate new API keys from your provider dashboards and update the `backend/.env` file.

*   [ ] **Restrict Network Access:**
    *   In a production environment, ensure that only the necessary ports (e.g., 80/443 for the frontend) are exposed to the public internet. Database ports should never be public.

*   [ ] **Review User Access:**
    *   Ensure that only authorized personnel have access to the server running the Docker containers.

*   [ ] **Check for Vulnerabilities:**
    *   Use tools like `trivy` or Docker Hub\'s security scanning to check your images for known vulnerabilities.
    *   `trivy image <image_name>:<tag>`

---

This checklist provides a baseline for maintaining the health and security of your Zarqa al Yamama instance. Adapt it as needed to fit your organization\'s specific operational policies.


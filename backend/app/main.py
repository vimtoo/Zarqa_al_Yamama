import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.workflow import ZarqaWorkflow
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION
)

# CORS
origins = settings.CORS_ORIGINS.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.core.http_client import GlobalHTTPClient
from app.db.neo4j import get_neo4j_graph

@app.on_event("startup")
async def startup_event():
    await GlobalHTTPClient.start()
    await get_neo4j_graph().verify_connection()
    
    # ================================================================
    # RUNTIME GUARD — Verify v2 workflow is active (runs once per process)
    # ================================================================
    nodes = getattr(getattr(workflow, "graph", None), "nodes", None)
    node_keys = list(nodes.keys()) if isinstance(nodes, dict) else []
    
    has_v2 = "quantifier_v2" in node_keys
    legacy_present = "quantifier" in node_keys or "critic" in node_keys
    
    logger.info(
        "[ZARQA STARTUP] workflow=%s.%s | nodes=%s | quantifier_v2=%s | legacy_present=%s",
        workflow.__class__.__module__, 
        workflow.__class__.__name__, 
        node_keys, 
        has_v2,
        legacy_present
    )
    
    if legacy_present and has_v2:
        logger.warning("mixed graph present; legacy must be unreachable in v2 mode")

@app.on_event("shutdown")
async def shutdown_event():
    await GlobalHTTPClient.stop()
    await get_neo4j_graph().close()

workflow = ZarqaWorkflow()

class ForecastRequest(BaseModel):
    scenario: str
    user_id: str = "user"

def _reports_dir() -> Path:
    base_dir = Path(settings.REPORTS_DIR)
    if not base_dir.is_absolute():
        base_dir = Path(__file__).resolve().parents[1] / base_dir
    return base_dir

def _media_type_for_report(path: Path) -> str:
    if path.suffix.lower() == ".md":
        return "text/markdown"
    if path.suffix.lower() == ".pdf":
        return "application/pdf"
    return "text/plain"

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/v1/forecast")
async def create_forecast(request: ForecastRequest):
    return await workflow.execute(request.scenario, request.user_id)

@app.get("/api/v1/reports/{filename}")
async def download_report(filename: str):
    reports_dir = _reports_dir()
    candidate = (reports_dir / filename).resolve()

    if reports_dir not in candidate.parents:
        raise HTTPException(status_code=400, detail="Invalid report path")
    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(candidate, filename=filename, media_type=_media_type_for_report(candidate))

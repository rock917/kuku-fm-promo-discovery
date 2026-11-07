# =============================================================================
# api.py — FastAPI Backend for Azure App Service Deployment
#
# REST API endpoints for:
#   - Promo candidates & ranked recommendations
#   - Quality reports & validation failure statistics
#   - Failure analysis & documented system limitations
#   - Screenplay source viewer (scene-relative traceability)
#   - Pipeline execution trigger
#
# Fully compatible with Azure App Service / Container Apps and Vercel frontend.
# =============================================================================

from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kuku-promo-api")

# Paths
ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "outputs"
SCRIPTS = ROOT / "data" / "scripts" / "I Married a Broken Soldier. He was a Duke"
PROMOS_JSON = OUTPUTS / "promos.json"
QUALITY_JSON = OUTPUTS / "quality_report.json"
FAILURE_JSON = OUTPUTS / "failure_analysis.json"

app = FastAPI(
    title="Kuku FM Promo Discovery API",
    description="Backend API for microdrama screenplay analysis and promo discovery.",
    version="1.0.0",
)

# CORS configuration — allows Vercel frontend and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Can be restricted to specific Vercel domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Pydantic Request/Response Models
# ---------------------------------------------------------------------------

class PipelineRunRequest(BaseModel):
    provider: str = Field(default="mock", description="LLM provider: mock, gemini, openai")
    model: Optional[str] = Field(default="gemini-1.5-flash", description="Model name")
    top_n: int = Field(default=20, ge=1, le=100, description="Top N promos to rank")
    episodes: Optional[List[int]] = Field(default=None, description="Specific episode numbers to process")


class PipelineRunResponse(BaseModel):
    status: str
    message: str
    command: List[str]


# ---------------------------------------------------------------------------
# Helper File Loaders
# ---------------------------------------------------------------------------

def _load_json_file(file_path: Path) -> dict:
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Resource not found: {file_path.name}. Please run the pipeline first.",
        )
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading {file_path.name}: {str(e)}",
        )


def _get_episode_script(episode_number: int) -> str:
    if not SCRIPTS.exists():
        raise HTTPException(status_code=404, detail="Screenplay scripts directory not found.")
    for file in SCRIPTS.glob("*.txt"):
        stem = file.stem.lower()
        if f"episode {episode_number} " in stem + " " or f"episode {episode_number:02d} " in stem + " ":
            return file.read_text(encoding="utf-8", errors="replace")
    raise HTTPException(status_code=404, detail=f"Screenplay for Episode {episode_number} not found.")


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
def health_check():
    """Health check endpoint for Azure App Service probes and Vercel frontend connectivity."""
    return {
        "status": "healthy",
        "service": "kuku-promo-discovery-api",
        "has_outputs": PROMOS_JSON.exists(),
        "has_scripts": SCRIPTS.exists(),
    }


@app.get("/api/metadata", tags=["Metadata"])
def get_metadata():
    """Return pipeline run metadata (show title, scoring weights, provider info)."""
    data = _load_json_file(PROMOS_JSON)
    return data.get("metadata", {})


@app.get("/api/promos", tags=["Promos"])
def get_promos(
    episode: Optional[int] = Query(None, description="Filter by episode number"),
    min_score: Optional[float] = Query(0.0, description="Filter by minimum final score"),
    min_duration: Optional[float] = Query(20.0, description="Minimum duration in seconds"),
    max_duration: Optional[float] = Query(60.0, description="Maximum duration in seconds"),
    limit: Optional[int] = Query(50, ge=1, le=100, description="Limit number of returned promos"),
):
    """
    Retrieve ranked promo recommendations with flexible filtering.
    All scores clearly distinguish AI-generated estimates from programmatic rules.
    """
    data = _load_json_file(PROMOS_JSON)
    promos = data.get("ranked_promos", [])

    filtered = []
    for p in promos:
        score = p.get("final_score") or 0.0
        dur = p.get("total_duration_sec") or 0.0
        episodes = p.get("episodes") or []

        if episode is not None and episode not in episodes:
            continue
        if score < min_score:
            continue
        if dur < min_duration or dur > max_duration:
            continue
        filtered.append(p)

    return {
        "total_ranked": len(promos),
        "total_matching": len(filtered),
        "results": filtered[:limit],
    }


@app.get("/api/promos/{candidate_id}", tags=["Promos"])
def get_promo_detail(candidate_id: str):
    """Retrieve full details of a specific promo candidate by ID."""
    data = _load_json_file(PROMOS_JSON)
    promos = data.get("ranked_promos", [])
    for p in promos:
        if p.get("candidate_id") == candidate_id:
            return p
    raise HTTPException(status_code=404, detail=f"Promo candidate '{candidate_id}' not found.")


@app.get("/api/quality-report", tags=["Quality"])
def get_quality_report():
    """Retrieve the comprehensive quality audit report."""
    return _load_json_file(QUALITY_JSON)


@app.get("/api/failure-analysis", tags=["Quality"])
def get_failure_analysis():
    """Retrieve failure analysis documentation, including system limitations and invalid candidate audits."""
    return _load_json_file(FAILURE_JSON)


@app.get("/api/episodes", tags=["Screenplay"])
def list_episodes():
    """List all available episodes (1 to 50) and their script availability."""
    if not SCRIPTS.exists():
        return {"episodes": list(range(1, 51)), "scripts_available": False}

    available = []
    for ep in range(1, 51):
        found = any(
            f"episode {ep} " in f.stem.lower() + " " or f"episode {ep:02d} " in f.stem.lower() + " "
            for f in SCRIPTS.glob("*.txt")
        )
        available.append({"episode_number": ep, "available": found})

    return {"total": len(available), "episodes": available}


@app.get("/api/episodes/{episode_number}", tags=["Screenplay"])
def get_episode_content(episode_number: int):
    """
    Retrieve raw screenplay content for an episode to allow full source traceability.
    Timestamps are scene-relative (reset to 00:00.00 per scene).
    """
    content = _get_episode_script(episode_number)
    return {
        "episode_number": episode_number,
        "screenplay_text": content,
        "timestamp_note": "Timestamps are scene-relative (reset to 00:00.00 per scene).",
    }


@app.post("/api/pipeline/run", tags=["Pipeline"])
def trigger_pipeline(request: PipelineRunRequest, background_tasks: BackgroundTasks):
    """
    Trigger a fresh analysis run.
    Can be run with provider=mock (no API key required) or gemini/openai.
    """
    cmd = [
        sys.executable,
        str(ROOT / "src" / "pipeline.py"),
        "--provider",
        request.provider,
        "--model",
        request.model or "gemini-1.5-flash",
        "--top-n",
        str(request.top_n),
    ]
    if request.episodes:
        cmd += ["--episodes"] + [str(e) for e in request.episodes]

    def _execute():
        logger.info(f"Executing pipeline: {' '.join(cmd)}")
        try:
            res = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=True)
            logger.info(f"Pipeline executed successfully: {res.stdout[-200:]}")
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")

    background_tasks.add_task(_execute)

    return {
        "status": "queued",
        "message": f"Pipeline analysis queued using provider '{request.provider}'.",
        "command": cmd,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)


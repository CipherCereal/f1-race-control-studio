import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from src.storage.schema import Incident, ConsistencyReport, MatchResult
from src.storage.vector_store import VectorStore
from src.engine.matcher import IncidentMatcher

app = FastAPI(
    title="PRECEDENT — F1 Stewarding Precedent & Consistency Engine",
    description="Telemetry-grounded retrieval and consistency analysis for Formula 1 stewarding decisions",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = VectorStore()
matcher = IncidentMatcher(store)


class MatchRequest(BaseModel):
    incident_id: Optional[str] = None
    k: int = 5
    # Optional arbitrary telemetry input payload
    corner_type: Optional[str] = None
    closing_speed_delta: Optional[float] = None
    overlap_pct_at_apex: Optional[float] = None
    had_inside_line: Optional[int] = None
    contact_occurred: Optional[int] = None
    tyre_age_delta: Optional[int] = None
    race_progression: Optional[float] = None
    ruling: Optional[str] = None


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "precedent-engine", "version": "1.0.0"}


@app.get("/api/incidents", response_model=List[Incident])
def list_incidents():
    """Returns all curated incidents in the database."""
    return store.list_incidents()


@app.get("/api/incidents/{incident_id}", response_model=Incident)
def get_incident(incident_id: str):
    """Returns full metadata and feature vector for a specific incident."""
    inc = store.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")
    return inc


@app.post("/api/incidents/match", response_model=ConsistencyReport)
def match_incident(req: MatchRequest):
    """
    Retrieves top-k historical precedents and computes consistency verdict
    (Clean match, Split verdict, or Novel incident).
    """
    if req.incident_id:
        try:
            return matcher.match_by_id(req.incident_id, k=req.k)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    else:
        # Match using arbitrary feature parameters
        data = req.model_dump(exclude_unset=True)
        return matcher.match_arbitrary_incident(data, k=req.k)


@app.get("/api/incidents/{incident_id}/telemetry")
def get_incident_telemetry(incident_id: str):
    """
    Generates 5-second synchronized high-fidelity telemetry traces (-3.0s to +2.0s around apex)
    for interactive frontend charting.
    """
    inc = store.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")

    # Synthesize physics-accurate telemetry curve centered at apex (t = 0.0s)
    # based on the incident'\''s closing_speed_delta, overlap, and corner characteristics
    import numpy as np
    t = np.linspace(-3.0, 2.0, 51)  # 10Hz sampling
    v_base = 310.0 if inc.corner_type in ["chicane", "hairpin"] else 240.0
    v_apex = 95.0 if inc.corner_type == "hairpin" else (135.0 if inc.corner_type == "chicane" else 190.0)

    # Braking profile
    brake_curve = 1.0 / (1.0 + np.exp(2.5 * (t + 1.2)))  # drops as cars brake into apex
    t_pre = np.clip(-t / 3.0, 0.0, 1.0)
    t_post = np.clip(t / 2.0, 0.0, 1.0)
    speed_def = v_apex + (v_base - v_apex) * (t_pre ** 1.8) * (t < 0) + (100.0 * (t_post ** 1.2)) * (t >= 0)
    speed_def = np.clip(speed_def, v_apex, v_base)

    # Attacker carries closing_speed_delta deeper into braking zone
    speed_atk = speed_def.copy()
    speed_atk[t < 0] += inc.closing_speed_delta * (1.0 - np.abs(t[t < 0]) / 3.0)

    # Lateral gap decreases until apex / contact
    min_gap = 0.8 if inc.contact_occurred else 2.4
    initial_gap = 5.5
    gap_curve = min_gap + (initial_gap - min_gap) * (np.abs(t) / 3.0) ** 1.5

    data_points = []
    for i in range(len(t)):
        data_points.append({
            "time": round(float(t[i]), 2),
            "speed_attacker": round(float(speed_atk[i]), 1),
            "speed_defender": round(float(speed_def[i]), 1),
            "throttle_attacker": int(np.clip(100 if t[i] > 0.3 else (0 if t[i] < -0.2 else 40), 0, 100)),
            "throttle_defender": int(np.clip(100 if t[i] > 0.1 else (0 if t[i] < -0.5 else 60), 0, 100)),
            "brake_attacker": int(np.clip(100 if -2.2 < t[i] < -0.2 else 0, 0, 100)),
            "brake_defender": int(np.clip(90 if -2.5 < t[i] < -0.4 else 0, 0, 100)),
            "lateral_gap_meters": round(float(gap_curve[i]), 2),
            "overlap_pct": round(float(np.clip(inc.overlap_pct_at_apex * (1.0 - abs(t[i]) / 2.5), 0.0, 1.0)), 2)
        })

    return {
        "incident_id": inc.id,
        "incident_name": inc.name,
        "apex_time": 0.0,
        "sampling_hz": 10,
        "traces": data_points
    }


# Mount static directory if it exists
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../static"))
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    def index():
        return FileResponse(os.path.join(static_dir, "index.html"))

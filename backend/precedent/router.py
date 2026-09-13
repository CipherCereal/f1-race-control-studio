import os
from typing import List, Optional, Dict, Any
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.precedent.storage.schema import Incident, ConsistencyReport
from backend.precedent.storage.vector_store import VectorStore
from backend.precedent.engine.matcher import IncidentMatcher

router = APIRouter(prefix="/api", tags=["precedent"])

store = VectorStore()
matcher = IncidentMatcher(store)


class MatchRequest(BaseModel):
    incident_id: Optional[str] = None
    k: int = 5
    corner_type: Optional[str] = None
    closing_speed_delta: Optional[float] = None
    overlap_pct_at_apex: Optional[float] = None
    had_inside_line: Optional[int] = None
    contact_occurred: Optional[int] = None
    tyre_age_delta: Optional[int] = None
    race_progression: Optional[float] = None
    ruling: Optional[str] = None


@router.get("/incidents", response_model=List[Incident])
def list_incidents():
    """Returns all curated incidents in the database."""
    return store.list_incidents()


@router.get("/incidents/{incident_id}", response_model=Incident)
def get_incident(incident_id: str):
    """Returns full metadata and feature vector for a specific incident."""
    inc = store.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")
    return inc


@router.post("/incidents/match", response_model=ConsistencyReport)
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
        data = req.model_dump(exclude_unset=True)
        return matcher.match_arbitrary_incident(data, k=req.k)


@router.get("/incidents/{incident_id}/telemetry")
def get_incident_telemetry(incident_id: str):
    """
    Generates 5-second synchronized high-fidelity telemetry traces (-3.0s to +2.0s around apex)
    for interactive frontend charting.
    """
    inc = store.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")

    t = np.linspace(-3.0, 2.0, 51)
    v_base = 310.0 if inc.corner_type in ["chicane", "hairpin"] else 240.0
    v_apex = 95.0 if inc.corner_type == "hairpin" else (135.0 if inc.corner_type == "chicane" else 190.0)

    speed_def = v_base - (v_base - v_apex) * np.exp(-0.5 * (t / 0.9) ** 2)
    speed_att = speed_def + (inc.closing_speed_delta * np.exp(-1.2 * (t + 0.8) ** 2))

    gap_base = 0.4 if inc.contact_occurred else 1.2
    gap_curve = gap_base + 3.0 * (np.abs(t) / 2.0) ** 1.5

    data_points = []
    for i in range(len(t)):
        data_points.append({
            "time_offset_sec": round(float(t[i]), 2),
            "speed_attacker": round(float(speed_att[i]), 1),
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

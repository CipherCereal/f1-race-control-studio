from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Incident(BaseModel):
    id: str
    name: str
    year: int
    round_name: str
    session: str
    lap: int
    corner: int
    corner_type: str
    driver_attacking: str
    driver_defending: str
    ruling: str  # 'penalized' | 'no_action' | 'reprimand'
    ruling_category: str
    penalty_seconds: int = 0
    fia_doc_title: str
    fia_doc_url: str
    steward_rationale: str

    # Raw telemetry-derived features
    closing_speed_delta: float  # km/h
    overlap_pct_at_apex: float  # 0.0 - 1.0 (overlap of front axle to rear/cockpit)
    had_inside_line: int  # 1 or 0
    had_apex_possession: int  # 1 or 0
    contact_occurred: int  # 1 or 0
    tyre_age_delta: int  # attacker tyre age - defender tyre age in laps
    race_progression: float  # lap / total laps (0.0 - 1.0)

    # Standardized 8D feature vector
    feature_vector: Optional[List[float]] = None


class MatchResult(BaseModel):
    precedent: Incident
    distance: float
    similarity_score: float
    is_same_ruling: bool


class DifferentiatingFactor(BaseModel):
    feature_name: str
    display_name: str
    target_value: Any
    precedent_value: Any
    delta: float
    explanation: str


class ConsistencyReport(BaseModel):
    target_incident: Incident
    matches: List[MatchResult]
    verdict_status: str  # "consistent" | "split" | "novel"
    majority_ruling: str
    is_consistent: bool
    novelty_score: float
    differentiating_factors: List[DifferentiatingFactor] = []
    summary_verdict: str
    fia_rules_reference: str

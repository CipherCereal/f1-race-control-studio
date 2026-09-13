import numpy as np
from typing import Dict, Any, List, Tuple

# Standard 7-dimensional feature schema as formulated in planv1
FEATURE_NAMES = [
    "corner_type_encoded",
    "closing_speed_norm",
    "overlap_pct",
    "had_inside_line",
    "contact_occurred",
    "tyre_age_norm",
    "race_progression"
]

FEATURE_LABELS = {
    "corner_type_encoded": "Corner Geometry Type",
    "closing_speed_norm": "Closing Speed Delta",
    "overlap_pct": "Overlap % at Apex",
    "had_inside_line": "Inside Line Trajectory",
    "contact_occurred": "Physical Contact Occurred",
    "tyre_age_norm": "Tyre Age Differential",
    "race_progression": "Race Progression Phase"
}

CORNER_TYPE_MAP = {
    "hairpin": 0.2,
    "chicane": 0.3,
    "high_speed": 0.7,
    "straight": 0.9
}


def encode_corner_type(corner_type: str) -> float:
    return CORNER_TYPE_MAP.get(str(corner_type).lower(), 0.5)


def build_incident_vector(data: Dict[str, Any]) -> List[float]:
    """
    Constructs a 7-dimensional normalized feature vector for an incident.
    All dimensions are strictly scaled to [0.0, 1.0].
    """
    # 1. Corner geometry type
    corner_type_enc = encode_corner_type(str(data.get("corner_type", "chicane")))

    # 2. Closing speed delta (normalized 0 to 50 km/h)
    closing_speed = float(data.get("closing_speed_delta", 0.0))
    closing_speed_norm = float(np.clip(closing_speed / 50.0, 0.0, 1.0))

    # 3. Overlap percentage at apex (0.0 to 1.0)
    overlap_pct = float(np.clip(float(data.get("overlap_pct_at_apex", 0.0)), 0.0, 1.0))

    # 4. Racing line position (1.0 = inside, 0.0 = outside)
    had_inside = 1.0 if int(data.get("had_inside_line", 0)) == 1 else 0.0

    # 5. Physical contact occurred (1.0 = yes, 0.0 = no)
    contact = 1.0 if int(data.get("contact_occurred", 0)) == 1 else 0.0

    # 6. Tyre age delta (normalized from [-15, 15] laps)
    tyre_age = float(data.get("tyre_age_delta", 0))
    tyre_age_norm = float(np.clip((tyre_age + 15.0) / 30.0, 0.0, 1.0))

    # 7. Race progression (lap / total laps)
    race_prog = float(np.clip(float(data.get("race_progression", 0.5)), 0.0, 1.0))

    vector = [
        round(corner_type_enc, 4),
        round(closing_speed_norm, 4),
        round(overlap_pct, 4),
        round(had_inside, 4),
        round(contact, 4),
        round(tyre_age_norm, 4),
        round(race_prog, 4)
    ]
    return vector


def compute_l2_distance(vec1: List[float], vec2: List[float]) -> float:
    """Computes exact Euclidean distance (<-> in pgvector)."""
    a = np.array(vec1, dtype=np.float32)
    b = np.array(vec2, dtype=np.float32)
    return float(np.linalg.norm(a - b))


def compute_similarity_percentage(distance: float) -> float:
    """Converts L2 distance into a 0-100% similarity score."""
    # Distance in 7D unit hypercube has max possible distance sqrt(7) ~= 2.645
    # For F1 incidents, distances under 0.35 represent extremely tight precedents (>85% match)
    sim = max(0.0, 1.0 - (distance / 2.0)) * 100.0
    return round(sim, 1)


def find_top_differentiating_features(vec_target: List[float], vec_precedent: List[float]) -> List[Tuple[str, float]]:
    """Identifies which features account for the greatest divergence between two vectors."""
    diffs = []
    for i, name in enumerate(FEATURE_NAMES):
        delta = abs(vec_target[i] - vec_precedent[i])
        diffs.append((name, round(delta, 4)))
    diffs.sort(key=lambda x: x[1], reverse=True)
    return diffs

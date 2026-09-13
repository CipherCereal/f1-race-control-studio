from typing import List, Optional, Dict, Any, Union
from backend.precedent.storage.schema import Incident, MatchResult, ConsistencyReport
from backend.precedent.storage.vector_store import VectorStore
from backend.precedent.features.vectorizer import build_incident_vector, compute_similarity_percentage
from backend.precedent.engine.consistency import analyze_consistency


class IncidentMatcher:
    def __init__(self, vector_store: Optional[VectorStore] = None):
        self.store = vector_store or VectorStore()

    def match_by_id(self, incident_id: str, k: int = 5) -> ConsistencyReport:
        """
        Looks up an existing incident, retrieves its top-k nearest precedents,
        and generates a consistency report.
        """
        target = self.store.get_incident(incident_id)
        if not target:
            raise ValueError(f"Incident with ID '{incident_id}' not found in database.")

        knn_results = self.store.query_knn(
            query_vector=target.feature_vector,
            k=k,
            exclude_id=incident_id
        )

        matches = []
        for prec, dist in knn_results:
            matches.append(MatchResult(
                precedent=prec,
                distance=round(dist, 4),
                similarity_score=compute_similarity_percentage(dist),
                is_same_ruling=(prec.ruling == target.ruling)
            ))

        return analyze_consistency(target, matches)

    def match_arbitrary_incident(self, incident_data: Dict[str, Any], k: int = 5) -> ConsistencyReport:
        """
        Takes raw incident data or a newly submitted query incident, builds its vector,
        retrieves precedents, and analyzes consistency.
        """
        vec = build_incident_vector(incident_data)

        # Create temporary Incident object
        target = Incident(
            id=str(incident_data.get("id", "custom_query")),
            name=str(incident_data.get("name", "Custom / Live Query Incident")),
            year=int(incident_data.get("year", 2026)),
            round_name=str(incident_data.get("round_name", "Live Grand Prix")),
            session=str(incident_data.get("session", "Race")),
            lap=int(incident_data.get("lap", 1)),
            corner=int(incident_data.get("corner", 1)),
            corner_type=str(incident_data.get("corner_type", "hairpin")),
            driver_attacking=str(incident_data.get("driver_attacking", "CAR_A")),
            driver_defending=str(incident_data.get("driver_defending", "CAR_B")),
            ruling=str(incident_data.get("ruling", "under_investigation")),
            ruling_category=str(incident_data.get("ruling_category", "investigation")),
            penalty_seconds=int(incident_data.get("penalty_seconds", 0)),
            fia_doc_title=str(incident_data.get("fia_doc_title", "Live Telemetry Telemetry Query")),
            fia_doc_url=str(incident_data.get("fia_doc_url", "https://www.fia.com/documents")),
            steward_rationale=str(incident_data.get("steward_rationale", "Under active stewards inquiry.")),
            closing_speed_delta=float(incident_data.get("closing_speed_delta", 25.0)),
            overlap_pct_at_apex=float(incident_data.get("overlap_pct_at_apex", 0.5)),
            had_inside_line=int(incident_data.get("had_inside_line", 1)),
            had_apex_possession=int(incident_data.get("had_apex_possession", 0)),
            contact_occurred=int(incident_data.get("contact_occurred", 1)),
            tyre_age_delta=int(incident_data.get("tyre_age_delta", 0)),
            race_progression=float(incident_data.get("race_progression", 0.5)),
            feature_vector=vec
        )

        knn_results = self.store.query_knn(
            query_vector=vec,
            k=k,
            exclude_id=target.id
        )

        matches = []
        for prec, dist in knn_results:
            matches.append(MatchResult(
                precedent=prec,
                distance=round(dist, 4),
                similarity_score=compute_similarity_percentage(dist),
                is_same_ruling=(prec.ruling == target.ruling)
            ))

        return analyze_consistency(target, matches)

import sqlite3
import json
import os
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from backend.precedent.storage.schema import Incident
from backend.precedent.features.vectorizer import build_incident_vector, compute_l2_distance, compute_similarity_percentage

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/precedent/precedent.db"))
if not os.path.exists(DB_PATH):
    # fallback check
    fallback = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/precedent.db"))
    if os.path.exists(fallback):
        DB_PATH = fallback


class VectorStore:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    round_name TEXT NOT NULL,
                    session TEXT NOT NULL,
                    lap INTEGER NOT NULL,
                    corner INTEGER NOT NULL,
                    corner_type TEXT NOT NULL,
                    driver_attacking TEXT NOT NULL,
                    driver_defending TEXT NOT NULL,
                    ruling TEXT NOT NULL,
                    ruling_category TEXT NOT NULL,
                    penalty_seconds INTEGER DEFAULT 0,
                    fia_doc_title TEXT NOT NULL,
                    fia_doc_url TEXT NOT NULL,
                    steward_rationale TEXT NOT NULL,
                    closing_speed_delta REAL NOT NULL,
                    overlap_pct_at_apex REAL NOT NULL,
                    had_inside_line INTEGER NOT NULL,
                    had_apex_possession INTEGER NOT NULL,
                    contact_occurred INTEGER NOT NULL,
                    tyre_age_delta INTEGER NOT NULL,
                    race_progression REAL NOT NULL,
                    feature_vector_json TEXT NOT NULL
                )
            """)
            conn.commit()

    def upsert_incident(self, incident: Incident) -> None:
        vec = incident.feature_vector or build_incident_vector(incident.model_dump())
        vec_json = json.dumps(vec)
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO incidents (
                    id, name, year, round_name, session, lap, corner, corner_type,
                    driver_attacking, driver_defending, ruling, ruling_category,
                    penalty_seconds, fia_doc_title, fia_doc_url, steward_rationale,
                    closing_speed_delta, overlap_pct_at_apex, had_inside_line,
                    had_apex_possession, contact_occurred, tyre_age_delta,
                    race_progression, feature_vector_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    year=excluded.year,
                    round_name=excluded.round_name,
                    session=excluded.session,
                    lap=excluded.lap,
                    corner=excluded.corner,
                    corner_type=excluded.corner_type,
                    driver_attacking=excluded.driver_attacking,
                    driver_defending=excluded.driver_defending,
                    ruling=excluded.ruling,
                    ruling_category=excluded.ruling_category,
                    penalty_seconds=excluded.penalty_seconds,
                    fia_doc_title=excluded.fia_doc_title,
                    fia_doc_url=excluded.fia_doc_url,
                    steward_rationale=excluded.steward_rationale,
                    closing_speed_delta=excluded.closing_speed_delta,
                    overlap_pct_at_apex=excluded.overlap_pct_at_apex,
                    had_inside_line=excluded.had_inside_line,
                    had_apex_possession=excluded.had_apex_possession,
                    contact_occurred=excluded.contact_occurred,
                    tyre_age_delta=excluded.tyre_age_delta,
                    race_progression=excluded.race_progression,
                    feature_vector_json=excluded.feature_vector_json
            """, (
                incident.id, incident.name, incident.year, incident.round_name, incident.session,
                incident.lap, incident.corner, incident.corner_type, incident.driver_attacking,
                incident.driver_defending, incident.ruling, incident.ruling_category,
                incident.penalty_seconds, incident.fia_doc_title, incident.fia_doc_url,
                incident.steward_rationale, incident.closing_speed_delta, incident.overlap_pct_at_apex,
                incident.had_inside_line, incident.had_apex_possession, incident.contact_occurred,
                incident.tyre_age_delta, incident.race_progression, vec_json
            ))
            conn.commit()

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_incident(row)

    def list_incidents(self) -> List[Incident]:
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM incidents ORDER BY year DESC, id ASC")
            rows = cursor.fetchall()
            return [self._row_to_incident(r) for r in rows]

    def query_knn(
        self,
        query_vector: List[float],
        k: int = 5,
        exclude_id: Optional[str] = None
    ) -> List[Tuple[Incident, float]]:
        """
        Calculates exact nearest-neighbor distance (identical to SELECT ... feature_vector <-> %s).
        Returns list of (Incident, distance) ordered by closest distance ascending.
        """
        all_incidents = self.list_incidents()
        if not all_incidents:
            return []

        q_vec = np.array(query_vector, dtype=np.float32)
        results = []

        for inc in all_incidents:
            if exclude_id and inc.id == exclude_id:
                continue
            if not inc.feature_vector:
                continue
            v = np.array(inc.feature_vector, dtype=np.float32)
            dist = float(np.linalg.norm(q_vec - v))
            results.append((inc, dist))

        results.sort(key=lambda x: x[1])
        return results[:k]

    def _row_to_incident(self, row: sqlite3.Row) -> Incident:
        data = dict(row)
        vec = json.loads(data.pop("feature_vector_json"))
        return Incident(**data, feature_vector=vec)

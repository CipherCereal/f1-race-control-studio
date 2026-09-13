import os
import pandas as pd
from src.storage.schema import Incident
from src.storage.vector_store import VectorStore
from src.features.vectorizer import build_incident_vector

CSV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/ground_truth_incidents.csv"))


def seed_database(csv_path: str = CSV_PATH) -> int:
    store = VectorStore()
    df = pd.read_csv(csv_path)
    count = 0

    for _, row in df.iterrows():
        data = row.to_dict()
        vec = build_incident_vector(data)
        incident = Incident(
            id=data["id"],
            name=data["name"],
            year=int(data["year"]),
            round_name=data["round_name"],
            session=data["session"],
            lap=int(data["lap"]),
            corner=int(data["corner"]),
            corner_type=data["corner_type"],
            driver_attacking=data["driver_attacking"],
            driver_defending=data["driver_defending"],
            ruling=data["ruling"],
            ruling_category=data["ruling_category"],
            penalty_seconds=int(data["penalty_seconds"]),
            fia_doc_title=data["fia_doc_title"],
            fia_doc_url=data["fia_doc_url"],
            steward_rationale=data["steward_rationale"],
            closing_speed_delta=float(data["closing_speed_delta"]),
            overlap_pct_at_apex=float(data["overlap_pct_at_apex"]),
            had_inside_line=int(data["had_inside_line"]),
            had_apex_possession=int(data["had_apex_possession"]),
            contact_occurred=int(data["contact_occurred"]),
            tyre_age_delta=int(data["tyre_age_delta"]),
            race_progression=float(data["race_progression"]),
            feature_vector=vec
        )
        store.upsert_incident(incident)
        count += 1

    print(f"Successfully seeded {count} incidents into {store.db_path}")
    return count


if __name__ == "__main__":
    seed_database()

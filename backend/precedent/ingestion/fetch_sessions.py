import os
import fastf1
import pandas as pd
from typing import Optional, Tuple

CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/f1_cache"))
RAW_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw"))

# Ensure cache and raw directories exist
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(RAW_DIR, exist_ok=True)

# Enable FastF1 disk cache
try:
    fastf1.Cache.enable_cache(CACHE_DIR)
except Exception as e:
    print(f"Warning: Could not enable FastF1 cache: {e}")


def load_f1_session(year: int, event: str, session_type: str = "Race"):
    """
    Loads an F1 session using FastF1 with local caching.
    """
    print(f"Loading session: {year} {event} [{session_type}]...")
    session = fastf1.get_session(year, event, session_type)
    session.load(telemetry=True, laps=True)
    return session


def extract_incident_telemetry_slice(
    session,
    driver1: str,
    driver2: str,
    lap_number: int,
    output_filename: Optional[str] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Extracts telemetry for two drivers on a specific lap and optionally serializes to disk.
    """
    d1_lap = session.laps.pick_driver(driver1).pick_lap(lap_number)
    d2_lap = session.laps.pick_driver(driver2).pick_lap(lap_number)

    if d1_lap.empty or d2_lap.empty:
        raise ValueError(f"Lap {lap_number} not found for {driver1} or {driver2}")

    tel1 = d1_lap.get_telemetry().add_distance()
    tel2 = d2_lap.get_telemetry().add_distance()

    if output_filename:
        out_path = os.path.join(RAW_DIR, output_filename)
        # Store metadata and combined data
        combined = pd.DataFrame({
            "driver1": driver1,
            "driver2": driver2,
            "lap": lap_number
        }, index=[0])
        combined.to_json(out_path + ".meta.json")

    return tel1, tel2

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional


def align_telemetry_by_time(
    tel1: pd.DataFrame,
    tel2: pd.DataFrame,
    window_start_sec: Optional[float] = None,
    window_end_sec: Optional[float] = None,
    sample_rate_hz: int = 10
) -> pd.DataFrame:
    """
    Interpolates two drivers' telemetry onto a common synchronized time grid.
    FastF1 telemetry provides Time / SessionTime (Timedelta or seconds), X, Y, Speed, Throttle, Brake.
    """
    t1 = tel1.copy()
    t2 = tel2.copy()

    # Normalize time column to float seconds
    for df in [t1, t2]:
        if 'Time' in df.columns and pd.api.types.is_timedelta64_dtype(df['Time']):
            df['time_sec'] = df['Time'].dt.total_seconds()
        elif 'SessionTime' in df.columns and pd.api.types.is_timedelta64_dtype(df['SessionTime']):
            df['time_sec'] = df['SessionTime'].dt.total_seconds()
        elif 'time_sec' not in df.columns:
            df['time_sec'] = np.linspace(0, len(df) / 10.0, len(df))

    # Determine overlapping time window
    t_min = max(t1['time_sec'].min(), t2['time_sec'].min())
    t_max = min(t1['time_sec'].max(), t2['time_sec'].max())

    if window_start_sec is not None:
        t_min = max(t_min, window_start_sec)
    if window_end_sec is not None:
        t_max = min(t_max, window_end_sec)

    if t_max <= t_min:
        raise ValueError("Telemetry intervals for the two drivers do not overlap in time.")

    # Create uniform time grid
    grid = np.arange(t_min, t_max, 1.0 / sample_rate_hz)

    # Interpolate car 1
    car1_x = np.interp(grid, t1['time_sec'], t1['X']) if 'X' in t1.columns else np.zeros_like(grid)
    car1_y = np.interp(grid, t1['time_sec'], t1['Y']) if 'Y' in t1.columns else np.zeros_like(grid)
    car1_speed = np.interp(grid, t1['time_sec'], t1['Speed']) if 'Speed' in t1.columns else np.zeros_like(grid)

    # Interpolate car 2
    car2_x = np.interp(grid, t2['time_sec'], t2['X']) if 'X' in t2.columns else np.zeros_like(grid)
    car2_y = np.interp(grid, t2['time_sec'], t2['Y']) if 'Y' in t2.columns else np.zeros_like(grid)
    car2_speed = np.interp(grid, t2['time_sec'], t2['Speed']) if 'Speed' in t2.columns else np.zeros_like(grid)

    # Euclidean physical gap between cars (approx in decimeters/meters depending on FastF1 scale)
    lateral_gap = np.sqrt((car1_x - car2_x) ** 2 + (car1_y - car2_y) ** 2)

    aligned = pd.DataFrame({
        'time_sec': grid,
        'rel_time': grid - t_min,
        'car1_x': car1_x,
        'car1_y': car1_y,
        'car1_speed': car1_speed,
        'car2_x': car2_x,
        'car2_y': car2_y,
        'car2_speed': car2_speed,
        'speed_delta': car1_speed - car2_speed,
        'physical_gap': lateral_gap
    })
    return aligned


def extract_incident_features_from_telemetry(
    aligned_df: pd.DataFrame,
    apex_x: float,
    apex_y: float,
    car_length_units: float = 50.0  # Approx FastF1 coordinate length for 5.5m F1 chassis
) -> Dict[str, Any]:
    """
    Extracts closing speed, overlap percentage, and inside line flag
    from time-aligned multi-car telemetry.
    """
    # 1. Point of closest approach (closest physical gap)
    closest_idx = int(aligned_df['physical_gap'].argmin())
    closest_row = aligned_df.iloc[closest_idx]

    # 2. Closing speed delta at overlap initiation (~1 second prior to closest point)
    initiation_idx = max(0, closest_idx - 10)
    closing_speed = float(abs(aligned_df.iloc[initiation_idx]['speed_delta']))

    # 3. Overlap percentage: estimated from distance between cars along velocity vector
    # In F1, full overlap = 1.0 (alongside), front axle to rear axle = 0.5 - 0.7
    gap_at_apex = float(closest_row['physical_gap'])
    overlap_pct = float(np.clip(1.0 - (gap_at_apex / (car_length_units * 2.0)), 0.0, 1.0))

    # 4. Inside line determination: car closer to corner apex coordinates
    dist_car1_apex = np.sqrt((closest_row['car1_x'] - apex_x) ** 2 + (closest_row['car1_y'] - apex_y) ** 2)
    dist_car2_apex = np.sqrt((closest_row['car2_x'] - apex_x) ** 2 + (closest_row['car2_y'] - apex_y) ** 2)
    car1_had_inside = 1 if dist_car1_apex < dist_car2_apex else 0

    return {
        'closing_speed_delta': round(closing_speed, 1),
        'overlap_pct_at_apex': round(overlap_pct, 2),
        'had_inside_line': car1_had_inside,
        'contact_distance': round(gap_at_apex, 1),
        'closest_time_rel': round(float(closest_row['rel_time']), 2)
    }

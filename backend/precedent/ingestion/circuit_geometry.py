from typing import Dict, Any, Optional

# Curated reference corner classifications for standard F1 circuits
CIRCUIT_CORNER_PROFILES = {
    "interlagos": {
        1: {"type": "hairpin", "desc": "Senna S Turn 1 downhill tight left entry"},
        4: {"type": "high_speed", "desc": "Descida do Lago medium-fast left"},
    },
    "las_vegas": {
        1: {"type": "hairpin", "desc": "Turn 1 90-degree left hairpin"},
        14: {"type": "chicane", "desc": "Turn 14 sharp left-right chicane after Strip"},
    },
    "cota": {
        1: {"type": "hairpin", "desc": "Turn 1 steep uphill tight left hairpin"},
        12: {"type": "hairpin", "desc": "Turn 12 heavy braking left hairpin after back straight"},
    },
    "mexico": {
        1: {"type": "chicane", "desc": "Turn 1-2-3 opening chicane"},
        4: {"type": "chicane", "desc": "Turn 4 left-hand chicane entry"},
        8: {"type": "high_speed", "desc": "Turn 8 fast right sweeper"},
    },
    "baku": {
        1: {"type": "hairpin", "desc": "Turn 1 90-degree left at end of straight"},
        2: {"type": "hairpin", "desc": "Turn 2 tight 90-degree left and straight acceleration"},
    },
    "red_bull_ring": {
        3: {"type": "hairpin", "desc": "Turn 3 steep uphill right hairpin"},
        4: {"type": "high_speed", "desc": "Turn 4 downhill sweeping right"},
    },
    "montreal": {
        13: {"type": "chicane", "desc": "Turn 13-14 final chicane before Wall of Champions"},
    },
    "melbourne": {
        6: {"type": "high_speed", "desc": "Turn 6 high-speed right transition"},
    },
    "monza": {
        1: {"type": "chicane", "desc": "Variante del Rettifilo Turn 1-2 tight chicane"},
        4: {"type": "chicane", "desc": "Variante della Roggia Turn 4-5 chicane"},
    },
    "spa": {
        1: {"type": "hairpin", "desc": "La Source Turn 1 tight right hairpin"},
    },
    "shanghai": {
        14: {"type": "hairpin", "desc": "Turn 14 hairpin at end of long back straight"},
    }
}


def classify_corner(track_name: str, corner_number: int) -> str:
    """Returns the corner geometry classification for a given track and corner."""
    t_clean = track_name.lower().replace(" ", "_").replace("-", "_")
    for key, corners in CIRCUIT_CORNER_PROFILES.items():
        if key in t_clean:
            if corner_number in corners:
                return corners[corner_number]["type"]
    return "chicane"

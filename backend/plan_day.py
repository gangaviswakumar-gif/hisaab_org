
import math
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two GPS points in km."""
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def build_route(worker_lat: float, worker_lon: float, patients: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build a nearest-neighbor route starting from the worker's current GPS position.
    Each patient dict must have 'home_lat' and 'home_lon' keys.
    Returns a dict with the ordered route, total distance, and count.
    """
    if not patients:
        return {
            "route": [],
            "total_distance_km": 0.0,
            "patient_count": 0,
            "generated_at": datetime.now().isoformat()
        }

    remaining = list(patients)
    route = []
    total_dist = 0.0
    current_lat, current_lon = worker_lat, worker_lon

    while remaining:
        # Find nearest patient from current position
        best_idx = 0
        best_dist = haversine_km(current_lat, current_lon,
                                  remaining[0]["home_lat"], remaining[0]["home_lon"])
        for i in range(1, len(remaining)):
            d = haversine_km(current_lat, current_lon,
                             remaining[i]["home_lat"], remaining[i]["home_lon"])
            if d < best_dist:
                best_dist = d
                best_idx = i

        chosen = remaining.pop(best_idx)
        total_dist += best_dist
        current_lat = chosen["home_lat"]
        current_lon = chosen["home_lon"]

        route.append({
            "stop_number": len(route) + 1,
            "rch_id": chosen["rch_id"],
            "name": chosen.get("name", ""),
            "husband_name": chosen.get("husband_name", ""),
            "age": chosen.get("age"),
            "address": chosen.get("address", ""),
            "mobile": chosen.get("mobile", ""),
            "home_lat": chosen["home_lat"],
            "home_lon": chosen["home_lon"],
            "last_visit_date": chosen.get("last_visit_date", ""),
            "distance_from_previous_km": round(best_dist, 2),
            "lmp": chosen.get("lmp", ""),
            "edd": chosen.get("edd", ""),
            "gravida": chosen.get("gravida"),
            "para": chosen.get("para")
        })

    return {
        "route": route,
        "total_distance_km": round(total_dist, 2),
        "patient_count": len(route),
        "generated_at": datetime.now().isoformat()
    }


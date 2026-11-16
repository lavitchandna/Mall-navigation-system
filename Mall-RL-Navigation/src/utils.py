"""
Navigation Utilities for Mall-RL-Navigation.

Provides distance/time conversions, formatting helpers,
and navigation preference validations.
"""

from typing import Tuple, Dict, Any, List

# Standard indoor walking speed in meters per second
DEFAULT_WALKING_SPEED = 1.3  # ~4.7 km/h


def calculate_walking_time(distance_meters: float, speed_mps: float = DEFAULT_WALKING_SPEED) -> float:
    """
    Calculate estimated walking time in seconds.
    
    time = distance / speed
    """
    if speed_mps <= 0:
        speed_mps = DEFAULT_WALKING_SPEED
    return distance_meters / speed_mps


def format_walking_time(seconds: float) -> str:
    """
    Format seconds into a friendly string, e.g. '2 min 15 sec' or '45 sec'.
    """
    total_sec = max(0, int(round(seconds)))
    mins = total_sec // 60
    secs = total_sec % 60

    if mins > 0 and secs > 0:
        return f"{mins} min {secs} sec"
    elif mins > 0:
        return f"{mins} min"
    else:
        return f"{secs} sec"


def format_distance(meters: float) -> str:
    """Format meters cleanly, e.g. '185 m' or '1.2 km'."""
    if meters >= 1000:
        return f"{meters / 1000.0:.2f} km"
    return f"{meters:.1f} m"


def count_floor_changes(route_nodes: List[Dict[str, Any]]) -> int:
    """Count how many times the route transitions between floors."""
    if len(route_nodes) < 2:
        return 0
    changes = 0
    for i in range(len(route_nodes) - 1):
        if route_nodes[i].get("floor") != route_nodes[i + 1].get("floor"):
            changes += 1
    return changes


def is_route_accessible(route_edges: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """
    Verify whether all vertical connectors in a route are wheelchair/barrier-free accessible.
    """
    for edge in route_edges:
        edge_type = str(edge.get("type", "")).upper()
        if edge_type in ("STAIRS", "STAIRCASE"):
            return False, "Route uses stairs (not wheelchair accessible)"
        if edge_type == "ESCALATOR":
            return False, "Route uses escalator (not wheelchair accessible)"
    return True, "Fully wheelchair accessible (uses ramps/elevators)"

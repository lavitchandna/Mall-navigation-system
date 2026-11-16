"""
Mall Navigation Module.

Provides convenient high-level routing interfaces wrapping
the HybridRoutePlanner, navigation graph, and turn-by-turn guidance.
"""

from typing import Dict, Any, Optional
from src.route_planner import get_route_planner, HybridRoutePlanner
from src.directions import generate_turn_by_turn_directions
from src.utils import DEFAULT_WALKING_SPEED


def find_route(
    start_id: str,
    destination_id: str,
    preference: str = "Standard",
    walking_speed: float = DEFAULT_WALKING_SPEED,
    crowd_aware: bool = False,
) -> Dict[str, Any]:
    """
    High-level API: calculate hybrid route and generate turn-by-turn directions.
    """
    planner: HybridRoutePlanner = get_route_planner()
    route_result = planner.plan_route(
        start_id=start_id,
        destination_id=destination_id,
        preference=preference,
        walking_speed=walking_speed,
        crowd_aware=crowd_aware,
    )

    # Attach turn-by-turn directions for the chosen route
    chosen = route_result["rl_route"] if route_result["rl_route"]["nodes"] else route_result["shortest_path"]
    directions = generate_turn_by_turn_directions(chosen["nodes"], chosen["edges"])
    route_result["directions"] = directions

    return route_result

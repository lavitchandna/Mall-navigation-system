"""
Ambience Mall Gurugram: Store Recommendation & Proximity Engine.

Recommends real stores and nearby places across Ground, First, and Second floors
based on exact graph walking distance, walking time, categories, and crowd congestion.
"""

from typing import Dict, List, Optional, Any

from src.real_map_loader import get_real_map_loader, RealMallLoader
from src.navigation_graph import get_navigation_graph, NavigationGraph
from src.utils import calculate_walking_time, format_walking_time, format_distance, DEFAULT_WALKING_SPEED


class RecommendationEngine:
    """Spatial store recommendation and proximity engine."""

    def __init__(self):
        self.loader: RealMallLoader = get_real_map_loader()
        self.graph: NavigationGraph = get_navigation_graph()

    def get_nearby_places(
        self,
        current_node_id: str,
        max_distance: float = 75.0,
        walking_speed: float = DEFAULT_WALKING_SPEED,
        limit: int = 6,
    ) -> List[Dict[str, Any]]:
        resolved_curr = self.graph.resolve_node_id(current_node_id)
        if not resolved_curr or resolved_curr not in self.graph.nodes:
            return []

        curr_node = self.graph.get_node(resolved_curr)
        nearby = []

        for s in self.loader.stores:
            cand_id = s["id"]
            if cand_id == current_node_id or s.get("entrance_node") == resolved_curr:
                continue

            path_res = self.graph.find_shortest_path(resolved_curr, cand_id)
            if not path_res:
                continue

            dist = path_res["total_distance"]
            if dist <= max_distance:
                time_sec = calculate_walking_time(dist, walking_speed)
                same_floor = s.get("floor") == curr_node.get("floor")

                flr_num = s.get("floor", 0)
                flr_str = "Ground Floor" if flr_num == 0 else ("First Floor" if flr_num == 1 else "Second Floor")

                nearby.append({
                    "id": cand_id,
                    "name": s["name"],
                    "category": s.get("category", "General"),
                    "floor": flr_num,
                    "floor_name": flr_str,
                    "zone": s.get("zone", "Mall"),
                    "distance_meters": dist,
                    "distance_str": format_distance(dist),
                    "time_seconds": round(time_sec, 1),
                    "time_str": format_walking_time(time_sec),
                    "crowd_level": s.get("crowd_level", "Low"),
                    "same_floor": same_floor,
                    "description": s.get("description", ""),
                })

        nearby.sort(key=lambda x: x["distance_meters"])
        return nearby[:limit]

    def recommend_stores(
        self,
        current_node_id: str,
        category: str = "All",
        user_preference: str = "balanced",
        walking_speed: float = DEFAULT_WALKING_SPEED,
        limit: int = 6,
    ) -> List[Dict[str, Any]]:
        resolved_curr = self.graph.resolve_node_id(current_node_id)
        stores = self.loader.get_stores_by_category(category)
        if not stores:
            return []

        scored_stores = []
        for s in stores:
            store_id = s["id"]
            if store_id == current_node_id or s.get("entrance_node") == resolved_curr:
                continue

            path_res = self.graph.find_shortest_path(current_node_id, store_id)
            dist = path_res["total_distance"] if path_res else 999.0
            time_sec = calculate_walking_time(dist, walking_speed)

            crowd = s.get("crowd_level", "Low")
            crowd_penalty = 12.0 if crowd == "High" else (4.0 if crowd == "Medium" else 0.0)
            score = dist + crowd_penalty

            flr_num = s.get("floor", 0)
            flr_str = "Ground Floor" if flr_num == 0 else ("First Floor" if flr_num == 1 else "Second Floor")

            scored_stores.append({
                "id": store_id,
                "name": s["name"],
                "category": s.get("category", "Retail"),
                "floor": flr_num,
                "floor_name": flr_str,
                "zone": s.get("zone", "Mall"),
                "distance_meters": dist,
                "distance_str": format_distance(dist),
                "time_seconds": round(time_sec, 1),
                "time_str": format_walking_time(time_sec),
                "crowd_level": crowd,
                "description": s.get("description", ""),
                "score": score,
            })

        scored_stores.sort(key=lambda x: x["score"])
        return scored_stores[:limit]


_GLOBAL_RECOMMENDER: Optional[RecommendationEngine] = None


def get_recommendation_engine() -> RecommendationEngine:
    global _GLOBAL_RECOMMENDER
    if _GLOBAL_RECOMMENDER is None:
        _GLOBAL_RECOMMENDER = RecommendationEngine()
    return _GLOBAL_RECOMMENDER

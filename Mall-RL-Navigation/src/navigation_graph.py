"""
Ambience Mall Gurugram: Real Navigation Graph & Pathfinding Engine.

Topological graph model loaded from data/navigation_graph_real.json
Supports real walkable corridors, multi-floor transitions (Ground, First, Second),
wheelchair accessibility routing, crowd-aware penalties, and Dijkstra/A* search.
"""

import heapq
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
NAV_GRAPH_REAL_PATH = DATA_DIR / "navigation_graph_real.json"
NAV_GRAPH_LEGACY_PATH = DATA_DIR / "navigation_graph.json"


class NavigationGraph:
    """Walkable topological graph model of Ambience Mall Gurugram."""

    def __init__(self, graph_path: Optional[Path] = None):
        self.graph_path = Path(graph_path) if graph_path else NAV_GRAPH_REAL_PATH
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.adjacency: Dict[str, List[Dict[str, Any]]] = {}
        self.floor_maps: Dict[str, Any] = {}
        self.poi_to_entrance: Dict[str, str] = {}
        self.raw_edges: List[Dict[str, Any]] = []
        self.load_graph()

    def load_graph(self) -> None:
        if not self.graph_path.exists():
            raise FileNotFoundError(f"Graph file not found: {self.graph_path}")

        with open(self.graph_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.floor_maps = data.get("floor_maps", {})
        self.nodes = {n["id"]: dict(n) for n in data.get("nodes", [])}
        self.adjacency = {n_id: [] for n_id in self.nodes}
        self.raw_edges = list(data.get("edges", []))

        for n in data.get("nodes", []):
            if n.get("poi_id"):
                self.poi_to_entrance[n["poi_id"]] = n["id"]

        for edge in data.get("edges", []):
            u = edge["from"]
            v = edge["to"]
            dist = float(edge["distance"])
            edge_type = edge.get("type", "corridor").upper()
            accessible = edge.get("accessible", edge_type not in ["STAIRS", "ESCALATOR"])

            if u in self.adjacency and v in self.adjacency:
                # Add bidirectional connectivity
                self.adjacency[u].append({
                    "to": v,
                    "distance": dist,
                    "type": edge_type,
                    "accessible": accessible,
                })
                self.adjacency[v].append({
                    "to": u,
                    "distance": dist,
                    "type": edge_type,
                    "accessible": accessible,
                })

    def get_nodes_on_floor(self, floor_id: int) -> List[Dict[str, Any]]:
        return [n for n in self.nodes.values() if n.get("floor") == floor_id]

    def iter_same_floor_edges(self, floor_id: int) -> List[Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]]:
        """Return unique undirected same-floor edges as (u_node, v_node, edge)."""
        seen = set()
        result = []
        for u_id, nbrs in self.adjacency.items():
            u_node = self.nodes.get(u_id)
            if not u_node or u_node.get("floor") != floor_id:
                continue
            for nbr in nbrs:
                v_id = nbr["to"]
                pair = tuple(sorted((u_id, v_id)))
                if pair in seen:
                    continue
                v_node = self.nodes.get(v_id)
                if not v_node or v_node.get("floor") != floor_id:
                    continue
                seen.add(pair)
                result.append((u_node, v_node, nbr))
        return result

    def resolve_node_id(self, node_or_poi_id: str) -> Optional[str]:
        """Map a shop POI ID or direct node ID to a valid graph node ID."""
        if node_or_poi_id in self.nodes:
            return node_or_poi_id
        if node_or_poi_id in self.poi_to_entrance:
            return self.poi_to_entrance[node_or_poi_id]
        ent_key = f"ENT_{node_or_poi_id}"
        if ent_key in self.nodes:
            return ent_key
        return None

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        resolved = self.resolve_node_id(node_id)
        if resolved:
            return self.nodes.get(resolved)
        return self.nodes.get(node_id)

    def is_valid_node(self, node_id: str) -> bool:
        return self.resolve_node_id(node_id) is not None

    def get_neighbors(self, node_id: str) -> List[Dict[str, Any]]:
        resolved = self.resolve_node_id(node_id)
        if resolved:
            return self.adjacency.get(resolved, [])
        return []

    def calculate_edge_weight(
        self,
        edge: Dict[str, Any],
        crowd_aware: bool = False,
        accessible_only: bool = False,
        crowd_map: Optional[Dict[str, str]] = None,
    ) -> float:
        base_dist = edge["distance"]
        edge_type = edge.get("type", "WALK").upper()

        # Strict accessibility enforcement
        if accessible_only:
            if edge_type in ["STAIRS", "ESCALATOR"]:
                return float("inf")

        cost = base_dist

        # Stairs effort penalty for standard routing
        if edge_type == "STAIRS":
            cost *= 1.4

        # Vertical transition overhead (waiting for lift / riding escalator)
        if edge_type in ["ELEVATOR", "ESCALATOR", "STAIRS"]:
            cost += 6.0

        # Crowd penalty
        if crowd_aware and crowd_map:
            dest_node = edge["to"]
            crowd_level = crowd_map.get(dest_node, "Low")
            if crowd_level == "High":
                cost *= 1.8
            elif crowd_level == "Medium":
                cost *= 1.3

        return cost

    def find_shortest_path(
        self,
        start_id: str,
        goal_id: str,
        crowd_aware: bool = False,
        accessible_only: bool = False,
        crowd_map: Optional[Dict[str, str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Dijkstra / A* deterministic shortest path algorithm.
        Returns path dict with node IDs, total distance, traversed edges, and status.
        """
        s_id = self.resolve_node_id(start_id)
        g_id = self.resolve_node_id(goal_id)

        if not s_id or not g_id:
            return None

        if s_id == g_id:
            node_obj = self.nodes[s_id]
            return {
                "path": [s_id],
                "nodes": [node_obj],
                "edges": [],
                "total_distance": 0.0,
                "cost": 0.0,
                "success": True,
            }

        def _run_dijkstra(same_floor_only: bool = False) -> Optional[Dict[str, Any]]:
            pq = [(0.0, s_id, [s_id], [], 0.0)]
            visited = set()
            min_costs = {s_id: 0.0}

            while pq:
                cost, curr, path, edges, phys_dist = heapq.heappop(pq)

                if curr in visited:
                    continue
                visited.add(curr)

                if curr == g_id:
                    return {
                        "path": path,
                        "nodes": [self.nodes[n] for n in path],
                        "edges": edges,
                        "total_distance": round(phys_dist, 1),
                        "cost": round(cost, 1),
                        "success": True,
                    }

                for neighbor in self.adjacency.get(curr, []):
                    nxt = neighbor["to"]
                    nxt_node = self.nodes.get(nxt)
                    if not nxt_node:
                        continue

                    edge_type = neighbor.get("type", "WALK").upper()

                    # Phase 2 Strict Same-Floor Routing Rule:
                    # When searching on same floor, never cross floors or enter vertical connectors
                    if same_floor_only:
                        if nxt_node.get("floor") != start_floor:
                            continue
                        if edge_type in ["ELEVATOR", "ESCALATOR", "STAIRS"]:
                            continue
                        if any(nxt.startswith(p) for p in ["LIFT_", "ESC_", "STAIRS_"]):
                            continue

                    edge_cost = self.calculate_edge_weight(
                        neighbor,
                        crowd_aware=crowd_aware,
                        accessible_only=accessible_only,
                        crowd_map=crowd_map,
                    )
                    if edge_cost == float("inf"):
                        continue

                    new_cost = cost + edge_cost
                    if nxt not in min_costs or new_cost < min_costs[nxt]:
                        min_costs[nxt] = new_cost
                        heapq.heappush(
                            pq,
                            (
                                new_cost,
                                nxt,
                                path + [nxt],
                                edges + [neighbor],
                                phys_dist + neighbor["distance"],
                            ),
                        )
            return None

        start_floor = self.nodes[s_id].get("floor")
        goal_floor = self.nodes[g_id].get("floor")

        # If start and destination are on the same floor, strictly prefer the same-floor corridor route
        if start_floor == goal_floor:
            same_floor_res = _run_dijkstra(same_floor_only=True)
            if same_floor_res is not None:
                return same_floor_res

        # Otherwise (or if no same-floor path exists), run standard multi-floor search
        return _run_dijkstra(same_floor_only=False)


_GLOBAL_GRAPH: Optional[NavigationGraph] = None


def get_navigation_graph() -> NavigationGraph:
    global _GLOBAL_GRAPH
    if _GLOBAL_GRAPH is None:
        _GLOBAL_GRAPH = NavigationGraph()
    return _GLOBAL_GRAPH

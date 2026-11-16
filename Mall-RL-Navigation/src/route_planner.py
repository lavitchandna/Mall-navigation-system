"""
Ambience Mall Gurugram: Genuine Hybrid Route Planner.

Combines genuine Reinforcement Learning Tabular Q-policy rollout with
deterministic Dijkstra shortest path baseline across Ground Floor, First Floor,
and Second Floor.
"""

from pathlib import Path
import time
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from src.environment import (
    MallNavigationEnv,
    GRAPH_ACTION_NAMES,
    GRAPH_ACTION_VERTICAL,
    GRAPH_ACTION_CONNECTED,
    PROFILE_STANDARD,
    PROFILE_ACCESSIBLE,
    PROFILE_CROWD_AWARE,
)
from src.real_map_loader import get_real_map_loader, RealMallLoader
from src.navigation_graph import get_navigation_graph, NavigationGraph, NAV_GRAPH_REAL_PATH
from src.utils import (
    calculate_walking_time,
    format_walking_time,
    format_distance,
    count_floor_changes,
    is_route_accessible,
    DEFAULT_WALKING_SPEED,
)

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
Q_TABLE_PATH = MODELS_DIR / "q_table.npy"


def prune_cycles(path: List[str]) -> List[str]:
    """Eliminates intermediate loops or redundant backtracks from a node path."""
    cleaned: List[str] = []
    seen: Dict[str, int] = {}
    for node in path:
        if node in seen:
            idx = seen[node]
            for removed in cleaned[idx + 1:]:
                if removed in seen and seen[removed] > idx:
                    del seen[removed]
            cleaned = cleaned[:idx + 1]
        else:
            seen[node] = len(cleaned)
            cleaned.append(node)
    return cleaned


def validate_route(
    path: List[str],
    start_node_id: str,
    dest_node_id: str,
    graph: NavigationGraph,
) -> Tuple[bool, str]:
    """
    Phase 8 Route Validation:
    1. Route starts at requested start node.
    2. Route ends at requested destination node.
    3. Every consecutive node pair is a valid graph edge.
    4. No impossible floor transition.
    5. No repeated-node loop.
    6. Same-floor route does not unnecessarily change floors.
    """
    if not path or len(path) == 0:
        return False, "Route path is empty"

    if path[0] != start_node_id:
        return False, f"Route starts at {path[0]}, expected {start_node_id}"

    if path[-1] != dest_node_id:
        return False, f"Route ends at {path[-1]}, expected {dest_node_id}"

    start_node = graph.get_node(start_node_id)
    dest_node = graph.get_node(dest_node_id)
    if not start_node or not dest_node:
        return False, "Start or destination node not found in graph"

    start_floor = start_node.get("floor")
    dest_floor = dest_node.get("floor")

    # Check for duplicate nodes (cycles)
    if len(path) != len(set(path)):
        return False, "Route contains duplicate node cycle/loop"

    # Verify every consecutive pair is an actual graph edge
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        nbrs = [n for n in graph.get_neighbors(u) if n["to"] == v]
        if not nbrs:
            return False, f"Invalid graph transition: no edge between {u} and {v}"

        u_node = graph.get_node(u)
        v_node = graph.get_node(v)
        if u_node and v_node and u_node.get("floor") != v_node.get("floor"):
            edge_type = nbrs[0].get("type", "").upper()
            if edge_type not in ["ELEVATOR", "ESCALATOR", "STAIRS"]:
                return False, f"Impossible floor transition between {u} and {v} with edge type {edge_type}"

    # Phase 2 Strict Same-Floor Correctness Rule:
    if start_floor is not None and dest_floor is not None and start_floor == dest_floor:
        for nid in path:
            node = graph.get_node(nid)
            if node and node.get("floor") != start_floor:
                return False, f"Same-floor route ({start_floor} -> {dest_floor}) made unnecessary floor transition to floor {node.get('floor')}"
            if any(nid.startswith(p) for p in ["LIFT_", "ESC_", "STAIRS_"]):
                return False, f"Same-floor route ({start_floor} -> {dest_floor}) unnecessarily entered vertical connector {nid}"

    return True, "Valid verified route"


class HybridRoutePlanner:
    """Hybrid path planning engine comparing genuine RL policy vs Dijkstra shortest path."""

    def __init__(self, graph: Optional[NavigationGraph] = None, loader: Optional[RealMallLoader] = None):
        self.loader: RealMallLoader = loader if loader else get_real_map_loader()
        self.graph: NavigationGraph = graph if graph else get_navigation_graph()
        self.q_table: Optional[np.ndarray] = None
        self.env: Optional[MallNavigationEnv] = None
        self.load_model()

    def load_model(self) -> bool:
        if Q_TABLE_PATH.exists():
            try:
                self.q_table = np.load(Q_TABLE_PATH)
                self.env = MallNavigationEnv(graph=self.graph, loader=self.loader)
                return True
            except Exception:
                self.q_table = None
                self.env = None
        return False

    def is_model_loaded(self) -> bool:
        return self.q_table is not None

    def _rollout_rl_policy(
        self,
        start_id: str,
        destination_id: str,
        preference: str = "Standard",
        crowd_aware: bool = False,
        max_steps: int = 70,
    ) -> Dict[str, Any]:
        """
        Genuine RL policy rollout over learned Tabular Q-Table.
        Enforces physical graph constraints, invalid action masking, same-floor rules, and cycle prevention.
        """
        t0 = time.perf_counter()
        start_res = self.graph.resolve_node_id(start_id)
        dest_res = self.graph.resolve_node_id(destination_id)

        if not start_res or not dest_res or self.q_table is None or self.env is None:
            return {
                "success": False,
                "path": [],
                "nodes": [],
                "edges": [],
                "total_distance": 0.0,
                "steps": 0,
                "time_ms": 0.0,
                "q_values_at_start": {},
                "actions_taken": [],
                "validation_reason": "RL model unavailable or uncalibrated coordinates",
                "rl_status": "RL model unavailable or uncalibrated coordinates",
            }

        # Handle same start and destination trivially
        if start_res == dest_res:
            node = self.graph.get_node(start_res)
            return {
                "success": True,
                "path": [start_res],
                "nodes": [node] if node else [],
                "edges": [],
                "total_distance": 0.0,
                "steps": 1,
                "time_ms": 0.01,
                "q_values_at_start": {GRAPH_ACTION_NAMES[a]: 100.0 for a in range(6)},
                "actions_taken": ["ARRIVED"],
                "validation_reason": "Already at destination",
                "rl_status": "Already at destination",
            }

        is_accessible = "access" in preference.lower()
        is_crowd = crowd_aware and not is_accessible
        prof_idx = (
            PROFILE_ACCESSIBLE
            if is_accessible
            else (PROFILE_CROWD_AWARE if is_crowd else PROFILE_STANDARD)
        )
        prof_name = "accessible" if is_accessible else ("crowd_aware" if is_crowd else "standard")

        self.env.set_start_and_destination(start_res, dest_res, prof_name)

        # Inspect initial state Q-values for evaluation
        start_state = self.env._encode_state(start_res, dest_res, prof_idx)
        q_at_start = {
            GRAPH_ACTION_NAMES[a]: round(float(self.q_table[start_state, a]), 2)
            for a in range(6)
        }

        curr_id = start_res
        raw_path = [curr_id]
        visited = {curr_id}
        actions_taken = []

        for _ in range(max_steps):
            if curr_id == dest_res:
                break

            # Phase 6: Invalid Action Masking
            valid_actions = self.env.get_valid_actions(curr_id)
            if not valid_actions:
                break

            state = self.env._encode_state(curr_id, dest_res, prof_idx)
            q_vals = self.q_table[state].copy()

            # Rank candidate actions strictly among valid actions by Q-value
            action_order = sorted(valid_actions, key=lambda a: q_vals[a], reverse=True)

            chosen_edge = None
            chosen_action = None

            # 1. First pass: highest Q valid action leading to an unvisited node (or goal)
            for a in action_order:
                edge, hit = self.env._resolve_action_neighbor(curr_id, a)
                if not hit and edge is not None:
                    tgt = edge["to"]
                    if tgt not in visited or tgt == dest_res:
                        chosen_edge = edge
                        chosen_action = a
                        break

            # 2. Second pass: allow non-backtracking visited node
            if chosen_edge is None:
                for a in action_order:
                    edge, hit = self.env._resolve_action_neighbor(curr_id, a)
                    if not hit and edge is not None:
                        tgt = edge["to"]
                        if len(raw_path) > 1 and tgt == raw_path[-2]:
                            continue
                        chosen_edge = edge
                        chosen_action = a
                        break

            # 3. Third pass: any valid action
            if chosen_edge is None and action_order:
                edge, hit = self.env._resolve_action_neighbor(curr_id, action_order[0])
                if not hit and edge is not None:
                    chosen_edge = edge
                    chosen_action = action_order[0]

            if chosen_edge is None:
                break

            actions_taken.append(GRAPH_ACTION_NAMES[chosen_action])
            curr_id = chosen_edge["to"]
            raw_path.append(curr_id)
            visited.add(curr_id)

        t1 = time.perf_counter()
        time_ms = round((t1 - t0) * 1000, 2)

        # Apply cycle pruning
        path = prune_cycles(raw_path)

        # Phase 8: Strict Route Validation
        is_valid, validation_reason = validate_route(path, start_res, dest_res, self.graph)

        edges = []
        total_dist = 0.0
        if is_valid:
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                nbrs = [n for n in self.graph.get_neighbors(u) if n["to"] == v]
                if nbrs:
                    edges.append(nbrs[0])
                    total_dist += nbrs[0].get("distance", 1.0)

        nodes = [self.graph.get_node(n) for n in path]

        return {
            "success": is_valid,
            "path": path,
            "nodes": nodes,
            "edges": edges,
            "total_distance": round(total_dist, 2),
            "steps": len(path),
            "time_ms": time_ms,
            "q_values_at_start": q_at_start,
            "actions_taken": actions_taken,
            "validation_reason": validation_reason,
            "rl_status": (
                "Converged RL Q-policy route"
                if is_valid
                else f"RL policy did not converge safely: {validation_reason}"
            ),
        }

    def plan_route(
        self,
        start_id: str,
        destination_id: str,
        preference: str = "Standard",
        walking_speed: float = DEFAULT_WALKING_SPEED,
        crowd_aware: bool = False,
    ) -> Dict[str, Any]:
        """
        Plan and compare routes using Dijkstra (guaranteed baseline) and genuine RL Q-policy.
        """
        is_accessible = "accessible" in preference.lower()
        effective_crowd = crowd_aware and not is_accessible

        # 1. Classical Shortest / Optimal Graph Path (Deterministic Baseline)
        crowd_map: Dict[str, str] = {}
        t0_dijk = time.perf_counter()
        dijkstra_res = self.graph.find_shortest_path(
            start_id=start_id,
            goal_id=destination_id,
            crowd_aware=effective_crowd,
            accessible_only=is_accessible,
            crowd_map=crowd_map,
        )
        t1_dijk = time.perf_counter()
        dijkstra_time_ms = round((t1_dijk - t0_dijk) * 1000, 2)
        if dijkstra_res:
            dijkstra_res["time_ms"] = dijkstra_time_ms

        # 2. Genuine Reinforcement Learning Policy Rollout
        rl_res = self._rollout_rl_policy(
            start_id=start_id,
            destination_id=destination_id,
            preference=preference,
            crowd_aware=effective_crowd,
        )

        # 3. Controlled Fallback if RL did not converge or failed validation
        if not rl_res.get("success"):
            # Controlled fallback to Dijkstra baseline
            res_fallback = dict(dijkstra_res) if dijkstra_res else {"path": [], "nodes": [], "edges": [], "total_distance": 0.0, "success": False}
            res_fallback["rl_status"] = f"RL fallback active: {rl_res.get('validation_reason')}"
            res_fallback["q_values_at_start"] = rl_res.get("q_values_at_start", {})
            res_fallback["actions_taken"] = rl_res.get("actions_taken", [])
            res_fallback["time_ms"] = rl_res.get("time_ms", 0.0)
            res_fallback["validation_reason"] = rl_res.get("validation_reason")
            rl_candidate = res_fallback
            rl_policy_used = False
        else:
            rl_candidate = rl_res
            rl_policy_used = True

        # 4. Enrich both routes
        enriched_dijkstra = self._enrich_route(
            dijkstra_res,
            speed=walking_speed,
            method_name="Dijkstra Shortest Path (Baseline)",
        )
        enriched_rl = self._enrich_route(
            rl_candidate,
            speed=walking_speed,
            method_name="Reinforcement Learning (Tabular Q-Policy)",
        )

        start_node = self.graph.get_node(start_id)
        dest_node = self.graph.get_node(destination_id)
        start_calibrated = self.graph.resolve_node_id(start_id) is not None
        dest_calibrated = self.graph.resolve_node_id(destination_id) is not None

        if not start_calibrated or not dest_calibrated:
            missing = []
            if not start_calibrated:
                missing.append("origin")
            if not dest_calibrated:
                missing.append("destination")
            comp_text = (
                f"Location not calibrated: {', '.join(missing)} "
                "has no walkable node in the real navigation graph."
            )
        elif not dijkstra_res or not dijkstra_res.get("success"):
            comp_text = "No walkable route exists in the real navigation graph between these locations."
        elif rl_policy_used and enriched_rl["path"] == enriched_dijkstra["path"]:
            comp_text = "RL policy and Dijkstra converged to identical optimal corridor path."
        elif rl_policy_used:
            comp_text = f"RL policy ({enriched_rl['steps']} steps, cost {enriched_rl['graph_cost']}) vs Dijkstra baseline ({enriched_dijkstra['steps']} steps, cost {enriched_dijkstra['graph_cost']})."
        else:
            comp_text = f"RL policy did not converge safely ({rl_res.get('validation_reason')}); deterministic Dijkstra baseline active."

        # Evaluation scorecard
        evaluation = {
            "rl": {
                "success": rl_res.get("success", False),
                "validation_reason": rl_res.get("validation_reason", "N/A"),
                "steps": enriched_rl["steps"],
                "path_cost": enriched_rl["graph_cost"],
                "time_ms": rl_res.get("time_ms", 0.0),
                "floor_changes": enriched_rl["floor_changes"],
                "connectors": [e.get("type") for e in enriched_rl["edges"] if e.get("type", "").lower() in ["elevator", "escalator", "stairs"]],
                "q_values_at_start": rl_res.get("q_values_at_start", {}),
                "actions_sequence": rl_res.get("actions_taken", [])[:15],
            },
            "baseline": {
                "success": bool(dijkstra_res and dijkstra_res.get("success")),
                "steps": enriched_dijkstra["steps"],
                "path_cost": enriched_dijkstra["graph_cost"],
                "time_ms": dijkstra_time_ms,
                "floor_changes": enriched_dijkstra["floor_changes"],
                "connectors": [e.get("type") for e in enriched_dijkstra["edges"] if e.get("type", "").lower() in ["elevator", "escalator", "stairs"]],
            },
            "rl_policy_used": rl_policy_used,
            "fallback_active": not rl_policy_used,
            "preferred_method": "rl" if rl_policy_used else "dijkstra",
            "identical_path": enriched_rl["path"] == enriched_dijkstra["path"],
        }

        return {
            "start_id": start_id,
            "destination_id": destination_id,
            "start_node": start_node,
            "destination_node": dest_node,
            "start_calibrated": start_calibrated,
            "destination_calibrated": dest_calibrated,
            "preference": preference,
            "walking_speed": walking_speed,
            "crowd_aware": effective_crowd,
            "accessible": is_accessible,
            "rl_route": enriched_rl,
            "shortest_path": enriched_dijkstra,
            "evaluation": evaluation,
            "comparison_summary": comp_text,
            "distance_diff_meters": None,
            "time_diff_seconds": None,
            "metric_calibrated": False,
        }

    def _enrich_route(
        self,
        route_data: Optional[Dict[str, Any]],
        speed: float,
        method_name: str,
    ) -> Dict[str, Any]:
        if not route_data or not route_data.get("path"):
            return {
                "method": method_name,
                "path": [],
                "nodes": [],
                "edges": [],
                "graph_cost": 0.0,
                "distance_meters": None,
                "distance_str": "—",
                "time_seconds": None,
                "time_str": "—",
                "steps": 0,
                "hops": 0,
                "floor_changes": 0,
                "is_accessible": True,
                "accessible_desc": "N/A",
                "floor_segments": {0: [], 1: [], 2: []},
                "status": "No valid route found",
                "metric_calibrated": False,
            }

        path = route_data["path"]
        nodes = route_data.get("nodes", [self.graph.get_node(n) for n in path])
        edges = route_data.get("edges", [])
        dist = float(route_data.get("total_distance", 0.0))

        floor_changes = count_floor_changes(nodes)
        accessible, access_desc = is_route_accessible(edges)

        floor_segments: Dict[int, List[Dict[str, Any]]] = {0: [], 1: [], 2: []}
        for n in nodes:
            if n:
                flr = n.get("floor", 0)
                floor_segments.setdefault(flr, []).append(n)

        return {
            "method": method_name,
            "path": path,
            "nodes": nodes,
            "edges": edges,
            "graph_cost": round(dist, 2),
            "distance_meters": None,
            "distance_str": "—",
            "time_seconds": None,
            "time_str": "—",
            "steps": len(path),
            "hops": max(0, len(path) - 1),
            "floor_changes": floor_changes,
            "is_accessible": accessible,
            "accessible_desc": access_desc,
            "floor_segments": floor_segments,
            "status": route_data.get("rl_status", "Verified graph path"),
            "metric_calibrated": False,
        }


_GLOBAL_PLANNER: Optional[HybridRoutePlanner] = None


def get_route_planner() -> HybridRoutePlanner:
    global _GLOBAL_PLANNER
    if _GLOBAL_PLANNER is None:
        _GLOBAL_PLANNER = HybridRoutePlanner()
    return _GLOBAL_PLANNER

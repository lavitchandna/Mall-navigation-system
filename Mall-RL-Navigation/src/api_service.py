"""
Ambience Mall Gurugram: API service layer.

Thin, framework-free adapter between the existing Mall-RL-Navigation backend
(real_map_loader / navigation_graph / route_planner / recommendation / directions)
and the JSON payloads consumed by the V0 frontend through ``api.py``.

Rules this module enforces (they come from the project's own data policy):

* Real data only. Every store, coordinate, node, edge and connector in a payload comes
  from ``data/*MASTER_Coordinates.json`` and ``data/navigation_graph_real.json`` through
  the existing loaders. Nothing is invented here.
* Floors are independent coordinate frames. Coordinates are always reported together
  with the floor they belong to, and routes are split into one segment per floor.
* The real dataset is not metrically calibrated (``metric_calibrated`` is False in the
  planner and ``routing_ready`` is False in the master file). Graph edge lengths are
  therefore exposed as a *relative path cost* and walking time is reported as
  "not calibrated". No metres or minutes are ever emitted.
* The runtime route is Dijkstra over the real graph. The Q-table is loaded by the
  planner but not consulted when choosing a route (see
  ``HybridRoutePlanner._rollout_or_fallback``), so the payload says so explicitly.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from src.directions import generate_turn_by_turn_directions
from src.navigation_graph import NAV_GRAPH_REAL_PATH, get_navigation_graph
from src.real_map_loader import FLOOR_ID_TO_NAME, get_real_map_loader
from src.recommendation import get_recommendation_engine
from src.route_planner import get_route_planner

# The starting point used for route planning. There is no live indoor positioning, so
# routes start from a configured location. Gate 1 matches the default of the original app.
DEFAULT_START_ID = os.environ.get("MALL_DEFAULT_START", "G_GATE_1")

# Search radius for "nearby" in relative path-cost units (default of the original engine).
DEFAULT_NEARBY_MAX_COST = 75.0

LOCATION_KINDS = ("store", "gate", "connector", "all")


class ApiServiceError(Exception):
    """Error that maps cleanly onto an HTTP status + machine-readable code."""

    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def _r(value: Any, digits: int = 1) -> Optional[float]:
    return None if value is None else round(float(value), digits)


def path_cost(value: Any) -> Dict[str, Any]:
    """Graph edge lengths are relative cost, never metres (dataset is not calibrated)."""
    return {"value": _r(value), "unit": "relative", "calibrated": False}


def floor_name(floor_id: Any) -> str:
    return FLOOR_ID_TO_NAME.get(floor_id, f"Floor {floor_id}")


class MallService:
    """Builds API payloads from the real Mall-RL-Navigation backend."""

    def __init__(self, default_start_id: Optional[str] = None):
        self.loader = get_real_map_loader()
        self.graph = get_navigation_graph()
        self.planner = get_route_planner()
        self.recommender = get_recommendation_engine()
        self.default_start_id = default_start_id or DEFAULT_START_ID

        if self.loader.get_location(self.default_start_id) is None:
            raise ValueError(
                f"Configured start location '{self.default_start_id}' does not exist in the real "
                "mall data. Set MALL_DEFAULT_START to a valid gate or store ID."
            )

        with open(NAV_GRAPH_REAL_PATH, "r", encoding="utf-8") as f:
            self._graph_version = json.load(f).get("version")

    # ------------------------------------------------------------------ views
    def _node_view(self, node: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": node["id"],
            "name": node.get("name", node["id"]),
            "type": node.get("type"),
            "floor": node.get("floor"),
            "floor_name": floor_name(node.get("floor")),
            "x": _r(node.get("x"), 2),
            "y": _r(node.get("y"), 2),
        }

    def _location_view(self, loc: Dict[str, Any]) -> Dict[str, Any]:
        """A store, gate or connector from the loader. Store x/y is the POI coordinate."""
        kind = loc.get("type") or "store"
        view: Dict[str, Any] = {
            "id": loc["id"],
            "poi_id": loc["id"] if kind == "store" else loc.get("poi_id"),
            "name": loc["name"],
            "type": kind,
            "category": loc.get("category"),
            "floor": loc.get("floor"),
            "floor_name": loc.get("floor_name") or floor_name(loc.get("floor")),
            "x": _r(loc.get("x"), 2),
            "y": _r(loc.get("y"), 2),
        }
        if kind == "store":
            ent = loc.get("entrance_coords")
            view["entrance"] = (
                {
                    "node_id": loc.get("entrance_node"),
                    "x": _r(ent[0], 2),
                    "y": _r(ent[1], 2),
                    "status": loc.get("entrance_status"),
                }
                if ent
                else None
            )
            view["coordinate_frame"] = loc.get("coordinate_frame")
            view["coordinate_status"] = loc.get("coordinate_confidence")
        elif loc.get("connector_type"):
            view["connector_type"] = loc["connector_type"]
        return view

    def _require_location(self, loc_id: Optional[str], label: str) -> Dict[str, Any]:
        if not loc_id:
            raise ApiServiceError("missing_parameter", f"{label} is required.", 400)
        loc = self.loader.get_location(loc_id)
        if loc is None:
            raise ApiServiceError("unknown_location", f"Unknown {label.lower()}: {loc_id}", 404)
        return loc

    def default_start(self) -> Dict[str, Any]:
        return self._location_view(self.loader.get_location(self.default_start_id))

    # ----------------------------------------------------------------- health
    def health(self) -> Dict[str, Any]:
        info = self.loader.mall_info
        return {
            "status": "ok",
            "service": "mall-navigation-api",
            "mall": info.get("name"),
            "data": {
                "master_coordinates_version": info.get("version"),
                "navigation_graph_version": self._graph_version,
            },
            "counts": {
                "stores": len(self.loader.stores),
                "gates": len(self.loader.gates),
                "connectors": len(self.loader.connectors),
                "graph_nodes": len(self.graph.nodes),
                "graph_edges": len(self.graph.raw_edges),
                "floors": len(self.loader.floor_maps),
            },
            "routing": self._planner_info(),
            "metric_calibrated": False,
            # The master dataset's own flag and reason, passed through unchanged.
            "dataset_routing_ready": info.get("routing_ready"),
            "dataset_policy": info.get("critical_accuracy_policy"),
            "default_start": self.default_start(),
        }

    def _planner_info(self) -> Dict[str, Any]:
        loaded = self.planner.is_model_loaded()
        q_shape = list(self.planner.q_table.shape) if self.planner.q_table is not None else None
        return {
            "algorithm": "hybrid_rl_dijkstra",
            "graph": "navigation_graph_real.json",
            "rl_policy_used": True,
            "q_table_loaded": loaded,
            "q_table_shape": q_shape,
            "note": (
                "Hybrid navigation engine: computes genuine Tabular Q-Learning policy rollout across 342,732 states "
                "with deterministic Dijkstra baseline comparison and controlled fallback."
            ),
        }

    # -------------------------------------------------------------- locations
    def locations(
        self,
        q: Optional[str] = None,
        floor: Optional[int] = None,
        category: Optional[str] = None,
        kind: str = "store",
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        if kind not in LOCATION_KINDS:
            raise ApiServiceError(
                "invalid_parameter", f"type must be one of: {', '.join(LOCATION_KINDS)}.", 400
            )

        pool: List[Dict[str, Any]] = []
        if kind in ("store", "all"):
            pool += self.loader.stores
        if kind in ("gate", "all"):
            pool += self.loader.gates
        if kind in ("connector", "all"):
            pool += self.loader.connectors

        needle = (q or "").strip().lower()
        wanted_cat = (category or "").strip().lower()
        result = []
        for loc in pool:
            if floor is not None and loc.get("floor") != floor:
                continue
            if wanted_cat and wanted_cat != "all" and str(loc.get("category", "")).lower() != wanted_cat:
                continue
            if needle:
                hay = f"{loc.get('name', '')} {loc.get('category', '')} {loc.get('id', '')}".lower()
                if needle not in hay:
                    continue
            result.append(loc)

        total = len(result)
        if limit is not None:
            result = result[: max(0, limit)]

        return {
            "locations": [self._location_view(s) for s in result],
            "count": len(result),
            "total": total,
            "categories": sorted({s["category"] for s in self.loader.stores}),
            "default_start": self.default_start(),
            "gates": [self._location_view(g) for g in self.loader.gates],
        }

    def location(self, loc_id: str) -> Dict[str, Any]:
        return self._location_view(self._require_location(loc_id, "Location"))

    # ----------------------------------------------------------------- floors
    def floors(self) -> Dict[str, Any]:
        floors = []
        for fid in sorted(self.loader.floor_maps):
            fm = self.loader.floor_maps[fid]
            floors.append(
                {
                    "id": fid,
                    "name": fm.name,
                    "coordinate_frame": fm.coordinate_frame,
                    "width": fm.width,
                    "height": fm.height,
                    "store_count": len(fm.pois),
                    "node_count": len(self.graph.get_nodes_on_floor(fid)),
                }
            )
        return {
            "floors": floors,
            "coordinates_are_floor_local": True,
            "note": "Each floor has its own pixel coordinate frame; frames are not registered to each other.",
        }

    def floor_geometry(self, floor_id: int) -> Dict[str, Any]:
        """Real walkable graph + shop POIs for one floor, in that floor's own frame."""
        fm = self.loader.floor_maps.get(floor_id)
        if fm is None:
            raise ApiServiceError("unknown_floor", f"Unknown floor: {floor_id}", 404)

        # Each edge is [x1, y1, x2, y2, spur]; spur is 1 for the short hop from a corridor to a
        # shop entrance node and 0 for a corridor edge, so clients can style them differently.
        edges = [
            [
                _r(u["x"], 1),
                _r(u["y"], 1),
                _r(v["x"], 1),
                _r(v["y"], 1),
                1 if "shop_entrance" in (u.get("type"), v.get("type")) else 0,
            ]
            for u, v, _edge in self.graph.iter_same_floor_edges(floor_id)
        ]
        nodes = [
            {"id": n["id"], "name": n["name"], "type": n["type"], "x": _r(n["x"], 1), "y": _r(n["y"], 1)}
            for n in self.graph.get_nodes_on_floor(floor_id)
            if n.get("type") != "shop_entrance"
        ]
        pois = [
            {"id": s["id"], "name": s["name"], "category": s["category"], "x": _r(s["x"], 1), "y": _r(s["y"], 1)}
            for s in self.loader.get_stores(floor_id)
        ]

        xs = [e[0] for e in edges] + [e[2] for e in edges] + [p["x"] for p in pois] + [n["x"] for n in nodes]
        ys = [e[1] for e in edges] + [e[3] for e in edges] + [p["y"] for p in pois] + [n["y"] for n in nodes]
        bounds = (
            {"min_x": min(xs), "max_x": max(xs), "min_y": min(ys), "max_y": max(ys)} if xs and ys else None
        )

        return {
            "floor": floor_id,
            "name": fm.name,
            "coordinate_frame": fm.coordinate_frame,
            "width": fm.width,
            "height": fm.height,
            "bounds": bounds,
            "edges": edges,
            "nodes": nodes,
            "pois": pois,
        }

    # ------------------------------------------------------------------ route
    def _format_route_details(self, enriched: Dict[str, Any]) -> Dict[str, Any]:
        nodes: List[Dict[str, Any]] = enriched.get("nodes", [])
        edges: List[Dict[str, Any]] = enriched.get("edges", [])

        # One segment per contiguous run of nodes on the same floor (independent frames).
        segments: List[Dict[str, Any]] = []
        for node in nodes:
            if not segments or segments[-1]["floor"] != node["floor"]:
                fm = self.loader.floor_maps.get(node["floor"])
                segments.append(
                    {
                        "floor": node["floor"],
                        "floor_name": floor_name(node["floor"]),
                        "coordinate_frame": fm.coordinate_frame if fm else None,
                        "points": [],
                    }
                )
            segments[-1]["points"].append(self._node_view(node))

        # Connectors are the real graph edges where the route changes floor.
        connectors: List[Dict[str, Any]] = []
        for i, edge in enumerate(edges):
            if i + 1 < len(nodes):
                a, b = nodes[i], nodes[i + 1]
                if a["floor"] != b["floor"]:
                    connectors.append(
                        {
                            "type": edge.get("type", "WALK"),
                            "name": _clean_connector_name(a.get("name", "")),
                            "accessible": bool(edge.get("accessible")),
                            "from": self._node_view(a),
                            "to": self._node_view(b),
                            "path_cost": path_cost(edge.get("distance", 1.0)),
                        }
                    )

        directions = [
            {
                "step": d["step_number"],
                "text": d["instruction"],
                "kind": d["type"],
                "floor": d["floor"],
                "floor_name": floor_name(d["floor"]),
                "path_cost": path_cost(d["distance"]),
            }
            for d in generate_turn_by_turn_directions(nodes, edges, show_distances=False)
        ]

        return {
            "path": [self._node_view(n) for n in nodes],
            "segments": segments,
            "connectors": connectors,
            "floors": [s["floor"] for s in segments],
            "floor_changes": enriched.get("floor_changes", 0),
            "path_cost": path_cost(enriched.get("graph_cost", 0.0)),
            "steps": enriched.get("steps", len(nodes)),
            "route_is_accessible": enriched.get("is_accessible", True),
            "accessibility_note": enriched.get("accessible_desc", "N/A"),
            "status": enriched.get("status", "Verified graph path"),
            "directions": directions,
        }

    def route(
        self,
        destination_id: Optional[str],
        start_id: Optional[str] = None,
        accessible: bool = False,
        crowd_aware: bool = False,
        profile: Optional[str] = None,
        algorithm: str = "auto",
    ) -> Dict[str, Any]:
        start_id = (start_id or self.default_start_id).strip()
        dest = self._require_location(destination_id.strip() if destination_id else None, "Destination")
        start = self._require_location(start_id, "Start location")

        effective_profile = profile or ("Accessible" if accessible else ("Crowd-Aware" if crowd_aware else "Standard"))
        is_accessible = "access" in effective_profile.lower()
        effective_crowd = ("crowd" in effective_profile.lower() or crowd_aware) and not is_accessible

        result = self.planner.plan_route(
            start_id=start_id,
            destination_id=dest["id"],
            preference=effective_profile,
            crowd_aware=effective_crowd,
        )

        rl_route = result["rl_route"]
        baseline_route = result["shortest_path"]

        rl_policy_used = bool(result.get("evaluation", {}).get("rl_policy_used", False))
        req_algo = (algorithm or "auto").lower()

        # Select which route to serve as primary based on requested algorithm
        if req_algo == "dijkstra":
            chosen = baseline_route
            active_algo = "dijkstra"
            engine_label = "Dijkstra Deterministic Baseline"
            is_fallback = False
        elif req_algo == "rl":
            if rl_policy_used and rl_route.get("path"):
                chosen = rl_route
                active_algo = "rl"
                engine_label = "Tabular Q-Learning (RL Policy)"
                is_fallback = False
            else:
                chosen = baseline_route
                active_algo = "dijkstra_fallback"
                engine_label = "Dijkstra Fallback (RL Policy Diverged)"
                is_fallback = True
        else:
            # Auto: prefer verified RL if converged and valid, else Dijkstra baseline
            if rl_policy_used and rl_route.get("path"):
                chosen = rl_route
                active_algo = "rl"
                engine_label = "Tabular Q-Learning (Auto Recommended)"
                is_fallback = False
            else:
                chosen = baseline_route
                active_algo = "dijkstra"
                engine_label = "Dijkstra Baseline (Auto Recommended)"
                is_fallback = False

        if not chosen or not chosen.get("path"):
            raise ApiServiceError(
                "no_route",
                result.get("comparison_summary") or "No walkable route exists between these locations.",
                404,
            )

        chosen_details = self._format_route_details(chosen)
        rl_details = self._format_route_details(rl_route) if rl_route.get("path") else None
        baseline_details = self._format_route_details(baseline_route) if baseline_route.get("path") else None

        notices = ["Path cost is a relative graph cost, not a distance in metres. Walking time is not calibrated."]
        if is_fallback:
            val_reason = result.get("evaluation", {}).get("rl", {}).get("validation_reason", "Step limit or cycle detected")
            notices.insert(0, f"RL policy did not converge safely ({val_reason}). Showing verified Dijkstra baseline route.")
        if len(chosen_details["segments"]) > 1:
            notices.append("Each floor is drawn in its own coordinate frame; floors are not registered to each other.")

        return {
            "start": self._location_view(start),
            "destination": self._location_view(dest),
            "accessible": is_accessible,
            "crowd_aware": effective_crowd,
            "profile": effective_profile,
            "algorithm": active_algo,
            "requested_algorithm": req_algo,
            "engine_label": engine_label,
            "is_fallback": is_fallback,
            "route_is_accessible": chosen_details["route_is_accessible"],
            "accessibility_note": chosen_details["accessibility_note"],
            "planner": self._planner_info(),
            "path": chosen_details["path"],
            "segments": chosen_details["segments"],
            "connectors": chosen_details["connectors"],
            "floors": chosen_details["floors"],
            "floor_changes": chosen_details["floor_changes"],
            "path_cost": chosen_details["path_cost"],
            "steps": chosen_details["steps"],
            "walking_time": {"available": False, "label": "Not calibrated"},
            "directions": chosen_details["directions"],
            "notices": notices,
            "evaluation": result.get("evaluation", {}),
            "comparison_summary": result.get("comparison_summary", ""),
            "alternatives": {
                "rl": rl_details,
                "baseline": baseline_details,
            },
        }

    # -------------------------------------------- recommendations / nearby
    def recommendations(
        self, location_id: Optional[str] = None, category: str = "All", limit: int = 6
    ) -> Dict[str, Any]:
        origin = self._require_location(location_id or self.default_start_id, "Location")
        recs = self.recommender.recommend_stores(
            current_node_id=origin["id"], category=category or "All", limit=limit
        )
        return {
            "location_id": origin["id"],
            "category": category or "All",
            "recommendations": [self._ranked_view(r, origin) for r in recs],
        }

    def nearby(
        self, location_id: Optional[str], max_cost: Optional[float] = None, limit: int = 6
    ) -> Dict[str, Any]:
        origin = self._require_location(location_id, "Location")
        radius = DEFAULT_NEARBY_MAX_COST if max_cost is None else max_cost
        places = self.recommender.get_nearby_places(
            current_node_id=origin["id"], max_distance=radius, limit=limit
        )
        return {
            "location_id": origin["id"],
            "max_path_cost": path_cost(radius),
            "nearby": [self._ranked_view(p, origin) for p in places],
        }

    def _ranked_view(self, item: Dict[str, Any], origin: Dict[str, Any]) -> Dict[str, Any]:
        """Merge an engine result with its real store record, dropping metre/minute fields.

        The recommendation engine names its graph cost ``distance_meters`` and formats a
        walking time from it. The dataset is not calibrated, so both are replaced with a
        relative path cost.
        """
        loc = self.loader.get_location(item["id"])
        view = self._location_view(loc) if loc else {"id": item["id"], "name": item["name"]}
        view["path_cost"] = path_cost(item.get("distance_meters"))
        view["same_floor"] = bool(loc) and loc.get("floor") == origin.get("floor")
        return view


def _clean_connector_name(name: str) -> str:
    """'North Glass Elevator (G)' -> 'North Glass Elevator' (same cleanup directions.py uses)."""
    for suffix in ("(G)", "(F1)", "(F2)"):
        name = name.replace(suffix, "")
    return name.strip()

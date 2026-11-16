"""
Ambience Mall Gurugram: Real Map Data & Graph Topology Validator.

Performs data integrity and topological connectivity checks on:
- data/Ambience_Gurugram_Ground_First_Second_MASTER_Coordinates.json
- data/navigation_graph_real.json
"""

import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, List, Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MASTER_DATA_PATH = DATA_DIR / "Ambience_Gurugram_Ground_First_Second_MASTER_Coordinates.json"
REAL_GRAPH_PATH = DATA_DIR / "navigation_graph_real.json"


class MapValidator:
    """Validates spatial dataset integrity, shop entrance coverage, and graph connectivity."""

    def __init__(
        self,
        master_path: Path = MASTER_DATA_PATH,
        graph_path: Path = REAL_GRAPH_PATH,
    ):
        self.master_path = master_path
        self.graph_path = graph_path
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.stats: Dict[str, Any] = {}

    def run_all_checks(self) -> Dict[str, Any]:
        self.issues.clear()
        self.warnings.clear()
        self.stats.clear()

        # 1. Master JSON Schema Checks
        if not self.master_path.exists():
            self.issues.append(f"Master file missing: {self.master_path}")
            return self._build_report()

        with open(self.master_path, "r", encoding="utf-8") as f:
            master = json.load(f)

        total_pois = 0
        poi_ids = set()
        poi_names = set()
        duplicate_ids = []
        duplicate_names = []

        floors = master.get("floors", {})
        for floor_name, f_data in floors.items():
            for p in f_data.get("pois", []):
                total_pois += 1
                pid = p.get("id")
                name = p.get("name")

                # Missing checks
                if not pid:
                    self.issues.append(f"Missing ID for POI on {floor_name}")
                elif pid in poi_ids:
                    duplicate_ids.append(pid)
                else:
                    poi_ids.add(pid)

                if not name:
                    self.issues.append(f"Missing name for POI {pid}")
                elif name in poi_names:
                    duplicate_names.append(name)
                else:
                    poi_names.add(name)

                # Coordinate presence
                if floor_name == "Ground Floor":
                    if "x_px" not in p or "y_px" not in p:
                        self.issues.append(f"Ground POI {pid} missing x_px or y_px")
                elif floor_name == "First Floor":
                    if "map_x_px" not in p or "map_y_px" not in p:
                        self.issues.append(f"First Floor POI {pid} missing map_x_px or map_y_px")
                elif floor_name == "Second Floor":
                    if "representative_x_px" not in p or "representative_y_px" not in p:
                        self.issues.append(f"Second Floor POI {pid} missing representative coordinates")

        if duplicate_ids:
            self.issues.append(f"Duplicate shop IDs found: {duplicate_ids}")
        if duplicate_names:
            self.warnings.append(f"Multiple branches of same brand name found (allowed in real malls): {duplicate_names}")

        self.stats["total_master_pois"] = total_pois
        self.stats["unique_poi_ids"] = len(poi_ids)

        # 2. Navigation Graph Checks
        if not self.graph_path.exists():
            self.issues.append(f"Navigation graph file missing: {self.graph_path}")
            return self._build_report()

        with open(self.graph_path, "r", encoding="utf-8") as f:
            graph_data = json.load(f)

        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        node_dict = {n["id"]: n for n in nodes}
        adj = defaultdict(list)
        for e in edges:
            u, v = e.get("from"), e.get("to")
            if u not in node_dict:
                self.issues.append(f"Edge refers to non-existent source node: {u}")
            if v not in node_dict:
                self.issues.append(f"Edge refers to non-existent target node: {v}")
            if e.get("distance", 0) <= 0:
                self.issues.append(f"Edge ({u}, {v}) has non-positive distance: {e.get('distance')}")
            adj[u].append(v)
            adj[v].append(u)

        # Check for disconnected nodes (isolated vertices)
        isolated_nodes = [nid for nid in node_dict if len(adj[nid]) == 0]
        if isolated_nodes:
            self.issues.append(f"Isolated nodes with 0 connections found: {isolated_nodes}")

        # Check global graph connectivity via BFS
        if nodes:
            start_nid = nodes[0]["id"]
            visited = set()
            queue = deque([start_nid])
            visited.add(start_nid)

            while queue:
                curr = queue.popleft()
                for nxt in adj[curr]:
                    if nxt not in visited:
                        visited.add(nxt)
                        queue.append(nxt)

            unreachable = set(node_dict.keys()) - visited
            if unreachable:
                self.issues.append(f"{len(unreachable)} unreachable nodes found in navigation graph! Example: {list(unreachable)[:5]}")
            else:
                self.stats["graph_fully_connected"] = True

        # Check every shop POI has a walkable entrance node in the graph
        missing_entrances = []
        for pid in poi_ids:
            ent_id = f"ENT_{pid}"
            if ent_id not in node_dict:
                missing_entrances.append(pid)
        if missing_entrances:
            self.issues.append(f"{len(missing_entrances)} POIs have no entrance node in graph: {missing_entrances[:5]}")

        # Check floor transitions are only through valid connectors
        invalid_floor_jumps = []
        for e in edges:
            u, v = e["from"], e["to"]
            if u in node_dict and v in node_dict:
                flr_u = node_dict[u]["floor"]
                flr_v = node_dict[v]["floor"]
                if flr_u != flr_v:
                    etype = e.get("type", "")
                    if etype not in ["ELEVATOR", "ESCALATOR", "STAIRS"]:
                        invalid_floor_jumps.append((u, v, etype))
        if invalid_floor_jumps:
            self.issues.append(f"Invalid floor change without vertical connector: {invalid_floor_jumps}")

        self.stats["total_graph_nodes"] = len(nodes)
        self.stats["total_graph_edges"] = len(edges)
        self.stats["ground_nodes"] = sum(1 for n in nodes if n.get("floor") == 0)
        self.stats["first_floor_nodes"] = sum(1 for n in nodes if n.get("floor") == 1)
        self.stats["second_floor_nodes"] = sum(1 for n in nodes if n.get("floor") == 2)

        return self._build_report()

    def _build_report(self) -> Dict[str, Any]:
        return {
            "passed": len(self.issues) == 0,
            "issues": self.issues,
            "warnings": self.warnings,
            "stats": self.stats,
        }

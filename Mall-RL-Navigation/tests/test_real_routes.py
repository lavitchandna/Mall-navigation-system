"""
Automated Route Validation Suite for Ambience Mall Gurugram.

Validates:
- Single-floor navigation (Ground, First, Second)
- All 6 pairs of multi-floor navigation (Ground <-> First <-> Second)
- Wheelchair accessible routes (zero stairs, zero escalators)
- Physical validity: no teleportation, valid connector transitions, positive distances
"""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.navigation_graph import get_navigation_graph
from src.real_map_loader import get_real_map_loader


class TestRealRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = get_navigation_graph()
        cls.loader = get_real_map_loader()

    def _verify_route_validity(self, route_result, expected_start, expected_dest, accessible_only=False):
        self.assertIsNotNone(route_result, f"Route from {expected_start} to {expected_dest} was None")
        self.assertTrue(route_result["success"], "Route marked as not successful")

        path = route_result["path"]
        nodes = route_result["nodes"]
        edges = route_result["edges"]

        self.assertGreaterEqual(len(path), 1, "Path has no nodes")
        resolved_start = self.graph.resolve_node_id(expected_start)
        resolved_dest = self.graph.resolve_node_id(expected_dest)
        self.assertEqual(path[0], resolved_start, f"Path start {path[0]} does not match {resolved_start}")
        self.assertEqual(path[-1], resolved_dest, f"Path end {path[-1]} does not match {resolved_dest}")

        # Positive distances
        self.assertGreater(route_result["total_distance"], 0.0, "Total distance must be positive")

        # Verify edge continuity and valid connector usage
        for i in range(len(edges)):
            u_node = nodes[i]
            v_node = nodes[i+1]
            e = edges[i]

            self.assertIn(u_node.get("floor"), [0, 1, 2], "Node floor must be 0, 1, or 2")
            self.assertIn(v_node.get("floor"), [0, 1, 2], "Node floor must be 0, 1, or 2")

            if u_node.get("floor") != v_node.get("floor"):
                self.assertIn(e["type"], ["ELEVATOR", "ESCALATOR", "STAIRS"],
                              f"Floor change from {u_node['name']} to {v_node['name']} used invalid edge type {e['type']}")

            if accessible_only:
                self.assertNotIn(e["type"], ["STAIRS", "ESCALATOR"],
                                 f"Accessible route contained prohibited edge type {e['type']}")

    def test_01_ground_to_ground(self):
        # Gate 1 to Zara
        res = self.graph.find_shortest_path("G_GATE_1", "G_005")
        self._verify_route_validity(res, "G_GATE_1", "G_005")

    def test_02_ground_to_ground_long_spine(self):
        # Zara to UNIQLO
        res = self.graph.find_shortest_path("G_005", "G_072")
        self._verify_route_validity(res, "G_005", "G_072")

    def test_03_first_to_first(self):
        # Asics to Hamley's
        res = self.graph.find_shortest_path("F1_001", "F1_004")
        self._verify_route_validity(res, "F1_001", "F1_004")

    def test_04_second_to_second(self):
        # Croma to Reliance Digital
        res = self.graph.find_shortest_path("F2_CROMA", "F2_RELIANCEDIGITAL")
        self._verify_route_validity(res, "F2_CROMA", "F2_RELIANCEDIGITAL")

    def test_05_ground_to_first(self):
        # Gate 1 to Hamley's
        res = self.graph.find_shortest_path("G_GATE_1", "F1_004")
        self._verify_route_validity(res, "G_GATE_1", "F1_004")

    def test_06_first_to_ground(self):
        # Nike to Gate 3
        res = self.graph.find_shortest_path("F1_009", "G_GATE_3")
        self._verify_route_validity(res, "F1_009", "G_GATE_3")

    def test_07_ground_to_second(self):
        # Gate 1 to Croma
        res = self.graph.find_shortest_path("G_GATE_1", "F2_CROMA")
        self._verify_route_validity(res, "G_GATE_1", "F2_CROMA")

    def test_08_second_to_ground(self):
        # Lenovo to Paul's Bakery
        res = self.graph.find_shortest_path("F2_LENOVO", "G_001")
        self._verify_route_validity(res, "F2_LENOVO", "G_001")

    def test_09_first_to_second(self):
        # Puma to Soch
        res = self.graph.find_shortest_path("F1_012", "F2_SOCH")
        self._verify_route_validity(res, "F1_012", "F2_SOCH")

    def test_10_second_to_first(self):
        # Fab India to Marks & Spencer
        res = self.graph.find_shortest_path("F2_FABINDIA", "F1_059")
        self._verify_route_validity(res, "F2_FABINDIA", "F1_059")

    def test_11_wheelchair_accessible_elevator_only(self):
        # Gate 1 to Second Floor Croma in accessible mode
        res = self.graph.find_shortest_path("G_GATE_1", "F2_CROMA", accessible_only=True)
        self._verify_route_validity(res, "G_GATE_1", "F2_CROMA", accessible_only=True)

    def test_12_accessible_multi_floor_reverse(self):
        # Second Floor Reliance Digital to Ground Floor UNIQLO in accessible mode
        res = self.graph.find_shortest_path("F2_RELIANCEDIGITAL", "G_072", accessible_only=True)
        self._verify_route_validity(res, "F2_RELIANCEDIGITAL", "G_072", accessible_only=True)


if __name__ == "__main__":
    unittest.main()

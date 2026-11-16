"""
Tests for the Flask API (api.py + src/api_service.py).

Run from the project root:
    python -m unittest tests/test_api.py -v

The data cross-checks read the raw JSON files directly (not through the loaders) so they
verify that API payloads really come from the real dataset and nothing is fabricated.
"""

import itertools
import json
import re
import sys
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api import create_app  # noqa: E402
from src.api_service import MallService  # noqa: E402

DATA_DIR = PROJECT_ROOT / "data"
MASTER = json.loads((DATA_DIR / "Ambience_Gurugram_Ground_First_Second_MASTER_Coordinates.json").read_text("utf-8"))
GRAPH = json.loads((DATA_DIR / "navigation_graph_real.json").read_text("utf-8"))

FLOOR_FIELDS = {
    "Ground Floor": ("x_px", "y_px"),
    "First Floor": ("map_x_px", "map_y_px"),
    "Second Floor": ("representative_x_px", "representative_y_px"),
}
NODES = {n["id"]: n for n in GRAPH["nodes"]}
EDGES = {}
for _e in GRAPH["edges"]:
    EDGES[(_e["from"], _e["to"])] = _e
    EDGES[(_e["to"], _e["from"])] = _e

METRIC_TEXT = re.compile(r"\b\d+(\.\d+)?\s*(m|km|meters?|metres?|min|mins|minutes?|sec|seconds?)\b", re.I)
VERTICAL = {"ELEVATOR", "ESCALATOR", "STAIRS"}


def master_pois():
    pois = {}
    for floor_name, fields in FLOOR_FIELDS.items():
        for p in MASTER["floors"][floor_name]["pois"]:
            pois[p["id"]] = (floor_name, p[fields[0]], p[fields[1]], p["name"])
    return pois


def walk_keys(obj, path=""):
    """Yield (path, key) for every dict key in a nested payload."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield f"{path}/{k}", k
            yield from walk_keys(v, f"{path}/{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_keys(v, f"{path}[{i}]")


class ApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()
        cls.pois = master_pois()

    def get(self, url, status=200):
        r = self.client.get(url)
        self.assertEqual(r.status_code, status, r.get_data(as_text=True)[:300])
        return r.get_json()

    def route(self, dest, start=None, accessible=False, status=200):
        body = {"destination_location_id": dest, "accessible": accessible}
        if start:
            body["start_location_id"] = start
        r = self.client.post("/api/route", json=body)
        self.assertEqual(r.status_code, status, r.get_data(as_text=True)[:300])
        return r.get_json()

    def assert_valid_route(self, route, start_id, dest_id, accessible=False):
        path = route["path"]
        # 1. Every consecutive pair is a real edge of the real graph.
        for a, b in zip(path, path[1:]):
            self.assertIn((a["id"], b["id"]), EDGES, f"{a['id']} -> {b['id']} is not an edge of the real graph")
            if accessible:
                self.assertNotIn(EDGES[(a["id"], b["id"])]["type"], ("STAIRS", "ESCALATOR"))
        # 2. Endpoints. The route ends at the destination's real entrance node.
        self.assertEqual(path[-1]["id"], f"ENT_{dest_id}")
        # 3. Node coordinates are exactly the graph's coordinates.
        for p in path:
            self.assertEqual((p["x"], p["y"]), (round(NODES[p["id"]]["x"], 2), round(NODES[p["id"]]["y"], 2)))
            self.assertEqual(p["floor"], NODES[p["id"]]["floor"])
        # 4. Segments partition the path in order, one per contiguous floor run.
        flat = [pt["id"] for seg in route["segments"] for pt in seg["points"]]
        self.assertEqual(flat, [p["id"] for p in path])
        for seg in route["segments"]:
            self.assertTrue(all(pt["floor"] == seg["floor"] for pt in seg["points"]))
        for s1, s2 in zip(route["segments"], route["segments"][1:]):
            self.assertNotEqual(s1["floor"], s2["floor"])
        self.assertEqual(route["floors"], [s["floor"] for s in route["segments"]])
        # 5. Connectors are exactly the real vertical edges on the path (nothing fabricated).
        expected = [(a, b) for a, b in zip(path, path[1:]) if a["floor"] != b["floor"]]
        self.assertEqual(len(route["connectors"]), len(expected))
        self.assertEqual(route["floor_changes"], len(expected))
        for c, (a, b) in zip(route["connectors"], expected):
            self.assertEqual((c["from"]["id"], c["to"]["id"]), (a["id"], b["id"]))
            self.assertIn(c["type"], VERTICAL)
            self.assertEqual(c["type"], EDGES[(a["id"], b["id"])]["type"])
        # 6. Destination marker uses the master file's POI coordinates.
        _, x, y, name = self.pois[dest_id]
        self.assertEqual((route["destination"]["x"], route["destination"]["y"]), (round(x, 2), round(y, 2)))
        self.assertEqual(route["destination"]["name"], name)
        # 7. No metres / minutes anywhere.
        keys = [k for _, k in walk_keys(route)]
        self.assertFalse([k for k in keys if "meter" in k.lower() or k in ("time_seconds", "time_str", "distance_str")])
        for d in route["directions"]:
            self.assertIsNone(METRIC_TEXT.search(d["text"]), d["text"])
        self.assertFalse(route["path_cost"]["calibrated"])
        self.assertEqual(route["path_cost"]["unit"], "relative")
        self.assertFalse(route["walking_time"]["available"])
        # 8. Directions are present and framed by a start and an arrival.
        self.assertGreaterEqual(len(route["directions"]), 1)
        if len(path) > 1:
            self.assertEqual(route["directions"][0]["kind"], "start")
            self.assertEqual(route["directions"][-1]["kind"], "arrival")


class TestHealthAndData(ApiTestCase):
    def test_health(self):
        h = self.get("/api/health")
        self.assertEqual(h["status"], "ok")
        self.assertEqual(h["counts"]["stores"], len(self.pois))
        self.assertEqual(h["counts"]["graph_nodes"], len(GRAPH["nodes"]))
        self.assertEqual(h["counts"]["graph_edges"], len(GRAPH["edges"]))
        self.assertEqual(h["default_start"]["id"], "G_GATE_1")

    def test_health_reports_dataset_policy_and_runtime_planner_honestly(self):
        h = self.get("/api/health")
        self.assertEqual(h["dataset_routing_ready"], MASTER["critical_accuracy_policy"]["routing_ready"])
        self.assertFalse(h["metric_calibrated"])
        self.assertEqual(h["routing"]["algorithm"], "dijkstra")
        self.assertFalse(h["routing"]["rl_policy_used"])

    def test_locations_are_exactly_the_master_pois(self):
        d = self.get("/api/locations")
        self.assertEqual({loc["id"] for loc in d["locations"]}, set(self.pois))
        self.assertEqual(d["total"], 221)

    def test_location_coordinates_come_from_master_file(self):
        for loc in self.get("/api/locations")["locations"]:
            floor_name, x, y, name = self.pois[loc["id"]]
            self.assertEqual(loc["floor_name"], floor_name)
            self.assertEqual(loc["name"], name)
            self.assertEqual((loc["x"], loc["y"]), (round(x, 2), round(y, 2)))
            self.assertEqual(loc["entrance"]["node_id"], f"ENT_{loc['id']}")

    def test_filters(self):
        self.assertEqual([l["id"] for l in self.get("/api/locations?q=zara")["locations"]], ["G_005"])
        self.assertTrue(all(l["floor"] == 2 for l in self.get("/api/locations?floor=Second%20Floor")["locations"]))
        self.assertEqual(self.get("/api/locations?floor=1")["total"], 59)
        self.assertEqual(self.get("/api/locations?limit=3")["count"], 3)
        self.assertEqual([g["id"] for g in self.get("/api/locations?type=gate")["locations"]][:1], ["G_GATE_1"])

    def test_location_detail(self):
        z = self.get("/api/locations/G_005")
        self.assertEqual((z["name"], z["floor_name"]), ("ZARA", "Ground Floor"))
        self.get("/api/locations/NOPE", 404)

    def test_floors(self):
        f = self.get("/api/floors")["floors"]
        self.assertEqual([x["name"] for x in f], ["Ground Floor", "First Floor", "Second Floor"])
        self.assertEqual([x["store_count"] for x in f], [72, 59, 90])

    def test_floor_geometry_matches_graph_and_never_crosses_floors(self):
        for fid in (0, 1, 2):
            g = self.get(f"/api/floors/{fid}/geometry")
            floor_nodes = {n["id"] for n in GRAPH["nodes"] if n["floor"] == fid}
            expected = {
                tuple(sorted(((NODES[e["from"]]["x"], NODES[e["from"]]["y"]), (NODES[e["to"]]["x"], NODES[e["to"]]["y"]))))
                for e in GRAPH["edges"]
                if e["from"] in floor_nodes and e["to"] in floor_nodes
            }
            got = {tuple(sorted(((round(a, 1), round(b, 1)), (round(c, 1), round(d, 1))))) for a, b, c, d, _spur in g["edges"]}
            self.assertEqual(len(g["edges"]), len(expected))
            self.assertEqual(len(got), len(expected))
            b = g["bounds"]
            for x1, y1, x2, y2, _spur in g["edges"]:
                self.assertTrue(b["min_x"] <= x1 <= b["max_x"] and b["min_y"] <= y1 <= b["max_y"])
            self.assertEqual(len(g["pois"]), sum(1 for p in self.pois.values() if p[0] == g["name"]))
            # spur flag: exactly the edges that touch a shop entrance node
            spurs = sum(
                1
                for e in GRAPH["edges"]
                if e["from"] in floor_nodes and e["to"] in floor_nodes
                and "shop_entrance" in (NODES[e["from"]]["type"], NODES[e["to"]]["type"])
            )
            self.assertEqual(sum(e[4] for e in g["edges"]), spurs)
        self.get("/api/floors/7/geometry", 404)


class TestRoutes(ApiTestCase):
    def test_same_floor_route(self):
        r = self.route("G_005")
        self.assert_valid_route(r, "G_GATE_1", "G_005")
        self.assertEqual(r["floors"], [0])
        self.assertEqual(r["connectors"], [])
        self.assertEqual(r["start"]["id"], "G_GATE_1")

    def test_all_multi_floor_pairs(self):
        cases = {
            (0, 1): ("G_GATE_1", "F1_004"),
            (0, 2): ("G_GATE_1", "F2_CROMA"),
            (1, 0): ("F1_009", "G_072"),
            (1, 2): ("F1_012", "F2_SOCH"),
            (2, 0): ("F2_LENOVO", "G_001"),
            (2, 1): ("F2_FABINDIA", "F1_059"),
        }
        for (a, b), (start, dest) in cases.items():
            with self.subTest(route=f"{a}->{b}"):
                r = self.route(dest, start)
                self.assert_valid_route(r, start, dest)
                self.assertEqual(r["floors"][0], a)
                self.assertEqual(r["floors"][-1], b)
                self.assertGreaterEqual(r["floor_changes"], 1)

    def test_accessible_routes_never_use_stairs_or_escalators(self):
        for start, dest in [("G_GATE_1", "F2_CROMA"), ("F2_RELIANCEDIGITAL", "G_072"), ("G_GATE_3", "F1_004")]:
            with self.subTest(route=f"{start}->{dest}"):
                r = self.route(dest, start, accessible=True)
                self.assert_valid_route(r, start, dest, accessible=True)
                self.assertTrue(all(c["type"] == "ELEVATOR" and c["accessible"] for c in r["connectors"]))
                self.assertTrue(r["route_is_accessible"])

    def test_accessible_flag_reaches_the_planner(self):
        svc = MallService()
        real = svc.planner.plan_route
        with mock.patch.object(svc.planner, "plan_route", wraps=real) as spy:
            svc.route("F2_CROMA", accessible=True)
            self.assertEqual(spy.call_args.kwargs["preference"], "Accessible")
            svc.route("F2_CROMA", accessible=False)
            self.assertEqual(spy.call_args.kwargs["preference"], "Standard")

    def test_every_gate_reaches_a_sample_of_stores_on_every_floor(self):
        gates = self.get("/api/locations?type=gate")["locations"]
        stores = self.get("/api/locations")["locations"]
        sample = [s for fl in (0, 1, 2) for s in [x for x in stores if x["floor"] == fl][::12]]
        for g, s in itertools.product(gates, sample):
            r = self.route(s["id"], g["id"])
            self.assert_valid_route(r, g["id"], s["id"])

    def test_start_can_be_a_store(self):
        r = self.route("G_001", "F2_LENOVO")
        self.assertEqual(r["start"]["id"], "F2_LENOVO")
        self.assertEqual(r["path"][0]["id"], "ENT_F2_LENOVO")

    def test_already_there(self):
        r = self.route("G_005", "G_005")
        self.assertEqual(r["path_cost"]["value"], 0.0)
        self.assertIn("already at", r["directions"][0]["text"])

    def test_route_errors(self):
        self.assertEqual(self.route("NOPE", status=404)["error"]["code"], "unknown_location")
        self.assertEqual(self.route("G_005", "ZZZ", status=404)["error"]["code"], "unknown_location")
        self.assertEqual(self.client.post("/api/route", json={}).status_code, 400)
        self.assertEqual(self.client.post("/api/route", data="x", content_type="application/json").status_code, 400)
        self.assertEqual(self.client.post("/api/route", json={"destination_location_id": 5}).status_code, 400)
        self.assertEqual(self.client.put("/api/route").status_code, 405)

    def test_runtime_planner_is_dijkstra_and_ignores_the_q_table(self):
        """Documents the real runtime behaviour: the Q-table is loaded but never consulted."""
        svc = MallService()
        baseline = svc.route("F2_CROMA")["path"]
        original = svc.planner.q_table
        try:
            for replacement in (None, np.random.default_rng(0).normal(size=(7500, 6)), np.zeros((3, 3))):
                svc.planner.q_table = replacement
                self.assertEqual(svc.route("F2_CROMA")["path"], baseline)
        finally:
            svc.planner.q_table = original
        self.assertFalse(svc.route("G_005")["planner"]["rl_policy_used"])


class TestNearbyAndRecommendations(ApiTestCase):
    def test_nearby(self):
        d = self.get("/api/nearby?location_id=G_005")
        self.assertTrue(d["nearby"])
        costs = [n["path_cost"]["value"] for n in d["nearby"]]
        self.assertEqual(costs, sorted(costs))
        self.assertTrue(all(n["id"] in self.pois and n["id"] != "G_005" for n in d["nearby"]))
        self.assertTrue(all(c <= d["max_path_cost"]["value"] for c in costs))
        keys = [k for _, k in walk_keys(d)]
        self.assertFalse([k for k in keys if "meter" in k.lower() or k in ("time_seconds", "time_str", "distance_str")])

    def test_nearby_validation(self):
        self.get("/api/nearby", 400)
        self.get("/api/nearby?location_id=NOPE", 404)
        self.get("/api/nearby?location_id=G_005&limit=x", 400)
        self.get("/api/nearby?location_id=G_005&max_cost=-1", 400)

    def test_recommendations_default_to_configured_start(self):
        d = self.get("/api/recommendations")
        self.assertEqual(d["location_id"], "G_GATE_1")
        self.assertEqual(len(d["recommendations"]), 6)
        costs = [r["path_cost"]["value"] for r in d["recommendations"]]
        self.assertEqual(costs, sorted(costs))
        self.assertTrue(all(r["id"] in self.pois for r in d["recommendations"]))

    def test_recommendations_category_filter(self):
        d = self.get("/api/recommendations?location_id=G_GATE_3&category=Electronics&limit=3")
        self.assertTrue(d["recommendations"])
        self.assertTrue(all("electronics" in r["category"].lower() for r in d["recommendations"]))


class TestPlumbing(ApiTestCase):
    def test_cors_headers(self):
        r = self.client.options(
            "/api/route",
            headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["Access-Control-Allow-Origin"], "*")
        self.assertIn("POST", r.headers["Access-Control-Allow-Methods"])

    def test_unknown_endpoint_is_json(self):
        r = self.client.get("/api/nope")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.get_json()["error"]["code"], "not_found")

    def test_invalid_configured_start_fails_fast(self):
        with self.assertRaises(ValueError):
            MallService(default_start_id="NOT_A_LOCATION")


if __name__ == "__main__":
    unittest.main()

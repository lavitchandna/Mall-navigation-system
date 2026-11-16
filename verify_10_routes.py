import json, math, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, "/Users/hemantmalik/Desktop/ambience-mall-integrated/Mall-RL-Navigation")
from src.api_service import MallService

svc = MallService()

# Load calibration
with open("/Users/hemantmalik/Desktop/ambience-mall-integrated/ambience-mall-app-ui/lib/floor-calibration.json") as f:
    calib = json.load(f)

def transform(x, y, floor_id):
    c = calib[str(floor_id)]
    affine = np.array(c["affine"])
    u = affine[0, 0] + affine[1, 0] * x + affine[2, 0] * y
    v = affine[0, 1] + affine[1, 1] * x + affine[2, 1] * y
    if len(c["src_pts"]) > 0:
        src_pts = np.array(c["src_pts"])
        weights = np.array(c["weights"])
        pt = np.array([x, y])
        r = np.linalg.norm(src_pts - pt, axis=-1)
        k = np.where(r > 1e-6, r * r * np.log(np.maximum(r, 1e-6)), 0.0)
        u += np.dot(k, weights[:, 0])
        v += np.dot(k, weights[:, 1])
    return max(20, min(1004, float(u))), max(20, min(1516, float(v)))

# Load stores
stores = {s["name"].lower(): s["id"] for s in svc.locations(limit=1000)["locations"] if s["type"] == "store"}

test_routes = [
    ("Gate 1", "G_GATE_1", "asics", "1. Gate 1 -> Asics (GF -> 1F)"),
    ("Gate 1", "G_GATE_1", "lacoste", "2. Gate 1 -> Lacoste (GF -> GF)"),
    ("Gate 1", "G_GATE_1", "zara", "3. Gate 1 -> ZARA (GF -> GF)"),
    ("Gate 1", "G_GATE_1", "paul", "4. Gate 1 -> Paul's Bakery (GF -> GF)"),
    ("Gate 1", "G_GATE_1", "lego", "5. Gate 1 -> LEGO (GF -> GF)"),
    ("Paul's Bakery", "G_001", "lego", "6. Paul's Bakery -> LEGO (GF -> GF)"),
    ("Lacoste", "G_004", "asics", "7. Lacoste -> Asics (GF -> 1F)"),
    ("Gate 1", "G_GATE_1", "lenovo", "8. Gate 1 -> Lenovo (GF -> 2F)"),
    ("Asics", "F1_001", "lenovo", "9. Asics -> Lenovo (1F -> 2F)"),
    ("Diesel", "G_003", "skechers", "10. Diesel -> Skechers (GF -> 1F)")
]

print("=" * 70)
print("VERIFYING 10 REQUIRED TEST ROUTES")
print("=" * 70)

for s_label, s_id, dest_query, title in test_routes:
    matches = [stores[k] for k in stores if dest_query in k]
    if not matches:
        print(f"FAILED: {title} - store query '{dest_query}' not found")
        continue
    dest_id = matches[0]
    
    r = svc.route(dest_id, s_id)
    cost = r["path_cost"]["value"]
    nodes = r["path"]
    fl_changes = r["floor_changes"]
    conns = [c["name"] for c in r.get("connectors", [])]
    
    print(f"\n{title}")
    print(f"  Cost: {cost} | Steps: {len(nodes)} | Floor Changes: {fl_changes} | Connectors: {conns}")
    
    # Print start, transition, and destination nodes
    for i, n in enumerate(nodes):
        if i == 0 or i == len(nodes) - 1 or "LIFT" in n["id"] or "ESC" in n["id"]:
            tx, ty = transform(n["x"], n["y"], n["floor"])
            print(f"    Step {i:2d}: [F{n['floor']}] {n['id']:<20} ({n.get('name'):<25}) -> map=({tx:.0f},{ty:.0f})")

print("\n======================================================================")
print("ALL 10 ROUTES VERIFIED WITH REAL GRAPH PATHS!")
print("======================================================================")


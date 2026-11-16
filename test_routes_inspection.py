import sys
from pathlib import Path
sys.path.insert(0, "/Users/hemantmalik/Desktop/ambience-mall-integrated/Mall-RL-Navigation")
from src.api_service import MallService

svc = MallService()

stores = {s["name"].lower(): s["id"] for s in svc.locations(limit=1000)["locations"] if s["type"] == "store"}
print(f"Loaded {len(stores)} stores.")

def analyze_route(start_id, dest_query):
    matches = [stores[k] for k in stores if dest_query.lower() in k]
    if not matches:
        print(f"Store '{dest_query}' not found!")
        return
    dest_id = matches[0]
    r = svc.route(dest_id, start_id)
    start_name = r["start"]["name"]
    dest_name = r["destination"]["name"]
    dest_floor = r["destination"]["floor_name"]
    cost = r["path_cost"]["value"]
    path_nodes = r["path"]
    print("=" * 65)
    print(f"ROUTE: {start_name} -> {dest_name} ({dest_floor})")
    print(f"Cost: {cost}, Steps: {len(path_nodes)}, Floor changes: {r['floor_changes']}")
    print("Connectors traversed:", [c["name"] for c in r.get("connectors", [])])
    print("Node sequence:")
    for idx, n in enumerate(path_nodes):
        print(f"  {idx:2d}. [F{n['floor']}] {n['id']:<18} ({n.get('name', ''):<20}) ({n.get('x', 0):.1f}, {n.get('y', 0):.1f})")

print("--- TEST 1: Gate 1 -> Lacoste ---")
analyze_route("G_GATE_1", "lacoste")

print("--- TEST 2: Gate 1 -> Asics ---")
analyze_route("G_GATE_1", "asics")

print("--- TEST 3: Gate 1 -> H&M ---")
analyze_route("G_GATE_1", "h&m")

print("--- TEST 4: Gate 1 -> Paul's Bakery ---")
analyze_route("G_GATE_1", "paul")

print("--- TEST 5: Gate 1 -> LEGO ---")
analyze_route("G_GATE_1", "lego")


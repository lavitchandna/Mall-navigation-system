import json
from src.navigation_graph import get_navigation_graph
from src.route_planner import get_route_planner
from src.real_map_loader import get_real_map_loader

graph = get_navigation_graph()
loader = get_real_map_loader()
planner = get_route_planner()

dest_id = "G_002"
print(f"Target: {dest_id} - Onitsuka Tiger (Floor 0)")

print("\n=== TESTING ALL GATES TO ONITSUKA TIGER ===")
for g in loader.gates:
    start_id = g["id"]
    res = planner.plan_route(start_id, dest_id)
    dijk = res.get("shortest_path", {})
    rl = res.get("rl_route", {})
    d_floors = [n["floor"] for n in dijk.get("nodes", [])]
    r_floors = [n["floor"] for n in rl.get("nodes", [])]
    print(f"Gate {start_id} ({g.get('name')}):")
    print(f"  Dijkstra floors: {d_floors}")
    print(f"  RL floors:       {r_floors}")
    if set(d_floors) != {0} or set(r_floors) != {0}:
        print(f"  *** UNNECESSARY FLOOR CHANGE DETECTED! ***")
        print(f"  Dijkstra path: {dijk.get('path')}")
        print(f"  RL path:       {rl.get('path')}")

print("\n=== TESTING OTHER GROUND FLOOR STORES TO ONITSUKA TIGER ===")
gf_stores = [s for s in loader.stores if s.get("floor") == 0]
bad_cases = []
for s in gf_stores:
    start_id = s["id"]
    if start_id == dest_id:
        continue
    res = planner.plan_route(start_id, dest_id)
    dijk = res.get("shortest_path", {})
    rl = res.get("rl_route", {})
    d_floors = [n["floor"] for n in dijk.get("nodes", [])]
    r_floors = [n["floor"] for n in rl.get("nodes", [])]
    if set(d_floors) != {0} or set(r_floors) != {0}:
        bad_cases.append((start_id, s.get("name"), d_floors, r_floors, dijk.get("path"), rl.get("path")))

print(f"Total GF stores tested: {len(gf_stores)}")
print(f"Found {len(bad_cases)} cases with floor transitions for same-floor routing!")
for b in bad_cases[:10]:
    print(f"\nStore {b[0]} ({b[1]}):")
    print(f"  Dijkstra floors: {b[2]} | path: {b[4]}")
    print(f"  RL floors:       {b[3]} | path: {b[5]}")

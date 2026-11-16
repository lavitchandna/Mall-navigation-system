import sys, math
from pathlib import Path
sys.path.insert(0, "/Users/hemantmalik/Desktop/ambience-mall-integrated/Mall-RL-Navigation")
from src.navigation_graph import NavigationGraph

graph = NavigationGraph()

print("Graph loaded:", len(graph.nodes), "nodes,", len(graph.raw_edges), "edges.")

# Test pairs:
# 1. Gate 1 -> Asics (F0 -> F1)
# 2. Gate 1 -> Lacoste (F0 -> F0)
# 3. Gate 1 -> ZARA (F0 -> F0)
# 4. Gate 1 -> Paul's Bakery (F0 -> F0)
# 5. Gate 1 -> LEGO (F0 -> F0)
# 6. F0 store -> F0 store (e.g. Paul's -> LEGO)
# 7. F0 -> F1 (e.g. ZARA -> Asics)
# 8. F0 -> F2 (e.g. Gate 1 -> Hamleys/Lenovo/Chicco)
# 9. F1 -> F2 (e.g. Asics -> Lenovo)
# 10. Store -> Store (e.g. Diesel -> Skechers)

pairs = [
    ("G_GATE_1", "ENT_F1_001", "Gate 1 -> Asics (F0->F1)"),
    ("G_GATE_1", "ENT_G_004", "Gate 1 -> Lacoste (F0->F0)"),
    ("G_GATE_1", "ENT_G_005", "Gate 1 -> ZARA (F0->F0)"),
    ("G_GATE_1", "ENT_G_001", "Gate 1 -> Paul's Bakery (F0->F0)"),
    ("G_GATE_1", "ENT_G_059", "Gate 1 -> LEGO (F0->F0)"),
    ("ENT_G_001", "ENT_G_059", "Paul's Bakery -> LEGO (F0->F0)"),
    ("ENT_G_005", "ENT_F1_001", "ZARA -> Asics (F0->F1)"),
    ("G_GATE_1", "ENT_F2_LENOVO", "Gate 1 -> Lenovo (F0->F2)"),
    ("ENT_F1_001", "ENT_F2_LENOVO", "Asics -> Lenovo (F1->F2)"),
    ("ENT_G_003", "ENT_F1_016", "Diesel -> Skechers (F0->F1)")
]

for s, g, desc in pairs:
    res = graph.find_shortest_path(s, g)
    if not res:
        print(f"FAILED: {desc} - No path found!")
        continue
    path = res["path"]
    cost = res["cost"]
    nodes = [graph.get_node(n) for n in path]
    
    # Check floor changes and connectors
    floors = [n["floor"] for n in nodes]
    connectors = [n["id"] for n in nodes if any(k in n["id"] for k in ["LIFT", "ESC", "STAIR"])]
    
    # Check for loops (visited same node more than once)
    has_dup = len(path) != len(set(path))
    
    # Check if path oscillates in y (going forward then backward then forward)
    # on each floor
    oscillations = 0
    by_floor = {}
    for n in nodes:
        by_floor.setdefault(n["floor"], []).append(n)
    
    print(f"\n[{desc}]")
    print(f"  Cost: {cost}, Steps: {len(path)}, Connectors: {connectors}, Duplicates: {has_dup}")
    for fl, fl_nodes in by_floor.items():
        y_vals = [round(n["y"], 1) for n in fl_nodes]
        print(f"  Floor {fl} y-progression ({len(fl_nodes)} nodes): {y_vals[:4]} ... {y_vals[-4:] if len(y_vals)>4 else ''}")


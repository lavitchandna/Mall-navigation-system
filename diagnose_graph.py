import json, math
from pathlib import Path

path = Path("/Users/hemantmalik/Desktop/ambience-mall-integrated/Mall-RL-Navigation/data/navigation_graph_real.json")
with open(path) as f:
    data = json.load(f)

nodes = {n["id"]: n for n in data["nodes"]}
edges = data["edges"]

print("=== GRAPH DIAGNOSTICS ===")
print(f"Total Nodes: {len(nodes)}")
print(f"Total Edges: {len(edges)}")

# Check 1: Missing endpoint nodes
missing_endpoints = []
for e in edges:
    if e["from"] not in nodes or e["to"] not in nodes:
        missing_endpoints.append(e)
print(f"Edges with missing endpoints: {len(missing_endpoints)}")

# Check 2: Duplicate edges
seen_pairs = {}
duplicates = []
for idx, e in enumerate(edges):
    pair = tuple(sorted([e["from"], e["to"]]))
    if pair in seen_pairs:
        duplicates.append((seen_pairs[pair], idx, pair))
    else:
        seen_pairs[pair] = idx
print(f"Duplicate edge pairs: {len(duplicates)}")
for d in duplicates[:5]:
    print(f"  Duplicate: edge {d[0]} and {d[1]}: {d[2]}")

# Check 3: Orphan nodes (degree 0)
degree = {n_id: 0 for n_id in nodes}
for e in edges:
    if e["from"] in degree: degree[e["from"]] += 1
    if e["to"] in degree: degree[e["to"]] += 1
orphans = [n_id for n_id, deg in degree.items() if deg == 0]
print(f"Orphan nodes (degree 0): {len(orphans)}")
for o in orphans:
    print(f"  Orphan: {o} ({nodes[o].get('name')})")

# Check 4: Unusually long same-floor edges
long_edges = []
for e in edges:
    un = nodes.get(e["from"])
    vn = nodes.get(e["to"])
    if un and vn and un["floor"] == vn["floor"]:
        geo = math.hypot(un["x"] - vn["x"], un["y"] - vn["y"])
        # Check if corridor or entrance has huge jump
        if geo > 500 and un["floor"] in [0, 1]:
            long_edges.append((e["from"], e["to"], geo, e.get("type"), un["floor"]))
        elif geo > 150 and un["floor"] == 2:
            long_edges.append((e["from"], e["to"], geo, e.get("type"), un["floor"]))
print(f"Potentially huge jumps / long edges: {len(long_edges)}")
for le in long_edges:
    print(f"  Long edge [F{le[4]}]: {le[0]} <-> {le[1]} (geo={le[2]:.1f}, type={le[3]})")


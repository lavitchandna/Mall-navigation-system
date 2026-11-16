import json, math
from PIL import Image, ImageDraw

# Load ground-floor.png
img = Image.open("/Users/hemantmalik/Desktop/ambience-mall-integrated/ambience-mall-app-ui/public/maps/ground-floor.png")
draw_img = img.copy()
draw = ImageDraw.Draw(draw_img)

# Load graph
with open("/Users/hemantmalik/Desktop/ambience-mall-integrated/Mall-RL-Navigation/data/navigation_graph_real.json") as f:
    graph = json.load(f)

nodes = {n["id"]: n for n in graph["nodes"]}

# Verified key anchor points on Ground Floor:
# 1. North Entry (G_GATE_1): backend (450, 180) -> visual map (415, 140)
# 2. North Atrium (G_CORR_N06): backend (450, 850) -> visual map (460, 310)
# 3. North-Central (G_CORR_NC03): backend (1000, 1380) -> visual map (510, 460)
# 4. Central Spine (G_CORR_C05): backend (1400, 2070) -> visual map (545, 660)
# 5. Central Grand Atrium (G_CORR_ATRIUM): backend (1550, 2850) -> visual map (575, 880)
# 6. South Promenade (G_CORR_S06): backend (1780, 3960) -> visual map (570, 1150)
# 7. South Entry / Gate 3 (G_GATE_3): backend (1750, 4750) -> visual map (585, 1375)

anchors = [
    ((450.0, 180.0), (415.0, 140.0)),
    ((450.0, 850.0), (460.0, 310.0)),
    ((1000.0, 1380.0), (510.0, 460.0)),
    ((1400.0, 2070.0), (545.0, 660.0)),
    ((1550.0, 2850.0), (575.0, 880.0)),
    ((1780.0, 3960.0), (570.0, 1150.0)),
    ((1750.0, 4750.0), (585.0, 1375.0)),
    # East Wing / Gate 2:
    ((2150.0, 3240.0), (745.0, 930.0)),
    # West Plaza / Gate 4:
    ((950.0, 2100.0), (370.0, 670.0))
]

# Let us solve for a 2D polynomial or piecewise / RBF spline mapping
import numpy as np

src_pts = np.array([a[0] for a in anchors])
dst_pts = np.array([a[1] for a in anchors])
n = len(anchors)

# Thin-plate spline
def compute_tps(src, dst):
    def rbf(r):
        return np.where(r > 1e-6, r * r * np.log(np.maximum(r, 1e-6)), 0.0)
    
    diff = src[:, None, :] - src[None, :, :]
    dist = np.linalg.norm(diff, axis=-1)
    K = rbf(dist)
    
    P = np.column_stack([np.ones(n), src])
    L = np.zeros((n + 3, n + 3))
    L[:n, :n] = K
    L[:n, n:] = P
    L[n:, :n] = P.T
    
    Y = np.zeros((n + 3, 2))
    Y[:n, :] = dst
    
    coeffs = np.linalg.lstsq(L, Y, rcond=None)[0]
    weights = coeffs[:n, :]
    affine = coeffs[n:, :]
    return weights, affine

weights, affine = compute_tps(src_pts, dst_pts)

def map_point(x, y):
    pt = np.array([x, y])
    r = np.linalg.norm(src_pts - pt, axis=-1)
    k = np.where(r > 1e-6, r * r * np.log(np.maximum(r, 1e-6)), 0.0)
    u = affine[0, 0] + affine[1, 0] * x + affine[2, 0] * y + np.dot(k, weights[:, 0])
    v = affine[0, 1] + affine[1, 1] * x + affine[2, 1] * y + np.dot(k, weights[:, 1])
    return float(u), float(v)

# Draw all corridor edges
gf_edges = [e for e in graph["edges"] if nodes[e["from"]]["floor"] == 0 and nodes[e["to"]]["floor"] == 0 and "CORR" in e["from"] and "CORR" in e["to"]]
for e in gf_edges:
    u = nodes[e["from"]]
    v = nodes[e["to"]]
    pu = map_point(u["x"], u["y"])
    pv = map_point(v["x"], v["y"])
    draw.line([pu, pv], fill=(237, 27, 47), width=6)

# Draw test route Gate 1 -> Lacoste (F0)
# and Gate 1 -> LEGO
art_dir = "/Users/hemantmalik/.gemini/antigravity-ide/brain/a9799fa1-ec84-4590-a886-7db53879cac6"
draw_img.save(f"{art_dir}/gf_test_corridor_overlay.png")
print("Saved gf_test_corridor_overlay.png")


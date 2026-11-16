import json, math
import numpy as np

# Function to compute Thin-Plate Spline
def compute_tps(src_pts, dst_pts, lambda_reg=1e-2):
    src = np.array(src_pts, dtype=float)
    dst = np.array(dst_pts, dtype=float)
    n = len(src)
    
    def rbf(r):
        return np.where(r > 1e-6, r * r * np.log(np.maximum(r, 1e-6)), 0.0)
    
    diff = src[:, None, :] - src[None, :, :]
    dist = np.linalg.norm(diff, axis=-1)
    K = rbf(dist)
    
    P = np.column_stack([np.ones(n), src])
    L = np.zeros((n + 3, n + 3))
    L[:n, :n] = K + lambda_reg * np.eye(n)
    L[:n, n:] = P
    L[n:, :n] = P.T
    
    Y = np.zeros((n + 3, 2))
    Y[:n, :] = dst
    
    coeffs = np.linalg.lstsq(L, Y, rcond=None)[0]
    weights = coeffs[:n, :]
    affine = coeffs[n:, :]
    return {
        "src_pts": [[float(x), float(y)] for x, y in src_pts],
        "dst_pts": [[float(x), float(y)] for x, y in dst_pts],
        "weights": [[float(w[0]), float(w[1])] for w in weights],
        "affine": [[float(a[0]), float(a[1])] for a in affine]
    }

# ==========================================
# FLOOR 0: GROUND FLOOR
# ==========================================
# Ground Floor is 1:1 aligned directly with ground-floor.png (1024 x 1536)
# Pure identity affine mapping without spline buckling
gf_calib = {
    "src_pts": [],
    "dst_pts": [],
    "weights": [],
    "affine": [
        [0.0, 0.0],
        [1.0, 0.0],
        [0.0, 1.0]
    ]
}

# ==========================================
# FLOOR 1: FIRST FLOOR
# ==========================================
# Monotonically verified anchors (0 inversions)
ff_anchors = [
    ((350.0, 200.0), (350.0, 150.0)),
    ((500.0, 500.0), (380.0, 260.0)),
    ((700.0, 900.0), (410.0, 350.0)),
    ((700.0, 1000.0), (430.0, 400.0)),
    ((700.0, 1150.0), (450.0, 460.0)),
    ((800.0, 1380.0), (475.0, 530.0)),
    ((950.0, 1460.0), (490.0, 580.0)),
    ((700.0, 1850.0), (505.0, 640.0)),
    ((700.0, 2500.0), (515.0, 720.0)),
    ((850.0, 2750.0), (525.0, 780.0)),
    ((950.0, 2870.0), (535.0, 830.0)),
    ((1050.0, 3100.0), (545.0, 880.0)),
    ((1100.0, 3350.0), (555.0, 950.0)),
    ((1100.0, 3750.0), (560.0, 1040.0)),
    ((1150.0, 4150.0), (565.0, 1100.0)),
    ((1150.0, 4450.0), (565.0, 1150.0)),
    ((1000.0, 4960.0), (565.0, 1220.0)),
    ((1200.0, 5250.0), (570.0, 1260.0)),
    ((1400.0, 6135.0), (680.0, 1340.0))
]

# ==========================================
# FLOOR 2: SECOND FLOOR
# ==========================================
# Monotonically verified anchors (0 inversions)
sf_anchors = [
    ((260.0, 80.0), (450.0, 160.0)),
    ((260.0, 170.0), (455.0, 300.0)),
    ((260.0, 200.0), (460.0, 360.0)),
    ((250.0, 350.0), (460.0, 520.0)),
    ((260.0, 500.0), (465.0, 700.0)),
    ((250.0, 620.0), (465.0, 850.0)),
    ((250.0, 750.0), (465.0, 1000.0)),
    ((260.0, 820.0), (465.0, 1080.0)),
    ((260.0, 930.0), (465.0, 1200.0))
]

calib_result = {
    "0": gf_calib,
    "1": compute_tps([a[0] for a in ff_anchors], [a[1] for a in ff_anchors]),
    "2": compute_tps([a[0] for a in sf_anchors], [a[1] for a in sf_anchors])
}

# Save calibration
out_path = "/Users/hemantmalik/Desktop/ambience-mall-integrated/ambience-mall-app-ui/lib/floor-calibration.json"
with open(out_path, "w") as f:
    json.dump(calib_result, f, indent=2)

print("Master floor calibration generated and saved to floor-calibration.json!")

import json, math
from pathlib import Path

# Paths
NAV_GRAPH_PATH = Path("/Users/hemantmalik/Desktop/ambience-mall-integrated/Mall-RL-Navigation/data/navigation_graph_real.json")
MASTER_PATH = Path("/Users/hemantmalik/Desktop/ambience-mall-integrated/Mall-RL-Navigation/data/Ambience_Gurugram_Ground_First_Second_MASTER_Coordinates.json")

with open(NAV_GRAPH_PATH) as f:
    nav_graph = json.load(f)

with open(MASTER_PATH) as f:
    master = json.load(f)

# Existing non-GF nodes and edges to preserve
non_gf_nodes = [n for n in nav_graph["nodes"] if n["floor"] != 0]
inter_floor_edges = [e for e in nav_graph["edges"] if any(k in e["from"] or k in e["to"] for k in ["LIFT", "ESC", "STAIRS"])]
# preserve edges where both nodes are non-GF
node_floors = {n["id"]: n["floor"] for n in nav_graph["nodes"]}
f12_edges = [e for e in nav_graph["edges"] if node_floors.get(e["from"]) in [1, 2] and node_floors.get(e["to"]) in [1, 2]]

# Define Ground Floor Corridors & Landmarks (image space 1024 x 1536)
gf_corridors = {
    # North Gate & Promenade (NH-8 Side)
    "G_GATE_1": {"name": "Gate 1 (North Entry / NH-8)", "type": "mall_entrance", "x": 415.0, "y": 140.0},
    "G_CORR_N01": {"name": "North Promenade (Paul's / Zoya)", "type": "corridor", "x": 440.0, "y": 210.0},
    "G_CORR_N02": {"name": "North Promenade (Onitsuka / Charles & Keith)", "type": "corridor", "x": 465.0, "y": 260.0},
    "G_CORR_N03": {"name": "North Promenade (Diesel / Isharya)", "type": "corridor", "x": 490.0, "y": 320.0},
    "G_CORR_N04": {"name": "North Promenade (Lacoste / Hackett)", "type": "corridor", "x": 510.0, "y": 370.0},
    "G_CORR_N05": {"name": "North Promenade (Zara / West Elm / Nicobar)", "type": "corridor", "x": 530.0, "y": 430.0},
    "G_CORR_N06": {"name": "North Spine (Hugo Boss / Armani)", "type": "corridor", "x": 540.0, "y": 500.0},
    "G_CORR_NC01": {"name": "Central Spine (Shantnu / Dior)", "type": "corridor", "x": 545.0, "y": 540.0},
    "G_CORR_NC02": {"name": "Central Spine (TUMI / NARS)", "type": "corridor", "x": 550.0, "y": 580.0},
    "G_CORR_NC03": {"name": "Central Spine (Laduree / Frozen Bottle)", "type": "corridor", "x": 555.0, "y": 640.0},
    "G_CORR_C00": {"name": "Central Spine (Superdry / Wow Momo)", "type": "corridor", "x": 555.0, "y": 680.0},
    "G_CORR_C01": {"name": "Central Spine (Dyson / Diversion Dine)", "type": "corridor", "x": 555.0, "y": 720.0},
    "G_CORR_C02": {"name": "Central Spine (LEGO / Mala Akbari)", "type": "corridor", "x": 555.0, "y": 760.0},
    "G_CORR_C03": {"name": "Central Spine (Marks & Spencer / Pantaloons / Mango)", "type": "corridor", "x": 560.0, "y": 810.0},

    # Grand Atrium Hub (Center of Mall)
    "G_CORR_ATRIUM": {"name": "Central Grand Atrium", "type": "junction", "x": 580.0, "y": 880.0},
    "G_CORR_ATRIUM_W": {"name": "Atrium West Crossing", "type": "junction", "x": 520.0, "y": 880.0},
    "G_CORR_ATRIUM_E": {"name": "Atrium East Crossing", "type": "junction", "x": 650.0, "y": 880.0},

    # South Section - West Promenade
    "G_CORR_SW01": {"name": "West Promenade (UNIQLO / Starbucks)", "type": "corridor", "x": 520.0, "y": 920.0},
    "G_CORR_SW02": {"name": "West Promenade (Bateel)", "type": "corridor", "x": 520.0, "y": 990.0},
    "G_CORR_SW03": {"name": "West Promenade (Lenscrafters)", "type": "corridor", "x": 520.0, "y": 1030.0},
    "G_CORR_SW04": {"name": "West Promenade (Sunglass Hut)", "type": "corridor", "x": 520.0, "y": 1060.0},
    "G_CORR_SW05": {"name": "West Promenade (Lladro Spain)", "type": "corridor", "x": 520.0, "y": 1100.0},
    "G_CORR_SW06": {"name": "West Promenade (Polo Ralph Lauren)", "type": "corridor", "x": 520.0, "y": 1165.0},
    "G_CORR_SW07": {"name": "West Promenade (Swarovski)", "type": "corridor", "x": 520.0, "y": 1210.0},
    "G_CORR_SW08": {"name": "West Promenade (L'Occitane)", "type": "corridor", "x": 520.0, "y": 1240.0},
    "G_CORR_SW09": {"name": "West Promenade (MAC)", "type": "corridor", "x": 520.0, "y": 1280.0},
    "G_CORR_SW10": {"name": "West Promenade (Estee Lauder)", "type": "corridor", "x": 520.0, "y": 1315.0},
    "G_CORR_SW_EXIT": {"name": "West Plaza Exit Corridor", "type": "corridor", "x": 530.0, "y": 1380.0},

    # South Section - East Promenade
    "G_CORR_SE01": {"name": "East Promenade (Mark Forex)", "type": "corridor", "x": 650.0, "y": 900.0},
    "G_CORR_SE02": {"name": "East Promenade (Cover Story)", "type": "corridor", "x": 650.0, "y": 930.0},
    "G_CORR_SE03": {"name": "East Promenade (Nespresso)", "type": "corridor", "x": 650.0, "y": 970.0},
    "G_CORR_SE04": {"name": "East Promenade (Trends)", "type": "corridor", "x": 650.0, "y": 1010.0},
    "G_CORR_SE05": {"name": "East Promenade (Victoria's Secret)", "type": "corridor", "x": 640.0, "y": 1060.0},
    "G_CORR_SE06": {"name": "East Promenade (Tira / H&M)", "type": "corridor", "x": 650.0, "y": 1110.0},
    "G_CORR_SE07": {"name": "East Promenade (Gelato Vinto)", "type": "corridor", "x": 650.0, "y": 1195.0},
    "G_CORR_SE08": {"name": "East Promenade (Oma Living)", "type": "corridor", "x": 650.0, "y": 1240.0},
    "G_CORR_SE09": {"name": "East Promenade (Bath & Body Works)", "type": "corridor", "x": 645.0, "y": 1290.0},
    "G_CORR_SE_EXIT": {"name": "East Plaza Exit Corridor", "type": "corridor", "x": 630.0, "y": 1380.0},

    # South Main Gate (Gate 1 on Floor Map)
    "G_GATE_3": {"name": "Main Entry / Exit (Gate 1)", "type": "mall_entrance", "x": 580.0, "y": 1430.0},
    "G_GATE_2": {"name": "Gate 2 (East Promenade Entry)", "type": "mall_entrance", "x": 745.0, "y": 930.0},
    "G_GATE_4": {"name": "Gate 4 (West Plaza Entry)", "type": "mall_entrance", "x": 370.0, "y": 670.0},
    "G_GATE_PARKING": {"name": "Parking Lobby Entry", "type": "mall_entrance", "x": 580.0, "y": 850.0},

    # Vertical connectors at Grand Atrium
    "LIFT_CENTRAL_G": {"name": "Central Atrium Elevator (G)", "type": "lift", "x": 580.0, "y": 880.0},
    "ESC_CENTRAL_G": {"name": "Central Atrium Escalator (G)", "type": "escalator", "x": 560.0, "y": 880.0},
    "STAIRS_CENTRAL_G": {"name": "Central Atrium Stairs (G)", "type": "staircase", "x": 540.0, "y": 880.0},
    "LIFT_NORTH_G": {"name": "North Glass Elevator (G)", "type": "lift", "x": 540.0, "y": 500.0},
    "ESC_NORTH_G": {"name": "North Escalator (G)", "type": "escalator", "x": 520.0, "y": 500.0},
    "STAIRS_NORTH_G": {"name": "North Staircase (G)", "type": "staircase", "x": 500.0, "y": 500.0},
    "LIFT_SOUTH_G": {"name": "South Boulevard Elevator (G)", "type": "lift", "x": 580.0, "y": 1400.0},
    "ESC_SOUTH_G": {"name": "South Escalator (G)", "type": "escalator", "x": 560.0, "y": 1400.0},
    "STAIRS_SOUTH_G": {"name": "South Staircase (G)", "type": "staircase", "x": 540.0, "y": 1400.0},
}

# Accurate Store POIs & Entrance Doorways
# (x_poi, y_poi, x_ent, y_ent, nearest_corr_id)
gf_stores_info = {
    "G_001": ("Paul's Bakery", 410.0, 160.0, 430.0, 180.0, "G_CORR_N01"),
    "G_002": ("Onitsuka Tiger", 465.0, 250.0, 470.0, 270.0, "G_CORR_N02"),
    "G_003": ("Diesel", 520.0, 290.0, 500.0, 310.0, "G_CORR_N03"),
    "G_004": ("Lacoste", 530.0, 350.0, 520.0, 360.0, "G_CORR_N04"),
    "G_005": ("ZARA", 350.0, 430.0, 450.0, 430.0, "G_CORR_N05"),
    "G_006": ("Isharya", 564.0, 281.0, 510.0, 281.0, "G_CORR_N02"),
    "G_007": ("Hackett London", 571.0, 324.0, 520.0, 324.0, "G_CORR_N03"),
    "G_008": ("Limited Edt", 590.0, 340.0, 530.0, 340.0, "G_CORR_N03"),
    "G_009": ("Oud Arabia", 580.0, 350.0, 530.0, 350.0, "G_CORR_N04"),
    "G_010": ("Levi's", 590.0, 370.0, 530.0, 370.0, "G_CORR_N04"),
    "G_011": ("Under Armour", 596.0, 359.0, 540.0, 359.0, "G_CORR_N04"),
    "G_012": ("Forest Essentials", 580.0, 380.0, 540.0, 380.0, "G_CORR_N04"),
    "G_013": ("NICOBAR", 622.0, 391.0, 550.0, 391.0, "G_CORR_N05"),
    "G_014": ("NARS", 685.0, 583.0, 580.0, 583.0, "G_CORR_NC02"),
    "G_015": ("Dior", 687.0, 540.0, 580.0, 540.0, "G_CORR_NC01"),
    "G_016": ("The Collective", 660.0, 510.0, 570.0, 510.0, "G_CORR_N06"),
    "G_017": ("Gelato", 649.0, 1194.0, 640.0, 1194.0, "G_CORR_SE07"),
    "G_018": ("Gel", 649.0, 1194.0, 640.0, 1194.0, "G_CORR_SE07"),
    "G_019": ("Vinto", 649.0, 1194.0, 640.0, 1194.0, "G_CORR_SE07"),
    "G_020": ("BODY", 651.0, 1286.0, 640.0, 1286.0, "G_CORR_SE09"),
    "G_021": ("Bath & Body Works", 651.0, 1286.0, 640.0, 1286.0, "G_CORR_SE09"),
    "G_022": ("Victoria's Secret", 636.0, 1060.0, 630.0, 1060.0, "G_CORR_SE05"),
    "G_023": ("Nykaa", 640.0, 1080.0, 635.0, 1080.0, "G_CORR_SE05"),
    "G_024": ("L'Occitane en Provence", 473.0, 1239.0, 500.0, 1239.0, "G_CORR_SW08"),
    "G_025": ("Clinique", 480.0, 1250.0, 505.0, 1250.0, "G_CORR_SW08"),
    "G_026": ("Estee Lauder", 484.0, 1313.0, 505.0, 1313.0, "G_CORR_SW10"),
    "G_027": ("Hugo Boss", 656.0, 460.0, 570.0, 460.0, "G_CORR_N06"),
    "G_028": ("Froze", 723.0, 638.0, 600.0, 638.0, "G_CORR_NC03"),
    "G_029": ("Shantnu Nikhil", 544.0, 518.0, 544.0, 530.0, "G_CORR_NC01"),
    "G_030": ("Laduree", 573.0, 641.0, 565.0, 641.0, "G_CORR_NC03"),
    "G_031": ("Tommy Hilfiger", 600.0, 610.0, 565.0, 610.0, "G_CORR_NC02"),
    "G_032": ("TUMI", 558.0, 567.0, 555.0, 575.0, "G_CORR_NC02"),
    "G_033": ("Ralph", 462.0, 1165.0, 500.0, 1165.0, "G_CORR_SW06"),
    "G_034": ("Polo Ralph Lauren", 462.0, 1165.0, 500.0, 1165.0, "G_CORR_SW06"),
    "G_035": ("Brooks Brothers", 680.0, 660.0, 580.0, 660.0, "G_CORR_C00"),
    "G_036": ("Frozen Bottle", 723.0, 638.0, 600.0, 638.0, "G_CORR_NC03"),
    "G_037": ("Lenscrafters", 439.0, 1027.0, 495.0, 1027.0, "G_CORR_SW03"),
    "G_038": ("Superdry", 690.0, 670.0, 580.0, 670.0, "G_CORR_C00"),
    "G_039": ("GAS", 690.0, 690.0, 580.0, 690.0, "G_CORR_C00"),
    "G_040": ("Birker", 700.0, 700.0, 580.0, 700.0, "G_CORR_C01"),
    "G_041": ("Ben's Cookies", 700.0, 700.0, 580.0, 700.0, "G_CORR_C01"),
    "G_042": ("Spain", 444.0, 1104.0, 495.0, 1104.0, "G_CORR_SW05"),
    "G_043": ("Sunglass Hut", 439.0, 1060.0, 495.0, 1060.0, "G_CORR_SW04"),
    "G_044": ("Kama Ayurveda", 500.0, 1040.0, 510.0, 1040.0, "G_CORR_SW03"),
    "G_045": ("Birkenstock", 500.0, 1050.0, 510.0, 1050.0, "G_CORR_SW04"),
    "G_046": ("Bateel", 460.0, 991.0, 495.0, 991.0, "G_CORR_SW02"),
    "G_047": ("Lladro", 444.0, 1104.0, 495.0, 1104.0, "G_CORR_SW05"),
    "G_048": ("La Sante", 500.0, 1080.0, 510.0, 1080.0, "G_CORR_SW05"),
    "G_049": ("ALCHEMIST", 500.0, 1090.0, 510.0, 1090.0, "G_CORR_SW05"),
    "G_050": ("Forever New", 740.0, 950.0, 670.0, 950.0, "G_CORR_SE03"),
    "G_051": ("Nespresso", 745.0, 969.0, 670.0, 969.0, "G_CORR_SE03"),
    "G_052": ("Wow! Momo", 734.0, 681.0, 600.0, 681.0, "G_CORR_C00"),
    "G_053": ("Dyson", 482.0, 719.0, 520.0, 719.0, "G_CORR_C01"),
    "G_054": ("Diversion", 721.0, 714.0, 600.0, 714.0, "G_CORR_C01"),
    "G_055": ("Dine", 721.0, 714.0, 600.0, 714.0, "G_CORR_C01"),
    "G_056": ("Cover Story", 736.0, 924.0, 670.0, 924.0, "G_CORR_SE02"),
    "G_057": ("Mala Akbari", 734.0, 754.0, 600.0, 754.0, "G_CORR_C02"),
    "G_058": ("Mango Man", 462.0, 826.0, 520.0, 826.0, "G_CORR_C03"),
    "G_059": ("LEGO", 475.0, 764.0, 520.0, 764.0, "G_CORR_C02"),
    "G_060": ("MARK", 730.0, 873.0, 670.0, 873.0, "G_CORR_SE01"),
    "G_061": ("FOREX", 730.0, 873.0, 670.0, 873.0, "G_CORR_SE01"),
    "G_062": ("Money", 730.0, 873.0, 670.0, 873.0, "G_CORR_SE01"),
    "G_063": ("Armani Exchange", 663.0, 496.0, 580.0, 496.0, "G_CORR_N06"),
    "G_064": ("Tira", 763.0, 1110.0, 680.0, 1110.0, "G_CORR_SE06"),
    "G_065": ("(Oma", 745.0, 1237.0, 670.0, 1237.0, "G_CORR_SE08"),
    "G_066": ("Living", 745.0, 1237.0, 670.0, 1237.0, "G_CORR_SE08"),
    "G_067": ("Pantaloons", 727.0, 810.0, 610.0, 810.0, "G_CORR_C03"),
    "G_068": ("Livin", 745.0, 1237.0, 670.0, 1237.0, "G_CORR_SE08"),
    "G_069": ("Trends", 754.0, 1011.0, 670.0, 1011.0, "G_CORR_SE04"),
    "G_070": ("Talk", 440.0, 910.0, 490.0, 910.0, "G_CORR_SW01"),
    "G_071": ("Bread", 440.0, 910.0, 490.0, 910.0, "G_CORR_SW01"),
    "G_072": ("UNIQLO", 464.0, 893.0, 500.0, 893.0, "G_CORR_SW01"),
}

# Construct full GF nodes list
new_gf_nodes = []
for cid, cinfo in gf_corridors.items():
    new_gf_nodes.append({
        "id": cid,
        "name": cinfo["name"],
        "floor": 0,
        "x": cinfo["x"],
        "y": cinfo["y"],
        "type": cinfo["type"],
        "poi_id": None,
        "entrance_status": "verified",
        "category": "General"
    })

# Add shop entrances
for pid, sinfo in gf_stores_info.items():
    name, px, py, ex, ey, corr_id = sinfo
    ent_id = f"ENT_{pid}"
    new_gf_nodes.append({
        "id": ent_id,
        "name": f"{name} (Entrance)",
        "floor": 0,
        "x": ex,
        "y": ey,
        "type": "shop_entrance",
        "poi_id": pid,
        "entrance_status": "verified",
        "category": "General"
    })

# Corridor Network Connections (Walkable edges)
corr_connections = [
    # North Corridor Chain (Gate 1 / NH-8 down to Atrium)
    ("G_GATE_1", "G_CORR_N01"),
    ("G_CORR_N01", "G_CORR_N02"),
    ("G_CORR_N02", "G_CORR_N03"),
    ("G_CORR_N03", "G_CORR_N04"),
    ("G_CORR_N04", "G_CORR_N05"),
    ("G_CORR_N05", "G_CORR_N06"),
    ("G_CORR_N06", "G_CORR_NC01"),
    ("G_CORR_NC01", "G_CORR_NC02"),
    ("G_CORR_NC02", "G_CORR_NC03"),
    ("G_CORR_NC03", "G_CORR_C00"),
    ("G_CORR_C00", "G_CORR_C01"),
    ("G_CORR_C01", "G_CORR_C02"),
    ("G_CORR_C02", "G_CORR_C03"),
    ("G_CORR_C03", "G_CORR_ATRIUM"),

    # Grand Atrium Crossway Hub
    ("G_CORR_ATRIUM_W", "G_CORR_ATRIUM"),
    ("G_CORR_ATRIUM", "G_CORR_ATRIUM_E"),
    ("G_CORR_C03", "G_CORR_ATRIUM_W"),
    ("G_CORR_C03", "G_CORR_ATRIUM_E"),

    # West Promenade Chain (Atrium West down to Gate 1 / South Entry)
    ("G_CORR_ATRIUM_W", "G_CORR_SW01"),
    ("G_CORR_SW01", "G_CORR_SW02"),
    ("G_CORR_SW02", "G_CORR_SW03"),
    ("G_CORR_SW03", "G_CORR_SW04"),
    ("G_CORR_SW04", "G_CORR_SW05"),
    ("G_CORR_SW05", "G_CORR_SW06"),
    ("G_CORR_SW06", "G_CORR_SW07"),
    ("G_CORR_SW07", "G_CORR_SW08"),
    ("G_CORR_SW08", "G_CORR_SW09"),
    ("G_CORR_SW09", "G_CORR_SW10"),
    ("G_CORR_SW10", "G_CORR_SW_EXIT"),
    ("G_CORR_SW_EXIT", "G_GATE_3"),

    # East Promenade Chain (Atrium East down to Gate 1 / South Entry)
    ("G_CORR_ATRIUM_E", "G_CORR_SE01"),
    ("G_CORR_SE01", "G_CORR_SE02"),
    ("G_CORR_SE02", "G_CORR_SE03"),
    ("G_CORR_SE03", "G_CORR_SE04"),
    ("G_CORR_SE04", "G_CORR_SE05"),
    ("G_CORR_SE05", "G_CORR_SE06"),
    ("G_CORR_SE06", "G_CORR_SE07"),
    ("G_CORR_SE07", "G_CORR_SE08"),
    ("G_CORR_SE08", "G_CORR_SE09"),
    ("G_CORR_SE09", "G_CORR_SE_EXIT"),
    ("G_CORR_SE_EXIT", "G_GATE_3"),

    # Secondary gates
    ("G_CORR_SE02", "G_GATE_2"),
    ("G_CORR_N05", "G_GATE_4"),
    ("G_CORR_ATRIUM", "G_GATE_PARKING"),

    # Connectors
    ("G_CORR_ATRIUM", "LIFT_CENTRAL_G"),
    ("G_CORR_ATRIUM", "ESC_CENTRAL_G"),
    ("G_CORR_ATRIUM", "STAIRS_CENTRAL_G"),
    ("G_CORR_N06", "LIFT_NORTH_G"),
    ("G_CORR_N06", "ESC_NORTH_G"),
    ("G_CORR_N06", "STAIRS_NORTH_G"),
    ("G_GATE_3", "LIFT_SOUTH_G"),
    ("G_GATE_3", "ESC_SOUTH_G"),
    ("G_GATE_3", "STAIRS_SOUTH_G"),
]

# Helper to calculate Euclidean distance
all_nodes_dict = {n["id"]: n for n in non_gf_nodes + new_gf_nodes}

def dist(u_id, v_id):
    u = all_nodes_dict[u_id]
    v = all_nodes_dict[v_id]
    dx = u["x"] - v["x"]
    dy = u["y"] - v["y"]
    return round(math.hypot(dx, dy) / 10.0, 1)

new_gf_edges = []
for u, v in corr_connections:
    d = dist(u, v)
    new_gf_edges.append({"from": u, "to": v, "distance": d, "accessible": True})
    new_gf_edges.append({"from": v, "to": u, "distance": d, "accessible": True})

# Connect shop entrances to their designated corridor node
for pid, sinfo in gf_stores_info.items():
    ent_id = f"ENT_{pid}"
    corr_id = sinfo[5]
    d = dist(ent_id, corr_id)
    new_gf_edges.append({"from": ent_id, "to": corr_id, "distance": d, "accessible": True})
    new_gf_edges.append({"from": corr_id, "to": ent_id, "distance": d, "accessible": True})

# Inter-floor connector edges (e.g. LIFT_CENTRAL_G <-> LIFT_CENTRAL_F1)
conn_pairs = [
    ("LIFT_CENTRAL_G", "LIFT_CENTRAL_F1"),
    ("ESC_CENTRAL_G", "ESC_CENTRAL_F1"),
    ("STAIRS_CENTRAL_G", "STAIRS_CENTRAL_F1"),
    ("LIFT_NORTH_G", "LIFT_NORTH_F1"),
    ("ESC_NORTH_G", "ESC_NORTH_F1"),
    ("STAIRS_NORTH_G", "STAIRS_NORTH_F1"),
    ("LIFT_SOUTH_G", "LIFT_SOUTH_F1"),
    ("ESC_SOUTH_G", "ESC_SOUTH_F1"),
    ("STAIRS_SOUTH_G", "STAIRS_SOUTH_F1"),
]
final_inter_edges = []
for u, v in conn_pairs:
    if u in all_nodes_dict and v in all_nodes_dict:
        is_acc = "ESC" not in u and "STAIRS" not in u
        final_inter_edges.append({"from": u, "to": v, "distance": 5.0, "accessible": is_acc})
        final_inter_edges.append({"from": v, "to": u, "distance": 5.0, "accessible": is_acc})

# Floor 1 <-> Floor 2 connector edges
f12_conn_pairs = [
    ("LIFT_CENTRAL_F1", "LIFT_CENTRAL_F2"),
    ("ESC_CENTRAL_F1", "ESC_CENTRAL_F2"),
    ("STAIRS_CENTRAL_F1", "STAIRS_CENTRAL_F2"),
    ("LIFT_NORTH_F1", "LIFT_NORTH_F2"),
    ("ESC_NORTH_F1", "ESC_NORTH_F2"),
    ("STAIRS_NORTH_F1", "STAIRS_NORTH_F2"),
    ("LIFT_SOUTH_F1", "LIFT_SOUTH_F2"),
    ("ESC_SOUTH_F1", "ESC_SOUTH_F2"),
    ("STAIRS_SOUTH_F1", "STAIRS_SOUTH_F2"),
]
for u, v in f12_conn_pairs:
    if u in all_nodes_dict and v in all_nodes_dict:
        is_acc = "ESC" not in u and "STAIRS" not in u
        final_inter_edges.append({"from": u, "to": v, "distance": 5.0, "accessible": is_acc})
        final_inter_edges.append({"from": v, "to": u, "distance": 5.0, "accessible": is_acc})

# Filter out duplicate edges
edge_set = set()
clean_edges = []
for e in f12_edges + new_gf_edges + final_inter_edges:
    pair = (e["from"], e["to"])
    if pair not in edge_set and e["from"] in all_nodes_dict and e["to"] in all_nodes_dict:
        edge_set.add(pair)
        clean_edges.append(e)

# Save updated navigation_graph_real.json
updated_graph = {
    "version": "4.0.0-accurate-indoor-aligned",
    "description": "Ground floor corridor network aligned 1:1 with official floor map",
    "nodes": non_gf_nodes + new_gf_nodes,
    "edges": clean_edges
}
with open(NAV_GRAPH_PATH, "w") as f:
    json.dump(updated_graph, f, indent=2)

# Save updated MASTER_Coordinates.json Ground Floor POIs
updated_gf_pois = []
for p in master["floors"]["Ground Floor"]["pois"]:
    pid = p["id"]
    if pid in gf_stores_info:
        name, px, py, ex, ey, corr_id = gf_stores_info[pid]
        p_updated = dict(p)
        p_updated["x_px"] = px
        p_updated["y_px"] = py
        p_updated["entrance_node"] = f"ENT_{pid}"
        p_updated["entrance_coords"] = [ex, ey]
        updated_gf_pois.append(p_updated)
    else:
        updated_gf_pois.append(p)

master["floors"]["Ground Floor"]["pois"] = updated_gf_pois
with open(MASTER_PATH, "w") as f:
    json.dump(master, f, indent=2)

print("Saved updated navigation_graph_real.json and MASTER_Coordinates.json successfully!")
print(f"Total nodes: {len(updated_graph['nodes'])}, total edges: {len(updated_graph['edges'])}")

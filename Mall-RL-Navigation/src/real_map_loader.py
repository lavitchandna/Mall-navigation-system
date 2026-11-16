"""
Real Map Data Loader for Ambience Mall Gurugram.

Authoritative spatial loader powered by:
data/Ambience_Gurugram_Ground_First_Second_MASTER_Coordinates.json
and data/navigation_graph_real.json

Manages multi-floor coordinate frames, real shop POIs, walkable entrance anchors,
and floor-local coordinate models without inventing geometry or merging floors.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MASTER_DATA_PATH = DATA_DIR / "Ambience_Gurugram_Ground_First_Second_MASTER_Coordinates.json"
REAL_GRAPH_PATH = DATA_DIR / "navigation_graph_real.json"

FLOOR_NAME_TO_ID = {
    "Ground Floor": 0,
    "First Floor": 1,
    "Second Floor": 2,
}
FLOOR_ID_TO_NAME = {v: k for k, v in FLOOR_NAME_TO_ID.items()}

# Floor-local coordinate fields as stored in the master JSON schema.
FLOOR_COORD_FIELDS = {
    "Ground Floor": ("x_px", "y_px"),
    "First Floor": ("map_x_px", "map_y_px"),
    "Second Floor": ("representative_x_px", "representative_y_px"),
}

CONNECTOR_NODE_TYPES = {"lift", "elevator", "escalator", "staircase", "stairs"}

# Category labels are UI metadata inferred from stored names, not spatial invention.
CATEGORY_KEYWORDS = {
    "Fashion": ["zara", "lacoste", "diesel", "hackett", "levi", "under armour", "nicobar",
                 "collective", "victoria", "boss", "shantnu", "tommy", "ralph", "brooks",
                 "superdry", "gas", "spain", "forever new", "cover story", "mango", "armani",
                 "pantaloons", "trends", "uniqlo", "asics", "crocs", "adidas", "nike",
                 "puma", "new balance", "polo", "skechers", "arrow", "souled", "celio",
                 "rare rabbit", "raymond", "van heusen", "louis philippe", "benetton",
                 "american eagle", "bluorng", "stride", "coyu", "style island", "anita dongre",
                 "basanti", "mulmul", "masaba", "loom", "valaya", "chique", "ranna gill",
                 "kazo", "kompanero", "letoe", "marks", "biba", "global desi", "ancestry",
                 "aurelia", "soch", "sabhyata", "suvasa", "sweet dreams", "access",
                 "accessorize", "atun", "iconic", "for women", "heusen", "kate"],
    "Electronics": ["apple", "dyson", "bose", "croma", "reliance digital", "sony", "samsung",
                    "lenovo", "gadget", "reliar"],
    "Food & Dining": ["paul", "gelato", "gel", "vinto", "froze", "laduree", "cookies", "bateel",
                       "nespresso", "momo", "dine", "diversion", "food", "bread", "chaayos",
                       "aur koffee", "barista"],
    "Beauty & Wellness": ["forest essentials", "nars", "dior", "body", "bath & body", "nykaa",
                           "loccitane", "clinique", "estee", "kama", "tira", "salon", "looks",
                           "geetanjali", "nail", "nailashes"],
    "Jewellery & Luxury": ["isharya", "tumi", "lladro", "kalyan", "tanishq", "taneira",
                            "tissot", "diamond", "bluestone", "panna", "meena"],
    "Eyewear": ["lenscrafters", "sunglass", "titan eye", "opticals", "gkb", "lenskart"],
    "Home & Lifestyle": ["oma", "living", "livin", "home centre", "sleep company", "uchaan",
                          "homestories", "samsonite", "delse", "delsey", "fab india", "jaypore"],
    "Books & Toys": ["lego", "hamley", "om book", "toy factory", "kids"],
    "Watches": ["watches", "titan", "helios"],
    "Services": ["forex", "money", "talk", "lounge", "edit", "zone", "alchemist", "sante"],
}


def infer_store_category(name: str) -> str:
    n = name.lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        for kw in kws:
            if kw in n:
                return cat
    return "Fashion & Retail"


def poi_xy(poi: Dict[str, Any], floor_name: str) -> Optional[Tuple[float, float]]:
    fx, fy = FLOOR_COORD_FIELDS[floor_name]
    if fx not in poi or fy not in poi:
        return None
    return float(poi[fx]), float(poi[fy])


@dataclass
class FloorMap:
    floor_id: int
    name: str
    coordinate_frame: str
    width: Optional[float] = None
    height: Optional[float] = None
    meters_per_pixel: Optional[float] = None
    pois: List[Dict[str, Any]] = field(default_factory=list)


class RealMallLoader:
    """Authoritative mall loader for the real master coordinates + real navigation graph."""

    def __init__(
        self,
        master_path: Optional[Path] = None,
        graph_path: Optional[Path] = None,
    ):
        self.master_path = Path(master_path) if master_path else MASTER_DATA_PATH
        self.graph_path = Path(graph_path) if graph_path else REAL_GRAPH_PATH

        self.floor_maps: Dict[int, FloorMap] = {}
        self.locations: Dict[str, Dict[str, Any]] = {}
        self.stores: List[Dict[str, Any]] = []
        self.gates: List[Dict[str, Any]] = []
        self.connectors: List[Dict[str, Any]] = []
        self.categories: List[str] = []
        self.zones: List[str] = []
        self.mall_info: Dict[str, Any] = {}
        self.graph_nodes: Dict[str, Dict[str, Any]] = {}
        self.load_data()

    def load_data(self) -> None:
        if not self.master_path.exists():
            raise FileNotFoundError(f"Master coordinates file not found: {self.master_path}")
        if not self.graph_path.exists():
            raise FileNotFoundError(f"Real navigation graph not found: {self.graph_path}")

        with open(self.master_path, "r", encoding="utf-8") as f:
            master = json.load(f)
        with open(self.graph_path, "r", encoding="utf-8") as gf:
            gdata = json.load(gf)

        self.mall_info = {
            "name": master.get("mall", "Ambience Mall Gurugram"),
            "version": master.get("version", "v1.0"),
            "critical_accuracy_policy": master.get("critical_accuracy_policy", {}),
            "floors_included": master.get("floors_included", list(FLOOR_NAME_TO_ID.keys())),
            "coordinate_frames": master.get("coordinate_frames", {}),
            "routing_ready": master.get("critical_accuracy_policy", {}).get("routing_ready", False),
        }

        graph_floor_maps = gdata.get("floor_maps", {})
        frames = master.get("coordinate_frames", {})
        self.floor_maps = {}
        for floor_name, floor_id in FLOOR_NAME_TO_ID.items():
            gfm = graph_floor_maps.get(str(floor_id), {})
            frame = frames.get(floor_name, {})
            self.floor_maps[floor_id] = FloorMap(
                floor_id=floor_id,
                name=gfm.get("name", floor_name),
                coordinate_frame=gfm.get("coordinate_frame", frame.get("type", "")),
                width=gfm.get("width"),
                height=gfm.get("height"),
                meters_per_pixel=gfm.get("meters_per_pixel"),
            )

        self.graph_nodes = {nd["id"]: nd for nd in gdata.get("nodes", [])}

        self.stores = []
        self.locations = {}
        floors = master.get("floors", {})
        for floor_name, floor_id in FLOOR_NAME_TO_ID.items():
            for p in floors.get(floor_name, {}).get("pois", []):
                xy = poi_xy(p, floor_name)
                if xy is None:
                    continue
                x, y = xy
                pid = p["id"]
                name = p["name"]
                ent_id = f"ENT_{pid}"
                ent_node = self.graph_nodes.get(ent_id)
                store_obj = {
                    "id": pid,
                    "name": name,
                    "floor": floor_id,
                    "floor_name": floor_name,
                    "x": x,
                    "y": y,
                    "shop_center": (x, y),
                    "entrance_node": ent_id if ent_node else None,
                    "entrance_coords": (ent_node["x"], ent_node["y"]) if ent_node else None,
                    "entrance_status": ent_node.get("entrance_status", "verified") if ent_node else "not_calibrated",
                    "category": infer_store_category(name),
                    "type": "store",
                    "coordinate_frame": p.get("coordinate_frame", floor_name),
                    "coordinate_confidence": p.get("coordinate_confidence") or p.get("status"),
                    "evidence": p.get("evidence"),
                }
                self.stores.append(store_obj)
                self.locations[pid] = store_obj
                self.floor_maps[floor_id].pois.append(store_obj)

        self.gates = []
        self.connectors = []
        for nd in gdata.get("nodes", []):
            ntype = str(nd.get("type", "")).lower()
            loc = {
                "id": nd["id"],
                "name": nd.get("name", nd["id"]),
                "floor": nd.get("floor"),
                "floor_name": FLOOR_ID_TO_NAME.get(nd.get("floor"), f"Floor {nd.get('floor')}"),
                "x": nd.get("x"),
                "y": nd.get("y"),
                "type": nd.get("type"),
                "poi_id": nd.get("poi_id"),
                "entrance_status": nd.get("entrance_status"),
                "category": nd.get("category", "General"),
                "entrance_node": nd["id"],
            }
            if ntype == "mall_entrance":
                loc["type"] = "gate"
                self.gates.append(loc)
                self.locations[nd["id"]] = loc
            elif ntype in CONNECTOR_NODE_TYPES:
                loc["connector_type"] = ntype
                self.connectors.append(loc)
                self.locations[nd["id"]] = loc

        self.categories = sorted({s["category"] for s in self.stores})
        self.zones = []

    def get_floor_map(self, floor_id: int) -> Optional[FloorMap]:
        return self.floor_maps.get(floor_id)

    def get_location(self, loc_id: str) -> Optional[Dict[str, Any]]:
        loc = self.locations.get(loc_id)
        if loc is not None:
            return loc
        node = self.graph_nodes.get(loc_id)
        if node is not None:
            return {
                "id": node["id"],
                "name": node.get("name", node["id"]),
                "floor": node.get("floor"),
                "floor_name": FLOOR_ID_TO_NAME.get(node.get("floor"), f"Floor {node.get('floor')}"),
                "x": node.get("x"),
                "y": node.get("y"),
                "type": node.get("type", "corridor"),
                "category": node.get("category", "General"),
                "entrance_node": node["id"],
            }
        return None

    def get_all_locations(self) -> Dict[str, Dict[str, Any]]:
        return self.locations

    def get_gates(self) -> List[Dict[str, Any]]:
        return self.gates

    def get_stores(self, floor: Optional[int] = None) -> List[Dict[str, Any]]:
        if floor is None:
            return self.stores
        return [s for s in self.stores if s.get("floor") == floor]

    def get_stores_by_category(self, category: str, floor: Optional[int] = None) -> List[Dict[str, Any]]:
        cat_lower = category.strip().lower()
        res = []
        for s in self.stores:
            s_cat = s.get("category", "").lower()
            if cat_lower == "all" or cat_lower in s_cat or s_cat in cat_lower:
                if floor is None or s.get("floor") == floor:
                    res.append(s)
        return res

    def search_locations(self, query: str, floor: Optional[int] = None) -> List[Dict[str, Any]]:
        q = query.strip().lower()
        if not q:
            return self.get_stores(floor)

        matches = []
        for loc in list(self.stores) + list(self.gates):
            if floor is not None and loc.get("floor") != floor:
                continue
            haystack = " ".join([
                str(loc.get("name", "")),
                str(loc.get("category", "")),
                str(loc.get("id", "")),
            ]).lower()
            if q in haystack:
                matches.append(loc)
        return matches


_GLOBAL_REAL_LOADER: Optional[RealMallLoader] = None


def get_real_map_loader() -> RealMallLoader:
    global _GLOBAL_REAL_LOADER
    if _GLOBAL_REAL_LOADER is None:
        _GLOBAL_REAL_LOADER = RealMallLoader()
    return _GLOBAL_REAL_LOADER

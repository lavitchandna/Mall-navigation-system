"""
Map Data Loader for Ambience Mall (Simulated Academic Prototype).

Loads structured mall information, stores, amenities, gates,
and vertical connectors from data/mall_data.json.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MALL_DATA_PATH = DATA_DIR / "mall_data.json"


class MallDataLoader:
    """Manages mall entities, metadata, and spatial queries."""

    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = Path(data_path) if data_path else MALL_DATA_PATH
        self._data: Dict[str, Any] = {}
        self.locations: Dict[str, Dict[str, Any]] = {}
        self.stores: List[Dict[str, Any]] = []
        self.gates: List[Dict[str, Any]] = []
        self.connectors: List[Dict[str, Any]] = []
        self.categories: List[str] = []
        self.zones: List[str] = []
        self.mall_info: Dict[str, Any] = {}
        self.load_data()

    def load_data(self) -> None:
        """Load and index all mall elements from JSON."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Mall data file not found at: {self.data_path}")

        with open(self.data_path, "r", encoding="utf-8") as f:
            self._data = json.load(f)

        self.mall_info = self._data.get("mall_info", {})
        self.categories = self.mall_info.get("categories", [])
        self.zones = self.mall_info.get("zones", [])
        self.stores = self._data.get("stores", [])
        self.gates = self._data.get("gates", [])
        self.connectors = self._data.get("vertical_connectors", [])

        self.locations = {}
        # Index gates
        for g in self.gates:
            g_copy = dict(g)
            g_copy["type"] = "gate"
            self.locations[g["id"]] = g_copy

        # Index stores
        for s in self.stores:
            s_copy = dict(s)
            s_copy["type"] = "store"
            self.locations[s["id"]] = s_copy

        # Index vertical connectors on Floor 1 and Floor 2
        for vc in self.connectors:
            vc_f1 = {
                "id": vc["id_f1"],
                "name": f"{vc['name']} (Floor 1)",
                "category": "Vertical Transport",
                "floor": 1,
                "x": vc["x"],
                "y": vc["y"],
                "zone": "Central Core",
                "type": vc["type"],
                "accessible": vc["accessible"],
                "distance_meters": vc["distance_meters"],
                "paired_id": vc["id_f2"],
                "description": vc["description"],
                "crowd_level": "Medium",
            }
            vc_f2 = {
                "id": vc["id_f2"],
                "name": f"{vc['name']} (Floor 2)",
                "category": "Vertical Transport",
                "floor": 2,
                "x": vc["x"],
                "y": vc["y"],
                "zone": "Central Core",
                "type": vc["type"],
                "accessible": vc["accessible"],
                "distance_meters": vc["distance_meters"],
                "paired_id": vc["id_f1"],
                "description": vc["description"],
                "crowd_level": "Medium",
            }
            self.locations[vc["id_f1"]] = vc_f1
            self.locations[vc["id_f2"]] = vc_f2

    def get_location(self, loc_id: str) -> Optional[Dict[str, Any]]:
        """Return full location object by unique ID."""
        return self.locations.get(loc_id)

    def get_all_locations(self) -> Dict[str, Dict[str, Any]]:
        """Return dict of all indexed locations."""
        return self.locations

    def get_gates(self) -> List[Dict[str, Any]]:
        """Return list of entry gates."""
        return self.gates

    def get_stores(self, floor: Optional[int] = None) -> List[Dict[str, Any]]:
        """Return list of stores, optionally filtered by floor."""
        if floor is None:
            return self.stores
        return [s for s in self.stores if s.get("floor") == floor]

    def get_stores_by_category(self, category: str, floor: Optional[int] = None) -> List[Dict[str, Any]]:
        """Filter stores by category (case-insensitive) and optional floor."""
        cat_lower = category.strip().lower()
        results = []
        for s in self.stores:
            s_cat = s.get("category", "").lower()
            if cat_lower == "all" or cat_lower in s_cat or s_cat in cat_lower:
                if floor is None or s.get("floor") == floor:
                    results.append(s)
        return results

    def search_locations(self, query: str, floor: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fuzzy search for stores, gates, or amenities by name, category, or description.
        """
        q = query.strip().lower()
        if not q:
            return list(self.locations.values())

        matches = []
        for loc in self.locations.values():
            if floor is not None and loc.get("floor") != floor:
                continue

            name = loc.get("name", "").lower()
            category = loc.get("category", "").lower()
            zone = loc.get("zone", "").lower()
            desc = loc.get("description", "").lower()

            # Direct or substring match
            if q in name or q in category or q in zone or q in desc:
                matches.append(loc)

        return matches


# Singleton instance for quick module-level access
_GLOBAL_LOADER: Optional[MallDataLoader] = None


def get_mall_loader() -> MallDataLoader:
    """Return shared MallDataLoader instance."""
    global _GLOBAL_LOADER
    if _GLOBAL_LOADER is None:
        _GLOBAL_LOADER = MallDataLoader()
    return _GLOBAL_LOADER

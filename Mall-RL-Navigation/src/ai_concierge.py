"""
Ambience Mall Gurugram: Official xAI Grok AI Concierge Service.

Architecture:
    User
      ↓
    AI Concierge frontend (components/ai-assistant.tsx & components/mall-app.tsx)
      ↓
    Flask AI endpoint (/api/chat, /api/chat/status)
      ↓
    xAI Grok API (https://api.x.ai/v1)
      ↓
    Tool / Function Calling
      ↓
    MallService (real mall catalog, navigation graph, RL/Q-Learning, Dijkstra)
      ↓
    Real mall data & navigation services
      ↓
    Grok contextual grounded response

Security Rules:
- Never log, expose or return XAI_API_KEY.
- Read XAI_API_KEY strictly on the backend.
- Classify connectivity errors accurately without exposing credentials.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests

logger = logging.getLogger("ai_concierge")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [AI-Concierge] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# -----------------------------------------------------------------------------
# Environment & Configuration
# -----------------------------------------------------------------------------

def _load_env_if_present():
    """Load environment variables from backend or root .env files if present."""
    base_dirs = [
        Path(__file__).resolve().parent.parent,  # Mall-RL-Navigation
        Path(__file__).resolve().parent.parent.parent,  # workspace root
    ]
    for d in base_dirs:
        env_file = d / ".env"
        if env_file.is_file():
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, val = line.split("=", 1)
                            key = key.strip()
                            val = val.strip().strip("'\"")
                            if key:
                                os.environ[key] = val
            except Exception as e:
                logger.warning("Could not read %s: %s", env_file, e)

_load_env_if_present()

XAI_BASE_URL = os.environ.get("XAI_BASE_URL", "https://api.x.ai/v1").rstrip("/")
DEFAULT_MODEL = "grok-4.7"

# Standard error classification types (Phase 3 & Phase 10)
FAILURE_MISSING_API_KEY = "missing_api_key"
FAILURE_INVALID_API_KEY = "invalid_api_key"
FAILURE_INSUFFICIENT_CREDITS = "insufficient_credits"
FAILURE_RATE_LIMIT = "rate_limit"
FAILURE_MODEL_UNAVAILABLE = "model_unavailable"
FAILURE_NETWORK_TIMEOUT = "network_timeout"
FAILURE_INVALID_REQUEST = "invalid_request"
FAILURE_SERVER_ERROR = "server_error"

# -----------------------------------------------------------------------------
# Tool Definitions for xAI Grok (Function Calling)
# -----------------------------------------------------------------------------

GROK_TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_stores",
            "description": (
                "Search verified stores and points of interest in Ambience Mall Gurugram. "
                "Returns genuine store names, categories, floors, coordinates, and entrance nodes. "
                "Always use this tool when a user asks about any brand or store (e.g. ZARA, coffee, Nike)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Store name, brand, or search keyword (e.g. 'ZARA', 'Paul Bakery', 'shoes').",
                    },
                    "category": {
                        "type": "string",
                        "description": (
                            "Filter by mall category: 'Fashion', 'Food & Dining', 'Footwear', 'Beauty & Wellness', "
                            "'Electronics', 'Books & Toys', 'Jewellery & Luxury', 'Watches', 'Home & Lifestyle', 'Services'."
                        ),
                    },
                    "floor": {
                        "type": "integer",
                        "description": "Filter by floor number: 0 (Ground Floor), 1 (First Floor), or 2 (Second Floor).",
                        "enum": [0, 1, 2],
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of stores to return (default 8, max 20).",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_store_details",
            "description": (
                "Retrieve complete verified details for a specific store in Ambience Mall Gurugram by its unique store ID. "
                "Returns floor, entrance coordinates, coordinate frame, and category."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "store_id": {
                        "type": "string",
                        "description": "Exact store ID (e.g. 'G_005' for ZARA, 'S_PAUL_BAKERY', 'F1_010').",
                    },
                },
                "required": ["store_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_floor_information",
            "description": (
                "Get information on all floors in Ambience Mall Gurugram: Ground Floor (0), "
                "First Floor (1), and Second Floor (2), including store counts and coordinate frames."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_nearby_places",
            "description": (
                "Find verified stores or amenities physically close to a specific location in Ambience Mall Gurugram "
                "using the real indoor navigation graph relative path cost."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "location_id": {
                        "type": "string",
                        "description": "Starting location ID (e.g. 'G_005' for ZARA or 'G_GATE_1' for Gate 1).",
                    },
                    "category": {
                        "type": "string",
                        "description": "Optional category filter (e.g. 'Food & Dining', 'Fashion').",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of nearby places to return (default 5).",
                    },
                },
                "required": ["location_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_facilities",
            "description": (
                "Locate mall amenities, entrances, elevator banks, escalators, and customer service desks in Ambience Mall."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "facility_type": {
                        "type": "string",
                        "description": "Type of facility to locate: 'gate', 'elevator', 'escalator', 'restroom', or 'all'.",
                        "enum": ["gate", "elevator", "escalator", "restroom", "all"],
                    },
                    "floor": {
                        "type": "integer",
                        "description": "Filter by floor number: 0 (Ground), 1 (First), 2 (Second).",
                        "enum": [0, 1, 2],
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recommendations",
            "description": (
                "Retrieve curated store recommendations in Ambience Mall Gurugram based on visitor interest or current location."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "preferences": {
                        "type": "string",
                        "description": "Category or interest (e.g. 'Fashion', 'Food & Dining', 'Footwear').",
                    },
                    "location_id": {
                        "type": "string",
                        "description": "Optional anchor store ID for proximity-aware recommendations.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of recommendations to return (default 5).",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_itinerary",
            "description": (
                "Construct an optimized multi-stop visit itinerary across Ambience Mall Gurugram. "
                "Selects genuine stores from the mall catalog and computes real routes between stops using the backend router. "
                "Never fabricates walking distances or times."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "activities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of activities or interests (e.g. ['coffee', 'shopping', 'dining']).",
                    },
                    "duration_hours": {
                        "type": "number",
                        "description": "Requested duration of visit in hours (default 2).",
                    },
                    "start_location_id": {
                        "type": "string",
                        "description": "Starting location ID (defaults to Gate 1 / G_GATE_1).",
                    },
                    "route_mode": {
                        "type": "string",
                        "description": "Routing preference: 'standard', 'accessible' (elevators only), or 'crowd_aware'.",
                        "enum": ["standard", "accessible", "crowd_aware"],
                    },
                },
                "required": ["activities"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "request_navigation",
            "description": (
                "Calculate indoor turn-by-turn navigation between locations in Ambience Mall Gurugram. "
                "Uses the mall's genuine Hybrid RL / Dijkstra routing engine. Returns step-by-step guidance and floor segments."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "destination_id": {
                        "type": "string",
                        "description": "Target store or gate ID (e.g. 'G_005' for ZARA).",
                    },
                    "start_id": {
                        "type": "string",
                        "description": "Starting location ID (defaults to Gate 1 / G_GATE_1).",
                    },
                    "route_mode": {
                        "type": "string",
                        "description": "Route profile: 'standard', 'accessible', or 'crowd_aware'.",
                        "enum": ["standard", "accessible", "crowd_aware"],
                    },
                    "algorithm": {
                        "type": "string",
                        "description": "Algorithm selection: 'auto' (RL policy with Dijkstra fallback), 'rl', or 'dijkstra'.",
                        "enum": ["auto", "rl", "dijkstra"],
                    },
                },
                "required": ["destination_id"],
            },
        },
    },
]

# -----------------------------------------------------------------------------
# System Prompt for Grok Agent
# -----------------------------------------------------------------------------

SYSTEM_PROMPT = """You are **Ambience AI Concierge**, the official, hyper-intelligent, and refined digital shopping and navigation concierge for **Ambience Mall Gurugram** (NH-8, Ambience Island, DLF Phase 3, Sector 24, Gurugram, Haryana 122002).

CORE GROUNDING RULES:
1. Ambience Mall Gurugram has 221 real stores across 3 floors: Ground Floor (0), First Floor (1), and Second Floor (2).
2. NEVER hallucinate or invent store names, store IDs, floor numbers, coordinates, opening hours, or walking distances.
3. When a user asks about any store (e.g. "Where is ZARA?", "Find coffee", "Show fashion on Ground Floor"):
   - Call the `search_stores` tool to obtain verified real store records.
   - If the store is found, state its exact floor and verified details. Offer navigation.
   - If a store cannot be found, honestly state that it is not in the directory.
4. When a user asks for navigation (e.g. "Take me to ZARA", "Navigate to Nike"):
   - Identify the destination store ID and call `request_navigation`.
   - Explain the route clearly, mentioning starting point, floor changes (if any), and connectors.
   - Preserve the true routing engine identity (RL Tabular Q-Learning policy or Dijkstra baseline).
5. When a user asks to plan a visit (e.g. "Plan a 2-hour visit with coffee, shopping and food"):
   - Call `create_itinerary` with the user's requested activities.
   - The tool selects real stores and calculates real routes between destinations.
   - Do NOT fabricate physical walking times or distances; note that path costs are relative graph costs.
6. Tone:
   - Welcoming, polished, efficient, and concise. Use clear markdown with bold headers and bullet points.
   - Do not repeat long boilerplate. Keep responses directly relevant to the user's intent.
"""

# -----------------------------------------------------------------------------
# AI Concierge Service Implementation
# -----------------------------------------------------------------------------

class AIConciergeService:
    """Manages xAI Grok API integration and connects it with Ambience MallService."""

    def __init__(self, mall_service: Any):
        self.svc = mall_service
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "AmbienceMall-AIConcierge/2.0"})

    @property
    def api_key(self) -> Optional[str]:
        # Support XAI_API_KEY or GROQ_API_KEY from environment/.env
        key = (os.environ.get("XAI_API_KEY") or os.environ.get("GROQ_API_KEY") or "").strip()
        return key if key else None

    @property
    def provider(self) -> str:
        key = self.api_key or ""
        if key.startswith("gsk_"):
            return "groq"
        return "xai"

    @property
    def base_url(self) -> str:
        if self.provider == "groq":
            return os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
        return os.environ.get("XAI_BASE_URL", "https://api.x.ai/v1").rstrip("/")

    @property
    def configured_model(self) -> str:
        if self.provider == "groq":
            return os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b").strip()
        return os.environ.get("XAI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL

    # -------------------------------------------------------------------------
    # Phase 3: Backend Connectivity Verification
    # -------------------------------------------------------------------------
    def check_connectivity(self) -> Dict[str, Any]:
        """
        Verify that the backend can connect and authenticate with configured AI provider.
        Auto-detects between official xAI Grok and Groq based on key prefix.
        Distinguishes failure types without logging or exposing the API key.
        """
        key = self.api_key
        model = self.configured_model
        endpoint = self.base_url
        prov_label = "xAI Grok" if self.provider == "xai" else "Groq LPU"

        if not key:
            return {
                "status": "error",
                "failure_type": FAILURE_MISSING_API_KEY,
                "configured": False,
                "provider": self.provider,
                "message": "AI API key is not configured in backend environment. Set XAI_API_KEY or GROQ_API_KEY.",
                "model": model,
                "endpoint": endpoint,
                "available_models": [],
                "test_inference_ok": False,
            }

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

        # Step 1: Reach models endpoint
        models_url = f"{endpoint}/models"
        available_models: List[str] = []
        try:
            resp = self.session.get(models_url, headers=headers, timeout=12)
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "failure_type": FAILURE_NETWORK_TIMEOUT,
                "configured": True,
                "provider": self.provider,
                "message": f"Connection to {prov_label} endpoint {endpoint} timed out.",
                "model": model,
                "endpoint": endpoint,
                "available_models": [],
                "test_inference_ok": False,
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "failure_type": FAILURE_NETWORK_TIMEOUT,
                "configured": True,
                "provider": self.provider,
                "message": f"Failed to connect to {prov_label} endpoint: {type(e).__name__}",
                "model": model,
                "endpoint": endpoint,
                "available_models": [],
                "test_inference_ok": False,
            }

        status_code = resp.status_code
        resp_text = resp.text.lower()

        if status_code in (401, 403) or (status_code == 400 and ("incorrect api key" in resp_text or "invalid" in resp_text)):
            return {
                "status": "error",
                "failure_type": FAILURE_INVALID_API_KEY,
                "configured": True,
                "message": "xAI authentication failed: Invalid API key.",
                "model": model,
                "endpoint": XAI_BASE_URL,
                "available_models": [],
                "test_inference_ok": False,
            }

        if status_code == 402 or "payment" in resp_text or "credit" in resp_text or "billing" in resp_text:
            return {
                "status": "error",
                "failure_type": FAILURE_INSUFFICIENT_CREDITS,
                "configured": True,
                "message": "xAI account has insufficient credits or billing restrictions.",
                "model": model,
                "endpoint": XAI_BASE_URL,
                "available_models": [],
                "test_inference_ok": False,
            }

        if status_code == 429:
            return {
                "status": "error",
                "failure_type": FAILURE_RATE_LIMIT,
                "configured": True,
                "message": "xAI rate limit exceeded.",
                "model": model,
                "endpoint": XAI_BASE_URL,
                "available_models": [],
                "test_inference_ok": False,
            }

            return {
                "status": "error",
                "failure_type": FAILURE_SERVER_ERROR,
                "configured": True,
                "provider": self.provider,
                "message": f"{prov_label} server error (HTTP {status_code}).",
                "model": model,
                "endpoint": endpoint,
                "available_models": [],
                "test_inference_ok": False,
            }

        if status_code != 200:
            return {
                "status": "error",
                "failure_type": FAILURE_INVALID_REQUEST,
                "configured": True,
                "provider": self.provider,
                "message": f"Unexpected response from {prov_label} API (HTTP {status_code}).",
                "model": model,
                "endpoint": endpoint,
                "available_models": [],
                "test_inference_ok": False,
            }

        try:
            data = resp.json()
            if isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
                available_models = [m["id"] for m in data["data"] if "id" in m]
            elif isinstance(data, list):
                available_models = [m.get("id") for m in data if isinstance(m, dict) and "id" in m]
        except Exception:
            available_models = []

        # Step 2: Check if configured model is available
        if available_models and model not in available_models:
            return {
                "status": "error",
                "failure_type": FAILURE_MODEL_UNAVAILABLE,
                "configured": True,
                "provider": self.provider,
                "message": (
                    f"Configured model '{model}' is not available for this API key. "
                    f"Available models: {', '.join(available_models[:8])}"
                ),
                "model": model,
                "endpoint": endpoint,
                "available_models": available_models,
                "test_inference_ok": False,
            }

        # Step 3: Run minimal test prompt
        test_payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Respond with 'ready'"}],
            "max_tokens": 8,
            "temperature": 0.0,
        }
        try:
            test_resp = self.session.post(
                f"{endpoint}/chat/completions",
                headers=headers,
                json=test_payload,
                timeout=15,
            )
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "failure_type": FAILURE_NETWORK_TIMEOUT,
                "configured": True,
                "provider": self.provider,
                "message": "Minimal test inference timed out.",
                "model": model,
                "endpoint": endpoint,
                "available_models": available_models,
                "test_inference_ok": False,
            }
        except Exception as e:
            return {
                "status": "error",
                "failure_type": FAILURE_NETWORK_TIMEOUT,
                "configured": True,
                "provider": self.provider,
                "message": f"Test inference connection error: {type(e).__name__}",
                "model": model,
                "endpoint": endpoint,
                "available_models": available_models,
                "test_inference_ok": False,
            }

        if test_resp.status_code != 200:
            test_text = test_resp.text.lower()
            if "credit" in test_text or "payment" in test_text or "quota" in test_text:
                f_type = FAILURE_INSUFFICIENT_CREDITS
                msg = f"{prov_label} account has insufficient credits for inference."
            elif test_resp.status_code == 429:
                f_type = FAILURE_RATE_LIMIT
                msg = f"{prov_label} rate limit reached during test inference."
            elif "model" in test_text and ("found" in test_text or "access" in test_text):
                f_type = FAILURE_MODEL_UNAVAILABLE
                msg = f"Model '{model}' is not accessible on this account."
            else:
                f_type = FAILURE_INVALID_REQUEST
                msg = f"Test inference returned HTTP {test_resp.status_code}."

            return {
                "status": "error",
                "failure_type": f_type,
                "configured": True,
                "provider": self.provider,
                "message": msg,
                "model": model,
                "endpoint": endpoint,
                "available_models": available_models,
                "test_inference_ok": False,
            }

        return {
            "status": "healthy",
            "failure_type": None,
            "configured": True,
            "provider": self.provider,
            "message": f"{prov_label} API ({model}) is fully authenticated, reachable, and ready.",
            "model": model,
            "endpoint": endpoint,
            "available_models": available_models,
            "test_inference_ok": True,
        }

    # -------------------------------------------------------------------------
    # Phase 5: Controlled Tool Execution Against MallService
    # -------------------------------------------------------------------------
    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[Any]]:
        """
        Execute a validated tool call against MallService.
        Returns: (json_serializable_result, structured_entity_payload)
        """
        logger.info("Executing tool '%s' with args %s", tool_name, args)

        if tool_name == "search_stores":
            query = args.get("query")
            category = args.get("category")
            floor = args.get("floor")
            limit = min(int(args.get("limit") or 8), 20)

            # Validate floor
            if floor is not None and floor not in (0, 1, 2):
                floor = None

            res = self.svc.locations(
                q=query,
                category=category,
                floor=floor,
                kind="store",
                limit=limit,
            )
            # Return concise store records to LLM
            locs = res.get("locations", [])
            output = {
                "total_matches": res.get("total", len(locs)),
                "returned_count": len(locs),
                "stores": [
                    {
                        "id": s["id"],
                        "name": s["name"],
                        "category": s.get("category"),
                        "floor": s.get("floor"),
                        "floor_name": s.get("floor_name"),
                        "entrance_node": s.get("entrance", {}).get("node_id") if s.get("entrance") else None,
                    }
                    for s in locs
                ],
            }
            return output, locs

        elif tool_name == "get_store_details":
            store_id = str(args.get("store_id") or "").strip()
            if not store_id:
                return {"error": "store_id is required"}, None
            try:
                detail = self.svc.location(store_id)
                output = {
                    "found": True,
                    "store": {
                        "id": detail["id"],
                        "name": detail["name"],
                        "category": detail.get("category"),
                        "floor": detail.get("floor"),
                        "floor_name": detail.get("floor_name"),
                        "x": detail.get("x"),
                        "y": detail.get("y"),
                        "entrance": detail.get("entrance"),
                    },
                }
                return output, [detail]
            except Exception:
                return {
                    "found": False,
                    "error": f"Store ID '{store_id}' was not found in Ambience Mall directory.",
                }, None

        elif tool_name == "get_floor_information":
            floors_data = self.svc.floors()
            return floors_data, None

        elif tool_name == "find_nearby_places":
            loc_id = str(args.get("location_id") or "").strip()
            cat = args.get("category")
            limit = min(int(args.get("limit") or 5), 15)
            if not loc_id:
                return {"error": "location_id is required"}, None
            try:
                nearby_data = self.svc.nearby(location_id=loc_id, limit=limit * 2)
                places = nearby_data.get("nearby", [])
                if cat:
                    places = [p for p in places if str(p.get("category", "")).lower() == cat.lower()]
                places = places[:limit]
                output = {
                    "origin": nearby_data.get("origin"),
                    "nearby_stores": [
                        {
                            "id": p["id"],
                            "name": p["name"],
                            "category": p.get("category"),
                            "floor": p.get("floor"),
                            "floor_name": p.get("floor_name"),
                            "relative_cost": p.get("path_cost"),
                        }
                        for p in places
                    ],
                }
                return output, places
            except Exception as e:
                return {"error": f"Failed to find nearby places: {e}"}, None

        elif tool_name == "get_facilities":
            fac_type = (args.get("facility_type") or "all").lower()
            target_floor = args.get("floor")
            if target_floor is not None and target_floor not in (0, 1, 2):
                target_floor = None

            gates = self.svc.loader.gates
            connectors = self.svc.loader.connectors

            results: List[Dict[str, Any]] = []
            if fac_type in ("gate", "all"):
                for g in gates:
                    if target_floor is None or g.get("floor") == target_floor:
                        results.append({
                            "id": g["id"],
                            "name": g["name"],
                            "type": "gate",
                            "floor": g.get("floor"),
                            "floor_name": g.get("floor_name"),
                        })
            if fac_type in ("elevator", "escalator", "all"):
                for c in connectors:
                    if target_floor is None or c.get("floor") == target_floor:
                        ctype = c.get("connector_type") or c.get("type") or ""
                        if fac_type == "elevator" and "lift" not in ctype and "elevator" not in ctype:
                            continue
                        if fac_type == "escalator" and "escalator" not in ctype:
                            continue
                        results.append({
                            "id": c["id"],
                            "name": c["name"],
                            "type": ctype,
                            "floor": c.get("floor"),
                            "floor_name": c.get("floor_name"),
                        })

            return {"facilities": results, "count": len(results)}, None

        elif tool_name == "get_recommendations":
            pref = args.get("preferences") or "All"
            loc_id = args.get("location_id")
            limit = min(int(args.get("limit") or 5), 10)
            rec_data = self.svc.recommendations(location_id=loc_id, category=pref, limit=limit)
            recs = rec_data.get("recommendations", [])
            output = {
                "recommendations": [
                    {
                        "id": r["id"],
                        "name": r["name"],
                        "category": r.get("category"),
                        "floor": r.get("floor"),
                        "floor_name": r.get("floor_name"),
                    }
                    for r in recs
                ],
            }
            return output, recs

        elif tool_name == "create_itinerary":
            activities = args.get("activities") or ["shopping", "coffee", "dining"]
            if isinstance(activities, str):
                activities = [a.strip() for a in activities.split(",") if a.strip()]
            duration = float(args.get("duration_hours") or 2.0)
            start_id = args.get("start_location_id") or self.svc.default_start_id
            route_mode = args.get("route_mode") or "standard"

            itinerary_result = self._build_grounded_itinerary(
                activities=activities,
                duration_hours=duration,
                start_id=start_id,
                route_mode=route_mode,
            )
            return itinerary_result["llm_summary"], itinerary_result

        elif tool_name == "request_navigation":
            dest_id = str(args.get("destination_id") or "").strip()
            start_id = str(args.get("start_id") or self.svc.default_start_id).strip()
            route_mode = args.get("route_mode") or "standard"
            algo = args.get("algorithm") or "auto"

            if not dest_id:
                return {"error": "destination_id is required"}, None

            try:
                route_res = self.svc.route(
                    destination_id=dest_id,
                    start_id=start_id,
                    profile=route_mode,
                    algorithm=algo,
                )
                summary = {
                    "start": route_res["start"]["name"],
                    "destination": route_res["destination"]["name"],
                    "destination_floor": route_res["destination"]["floor_name"],
                    "steps": route_res["steps"],
                    "floor_changes": route_res["floor_changes"],
                    "path_cost": route_res["path_cost"]["value"],
                    "cost_unit": "relative graph cost (not metres)",
                    "walking_time": "not calibrated (dataset policy)",
                    "algorithm_used": route_res["algorithm"],
                    "engine_label": route_res["engine_label"],
                    "is_fallback": route_res["is_fallback"],
                    "directions_steps": [
                        f"Step {d['step']}: {d['text']}" for d in route_res.get("directions", [])[:5]
                    ],
                }
                return summary, route_res
            except Exception as e:
                return {"error": f"Navigation routing error: {e}"}, None

        else:
            return {"error": f"Unknown tool name: {tool_name}"}, None

    # -------------------------------------------------------------------------
    # Phase 7: Real Grounded 2-Hour Itinerary Planner
    # -------------------------------------------------------------------------
    def _build_grounded_itinerary(
        self,
        activities: List[str],
        duration_hours: float,
        start_id: str,
        route_mode: str,
    ) -> Dict[str, Any]:
        """
        Builds a real multi-stop visit itinerary:
        1. Selects genuine candidate stores from the mall catalog for each activity.
        2. Computes genuine routes between consecutive stops using svc.route().
        3. Never hallucinates walking times or distances.
        """
        category_map = {
            "coffee": ("Food & Dining", ["Paul Bakery", "Barista", "Blue Tokai", "Chaayos", "Starbucks"]),
            "cafe": ("Food & Dining", ["Paul Bakery", "Barista", "Blue Tokai"]),
            "shopping": ("Fashion", ["ZARA", "Marks & Spencer", "H&M", "Mango", "Uniqlo"]),
            "fashion": ("Fashion", ["ZARA", "Marks & Spencer", "H&M", "Diesel", "Lacoste"]),
            "food": ("Food & Dining", ["Paul Bakery", "Haldiram", "Chili's", "Wow! Momo"]),
            "dining": ("Food & Dining", ["Paul Bakery", "Haldiram", "Chili's", "Nando's"]),
            "shoes": ("Footwear", ["Nike", "Adidas", "Asics", "Puma", "Skechers"]),
            "footwear": ("Footwear", ["Nike", "Adidas", "Asics", "Puma"]),
            "electronics": ("Electronics", ["Apple", "Croma", "Samsung", "Bose"]),
            "entertainment": ("Books & Toys", ["Hamleys", "LEGO"]),
        }

        chosen_stores: List[Dict[str, Any]] = []
        chosen_ids = set()

        for act in activities:
            act_clean = act.lower().strip()
            target_cat = None
            preferred_names = []

            for k, (cat, names) in category_map.items():
                if k in act_clean:
                    target_cat = cat
                    preferred_names = names
                    break

            # Search genuine stores
            candidates = self.svc.locations(
                category=target_cat,
                kind="store",
                limit=30,
            ).get("locations", [])

            # First try matching preferred brand names
            picked = None
            for pref in preferred_names:
                for c in candidates:
                    if c["id"] not in chosen_ids and pref.lower() in c["name"].lower():
                        picked = c
                        break
                if picked:
                    break

            # Fallback to any matching store in candidate pool
            if not picked:
                for c in candidates:
                    if c["id"] not in chosen_ids:
                        picked = c
                        break

            # Fallback to general pool
            if not picked:
                all_stores = self.svc.locations(kind="store", limit=50).get("locations", [])
                for s in all_stores:
                    if s["id"] not in chosen_ids:
                        picked = s
                        break

            if picked:
                chosen_ids.add(picked["id"])
                chosen_stores.append(picked)

        if not chosen_stores:
            # Fallback to defaults if no activity matched
            default_ids = ["G_005", "G_GATE_1"]
            for did in default_ids:
                try:
                    chosen_stores.append(self.svc.location(did))
                except Exception:
                    pass

        # Calculate actual routes between consecutive stops
        stops: List[Dict[str, Any]] = []
        current_loc_id = start_id
        legs: List[Dict[str, Any]] = []

        labels = ["First Experience", "Midpoint Refreshment", "Grand Finale", "Exploration Stop"]

        for i, store in enumerate(chosen_stores):
            label = labels[i] if i < len(labels) else f"Stop {i+1}"
            route_info = None
            try:
                calc_route = self.svc.route(
                    destination_id=store["id"],
                    start_id=current_loc_id,
                    profile=route_mode,
                )
                route_info = {
                    "from_location": calc_route["start"]["name"],
                    "to_location": calc_route["destination"]["name"],
                    "steps": calc_route["steps"],
                    "relative_path_cost": calc_route["path_cost"]["value"],
                    "floor_changes": calc_route["floor_changes"],
                    "algorithm": calc_route["algorithm"],
                    "engine_label": calc_route["engine_label"],
                    "is_fallback": calc_route["is_fallback"],
                }
                legs.append(calc_route)
                current_loc_id = store["id"]
            except Exception as e:
                logger.warning("Could not calculate route leg to %s: %s", store['id'], e)

            stops.append({
                "step": f"0{i+1}",
                "label": label.upper(),
                "store": {
                    "id": store["id"],
                    "name": store["name"],
                    "floor": store.get("floor_name") or f"Floor {store.get('floor')}",
                    "floorId": store.get("floor", 0),
                    "category": store.get("category", "Retail"),
                    "x": store.get("x"),
                    "y": store.get("y"),
                },
                "reason": f"Selected for {activities[i] if i < len(activities) else 'visit curation'} on {store.get('floor_name')}.",
                "route_from_previous": route_info,
            })

        total_cost = sum((s["route_from_previous"]["relative_path_cost"] for s in stops if s["route_from_previous"]), 0.0)

        llm_summary = {
            "duration_hours": duration_hours,
            "total_stops": len(stops),
            "stops": [
                {
                    "step": s["step"],
                    "store_name": s["store"]["name"],
                    "floor": s["store"]["floor"],
                    "category": s["store"]["category"],
                    "label": s["label"],
                    "leg_route": s["route_from_previous"],
                }
                for s in stops
            ],
            "total_relative_path_cost": round(total_cost, 1),
            "walking_time_note": "Path costs are relative graph edge costs; walking times are not artificially fabricated.",
        }

        return {
            "stops": stops,
            "legs": legs,
            "llm_summary": llm_summary,
        }

    # -------------------------------------------------------------------------
    # Phase 4 & Phase 9: Complete Grok Conversation & Tool Loop
    # -------------------------------------------------------------------------
    def process_chat(
        self,
        messages: List[Dict[str, str]],
        current_floor: Optional[int] = None,
        mock_response_generator: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Process chat with xAI Grok using function calling loop.
        Extracts structured suggestedStores, navigationTarget, action, and route.
        """
        key = self.api_key
        model = self.configured_model

        # If key is missing, return honest error state immediately (Phase 10)
        if not key and not mock_response_generator:
            return {
                "success": False,
                "error": {
                    "code": FAILURE_MISSING_API_KEY,
                    "message": "xAI API key is not configured on the backend server. Set XAI_API_KEY in environment or .env.",
                },
                "reply": (
                    "**xAI Grok API Key Required**\n\n"
                    "The AI Concierge is currently awaiting the xAI API configuration (`XAI_API_KEY`). "
                    "Once configured on the backend server, genuine Grok intelligence will curate your visit."
                ),
                "suggestedStores": [],
                "navigationTarget": None,
                "action": None,
                "route": None,
                "itinerary": None,
            }

        # Build message history with system prompt & context window
        conversation: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        # Keep last 10 messages for conversational context
        for m in messages[-10:]:
            role = "user" if m.get("role") == "user" or m.get("sender") == "user" else "assistant"
            content = m.get("content") or m.get("text") or ""
            if content:
                conversation.append({"role": role, "content": content})

        executed_tools: List[str] = []
        collected_stores: List[Dict[str, Any]] = []
        navigation_target: Optional[Dict[str, Any]] = None
        calculated_route: Optional[Dict[str, Any]] = None
        generated_itinerary: Optional[List[Dict[str, Any]]] = None
        action: Optional[str] = None

        # Tool calling loop (max 4 turns)
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

        final_reply = ""
        max_turns = 4

        for turn in range(max_turns):
            if mock_response_generator:
                llm_response = mock_response_generator(conversation, GROK_TOOLS)
            else:
                payload = {
                    "model": model,
                    "messages": conversation,
                    "tools": GROK_TOOLS,
                    "tool_choice": "auto",
                    "temperature": 0.3,
                    "max_tokens": 1500,
                }
                try:
                    res = self.session.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=25,
                    )
                except requests.exceptions.Timeout:
                    return {
                        "success": False,
                        "error": {"code": FAILURE_NETWORK_TIMEOUT, "message": "xAI Grok API request timed out."},
                        "reply": "I'm having trouble reaching the xAI Grok servers right now. Please try again in a moment.",
                        "suggestedStores": [],
                        "navigationTarget": None,
                        "action": None,
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": {"code": FAILURE_NETWORK_TIMEOUT, "message": str(e)},
                        "reply": f"Connection error: {e}",
                        "suggestedStores": [],
                        "navigationTarget": None,
                        "action": None,
                    }

                if res.status_code != 200:
                    text_err = res.text.lower()
                    code = FAILURE_SERVER_ERROR
                    if res.status_code in (401, 403):
                        code = FAILURE_INVALID_API_KEY
                    elif res.status_code == 402 or "credit" in text_err or "billing" in text_err:
                        code = FAILURE_INSUFFICIENT_CREDITS
                    elif res.status_code == 429:
                        code = FAILURE_RATE_LIMIT
                    elif "model" in text_err:
                        code = FAILURE_MODEL_UNAVAILABLE

                    logger.error("xAI API error (HTTP %s): %s", res.status_code, res.text)
                    return {
                        "success": False,
                        "error": {"code": code, "message": f"xAI API error (HTTP {res.status_code}): {res.text[:120]}"},
                        "reply": f"**xAI Service Error ({code})**\n\nThe AI provider returned HTTP {res.status_code}.",
                        "suggestedStores": [],
                        "navigationTarget": None,
                        "action": None,
                    }

                llm_response = res.json()

            choice = llm_response.get("choices", [{}])[0]
            message = choice.get("message", {})
            conversation.append(message)

            tool_calls = message.get("tool_calls")
            if not tool_calls:
                final_reply = message.get("content") or ""
                break

            # Execute tool calls
            for tc in tool_calls:
                fn_name = tc.get("function", {}).get("name", "")
                fn_args_raw = tc.get("function", {}).get("arguments", "{}")
                executed_tools.append(fn_name)

                try:
                    fn_args = json.loads(fn_args_raw) if isinstance(fn_args_raw, str) else fn_args_raw
                except Exception:
                    fn_args = {}

                tool_result, structured_payload = self.execute_tool(fn_name, fn_args)

                # Track entities for UI actions
                if fn_name == "search_stores" and structured_payload:
                    collected_stores.extend(structured_payload)
                elif fn_name == "get_store_details" and structured_payload:
                    collected_stores.extend(structured_payload)
                elif fn_name == "find_nearby_places" and structured_payload:
                    collected_stores.extend(structured_payload)
                elif fn_name == "request_navigation" and structured_payload:
                    calculated_route = structured_payload
                    navigation_target = structured_payload.get("destination")
                    action = "navigate"
                elif fn_name == "create_itinerary" and structured_payload:
                    generated_itinerary = structured_payload.get("stops")
                    for s in structured_payload.get("stops", []):
                        if s.get("store"):
                            collected_stores.append(s["store"])

                # Append tool response
                conversation.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", f"call_{turn}"),
                    "name": fn_name,
                    "content": json.dumps(tool_result),
                })

        # Deduplicate collected stores
        seen_ids = set()
        deduped_stores = []
        for s in collected_stores:
            sid = s.get("id") or s.get("poi_id")
            if sid and sid not in seen_ids:
                seen_ids.add(sid)
                deduped_stores.append({
                    "id": sid,
                    "name": s.get("name", sid),
                    "category": s.get("category", "Retail"),
                    "floor": s.get("floor_name") or (f"Floor {s.get('floor')}" if s.get("floor") is not None else "Ground Floor"),
                    "floorId": s.get("floor", 0),
                    "x": s.get("x", 500),
                    "y": s.get("y", 500),
                    "entrance": s.get("entrance"),
                })

        # If user explicitly asked for parking or facilities in query, set action
        last_user_query = ""
        for m in reversed(messages):
            if m.get("role") == "user" or m.get("sender") == "user":
                last_user_query = (m.get("content") or m.get("text") or "").lower()
                break

        if not action:
            if any(w in last_user_query for w in ["park", "car", "valet", "basement", "b1", "b2"]):
                action = "parking"
            elif any(w in last_user_query for w in ["washroom", "restroom", "toilet", "lift", "elevator", "escalator"]):
                action = "facilities"
            elif any(w in last_user_query for w in ["call", "helpline", "security", "lost"]):
                action = "call_concierge"
            elif any(w in last_user_query for w in ["take me", "navigate", "route to", "guide me"]) and deduped_stores:
                action = "navigate"
                navigation_target = deduped_stores[0]

        return {
            "success": True,
            "reply": final_reply or "I am ready to assist you in Ambience Mall Gurugram.",
            "suggestedStores": deduped_stores[:6],
            "navigationTarget": navigation_target,
            "action": action,
            "route": calculated_route,
            "itinerary": generated_itinerary,
            "model": model,
            "executed_tools": executed_tools,
        }

# Global singleton instance helper
_ai_concierge_instance: Optional[AIConciergeService] = None

def get_ai_concierge_service(mall_service: Optional[Any] = None) -> AIConciergeService:
    global _ai_concierge_instance
    if _ai_concierge_instance is None:
        if mall_service is None:
            from src.api_service import MallService
            mall_service = MallService()
        _ai_concierge_instance = AIConciergeService(mall_service)
    return _ai_concierge_instance

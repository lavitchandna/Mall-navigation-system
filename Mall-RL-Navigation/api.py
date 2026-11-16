"""
Ambience Mall Gurugram: Flask API for the V0 frontend.

    V0 frontend  ->  this Flask API  ->  Mall-RL-Navigation backend + real data

This file only exposes the existing backend (src/real_map_loader, navigation_graph,
route_planner, recommendation, directions). The navigation algorithms are unchanged.
The old Streamlit UI (app.py) is left intact but is not part of the served application.

Run:
    pip install -r requirements-api.txt
    python api.py                      # http://127.0.0.1:5001

Environment variables:
    MALL_API_HOST          bind address            (default 127.0.0.1)
    MALL_API_PORT          port                    (default 5001)
    MALL_API_CORS_ORIGINS  comma-separated origins (default *)
    MALL_DEFAULT_START     configured route start  (default G_GATE_1)

Endpoints:
    GET  /api/health
    GET  /api/locations[?q=&floor=&category=&type=store|gate|connector|all&limit=]
    GET  /api/locations/<id>
    GET  /api/floors
    GET  /api/floors/<floor_id>/geometry
    POST /api/route                     {destination_location_id, start_location_id?, accessible?}
    GET  /api/recommendations[?location_id=&category=&limit=]
    GET  /api/nearby?location_id=[&max_cost=&limit=]
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Optional

from flask import Flask, Response, jsonify, request

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ai_concierge import get_ai_concierge_service  # noqa: E402
from src.api_service import ApiServiceError, MallService  # noqa: E402

FLOOR_NAME_LOOKUP = {"ground": 0, "ground floor": 0, "first": 1, "first floor": 1, "second": 2, "second floor": 2}


def _error(code: str, message: str, status: int):
    response = jsonify({"error": {"code": code, "message": message}})
    response.status_code = status
    return response


def _int_arg(name: str, default: Optional[int] = None, minimum: int = 0, maximum: int = 500) -> Optional[int]:
    raw = request.args.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ApiServiceError("invalid_parameter", f"{name} must be an integer.", 400)
    if not minimum <= value <= maximum:
        raise ApiServiceError("invalid_parameter", f"{name} must be between {minimum} and {maximum}.", 400)
    return value


def _float_arg(name: str) -> Optional[float]:
    raw = request.args.get(name)
    if raw is None or raw == "":
        return None
    try:
        value = float(raw)
    except ValueError:
        raise ApiServiceError("invalid_parameter", f"{name} must be a number.", 400)
    if value < 0:
        raise ApiServiceError("invalid_parameter", f"{name} must not be negative.", 400)
    return value


def _floor_arg(name: str = "floor") -> Optional[int]:
    """Accepts a floor id (0/1/2) or a floor name ('Ground Floor')."""
    raw = request.args.get(name)
    if raw is None or raw.strip() == "":
        return None
    raw = raw.strip()
    if raw.lstrip("-").isdigit():
        return int(raw)
    if raw.lower() in FLOOR_NAME_LOOKUP:
        return FLOOR_NAME_LOOKUP[raw.lower()]
    raise ApiServiceError("invalid_parameter", f"Unknown floor: {raw}", 400)


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return bool(value)


def create_app(service: Optional[MallService] = None) -> Flask:
    app = Flask(__name__)
    app.json.sort_keys = False
    svc = service or MallService()

    allowed = [o.strip() for o in os.environ.get("MALL_API_CORS_ORIGINS", "*").split(",") if o.strip()]

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get("Origin")
        if "*" in allowed:
            response.headers["Access-Control-Allow-Origin"] = "*"
        elif origin and origin in allowed:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Accept"
        response.headers["Access-Control-Max-Age"] = "600"
        return response

    @app.errorhandler(ApiServiceError)
    def handle_service_error(err: ApiServiceError):
        return _error(err.code, err.message, err.status)

    @app.errorhandler(404)
    def handle_not_found(_err):
        return _error("not_found", "No such endpoint.", 404)

    @app.errorhandler(405)
    def handle_method_not_allowed(_err):
        return _error("method_not_allowed", "Method not allowed for this endpoint.", 405)

    @app.errorhandler(Exception)
    def handle_unexpected(err: Exception):
        app.logger.exception("Unhandled error: %s", err)
        return _error("internal_error", "The navigation service hit an unexpected error.", 500)

    @app.get("/favicon.ico")
    def favicon():
        return Response("", status=204)

    @app.get("/")
    @app.get("/api")
    def index():
        accept = request.headers.get("Accept", "")
        if "text/html" in accept or "*/*" in accept or not accept:
            html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ambience Mall Navigation Engine API</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🧭</text></svg>">
  <style>
    :root {
      --bg: #090d16;
      --card-bg: #111827;
      --border: #1f2937;
      --text: #f3f4f6;
      --text-muted: #9ca3af;
      --primary: #38bdf8;
      --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: var(--font);
      line-height: 1.5;
      padding: 2.5rem 1.5rem;
      min-height: 100vh;
      display: flex;
      justify-content: center;
    }
    .container { max-width: 900px; width: 100%; }
    .header {
      background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
      border: 1px solid #312e81;
      border-radius: 16px;
      padding: 2rem;
      margin-bottom: 2rem;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
    }
    .badge-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 1rem;
      flex-wrap: wrap;
      gap: 0.75rem;
    }
    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      background: rgba(16, 185, 129, 0.15);
      color: #34d399;
      padding: 0.35rem 0.85rem;
      border-radius: 9999px;
      font-size: 0.85rem;
      font-weight: 600;
      border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .status-dot {
      width: 8px;
      height: 8px;
      background: #10b981;
      border-radius: 50%;
      box-shadow: 0 0 8px #10b981;
    }
    h1 { font-size: 1.85rem; font-weight: 700; color: #fff; margin-bottom: 0.5rem; }
    .desc { color: var(--text-muted); font-size: 0.95rem; margin-bottom: 1.5rem; }
    .actions { display: flex; gap: 1rem; flex-wrap: wrap; }
    .btn {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.65rem 1.25rem;
      border-radius: 10px;
      font-size: 0.9rem;
      font-weight: 600;
      text-decoration: none;
      transition: all 0.2s ease;
      cursor: pointer;
    }
    .btn-primary { background: #38bdf8; color: #0f172a; }
    .btn-primary:hover { background: #7dd3fc; transform: translateY(-1px); }
    .btn-secondary { background: #1f2937; color: #f3f4f6; border: 1px solid #374151; }
    .btn-secondary:hover { background: #374151; }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
      margin-bottom: 2rem;
    }
    .stat-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.25rem;
    }
    .stat-val { font-size: 1.6rem; font-weight: 700; color: #fff; }
    .stat-label { color: var(--text-muted); font-size: 0.85rem; margin-top: 0.2rem; }
    .section-title {
      font-size: 1.2rem;
      font-weight: 600;
      color: #fff;
      margin-bottom: 1rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .endpoints {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 14px;
      overflow: hidden;
    }
    .endpoint-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 1rem 1.25rem;
      border-bottom: 1px solid var(--border);
      gap: 1rem;
      flex-wrap: wrap;
    }
    .endpoint-row:last-child { border-bottom: none; }
    .method {
      display: inline-block;
      padding: 0.2rem 0.55rem;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 700;
      min-width: 52px;
      text-align: center;
    }
    .method-get { background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }
    .method-post { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }
    .endpoint-path {
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 0.9rem;
      font-weight: 600;
      color: #e2e8f0;
      text-decoration: none;
    }
    .endpoint-path:hover { color: #38bdf8; text-decoration: underline; }
    .endpoint-info { display: flex; align-items: center; gap: 0.75rem; flex: 1; min-width: 280px; }
    .endpoint-desc { color: var(--text-muted); font-size: 0.85rem; }
    .endpoint-link {
      font-size: 0.8rem;
      color: #38bdf8;
      text-decoration: none;
      padding: 0.3rem 0.65rem;
      border-radius: 6px;
      background: rgba(56, 189, 248, 0.1);
      transition: all 0.15s;
    }
    .endpoint-link:hover { background: rgba(56, 189, 248, 0.2); }
    footer { text-align: center; margin-top: 2rem; color: #6b7280; font-size: 0.85rem; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="badge-bar">
        <div class="status-badge">
          <span class="status-dot"></span>
          Backend Navigation API is Online (Port 5001)
        </div>
        <span style="color: #94a3b8; font-size: 0.85rem;">Hybrid RL + Dijkstra Engine</span>
      </div>
      <h1>Ambience Mall Gurugram Navigation API</h1>
      <p class="desc">
        Source of truth for store directories, floor coordinate graphs, route planning, recommendations, and AI concierge navigation.
      </p>
      <div class="actions">
        <a href="http://localhost:3000" class="btn btn-primary" target="_blank" rel="noopener">
          🚀 Open Frontend Web App (Port 3000)
        </a>
        <a href="/api/health" class="btn btn-secondary">
          🔍 View Health JSON
        </a>
        <a href="/api/locations" class="btn btn-secondary">
          🏬 Browse 221 Stores
        </a>
      </div>
    </div>

    <div class="grid">
      <div class="stat-card">
        <div class="stat-val">221</div>
        <div class="stat-label">Stores & Brands</div>
      </div>
      <div class="stat-card">
        <div class="stat-val">3 Floors</div>
        <div class="stat-label">Ground, First & Second</div>
      </div>
      <div class="stat-card">
        <div class="stat-val">336 Nodes</div>
        <div class="stat-label">Corridors & Gates</div>
      </div>
      <div class="stat-card">
        <div class="stat-val">342k States</div>
        <div class="stat-label">Reinforcement Learning Q-Table</div>
      </div>
    </div>

    <div class="section-title">
      <span>Available API Endpoints</span>
    </div>

    <div class="endpoints">
      <div class="endpoint-row">
        <div class="endpoint-info">
          <span class="method method-get">GET</span>
          <a class="endpoint-path" href="/api/health">/api/health</a>
        </div>
        <div class="endpoint-desc">System health, graph version, model status & counts</div>
        <a class="endpoint-link" href="/api/health">Open &rarr;</a>
      </div>

      <div class="endpoint-row">
        <div class="endpoint-info">
          <span class="method method-get">GET</span>
          <a class="endpoint-path" href="/api/locations">/api/locations</a>
        </div>
        <div class="endpoint-desc">Directory of all stores, gates, and floor connectors</div>
        <a class="endpoint-link" href="/api/locations">Open &rarr;</a>
      </div>

      <div class="endpoint-row">
        <div class="endpoint-info">
          <span class="method method-get">GET</span>
          <a class="endpoint-path" href="/api/floors">/api/floors</a>
        </div>
        <div class="endpoint-desc">List of mall floors and their local coordinate frames</div>
        <a class="endpoint-link" href="/api/floors">Open &rarr;</a>
      </div>

      <div class="endpoint-row">
        <div class="endpoint-info">
          <span class="method method-get">GET</span>
          <a class="endpoint-path" href="/api/floors/0/geometry">/api/floors/0/geometry</a>
        </div>
        <div class="endpoint-desc">Ground floor corridor graph edges and store entrance POIs</div>
        <a class="endpoint-link" href="/api/floors/0/geometry">Open &rarr;</a>
      </div>

      <div class="endpoint-row">
        <div class="endpoint-info">
          <span class="method method-get">GET</span>
          <a class="endpoint-path" href="/api/recommendations?location_id=G_GATE_1&limit=6">/api/recommendations</a>
        </div>
        <div class="endpoint-desc">Top stores ranked by shortest path cost from a point</div>
        <a class="endpoint-link" href="/api/recommendations?location_id=G_GATE_1&limit=6">Open &rarr;</a>
      </div>

      <div class="endpoint-row">
        <div class="endpoint-info">
          <span class="method method-get">GET</span>
          <a class="endpoint-path" href="/api/nearby?location_id=G_GATE_1&limit=6">/api/nearby</a>
        </div>
        <div class="endpoint-desc">Closest stores to entrance/node along walkable graph</div>
        <a class="endpoint-link" href="/api/nearby?location_id=G_GATE_1&limit=6">Open &rarr;</a>
      </div>

      <div class="endpoint-row">
        <div class="endpoint-info">
          <span class="method method-post">POST</span>
          <span class="endpoint-path">/api/route</span>
        </div>
        <div class="endpoint-desc">Computes multi-floor route with turns and elevator/escalator hops</div>
        <span style="font-size: 0.8rem; color: #64748b;">JSON Body</span>
      </div>

      <div class="endpoint-row">
        <div class="endpoint-info">
          <span class="method method-get">GET</span>
          <a class="endpoint-path" href="/api/chat/status">/api/chat/status</a>
        </div>
        <div class="endpoint-desc">AI Concierge model status & Groq API connectivity</div>
        <a class="endpoint-link" href="/api/chat/status">Open &rarr;</a>
      </div>
    </div>

    <footer>
      Ambience Mall Gurugram Integrated System &bull; Flask Port 5001 &bull; Next.js Port 3000
    </footer>
  </div>
</body>
</html>
"""
            return Response(html, mimetype="text/html")

        return jsonify({
            "service": "Ambience Mall Gurugram Navigation API",
            "status": "online",
            "frontend_url": "http://localhost:3000",
            "endpoints": [
                "/api/health",
                "/api/locations",
                "/api/floors",
                "/api/floors/<floor_id>/geometry",
                "/api/route",
                "/api/recommendations",
                "/api/nearby",
                "/api/chat/status",
                "/api/chat",
                "/api/itinerary",
            ]
        })

    @app.get("/api/health")
    def health():
        return jsonify(svc.health())

    @app.get("/api/locations")
    def locations():
        return jsonify(
            svc.locations(
                q=request.args.get("q"),
                floor=_floor_arg("floor"),
                category=request.args.get("category"),
                kind=request.args.get("type", "store"),
                limit=_int_arg("limit", None, 0, 1000),
            )
        )

    @app.get("/api/locations/<path:location_id>")
    def location(location_id: str):
        return jsonify(svc.location(location_id))

    @app.get("/api/floors")
    def floors():
        return jsonify(svc.floors())

    @app.get("/api/floors/<int:floor_id>/geometry")
    def floor_geometry(floor_id: int):
        return jsonify(svc.floor_geometry(floor_id))

    @app.post("/api/route")
    def route():
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            raise ApiServiceError("invalid_body", "Request body must be a JSON object.", 400)
        destination = body.get("destination_location_id") or body.get("destination_id") or body.get("destination")
        start = body.get("start_location_id") or body.get("start_id") or body.get("start")
        for label, value in (("destination_location_id", destination), ("start_location_id", start)):
            if value is not None and not isinstance(value, str):
                raise ApiServiceError("invalid_parameter", f"{label} must be a string.", 400)
        return jsonify(
            svc.route(
                destination,
                start,
                accessible=_bool(body.get("accessible", False)),
                crowd_aware=_bool(body.get("crowd_aware", False)),
                profile=body.get("profile") or body.get("mode"),
                algorithm=body.get("algorithm", "auto"),
            )
        )

    @app.get("/api/recommendations")
    def recommendations():
        return jsonify(
            svc.recommendations(
                location_id=request.args.get("location_id"),
                category=request.args.get("category", "All"),
                limit=_int_arg("limit", 6, 1, 50),
            )
        )

    @app.get("/api/nearby")
    def nearby():
        return jsonify(
            svc.nearby(
                location_id=request.args.get("location_id"),
                max_cost=_float_arg("max_cost"),
                limit=_int_arg("limit", 6, 1, 50),
            )
        )

    ai_concierge = get_ai_concierge_service(svc)

    @app.get("/api/chat/status")
    def chat_status():
        return jsonify(ai_concierge.check_connectivity())

    @app.post("/api/chat")
    def chat():
        body = request.get_json(silent=True) or {}
        messages = body.get("messages", [])
        current_floor = body.get("current_floor") if "current_floor" in body else body.get("currentFloor")
        return jsonify(ai_concierge.process_chat(messages, current_floor=current_floor))

    @app.post("/api/itinerary")
    def itinerary():
        body = request.get_json(silent=True) or {}
        raw_acts = body.get("activities") or body.get("preferences") or ["shopping", "coffee", "dining"]
        if isinstance(raw_acts, str):
            activities = [raw_acts]
        else:
            activities = list(raw_acts)
        duration = float(body.get("duration") or body.get("duration_hours") or 2.0)
        start_id = body.get("start_location_id") or body.get("start_id") or svc.default_start_id
        route_mode = body.get("route_mode") or "standard"
        res = ai_concierge._build_grounded_itinerary(activities, duration, start_id, route_mode)
        return jsonify({
            "success": True,
            "duration_hours": duration,
            "stops": res["stops"],
            "summary": res["llm_summary"],
        })

    return app


_service = MallService()
app = create_app(_service)

if __name__ == "__main__":
    host = os.environ.get("MALL_API_HOST", "0.0.0.0")
    port = int(os.environ.get("MALL_API_PORT", "5001"))
    print(f"Mall navigation API on http://{host}:{port}  (route start: {_service.default_start()['name']})")
    app.run(host=host, port=port, debug=False, threaded=True)

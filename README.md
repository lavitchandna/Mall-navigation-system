# Ambience Mall Gurugram: V0 frontend + Mall-RL-Navigation backend

```
V0 frontend (Next.js)  ->  Flask API (Mall-RL-Navigation/api.py)  ->  real mall data + navigation graph
ambience-mall-app-ui/      Mall-RL-Navigation/                        data/*.json
```

The V0 UI is the only user-facing app. Mall-RL-Navigation is the source of truth for stores,
floors, coordinates, the navigation graph, routes, directions, recommendations and nearby places.

## Run it

**1. Backend** (Python 3.10+)
```bash
cd Mall-RL-Navigation
pip install -r requirements-api.txt
python api.py                 # http://127.0.0.1:5001
```
Optional env vars: `MALL_API_HOST`, `MALL_API_PORT` (default 5001; macOS uses 5000 for AirPlay),
`MALL_API_CORS_ORIGINS` (default `*`), `MALL_DEFAULT_START` (default `G_GATE_1`).

**2. Frontend** (Node 20+)
```bash
cd ambience-mall-app-ui
pnpm install                  # or: npm install
pnpm dev                      # http://localhost:3000
```
`.env.local` already contains `NEXT_PUBLIC_API_URL=http://localhost:5001` (see `.env.example`).

## API

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | status, data counts, planner facts, dataset flags |
| `GET /api/locations` | real store directory (`?q= &floor= &category= &type= &limit=`) |
| `GET /api/locations/<id>` | one store/gate/connector |
| `GET /api/floors` | floors and their coordinate frames |
| `GET /api/floors/<id>/geometry` | real corridor graph + shop POIs for one floor (drives the map) |
| `POST /api/route` | `{destination_location_id, start_location_id?, accessible?}` |
| `GET /api/recommendations` | stores ranked by path cost (`?location_id= &category= &limit=`) |
| `GET /api/nearby?location_id=` | closest stores by graph path |

## What changed

Backend: added `api.py`, `src/api_service.py`, `tests/test_api.py`, `requirements-api.txt`;
`flask` appended to `requirements.txt`; `src/directions.py` gained an optional `show_distances`
argument (default unchanged). No data, model, graph, planner or Streamlit file was modified.

Frontend: `lib/api.ts` (centralized API layer), `components/route-map.tsx` (new SVG floor map),
`components/mall-app.tsx` (data wiring), `app/globals.css` (appended rules only), `.env.*`.
Screens, layout, classes and copy are otherwise the V0 originals. Removed: the invented
"presentation" stores, the fabricated "Opening hours", and the placeholder map.

## Things to know

* **No live positioning.** Routes start from the configured location (Gate 1 by default). The
  map labels it "Start", not "You".
* **Uncalibrated distance.** The UI shows "Relative path cost" and "Walking time: Not calibrated".
* **Floors are separate coordinate frames** and are drawn one at a time; they are never merged.
* **No floor image assets exist** in Mall-RL-Navigation, so the map is drawn from the real graph
  geometry (corridors, shop entrances, connectors) and POI coordinates.
* **Dataset caveats.** The master file says `routing_ready: false`; most corridor/gate/connector
  coordinates are round numbers (hand-placed approximations); category labels are keyword-inferred
  and some store names carry OCR artifacts. These are properties of the source data.
* **Accessible routing** is enforced (elevator-only) but in the current data the standard route
  already always uses the elevator, so the toggle does not change the path.
* **RL:** routing is Dijkstra; the Q-table is preserved but not consulted (see backend README).

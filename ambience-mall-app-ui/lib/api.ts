/**
 * Centralized API layer for the Ambience Mall app.
 *
 *   V0 frontend  ->  Flask API (Mall-RL-Navigation/api.py)  ->  real mall data + navigation graph
 *
 * All network access lives in this file. Components import typed helpers from here and never
 * call fetch directly. Base URL comes from NEXT_PUBLIC_API_URL (see .env.example).
 *
 * Data rules mirrored from the backend:
 *  - Coordinates are floor-local pixel frames. Every coordinate travels with its floor and
 *    floors are never merged into one frame.
 *  - The dataset is not metrically calibrated. Route cost is a *relative path cost* and walking
 *    time is "not calibrated"; nothing in this file converts either into metres or minutes.
 */

// ---------------------------------------------------------------------------------------------
// UI types
// ---------------------------------------------------------------------------------------------

export interface Store {
  id: string
  name: string
  category?: string
  /** Floor label, e.g. "Ground Floor". */
  floor?: string
  floorId?: number
  poi_id?: string
  description?: string
  image?: string
  /** POI coordinates in the store's own floor frame. */
  x?: number
  y?: number
  favourite?: boolean
}

/** A store returned by recommendations / nearby, ranked by relative path cost. */
export interface RankedStore extends Store {
  pathCost?: number
  sameFloor?: boolean
}

export interface Floor {
  id: number
  name: string
  coordinateFrame?: string
  width?: number
  height?: number
  storeCount?: number
}

export interface Place {
  id: string
  name: string
  floorId: number
  floorName: string
  x: number
  y: number
  entrance?: { nodeId: string; x: number; y: number }
}

export interface Directory {
  stores: Store[]
  categories: string[]
  /** The configured route start (there is no live indoor positioning). */
  defaultStart?: Place
  gates?: Place[]
}

export interface RoutePoint {
  id: string
  name: string
  type: string
  floor: number
  floorName: string
  x: number
  y: number
}

/** The part of a route that lies on one floor, in that floor's own coordinate frame. */
export interface RouteSegment {
  floor: number
  floorName: string
  points: RoutePoint[]
}

export type ConnectorType = 'ELEVATOR' | 'ESCALATOR' | 'STAIRS'

export interface RouteConnector {
  type: ConnectorType
  name: string
  accessible: boolean
  from: RoutePoint
  to: RoutePoint
}

export interface RouteDirection {
  step: number
  text: string
  instruction?: string
  kind: string
  floor: number
  floorName: string
}

export type RouteMode = 'standard' | 'crowd_aware' | 'accessible'
export type RouteAlgorithm = 'auto' | 'rl' | 'dijkstra'

export interface RouteEvaluation {
  rl: {
    success: boolean
    validationReason?: string
    steps: number
    pathCost: number
    timeMs: number
    floorChanges: number
    connectors: string[]
    qValuesAtStart: Record<string, number>
    actionsSequence: string[]
  }
  baseline: {
    success: boolean
    steps: number
    pathCost: number
    timeMs: number
    floorChanges: number
    connectors: string[]
  }
  rlPolicyUsed: boolean
  fallbackActive?: boolean
  preferredMethod: 'rl' | 'dijkstra'
  identicalPath: boolean
}

export interface RouteAlternative {
  segments: RouteSegment[]
  connectors: RouteConnector[]
  floors: number[]
  floorChanges: number
  pathCost: number
  steps: number
  status: string
  directions: RouteDirection[]
}

export interface Route {
  start: Place
  destination: Place
  accessible: boolean
  crowdAware?: boolean
  profile?: string
  algorithm?: string
  requestedAlgorithm?: string
  engineLabel?: string
  isFallback?: boolean
  routeIsAccessible: boolean
  accessibilityNote?: string
  segments: RouteSegment[]
  connectors: RouteConnector[]
  /** Floors visited, in order. */
  floors: number[]
  floorChanges: number
  /** Relative graph cost. Not metres. */
  pathCost: number
  steps?: number
  status?: string
  walkingTime: { available: boolean; label: string }
  directions: RouteDirection[]
  notices: string[]
  evaluation?: RouteEvaluation
  comparisonSummary?: string
  alternatives?: {
    rl?: RouteAlternative | null
    baseline?: RouteAlternative | null
  }
}

export interface FloorGeometry {
  floor: number
  name: string
  bounds: { minX: number; maxX: number; minY: number; maxY: number } | null
  /** [x1, y1, x2, y2, spur] where spur = 1 for a corridor-to-shop-entrance hop. */
  edges: Array<[number, number, number, number, number]>
  nodes: Array<{ id: string; name: string; type: string; x: number; y: number }>
  pois: Array<{ id: string; name: string; category?: string; x: number; y: number }>
}

export interface Health {
  status: string
  mall?: string
  counts?: Record<string, number>
  routing?: { algorithm: string; rlPolicyUsed: boolean; qTableLoaded: boolean }
  metricCalibrated: boolean
  datasetRoutingReady?: boolean
  defaultStart?: Place
}

// ---------------------------------------------------------------------------------------------
// Errors + transport
// ---------------------------------------------------------------------------------------------

export type ApiErrorKind = 'config' | 'network' | 'timeout' | 'http'

export class ApiError extends Error {
  kind: ApiErrorKind
  status?: number
  code?: string

  constructor(kind: ApiErrorKind, message: string, status?: number, code?: string) {
    super(message)
    this.name = 'ApiError'
    this.kind = kind
    this.status = status
    this.code = code
  }

  /** True when the backend could not be reached (as opposed to it answering with an error). */
  get isConnection() {
    return this.kind !== 'http'
  }
}

const baseUrl = (process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_MALL_API_URL || 'http://127.0.0.1:5001').trim().replace(/\/+$/, '')
const REQUEST_TIMEOUT_MS = 10_000

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  if (!baseUrl) {
    throw new ApiError('config', 'The mall service address is not configured. Set NEXT_PUBLIC_API_URL in .env.local.')
  }

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)
  try {
    let response: Response
    try {
      response = await fetch(`${baseUrl}${path}`, {
        ...init,
        signal: controller.signal,
        headers: { Accept: 'application/json', ...init?.headers },
      })
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        throw new ApiError('timeout', 'The mall service took too long to respond.')
      }
      throw new ApiError('network', 'Cannot reach the mall service. Check that the backend is running.')
    }

    if (!response.ok) {
      let message = `The mall service returned an error (${response.status}).`
      let code: string | undefined
      try {
        const body = (await response.json()) as { error?: { message?: string; code?: string } }
        if (body.error?.message) message = body.error.message
        code = body.error?.code
      } catch {
        /* non-JSON error body: keep the generic message */
      }
      throw new ApiError('http', message, response.status, code)
    }

    try {
      return (await response.json()) as T
    } catch {
      throw new ApiError('http', 'The mall service sent a response that could not be read.', response.status)
    }
  } finally {
    clearTimeout(timer)
  }
}

// ---------------------------------------------------------------------------------------------
// Raw (backend) shapes + adapters
// ---------------------------------------------------------------------------------------------

interface RawLocation {
  id: string
  poi_id?: string | null
  name: string
  type?: string
  category?: string
  floor: number
  floor_name: string
  x: number
  y: number
  entrance?: { node_id: string; x: number; y: number } | null
  path_cost?: { value: number | null }
  same_floor?: boolean
}

interface RawPoint {
  id: string
  name: string
  type: string
  floor: number
  floor_name: string
  x: number
  y: number
}

function toStore(raw: RawLocation): Store {
  return {
    id: raw.id,
    poi_id: raw.poi_id ?? raw.id,
    name: raw.name,
    category: raw.category,
    floor: raw.floor_name,
    floorId: raw.floor,
    x: raw.x,
    y: raw.y,
  }
}

function toRanked(raw: RawLocation): RankedStore {
  return { ...toStore(raw), pathCost: raw.path_cost?.value ?? undefined, sameFloor: raw.same_floor }
}

function toPlace(raw: RawLocation): Place {
  return {
    id: raw.id,
    name: raw.name,
    floorId: raw.floor,
    floorName: raw.floor_name,
    x: raw.x,
    y: raw.y,
    entrance: raw.entrance ? { nodeId: raw.entrance.node_id, x: raw.entrance.x, y: raw.entrance.y } : undefined,
  }
}

function toPoint(raw: RawPoint): RoutePoint {
  return { id: raw.id, name: raw.name, type: raw.type, floor: raw.floor, floorName: raw.floor_name, x: raw.x, y: raw.y }
}

// ---------------------------------------------------------------------------------------------
// Endpoints
// ---------------------------------------------------------------------------------------------

/** GET /api/health */
export async function getHealth(): Promise<Health> {
  const raw = await request<{
    status: string
    mall?: string
    counts?: Record<string, number>
    routing?: { algorithm: string; rl_policy_used: boolean; q_table_loaded: boolean }
    metric_calibrated: boolean
    dataset_routing_ready?: boolean
    default_start?: RawLocation
  }>('/api/health')
  return {
    status: raw.status,
    mall: raw.mall,
    counts: raw.counts,
    routing: raw.routing && {
      algorithm: raw.routing.algorithm,
      rlPolicyUsed: raw.routing.rl_policy_used,
      qTableLoaded: raw.routing.q_table_loaded,
    },
    metricCalibrated: raw.metric_calibrated,
    datasetRoutingReady: raw.dataset_routing_ready,
    defaultStart: raw.default_start && toPlace(raw.default_start),
  }
}

/** GET /api/locations: the real store directory (POI ids, floors, categories). */
export async function getLocations(): Promise<Directory> {
  const raw = await request<{ locations: RawLocation[]; categories?: string[]; default_start?: RawLocation; gates?: RawLocation[] }>('/api/locations')
  return {
    stores: raw.locations.map(toStore),
    categories: raw.categories ?? [],
    defaultStart: raw.default_start && toPlace(raw.default_start),
    gates: raw.gates?.map(toPlace) ?? [],
  }
}

/** GET /api/locations/<id> */
export async function getLocation(id: string): Promise<Store> {
  return toStore(await request<RawLocation>(`/api/locations/${encodeURIComponent(id)}`))
}

/** GET /api/floors */
export async function getFloors(): Promise<Floor[]> {
  const raw = await request<{
    floors: Array<{ id: number; name: string; coordinate_frame?: string; width?: number; height?: number; store_count?: number }>
  }>('/api/floors')
  return raw.floors.map(f => ({
    id: f.id,
    name: f.name,
    coordinateFrame: f.coordinate_frame,
    width: f.width,
    height: f.height,
    storeCount: f.store_count,
  }))
}

/** GET /api/floors/<id>/geometry: the real walkable graph + shop POIs for one floor. */
export async function getFloorGeometry(floorId: number): Promise<FloorGeometry> {
  const raw = await request<{
    floor: number
    name: string
    bounds: { min_x: number; max_x: number; min_y: number; max_y: number } | null
    edges: FloorGeometry['edges']
    nodes: FloorGeometry['nodes']
    pois: FloorGeometry['pois']
  }>(`/api/floors/${floorId}/geometry`)
  return {
    floor: raw.floor,
    name: raw.name,
    bounds: raw.bounds && { minX: raw.bounds.min_x, maxX: raw.bounds.max_x, minY: raw.bounds.min_y, maxY: raw.bounds.max_y },
    edges: raw.edges,
    nodes: raw.nodes,
    pois: raw.pois,
  }
}

export interface RouteOptions {
  startId?: string
  accessible?: boolean
  crowdAware?: boolean
  profile?: RouteMode
  algorithm?: RouteAlgorithm
}

/**
 * POST /api/route
 * `startId` is optional: without it the backend uses its configured start location
 * (there is no live indoor positioning).
 */
export async function getRoute(destinationId: string, options: RouteOptions = {}): Promise<Route> {
  const effectiveProfile = options.profile || (options.accessible ? 'accessible' : (options.crowdAware ? 'crowd_aware' : 'standard'))
  const raw = await request<{
    start: RawLocation
    destination: RawLocation
    accessible: boolean
    crowd_aware?: boolean
    profile?: string
    algorithm?: string
    requested_algorithm?: string
    engine_label?: string
    is_fallback?: boolean
    route_is_accessible: boolean
    accessibility_note?: string
    segments: Array<{ floor: number; floor_name: string; points: RawPoint[] }>
    connectors: Array<{ type: ConnectorType; name: string; accessible: boolean; from: RawPoint; to: RawPoint }>
    floors: number[]
    floor_changes: number
    path_cost: { value: number }
    steps?: number
    walking_time: { available: boolean; label: string }
    directions: Array<{ step: number; text: string; kind: string; floor: number; floor_name: string }>
    notices: string[]
    evaluation?: any
    comparison_summary?: string
    alternatives?: {
      rl?: any
      baseline?: any
    }
  }>('/api/route', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      destination_location_id: destinationId,
      ...(options.startId ? { start_location_id: options.startId } : {}),
      accessible: options.accessible ?? (effectiveProfile === 'accessible'),
      crowd_aware: options.crowdAware ?? (effectiveProfile === 'crowd_aware'),
      profile: effectiveProfile,
      algorithm: options.algorithm ?? 'auto',
    }),
  })

  const parseAlternative = (alt: any): RouteAlternative | null => {
    if (!alt || !alt.segments) return null
    return {
      segments: alt.segments.map((s: any) => ({ floor: s.floor, floorName: s.floor_name, points: (s.points || []).map(toPoint) })),
      connectors: (alt.connectors || []).map((c: any) => ({
        type: c.type,
        name: c.name,
        accessible: c.accessible,
        from: toPoint(c.from),
        to: toPoint(c.to),
      })),
      floors: alt.floors || [],
      floorChanges: alt.floor_changes || 0,
      pathCost: alt.path_cost?.value ?? 0,
      steps: alt.steps || 0,
      status: alt.status || '',
      directions: (alt.directions || []).map((d: any) => ({
        step: d.step,
        text: d.text,
        instruction: d.text,
        kind: d.kind,
        floor: d.floor,
        floorName: d.floor_name,
      })),
    }
  }

  return {
    start: toPlace(raw.start),
    destination: toPlace(raw.destination),
    accessible: raw.accessible,
    crowdAware: raw.crowd_aware,
    profile: raw.profile,
    algorithm: raw.algorithm,
    requestedAlgorithm: raw.requested_algorithm,
    engineLabel: raw.engine_label,
    isFallback: raw.is_fallback,
    routeIsAccessible: raw.route_is_accessible,
    accessibilityNote: raw.accessibility_note,
    segments: raw.segments.map(s => ({ floor: s.floor, floorName: s.floor_name, points: s.points.map(toPoint) })),
    connectors: raw.connectors.map(c => ({
      type: c.type,
      name: c.name,
      accessible: c.accessible,
      from: toPoint(c.from),
      to: toPoint(c.to),
    })),
    floors: raw.floors,
    floorChanges: raw.floor_changes,
    pathCost: raw.path_cost.value,
    steps: raw.steps ?? raw.segments.reduce((acc, s) => acc + s.points.length, 0),
    walkingTime: raw.walking_time,
    directions: raw.directions.map(d => ({
      step: d.step,
      text: d.text,
      instruction: d.text,
      kind: d.kind,
      floor: d.floor,
      floorName: d.floor_name,
    })),
    notices: raw.notices,
    evaluation: raw.evaluation ? {
      rl: {
        success: raw.evaluation.rl?.success ?? false,
        validationReason: raw.evaluation.rl?.validation_reason,
        steps: raw.evaluation.rl?.steps ?? 0,
        pathCost: raw.evaluation.rl?.path_cost ?? 0,
        timeMs: raw.evaluation.rl?.time_ms ?? 0,
        floorChanges: raw.evaluation.rl?.floor_changes ?? 0,
        connectors: raw.evaluation.rl?.connectors ?? [],
        qValuesAtStart: raw.evaluation.rl?.q_values_at_start ?? {},
        actionsSequence: raw.evaluation.rl?.actions_sequence ?? [],
      },
      baseline: {
        success: raw.evaluation.baseline?.success ?? false,
        steps: raw.evaluation.baseline?.steps ?? 0,
        pathCost: raw.evaluation.baseline?.path_cost ?? 0,
        timeMs: raw.evaluation.baseline?.time_ms ?? 0,
        floorChanges: raw.evaluation.baseline?.floor_changes ?? 0,
        connectors: raw.evaluation.baseline?.connectors ?? [],
      },
      rlPolicyUsed: raw.evaluation.rl_policy_used ?? false,
      fallbackActive: raw.evaluation.fallback_active ?? false,
      preferredMethod: raw.evaluation.preferred_method ?? 'rl',
      identicalPath: raw.evaluation.identical_path ?? false,
    } : undefined,
    comparisonSummary: raw.comparison_summary,
    alternatives: raw.alternatives ? {
      rl: parseAlternative(raw.alternatives.rl),
      baseline: parseAlternative(raw.alternatives.baseline),
    } : undefined,
  }
}

/** GET /api/recommendations: stores ranked by relative path cost from a location (default: configured start). */
export async function getRecommendations(locationId?: string, limit = 6): Promise<RankedStore[]> {
  const params = new URLSearchParams({ limit: String(limit) })
  if (locationId) params.set('location_id', locationId)
  const raw = await request<{ recommendations: RawLocation[] }>(`/api/recommendations?${params}`)
  return raw.recommendations.map(toRanked)
}

/** GET /api/nearby: stores closest to a location by graph path. */
export async function getNearby(locationId: string, limit = 4): Promise<RankedStore[]> {
  const params = new URLSearchParams({ location_id: locationId, limit: String(limit) })
  const raw = await request<{ nearby: RawLocation[] }>(`/api/nearby?${params}`)
  return raw.nearby.map(toRanked)
}

// ---------------------------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------------------------

export function getErrorMessage(error: unknown, fallback = 'Navigation service unavailable. Please try again.') {
  if (error instanceof ApiError && error.isConnection) {
    return fallback
  }
  return error instanceof Error ? error.message : fallback
}

export function floorLabel(floor: Store['floor']) {
  return floor === undefined || floor === null || floor === '' ? 'Floor unavailable' : String(floor)
}

export function storeMark(store: Pick<Store, 'name'>) {
  return store.name.slice(0, 12)
}

export function connectorLabel(type: ConnectorType) {
  return type === 'ELEVATOR' ? 'Elevator' : type === 'ESCALATOR' ? 'Escalator' : 'Stairs'
}

export type { Store as Brand }



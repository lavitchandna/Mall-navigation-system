'use client'

import React, { useEffect, useMemo, useRef, useState } from 'react'
import { connectorLabel, type FloorGeometry, type Route, type RouteSegment } from '@/lib/api'
import { getFloorMapUrl, transformFloorPoint } from '@/lib/calibration'
import { getStoreBranding } from '@/lib/store-branding'

const RED = '#ed1b2f'
const BLUE = '#2563eb'

const MAP_WIDTH = 1024
const MAP_HEIGHT = 1536

interface Box {
  x: number
  y: number
  w: number
  h: number
}

export interface RouteMapProps {
  floorId: number
  floorName: string
  geometry?: FloorGeometry
  segments: RouteSegment[]
  route?: Route
  showStores: boolean
  zoom: number
  resetKey: number
  note?: string
}

function computeFit(
  floorId: number,
  segments: RouteSegment[],
  route?: Route
): Box {
  const activeSeg = segments.find(s => s.floor === floorId)
  const pts: Array<{ x: number; y: number }> = []

  if (activeSeg && activeSeg.points.length > 0) {
    for (const p of activeSeg.points) {
      pts.push(transformFloorPoint(p.x, p.y, floorId))
    }
  }

  if (route && route.destination.floorId === floorId) {
    pts.push(transformFloorPoint(route.destination.x, route.destination.y, floorId))
  }
  if (route && route.start.floorId === floorId) {
    pts.push(transformFloorPoint(route.start.x, route.start.y, floorId))
  }

  if (pts.length >= 2) {
    const xs = pts.map(p => p.x)
    const ys = pts.map(p => p.y)
    const minX = Math.min(...xs)
    const maxX = Math.max(...xs)
    const minY = Math.min(...ys)
    const maxY = Math.max(...ys)

    const minSpan = 320
    const w = Math.max(maxX - minX, minSpan)
    const h = Math.max(maxY - minY, minSpan)
    const pad = Math.max(w, h) * 0.35
    const cx = (minX + maxX) / 2
    const cy = (minY + maxY) / 2
    const extraBottom = Math.max(w, h) * 0.15

    return {
      x: Math.max(0, cx - w / 2 - pad),
      y: Math.max(0, cy - h / 2 - pad),
      w: Math.min(MAP_WIDTH, w + pad * 2),
      h: Math.min(MAP_HEIGHT, h + pad * 2 + extraBottom),
    }
  }

  return { x: 0, y: 0, w: MAP_WIDTH, h: MAP_HEIGHT }
}

export default function RouteMap({
  floorId,
  floorName,
  geometry,
  segments,
  route,
  showStores,
  zoom,
  resetKey,
  note,
}: RouteMapProps) {
  const wrapRef = useRef<HTMLDivElement>(null)
  const [size, setSize] = useState({ w: 360, h: 480 })
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [dragging, setDragging] = useState(false)
  const drag = useRef<{ x: number; y: number } | null>(null)

  useEffect(() => {
    const el = wrapRef.current
    if (!el || typeof ResizeObserver === 'undefined') return
    const observer = new ResizeObserver(() => {
      const r = el.getBoundingClientRect()
      if (r.width > 0 && r.height > 0) setSize({ w: r.width, h: r.height })
    })
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  const segmentKey = segments.map(s => s.points.length).join(',')
  useEffect(() => {
    setPan({ x: 0, y: 0 })
  }, [resetKey, floorId, segmentKey])

  const fit = useMemo(() => computeFit(floorId, segments, route), [floorId, segments, route])

  // ViewBox calculations based on container aspect ratio
  const aspect = size.w / size.h
  let vw = fit.w
  let vh = fit.h
  if (vw / vh > aspect) {
    vh = vw / aspect
  } else {
    vw = vh * aspect
  }
  vw /= zoom
  vh /= zoom

  const cx = fit.x + fit.w / 2 + pan.x
  const cy = fit.y + fit.h / 2 + pan.y
  const unit = vw / size.w // floor units per screen pixel
  const px = (n: number) => n * unit

  const onPointerDown = (e: React.PointerEvent<SVGSVGElement>) => {
    drag.current = { x: e.clientX, y: e.clientY }
    setDragging(true)
    e.currentTarget.setPointerCapture(e.pointerId)
  }
  const onPointerMove = (e: React.PointerEvent<SVGSVGElement>) => {
    if (!drag.current) return
    const dx = e.clientX - drag.current.x
    const dy = e.clientY - drag.current.y
    drag.current = { x: e.clientX, y: e.clientY }
    setPan(p => ({ x: p.x - dx * unit, y: p.y - dy * unit }))
  }
  const endDrag = () => {
    drag.current = null
    setDragging(false)
  }

  const onThisFloor = (f: number) => f === floorId
  const first = route?.segments[0]
  const last = route ? route.segments[route.segments.length - 1] : undefined

  // Transformed start, end and destination points
  const rawStart = route && first && onThisFloor(first.floor) ? first.points[0] : undefined
  const startPoint = rawStart ? transformFloorPoint(rawStart.x, rawStart.y, floorId) : undefined

  const rawEnd = route && last && onThisFloor(last.floor) ? last.points[last.points.length - 1] : undefined
  const endPoint = rawEnd ? transformFloorPoint(rawEnd.x, rawEnd.y, floorId) : undefined

  const destOnFloor = route && onThisFloor(route.destination.floorId)
  const destPoint = destOnFloor ? transformFloorPoint(route.destination.x, route.destination.y, floorId) : undefined
  const destBranding = useMemo(() => route ? getStoreBranding(route.destination) : null, [route])

  // Transformed route polyline points for active segments on this floor
  const transformedSegments = useMemo(() => {
    return segments.map(seg => ({
      ...seg,
      points: seg.points.map(p => transformFloorPoint(p.x, p.y, floorId)),
    }))
  }, [segments, floorId])

  // Transformed vertical connector marks on this floor
  const routeConnectors = useMemo(() => {
    return (route?.connectors ?? []).flatMap(c => {
      const marks: Array<{ key: string; x: number; y: number; label: string; isOut: boolean }> = []
      if (onThisFloor(c.from.floor)) {
        const pt = transformFloorPoint(c.from.x, c.from.y, floorId)
        marks.push({
          key: `${c.from.id}-out`,
          x: pt.x,
          y: pt.y,
          label: `Take ${connectorLabel(c.type)} to ${c.to.floorName}`,
          isOut: true,
        })
      }
      if (onThisFloor(c.to.floor)) {
        const pt = transformFloorPoint(c.to.x, c.to.y, floorId)
        marks.push({
          key: `${c.to.id}-in`,
          x: pt.x,
          y: pt.y,
          label: `${connectorLabel(c.type)} from ${c.from.floorName}`,
          isOut: false,
        })
      }
      return marks
    })
  }, [route, floorId])

  const mapImgUrl = getFloorMapUrl(floorId)

  return (
    <div ref={wrapRef} className="map-canvas">
      <svg
        className={`map-svg${dragging ? ' dragging' : ''}`}
        viewBox={`${cx - vw / 2} ${cy - vh / 2} ${vw} ${vh}`}
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label={`${floorName} map`}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={endDrag}
        onPointerCancel={endDrag}
      >
        <defs>
          <linearGradient id="routeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#ff2e43" />
            <stop offset="100%" stopColor="#dc2626" />
          </linearGradient>

          <linearGradient id="destPinGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#ef4444" />
            <stop offset="100%" stopColor="#b91c1c" />
          </linearGradient>

          <filter id="pinShadow" x="-30%" y="-30%" width="160%" height="160%">
            <feDropShadow dx="0" dy="3" stdDeviation="3" floodColor="#000000" floodOpacity="0.3" />
          </filter>

          <filter id="badgeShadow" x="-25%" y="-25%" width="150%" height="150%">
            <feDropShadow dx="0" dy="2" stdDeviation="2.5" floodColor="#000000" floodOpacity="0.2" />
          </filter>
        </defs>

        {/* 1. VISUAL BASE: Official Mall Floor Map Image */}
        <image
          href={mapImgUrl}
          x="0"
          y="0"
          width={MAP_WIDTH}
          height={MAP_HEIGHT}
          preserveAspectRatio="xMidYMid meet"
        />

        {/* 2. OPTIONAL STORE HIGHLIGHTS (When toggled) */}
        {showStores && geometry && (
          <g data-layer="store-highlights">
            {geometry.pois.map(p => {
              const pt = transformFloorPoint(p.x, p.y, floorId)
              const isTarget = destOnFloor && route?.destination.id === p.id
              if (isTarget) return null
              const branding = getStoreBranding(p)

              return (
                <g key={p.id} transform={`translate(${pt.x}, ${pt.y})`}>
                  <circle
                    r={px(6)}
                    fill={branding.bgColor}
                    stroke="#ffffff"
                    strokeWidth={px(1.5)}
                    filter="url(#badgeShadow)"
                  />
                  <text
                    y={px(2)}
                    fontSize={px(4.8)}
                    fontWeight="800"
                    textAnchor="middle"
                    fill={branding.textColor}
                    style={{ pointerEvents: 'none', userSelect: 'none' }}
                  >
                    {branding.monogram.slice(0, 2)}
                  </text>
                  <title>{p.name} ({p.category})</title>
                </g>
              )
            })}
          </g>
        )}

        {/* 3. NAVIGATION ROUTE OVERLAY */}
        <g data-layer="route">
          {transformedSegments.map((s, i) => {
            const pointsStr = s.points.map(p => `${p.x},${p.y}`).join(' ')
            return (
              <g key={`route-seg-${i}`}>
                {/* Outer route glow casing */}
                <polyline
                  points={pointsStr}
                  fill="none"
                  stroke="rgba(237, 27, 47, 0.28)"
                  strokeWidth={px(16)}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                {/* White border casing for high contrast against map */}
                <polyline
                  points={pointsStr}
                  fill="none"
                  stroke="#ffffff"
                  strokeWidth={px(8)}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                {/* Core Ambience Red Route */}
                <polyline
                  points={pointsStr}
                  fill="none"
                  stroke="url(#routeGrad)"
                  strokeWidth={px(5.5)}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                {/* Animated Directional Walking Flow */}
                <polyline
                  points={pointsStr}
                  fill="none"
                  stroke="#ffffff"
                  strokeWidth={px(2.2)}
                  strokeDasharray={`${px(6)} ${px(14)}`}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="route-flow-line"
                />
              </g>
            )
          })}

          {/* Entrance node -> POI store destination hop */}
          {endPoint && destPoint && (
            <line
              x1={endPoint.x}
              y1={endPoint.y}
              x2={destPoint.x}
              y2={destPoint.y}
              stroke={RED}
              strokeWidth={px(3)}
              strokeDasharray={`${px(4)} ${px(4)}`}
              strokeLinecap="round"
            />
          )}
        </g>

        {/* 4. FLOOR TRANSITION CONNECTOR BADGES */}
        {routeConnectors.map(m => (
          <g key={m.key} data-layer="route-connector">
            <g transform={`translate(${m.x}, ${m.y - px(18)})`}>
              <rect
                x={-px(60)}
                y={-px(12)}
                width={px(120)}
                height={px(24)}
                rx={px(12)}
                fill="#1e293b"
                stroke="#ffffff"
                strokeWidth={px(1.5)}
                filter="url(#badgeShadow)"
              />
              <text
                x={0}
                y={px(3.5)}
                fontSize={px(9)}
                fontWeight="700"
                textAnchor="middle"
                fill="#ffffff"
              >
                {m.label}
              </text>
            </g>
            <circle cx={m.x} cy={m.y} r={px(8)} fill="#1e293b" stroke="#ffffff" strokeWidth={px(2)} />
            <circle cx={m.x} cy={m.y} r={px(3)} fill="#ffffff" />
          </g>
        ))}

        {/* 5. START LOCATION PIN (Indoor GPS Beacon) */}
        {startPoint && (
          <g data-layer="start-beacon">
            {/* Pulsing beacon radar */}
            <circle
              cx={startPoint.x}
              cy={startPoint.y}
              r={px(16)}
              fill="rgba(37, 99, 235, 0.25)"
              className="beacon-pulse"
            />
            {/* Core blue beacon */}
            <circle
              cx={startPoint.x}
              cy={startPoint.y}
              r={px(8.5)}
              fill={BLUE}
              stroke="#ffffff"
              strokeWidth={px(2.5)}
              filter="url(#pinShadow)"
            />
            <circle cx={startPoint.x} cy={startPoint.y} r={px(3)} fill="#ffffff" />

            {/* Start Callout Pill */}
            <g transform={`translate(${startPoint.x}, ${startPoint.y - px(20)})`}>
              <rect
                x={-px(30)}
                y={-px(11)}
                width={px(60)}
                height={px(20)}
                rx={px(10)}
                fill="#2563eb"
                stroke="#ffffff"
                strokeWidth={px(1.5)}
                filter="url(#badgeShadow)"
              />
              <text
                x={0}
                y={px(3.5)}
                fontSize={px(9.5)}
                fontWeight="700"
                textAnchor="middle"
                fill="#ffffff"
              >
                Start
              </text>
            </g>
          </g>
        )}

        {/* 6. DESTINATION MARKER (Ambience Red 3D Pin & Highlight Card) */}
        {destPoint && (
          <g data-layer="destination-pin">
            {/* Ground shadow */}
            <ellipse
              cx={destPoint.x}
              cy={destPoint.y + px(3)}
              rx={px(8)}
              ry={px(3.5)}
              fill="rgba(0, 0, 0, 0.3)"
            />

            {/* Destination Store Callout Card with Brand Logo Emblem */}
            <g transform={`translate(${destPoint.x}, ${destPoint.y - px(34)})`}>
              <rect
                x={-px(75)}
                y={-px(14)}
                width={px(150)}
                height={px(28)}
                rx={px(14)}
                fill="#ffffff"
                stroke={destBranding?.bgColor || '#ed1b2f'}
                strokeWidth={px(2)}
                filter="url(#pinShadow)"
              />
              {/* Brand mini circle emblem */}
              <circle
                cx={-px(58)}
                cy={0}
                r={px(9.5)}
                fill={destBranding?.bgColor || '#ed1b2f'}
              />
              <text
                x={-px(58)}
                y={px(3)}
                fontSize={px(6.5)}
                fontWeight="800"
                textAnchor="middle"
                fill={destBranding?.textColor || '#ffffff'}
                style={{ userSelect: 'none' }}
              >
                {destBranding?.monogram}
              </text>
              <text
                x={px(8)}
                y={px(3.5)}
                fontSize={px(10)}
                fontWeight="800"
                textAnchor="middle"
                fill="#0f172a"
              >
                {route?.destination.name.slice(0, 18)}
              </text>
            </g>

            {/* Downward pointer triangle */}
            <polygon
              points={`${destPoint.x - px(7)},${destPoint.y - px(10)} ${destPoint.x + px(7)},${destPoint.y - px(10)} ${destPoint.x},${destPoint.y + px(2)}`}
              fill="#dc2626"
            />

            {/* Pin head */}
            <circle
              cx={destPoint.x}
              cy={destPoint.y - px(18)}
              r={px(12)}
              fill="url(#destPinGrad)"
              stroke="#ffffff"
              strokeWidth={px(2.5)}
              filter="url(#pinShadow)"
            />
            <circle cx={destPoint.x} cy={destPoint.y - px(18)} r={px(4.5)} fill="#ffffff" />
          </g>
        )}
      </svg>

      {note && <div className="map-note">{note}</div>}
    </div>
  )
}

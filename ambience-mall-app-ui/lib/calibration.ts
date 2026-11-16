import calibrationData from './floor-calibration.json'

interface FloorCalibration {
  src_pts: [number, number][]
  weights: [number, number][]
  affine: [number, number][]
}

/**
 * Deterministic coordinate transformation from backend graph/POI coordinates
 * to the visual floor map image pixel space (1024 x 1536).
 */
export function transformFloorPoint(
  x: number,
  y: number,
  floorId: number
): { x: number; y: number } {
  const calib = (calibrationData as unknown as Record<string, FloorCalibration>)[String(floorId)]
  if (!calib) {
    return { x, y }
  }

  const { src_pts, weights, affine } = calib
  let u = affine[0][0] + affine[1][0] * x + affine[2][0] * y
  let v = affine[0][1] + affine[1][1] * x + affine[2][1] * y

  for (let i = 0; i < src_pts.length; i++) {
    const dx = x - src_pts[i][0]
    const dy = y - src_pts[i][1]
    const distSq = dx * dx + dy * dy
    if (distSq > 1e-6) {
      const r = Math.sqrt(distSq)
      const kernel = r * r * Math.log(r)
      u += weights[i][0] * kernel
      v += weights[i][1] * kernel
    }
  }

  // Constrain inside image frame
  const clampedX = Math.max(20, Math.min(1004, u))
  const clampedY = Math.max(20, Math.min(1516, v))

  return {
    x: Math.round(clampedX * 10) / 10,
    y: Math.round(clampedY * 10) / 10,
  }
}

export function getFloorMapUrl(floorId: number): string {
  if (floorId === 1) return '/maps/first-floor.png'
  if (floorId === 2) return '/maps/second-floor.png'
  return '/maps/ground-floor.png'
}

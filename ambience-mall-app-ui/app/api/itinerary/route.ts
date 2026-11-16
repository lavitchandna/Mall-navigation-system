import { NextRequest, NextResponse } from 'next/server'

const MALL_API_URL = (
  process.env.NEXT_PUBLIC_MALL_API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://127.0.0.1:5001'
).replace(/\/+$/, '')

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const res = await fetch(`${MALL_API_URL}/api/itinerary`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(body),
      cache: 'no-store',
    })

    if (!res.ok) {
      return NextResponse.json(
        { success: false, error: `Flask itinerary returned HTTP ${res.status}` },
        { status: res.status }
      )
    }

    const data = await res.json()
    return NextResponse.json(data)
  } catch (err: any) {
    return NextResponse.json(
      { success: false, error: err?.message || 'Failed to reach itinerary backend' },
      { status: 500 }
    )
  }
}

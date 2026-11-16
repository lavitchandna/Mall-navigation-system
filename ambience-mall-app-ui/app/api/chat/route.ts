import { NextRequest, NextResponse } from 'next/server'

function getBackendBaseUrl(): string {
  const url =
    process.env.MALL_API_URL ||
    process.env.NEXT_PUBLIC_MALL_API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    'http://127.0.0.1:5001'
  return url.replace(/\/+$/, '')
}

export async function GET() {
  try {
    const targetUrl = new URL('/api/chat/status', getBackendBaseUrl())
    const res = await fetch(targetUrl, {
      headers: { Accept: 'application/json' },
      cache: 'no-store',
    })
    if (res.ok) {
      const data = await res.json()
      return NextResponse.json(data)
    }
    return NextResponse.json(
      {
        status: 'error',
        failure_type: 'server_error',
        configured: false,
        message: `Mall backend returned status HTTP ${res.status}`,
      },
      { status: res.status }
    )
  } catch (err: any) {
    return NextResponse.json(
      {
        status: 'error',
        failure_type: 'network_timeout',
        configured: false,
        message: 'Could not connect to Mall AI backend service on port 5001.',
      },
      { status: 503 }
    )
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { messages = [], currentFloor = null } = body

    // Forward to Flask backend which executes xAI Grok and real mall tools
    const targetUrl = new URL('/api/chat', getBackendBaseUrl())
    const flaskRes = await fetch(targetUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({
        messages,
        current_floor: currentFloor,
      }),
      cache: 'no-store',
    })

    if (!flaskRes.ok) {
      const errText = await flaskRes.text()
      console.warn(`Flask AI endpoint error (HTTP ${flaskRes.status}):`, errText)
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'backend_error',
            message: `Mall AI Service returned HTTP ${flaskRes.status}`,
          },
          reply:
            '**AI Concierge Notice**\n\nThe AI navigation service encountered an issue. You can still search all 221 stores, view floor maps, and request turn-by-turn routes directly in the app.',
          suggestedStores: [],
          navigationTarget: null,
          action: null,
        },
        { status: 200 }
      )
    }

    const data = await flaskRes.json()
    return NextResponse.json(data)
  } catch (error: any) {
    console.error('Error forwarding chat request to backend:', error)
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'network_error',
          message: error?.message || 'Failed to reach Flask AI endpoint',
        },
        reply:
          '**Backend Connection Notice**\n\nUnable to reach the Ambience Mall backend service. Please check that the navigation backend is running on port 5001.',
        suggestedStores: [],
        navigationTarget: null,
        action: null,
      },
      { status: 200 }
    )
  }
}

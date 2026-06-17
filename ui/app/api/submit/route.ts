import { NextRequest, NextResponse } from 'next/server'

const FASTAPI = process.env.FASTAPI_URL ?? 'http://localhost:8000'

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const res = await fetch(`${FASTAPI}/api/v1/project/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await res.json()
    if (!res.ok) {
      const detail = data.detail
      const message = Array.isArray(detail)
        ? detail.map((e: { msg?: string }) => e.msg ?? 'Invalid field').join('. ')
        : typeof detail === 'string' ? detail : 'Something went wrong. Please try again.'
      return NextResponse.json({ ok: false, message }, { status: res.status })
    }
    return NextResponse.json(data)
  } catch {
    return NextResponse.json(
      { ok: false, message: 'Unable to reach the server. Please try again shortly.' },
      { status: 503 }
    )
  }
}

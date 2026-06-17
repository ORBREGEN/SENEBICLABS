import { NextRequest, NextResponse } from 'next/server'

const FASTAPI = process.env.FASTAPI_URL ?? 'http://localhost:8000'

export async function GET(req: NextRequest) {
  const key = req.headers.get('x-admin-key') ?? ''
  try {
    const res = await fetch(`${FASTAPI}/api/v1/project/admin/submissions`, {
      headers: { 'X-Admin-Key': key },
      cache: 'no-store',
    })
    const data = await res.json()
    if (!res.ok) {
      const detail = data.detail
      const message = typeof detail === 'string' ? detail : 'Request failed.'
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

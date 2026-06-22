import { NextRequest, NextResponse } from 'next/server'

const FASTAPI = process.env.FASTAPI_URL ?? 'http://localhost:8000'

export async function GET(req: NextRequest) {
  const token = req.nextUrl.searchParams.get('token') ?? ''
  const project = req.nextUrl.searchParams.get('project') ?? ''
  try {
    const res = await fetch(
      `${FASTAPI}/api/v1/project/portal/results?token=${encodeURIComponent(token)}&project_id=${encodeURIComponent(project)}`,
      { cache: 'no-store' }
    )
    const data = await res.json()
    if (!res.ok) {
      const detail = data.detail
      const message = typeof detail === 'string' ? detail : 'Could not load results.'
      return NextResponse.json({ ok: false, message }, { status: res.status })
    }
    return NextResponse.json(data)
  } catch {
    return NextResponse.json({ ok: false, message: 'Unable to reach the server.' }, { status: 503 })
  }
}

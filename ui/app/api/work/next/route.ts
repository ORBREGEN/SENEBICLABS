import { NextRequest, NextResponse } from 'next/server'

const FASTAPI = process.env.FASTAPI_URL ?? 'http://localhost:8000'

export async function GET(req: NextRequest) {
  const code = req.headers.get('x-work-code') ?? ''
  const project = req.nextUrl.searchParams.get('project') ?? ''
  try {
    const res = await fetch(
      `${FASTAPI}/api/v1/project/work/next?project_id=${encodeURIComponent(project)}`,
      { headers: { 'X-Work-Code': code }, cache: 'no-store' }
    )
    const data = await res.json()
    if (!res.ok) {
      const detail = data.detail
      const message = typeof detail === 'string' ? detail : 'Could not load the next item.'
      return NextResponse.json({ ok: false, message }, { status: res.status })
    }
    return NextResponse.json(data)
  } catch {
    return NextResponse.json({ ok: false, message: 'Unable to reach the server.' }, { status: 503 })
  }
}

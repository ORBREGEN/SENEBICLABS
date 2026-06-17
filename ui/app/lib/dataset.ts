// Parse a customer's dataset file (CSV or JSON) into work items.
// Each row/record becomes one item; its columns/keys become the item content.

export type ParsedDataset = {
  items: Record<string, unknown>[]
  columns: string[]
}

// RFC-4180-ish CSV parser: handles quoted fields, escaped "" quotes,
// and commas / newlines inside quotes.
export function parseCSV(text: string): Record<string, string>[] {
  const rows: string[][] = []
  let field = ''
  let row: string[] = []
  let inQuotes = false
  let i = 0

  while (i < text.length) {
    const c = text[i]
    if (inQuotes) {
      if (c === '"') {
        if (text[i + 1] === '"') { field += '"'; i += 2; continue }
        inQuotes = false; i++; continue
      }
      field += c; i++; continue
    }
    if (c === '"') { inQuotes = true; i++; continue }
    if (c === ',') { row.push(field); field = ''; i++; continue }
    if (c === '\r') { i++; continue }
    if (c === '\n') { row.push(field); rows.push(row); field = ''; row = []; i++; continue }
    field += c; i++
  }
  if (field.length > 0 || row.length > 0) { row.push(field); rows.push(row) }
  if (!rows.length) return []

  const headers = rows[0].map(h => h.trim())
  return rows
    .slice(1)
    .filter(r => r.some(c => c.trim() !== ''))
    .map(r => {
      const obj: Record<string, string> = {}
      headers.forEach((h, idx) => { obj[h] = (r[idx] ?? '').trim() })
      return obj
    })
}

export function parseDataset(filename: string, text: string): ParsedDataset {
  const trimmed = text.trim()
  const looksJson = filename.toLowerCase().endsWith('.json') || trimmed.startsWith('[') || trimmed.startsWith('{')

  if (looksJson) {
    const data = JSON.parse(trimmed)
    const arr = Array.isArray(data) ? data : [data]
    const items = arr.map(x =>
      x && typeof x === 'object' && !Array.isArray(x) ? (x as Record<string, unknown>) : { value: x }
    )
    const columns = Array.from(new Set(items.flatMap(o => Object.keys(o))))
    return { items, columns }
  }

  const rows = parseCSV(text)
  const columns = rows.length ? Object.keys(rows[0]) : []
  return { items: rows, columns }
}

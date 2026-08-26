import { CareerEntity } from '@/types/career'

/** Path segment for an open record: slug when present, otherwise the id. */
export function recordUrlSegment(item: CareerEntity): string {
  const slug = typeof item.slug === 'string' ? item.slug.trim() : ''
  return encodeURIComponent(slug || String(item.id))
}

export function matchesRecordSegment(item: CareerEntity, segment: string): boolean {
  let decoded = segment
  try {
    decoded = decodeURIComponent(segment)
  } catch {
    decoded = segment
  }
  if (String(item.id) === decoded || String(item.id) === segment) return true
  const slug = typeof item.slug === 'string' ? item.slug.trim() : ''
  return Boolean(slug && (slug === decoded || slug === segment))
}

export function recordSegmentFromPath(pathname: string, listPath: string): string | undefined {
  const base = listPath.replace(/\/$/, '')
  if (pathname === base) return undefined
  if (!pathname.startsWith(`${base}/`)) return undefined
  const rest = pathname.slice(base.length + 1)
  const segment = rest.split('/')[0]
  return segment || undefined
}

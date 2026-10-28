import React from 'react'
import { ComposableMap, Geographies, Geography, Marker } from 'react-simple-maps'
import type { GeoJsonObject } from 'geojson'
// Bundled locally (world-atlas, low-res 110m) instead of fetching a CDN
// topojson on every page load or at runtime - Vite inlines this as a parsed
// JS module, so there's no extra network request to render the map.
import worldGeoDataRaw from 'world-atlas/countries-110m.json'
import { EmptyState } from './MetricsCharts'

// react-simple-maps's `geography` prop type is declared as GeoJsonObject,
// but its own docs/examples pass a TopoJSON Topology object directly (it
// detects and converts TopoJSON internally via topojson-client) - this cast
// bridges that upstream type-declaration gap, the runtime data is correct.
const worldGeoData = worldGeoDataRaw as unknown as GeoJsonObject

export interface LocationPoint {
  city: string | null
  country: string | null
  latitude: number
  longitude: number
  count: number
}

const MIN_RADIUS = 3
const MAX_RADIUS = 18

/** Area (not radius) proportional to the visit count - the standard
 * proportional-symbol/bubble-map convention, since a linear radius scale
 * visually exaggerates differences between values. */
function radiusFor(count: number, maxCount: number): number {
  if (maxCount <= 0) return MIN_RADIUS
  const scale = Math.sqrt(count / maxCount)
  return MIN_RADIUS + scale * (MAX_RADIUS - MIN_RADIUS)
}

const locationLabel = (point: LocationPoint): string => {
  const place = [point.city, point.country].filter(Boolean).join(', ') || 'Ubicación desconocida'
  return `${place}: ${point.count} visita${point.count === 1 ? '' : 's'}`
}

export const WorldBubbleMap: React.FC<{ data: LocationPoint[] }> = ({ data }) => {
  if (data.length === 0) {
    return <EmptyState message="Aún no hay visitas con ubicación registrada." />
  }

  const maxCount = Math.max(...data.map((d) => d.count))

  return (
    <div data-testid="world-bubble-map">
      <ComposableMap projectionConfig={{ scale: 140 }} style={{ width: '100%', height: 'auto' }}>
        <Geographies geography={worldGeoData}>
          {({ geographies }) =>
            geographies.map((geo) => (
              <Geography
                key={geo.rsmKey}
                geography={geo}
                fill="var(--bg-glass)"
                stroke="var(--border)"
                strokeWidth={0.5}
                style={{ outline: 'none' }}
              />
            ))
          }
        </Geographies>
        {data.map((point, i) => (
          <Marker key={`${point.city ?? ''}-${point.country ?? ''}-${i}`} coordinates={[point.longitude, point.latitude]}>
            <circle
              r={radiusFor(point.count, maxCount)}
              fill="var(--primary-color)"
              fillOpacity={0.55}
              stroke="var(--primary-color)"
              strokeWidth={1}
            >
              <title>{locationLabel(point)}</title>
            </circle>
          </Marker>
        ))}
      </ComposableMap>
    </div>
  )
}

const cache = new Map()

export async function reverseGeocode({latitude, longitude}) {
  const key = `${latitude.toFixed(5)},${longitude.toFixed(5)}`
  if (cache.has(key)) return cache.get(key)

  const base = import.meta.env.VITE_PHOTON_URL || 'https://photon.komoot.io'
  const url = new URL(`${base.replace(/\/$/, '')}/reverse`)
  url.search = new URLSearchParams({lat: latitude, lon: longitude, layer: 'street', limit: 1, radius: 0.2})
  const response = await fetch(url, {signal: AbortSignal.timeout(10000)})
  if (!response.ok) throw new Error('Address lookup failed')
  const data = await response.json()
  const place = data.features?.[0]?.properties
  const street = place?.street || (place?.osm_key === 'highway' ? place.name : '')
  if (!street) throw new Error('No street found nearby')

  const result = {
    street,
    area: [...new Set([place.district, place.city || place.county, place.state].filter(Boolean))].join(' · '),
  }
  cache.set(key, result)
  return result
}

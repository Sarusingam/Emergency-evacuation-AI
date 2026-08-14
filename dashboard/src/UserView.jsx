import { useState, useEffect, useCallback, useRef } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline, Circle, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { Link } from 'react-router-dom'

const API = '/api/user'
const POLL_MS = 3000

/* ── Custom Leaflet Icons for Hyderabad GIS Mode ───────────── */

const userIcon = L.divIcon({
  className: 'custom-marker user-marker',
  html: '<div class="marker-pin user-pin"><span>📍</span></div>',
  iconSize: [36, 36],
  iconAnchor: [18, 36],
  popupAnchor: [0, -36],
})

const exitIcon = L.divIcon({
  className: 'custom-marker exit-marker',
  html: '<div class="marker-pin exit-pin"><span>🚪</span></div>',
  iconSize: [32, 32],
  iconAnchor: [16, 32],
  popupAnchor: [0, -32],
})

const destIcon = L.divIcon({
  className: 'custom-marker dest-marker',
  html: '<div class="marker-pin dest-pin"><span>🏁</span></div>',
  iconSize: [40, 40],
  iconAnchor: [20, 40],
  popupAnchor: [0, -40],
})

const zoneIcon = L.divIcon({
  className: 'custom-marker zone-marker',
  html: '<div class="marker-pin zone-pin"><span>📌</span></div>',
  iconSize: [28, 28],
  iconAnchor: [14, 28],
  popupAnchor: [0, -28],
})

/* ── Leaflet Fit Bounds & View Setter ───────────────────────── */

function MapController({ coords, userZoneCoords }) {
  const map = useMap()

  useEffect(() => {
    if (userZoneCoords && userZoneCoords[0] && userZoneCoords[1]) {
      map.setView(userZoneCoords, 13, { animate: true })
    } else if (coords && coords.length > 1) {
      const validCoords = coords.filter(c => c[0] > 15 && c[0] < 20 && c[1] > 75 && c[1] < 82)
      if (validCoords.length > 1) {
        const bounds = L.latLngBounds(validCoords.map(c => [c[0], c[1]]))
        map.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 })
      }
    }
  }, [coords, userZoneCoords, map])

  return null
}

/* ── 1. DEMO MAP VIEW (Hyderabad Synthetic Topology SVG) ────── */

function DemoMapView({ mapData, selectedZone, routeData, isActive }) {
  if (!mapData) return null

  const allRoads = mapData.all_roads || []
  const allZones = mapData.all_zones || []
  const allExits = mapData.all_exits || []
  const routeRoads = mapData.route_roads || []
  const userZone = mapData.user_zone
  const destination = mapData.destination
  const riskZones = isActive ? (mapData.risk_zones || []) : []

  return (
    <div className="demo-map-canvas-container" role="region" aria-label="Hyderabad Evacuation Topology Map">
      <svg className="demo-svg-map" viewBox="0 0 920 600" preserveAspectRatio="xMidYMid meet">
        {/* Background Grid Pattern */}
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255, 255, 255, 0.04)" strokeWidth="1" />
          </pattern>
          <filter id="glow-green" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
          <filter id="glow-red" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="5" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
          <filter id="glow-indigo" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        <rect width="100%" height="100%" fill="#0a0e1a" />
        <rect width="100%" height="100%" fill="url(#grid)" />

        {/* Outer Ring / Hyderabad City Boundary Ambience */}
        <ellipse cx="460" cy="300" rx="420" ry="260" fill="none" stroke="rgba(99, 102, 241, 0.08)" strokeWidth="2" strokeDasharray="8 8" />
        <text x="460" y="580" fill="rgba(148, 163, 184, 0.4)" fontSize="11" fontWeight="700" textAnchor="middle" letterSpacing="0.1em">
          HYDERABAD OPERATIONAL EVACUATION GRID — PROTOTYPE SIMULATION
        </text>

        {/* Risk Zone Halos (only when emergency is active) */}
        {riskZones.map(rz => (
          <circle
            key={rz.id}
            cx={rz.grid_x}
            cy={rz.grid_y}
            r="65"
            fill={rz.risk_level === 'CRITICAL' ? 'rgba(239, 68, 68, 0.18)' : 'rgba(245, 158, 11, 0.14)'}
            stroke={rz.risk_level === 'CRITICAL' ? '#ef4444' : '#f59e0b'}
            strokeWidth="2"
            strokeDasharray="4 4"
            className="risk-circle-pulse"
          />
        ))}

        {/* Roads (Edges) */}
        {allRoads.map(road => {
          const isRoute = routeRoads.includes(road.id)
          const isBlocked = isActive && road.blocked
          const isCongested = isActive && road.congestion > 0.6 && !isBlocked

          let strokeColor = '#334155'
          let strokeWidth = 4
          let strokeDasharray = 'none'
          let filter = 'none'

          if (isBlocked) {
            strokeColor = '#ff1744'
            strokeWidth = 6
            strokeDasharray = '8 6'
            filter = 'url(#glow-red)'
          } else if (isRoute) {
            strokeColor = '#00e676'
            strokeWidth = 8
            filter = 'url(#glow-green)'
          } else if (isCongested) {
            strokeColor = '#ff9100'
            strokeWidth = 5
            strokeDasharray = '6 4'
          }

          const midX = (road.from_grid.x + road.to_grid.x) / 2
          const midY = (road.from_grid.y + road.to_grid.y) / 2

          return (
            <g key={road.id} className="svg-road-group">
              {/* Road line */}
              <line
                x1={road.from_grid.x}
                y1={road.from_grid.y}
                x2={road.to_grid.x}
                y2={road.to_grid.y}
                stroke={strokeColor}
                strokeWidth={strokeWidth}
                strokeDasharray={strokeDasharray}
                strokeLinecap="round"
                filter={filter}
                className={isRoute ? 'animated-route-line' : ''}
              />

              {/* Road Label / Badge */}
              {isBlocked ? (
                <g transform={`translate(${midX}, ${midY})`}>
                  <rect x="-44" y="-12" width="88" height="24" rx="6" fill="#1e1b4b" stroke="#ff1744" strokeWidth="2" />
                  <text x="0" y="4" fill="#ff1744" fontSize="10" fontWeight="900" textAnchor="middle">
                    🚧 BLOCKED ({road.id.replace('road_', '').toUpperCase()})
                  </text>
                </g>
              ) : isRoute ? (
                <g transform={`translate(${midX}, ${midY})`}>
                  <rect x="-38" y="-11" width="76" height="22" rx="6" fill="#064e3b" stroke="#00e676" strokeWidth="1.5" />
                  <text x="0" y="4" fill="#00e676" fontSize="9.5" fontWeight="800" textAnchor="middle">
                    {isActive ? 'RECOMMENDED' : 'DESIGNATED'}
                  </text>
                </g>
              ) : (
                <g transform={`translate(${midX}, ${midY})`}>
                  <rect x="-16" y="-9" width="32" height="18" rx="4" fill="#1e293b" stroke="#475569" strokeWidth="1" />
                  <text x="0" y="3" fill="#94a3b8" fontSize="8.5" fontWeight="700" textAnchor="middle">
                    {road.id.replace('road_', '').toUpperCase()}
                  </text>
                </g>
              )}
            </g>
          )
        })}

        {/* Peripheral Evacuation Exits */}
        {allExits.map(exit => {
          const isDest = destination?.id === exit.id
          return (
            <g key={exit.id} transform={`translate(${exit.grid_x}, ${exit.grid_y})`}>
              <rect
                x="-42"
                y="-26"
                width="84"
                height="52"
                rx="10"
                fill={isDest ? '#064e3b' : '#0f172a'}
                stroke={isDest ? '#00e676' : '#3b82f6'}
                strokeWidth={isDest ? 3 : 2}
                filter={isDest ? 'url(#glow-green)' : 'none'}
              />
              <text x="0" y="-6" fill={isDest ? '#00e676' : '#3b82f6'} fontSize="14" textAnchor="middle">
                {isDest ? '🏁' : '🚪'}
              </text>
              <text x="0" y="13" fill="#f8fafc" fontSize="9.5" fontWeight="800" textAnchor="middle">
                {exit.name.includes('(') ? exit.name.split('(')[1].replace(')', '') : exit.name}
              </text>
              {isDest && (
                <g transform="translate(0, -36)">
                  <rect x="-42" y="-10" width="84" height="20" rx="5" fill="#00e676" />
                  <text x="0" y="4" fill="#064e3b" fontSize="9" fontWeight="900" textAnchor="middle">
                    YOUR EXIT
                  </text>
                </g>
              )}
            </g>
          )
        })}

        {/* Hyderabad Operational Zones */}
        {allZones.map(zone => {
          const isUser = zone.is_user_zone
          const shortName = zone.name.includes(' - ') ? zone.name.split(' - ')[1] : zone.name
          const code = zone.name.includes(' - ') ? zone.name.split(' - ')[0] : zone.id.replace('zone_', '').toUpperCase()

          return (
            <g key={zone.id} transform={`translate(${zone.grid_x}, ${zone.grid_y})`}>
              {/* User Zone pulse ring */}
              {isUser && (
                <circle cx="0" cy="0" r="44" fill="none" stroke="#6366f1" strokeWidth="2" className="user-zone-pulse" />
              )}

              <circle
                cx="0"
                cy="0"
                r="32"
                fill={isUser ? '#312e81' : '#1e293b'}
                stroke={isUser ? '#6366f1' : '#64748b'}
                strokeWidth={isUser ? 3.5 : 2}
                filter={isUser ? 'url(#glow-indigo)' : 'none'}
              />
              <text x="0" y="-6" fill="#f8fafc" fontSize="12" fontWeight="900" textAnchor="middle">
                {code}
              </text>
              <text x="0" y="9" fill={isUser ? '#a5b4fc' : '#cbd5e1'} fontSize="9.5" fontWeight="800" textAnchor="middle">
                {shortName}
              </text>
              <text x="0" y="22" fill="#94a3b8" fontSize="8" fontWeight="600" textAnchor="middle">
                👥 {zone.crowd_count}
              </text>

              {/* User Location Label */}
              {isUser && (
                <g transform="translate(0, -44)">
                  <rect x="-50" y="-11" width="100" height="22" rx="6" fill="#6366f1" />
                  <text x="0" y="4" fill="#ffffff" fontSize="9" fontWeight="900" textAnchor="middle">
                    📍 YOU ARE HERE
                  </text>
                </g>
              )}
            </g>
          )
        })}
      </svg>

      {/* Demo Map Legend */}
      <div className="demo-map-legend" aria-label="Hyderabad Evacuation Map Legend">
        <div className="legend-item"><span className="legend-swatch route-swatch" />{isActive ? 'Recommended Route' : 'Designated Corridor'}</div>
        <div className="legend-item"><span className="legend-swatch blocked-swatch" />Blocked Road</div>
        <div className="legend-item"><span className="legend-swatch congested-swatch" />Heavy Traffic</div>
        <div className="legend-item"><span className="legend-swatch normal-swatch" />Open Road</div>
      </div>
    </div>
  )
}

/* ── 2. REAL MAP VIEW (Hyderabad OpenStreetMap Leaflet View) ── */

function RealMapView({ mapData, isActive }) {
  if (!mapData) return null

  const fitCoords = []
  if (mapData.route_coords?.length) fitCoords.push(...mapData.route_coords)
  if (mapData.user_zone) fitCoords.push([mapData.user_zone.lat, mapData.user_zone.lon])
  if (mapData.destination) fitCoords.push([mapData.destination.lat, mapData.destination.lon])
  mapData.all_exits?.forEach(e => fitCoords.push([e.lat, e.lon]))

  const userZoneCoords = mapData.user_zone ? [mapData.user_zone.lat, mapData.user_zone.lon] : null
  const defaultCenter = [17.4100, 78.4700] // Real Hyderabad center (Hussain Sagar / City Center)

  return (
    <div className="real-map-container" role="region" aria-label="Hyderabad OpenStreetMap GIS View">
      <MapContainer
        key={mapData.user_zone ? `${mapData.user_zone.id}` : 'hyd-center'}
        center={userZoneCoords || (mapData.map_center ? [mapData.map_center.lat, mapData.map_center.lon] : defaultCenter)}
        zoom={12}
        style={{ width: '100%', height: '100%' }}
        zoomControl={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <MapController coords={fitCoords} userZoneCoords={userZoneCoords} />

        {/* All Hyderabad zone markers */}
        {mapData.all_zones?.filter(z => !z.is_user_zone).map(z => (
          <Marker key={z.id} position={[z.lat, z.lon]} icon={zoneIcon}>
            <Popup><strong>{z.name}</strong><br />Simulated Crowd: {z.crowd_count} people</Popup>
          </Marker>
        ))}

        {/* User zone marker */}
        {mapData.user_zone && (
          <Marker position={[mapData.user_zone.lat, mapData.user_zone.lon]} icon={userIcon}>
            <Popup><strong>📍 You are in {mapData.user_zone.name}</strong><br />Follow the AI evacuation route.</Popup>
          </Marker>
        )}

        {/* Exits / Evacuation Points */}
        {mapData.all_exits?.map(e => {
          const isDest = mapData.destination?.id === e.id
          return (
            <Marker key={e.id} position={[e.lat, e.lon]} icon={isDest ? destIcon : exitIcon}>
              <Popup>{isDest ? <strong>🏁 YOUR SAFE DESTINATION: {e.name}</strong> : e.name}</Popup>
            </Marker>
          )
        })}

        {/* Recommended Evacuation Route Polyline */}
        {mapData.route_coords?.length >= 2 && (
          <Polyline
            positions={mapData.route_coords}
            pathOptions={{ color: '#00e676', weight: 6, opacity: 0.9, dashArray: '12 6' }}
          />
        )}

        {/* Blocked roads (only when emergency active) */}
        {isActive && mapData.blocked_segments?.map(seg => (
          <Polyline
            key={seg.road_id}
            positions={seg.coords}
            pathOptions={{ color: '#ff1744', weight: 5, opacity: 0.85, dashArray: '4 8' }}
          >
            <Popup>🚧 <strong>BLOCKED ROAD</strong>: {seg.name}</Popup>
          </Polyline>
        ))}

        {/* Congested roads (only when emergency active) */}
        {isActive && mapData.congested_segments?.map(seg => (
          <Polyline
            key={seg.road_id}
            positions={seg.coords}
            pathOptions={{ color: '#ff9100', weight: 4, opacity: 0.7, dashArray: '6 6' }}
          >
            <Popup>⚠️ Heavy Traffic: {seg.name}</Popup>
          </Polyline>
        ))}

        {/* Risk zones (only when emergency active) */}
        {isActive && mapData.risk_zones?.map(rz => (
          <Circle
            key={rz.id}
            center={[rz.lat, rz.lon]}
            radius={rz.radius || 400}
            pathOptions={{
              color: rz.risk_level === 'CRITICAL' ? '#ff1744' : '#ff9100',
              fillOpacity: 0.15,
              weight: 2,
            }}
          >
            <Popup>⚠️ {rz.risk_level} Risk Zone: {rz.name}</Popup>
          </Circle>
        ))}
      </MapContainer>
    </div>
  )
}

/* ── Main UserView Component ───────────────────────────────── */

export default function UserView() {
  const [zones, setZones] = useState([])
  const [selectedZone, setSelectedZone] = useState('zone_z1') // Default to Z1 Miyapur
  const [routeData, setRouteData] = useState(null)
  const [mapData, setMapData] = useState(null)
  const [status, setStatus] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [connected, setConnected] = useState(true)
  const [routeUpdated, setRouteUpdated] = useState(false)
  const [mapMode, setMapMode] = useState('demo') // 'demo' or 'real'
  const prevVersion = useRef(0)
  const routeUpdateTimer = useRef(null)

  /* Fetch zone list on mount */
  useEffect(() => {
    fetch(`${API}/zones`)
      .then(r => r.json())
      .then(d => {
        const zList = d.zones || []
        setZones(zList)
        if (zList.length > 0 && !selectedZone) {
          setSelectedZone(zList[0].zone_id)
        }
      })
      .catch(() => {})
  }, [])

  /* Poll status, route, map-data, alerts */
  const fetchAll = useCallback(async () => {
    if (!selectedZone) return
    try {
      const [statusR, routeR, mapR, alertR] = await Promise.all([
        fetch(`${API}/status`),
        fetch(`${API}/route?zone_id=${selectedZone}`),
        fetch(`${API}/map-data?zone_id=${selectedZone}`),
        fetch(`${API}/alerts`),
      ])
      if (statusR.ok) setStatus(await statusR.json())
      if (routeR.ok) setRouteData(await routeR.json())
      if (alertR.ok) {
        const a = await alertR.json()
        setAlerts(a.alerts || [])
      }
      if (mapR.ok) {
        const md = await mapR.json()
        setMapData(md)
        // Detect route version change
        if (prevVersion.current > 0 && md.route_version !== prevVersion.current) {
          setRouteUpdated(true)
          clearTimeout(routeUpdateTimer.current)
          routeUpdateTimer.current = setTimeout(() => setRouteUpdated(false), 14000)
        }
        prevVersion.current = md.route_version
      }
      setConnected(true)
    } catch {
      setConnected(false)
    }
  }, [selectedZone])

  useEffect(() => {
    fetchAll()
    const id = setInterval(fetchAll, POLL_MS)
    return () => clearInterval(id)
  }, [fetchAll])

  /* Use My Location (Hyderabad Geolocation) */
  const useMyLocation = () => {
    if (!navigator.geolocation) return
    navigator.geolocation.getCurrentPosition(async (pos) => {
      try {
        const r = await fetch(`${API}/location`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
        })
        if (r.ok) {
          const d = await r.json()
          if (d.zone_id) setSelectedZone(d.zone_id)
        }
      } catch {}
    })
  }

  const isActive = status?.emergency_active || false

  return (
    <>
      {/* Header */}
      <header className="user-header">
        <div className="user-header-left">
          <span className="user-header-icon">🚨</span>
          <div>
            <h1>Hyderabad Emergency Evacuation Assistant</h1>
            <div className="user-header-sub">Real Hyderabad Geography · Simulated Incident Protocol</div>
          </div>
        </div>
        <div className="user-header-right">
          <div className={`user-status-badge ${isActive ? 'active' : 'standby'}`}>
            {isActive ? '⚠️ EVACUATION IN PROGRESS' : '🟢 NO ACTIVE EMERGENCY — STANDBY'}
          </div>
          <Link to="/operator" className="user-nav-link" title="Open Operator Control Center">⚙️ Operator Control</Link>
        </div>
      </header>

      {/* Demo Simulation Notice */}
      <div className="user-demo-notice">
        🔬 DEMO MODE — Simulated emergency conditions & road closures on real Hyderabad geography (Miyapur, Raidurg, Nagole, LB Nagar, MGBS, JBS).
      </div>

      {/* Connection warning */}
      {!connected && (
        <div className="user-banner warning" role="alert">
          ⚠️ Connection lost. Evacuation information may be outdated. Do not rely on stale map data.
        </div>
      )}

      {/* Route updated alert banner */}
      {routeUpdated && (
        <div className="user-banner route-changed" role="alert">
          <strong>⚡ ROUTE UPDATED</strong>
          <span>A road blockage was detected. AI Route Agents have recalculated your evacuation corridor. Follow the highlighted route.</span>
        </div>
      )}

      <main className="user-main">
        {/* Left Panel: Sidebar controls & instructions */}
        <aside className="user-sidebar">
          {/* Zone Picker */}
          <div className="user-card">
            <div className="user-card-title">📍 Select Your Zone (Hyderabad)</div>
            <select
              id="zone-selector"
              className="user-select"
              value={selectedZone}
              onChange={e => setSelectedZone(e.target.value)}
              aria-label="Select your Hyderabad zone"
            >
              {zones.map(z => (
                <option key={z.zone_id} value={z.zone_id}>{z.zone_name}</option>
              ))}
            </select>
            <button className="user-btn location-btn" onClick={useMyLocation}>
              📡 Use My Location (GPS)
            </button>
          </div>

          {/* Route Instructions */}
          {routeData && selectedZone && (
            <div className="user-card">
              <div className="user-card-title">
                {isActive ? '🗺️ Recommended Evacuation Route' : '🗺️ Designated Evacuation Corridor'}
              </div>

              {isActive ? (
                routeData.risk_level && routeData.risk_level !== 'UNKNOWN' && (
                  <div className={`user-risk-badge risk-${routeData.risk_level?.toLowerCase()}`}>
                    Zone Risk: {routeData.risk_level}
                  </div>
                )
              ) : (
                <div className="user-risk-badge risk-low" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', borderColor: '#10b981' }}>
                  Status: Normal / Standby
                </div>
              )}

              {routeData.destination_exit_name && (
                <div className="user-destination">
                  <span className="dest-label">Assigned Safe Destination:</span>
                  <span className="dest-name">🏁 {routeData.destination_exit_name}</span>
                </div>
              )}

              {routeData.route_summary && (
                <div className="user-route-instruction" aria-live="polite">
                  {routeData.route_summary}
                </div>
              )}

              {routeData.eta_minutes > 0 && (
                <div className="user-eta">
                  ⏱️ Estimated Travel Time: <strong>{routeData.eta_minutes} mins</strong>
                </div>
              )}

              {isActive && routeData.roads_to_avoid?.length > 0 && (
                <div className="user-avoid-roads">
                  <span className="avoid-label">🚧 Blocked Corridors:</span>
                  {routeData.roads_to_avoid.map((r, i) => (
                    <span key={i} className="avoid-badge">{r}</span>
                  ))}
                </div>
              )}

              {routeData.route_steps?.length > 0 && (
                <ol className="user-route-steps">
                  {routeData.route_steps.map((s, i) => (
                    <li key={i} className={s.blocked && isActive ? 'step-blocked' : ''}>
                      {s.road_name}
                      {s.blocked && isActive && <span className="blocked-tag">BLOCKED</span>}
                    </li>
                  ))}
                </ol>
              )}
            </div>
          )}

          {/* Active Alerts (only during active emergency) */}
          {isActive && alerts.length > 0 && (
            <div className="user-card">
              <div className="user-card-title">🔔 Incident Broadcasts</div>
              {alerts.map((a, i) => (
                <div key={i} className={`user-alert alert-${a.severity}`}>
                  {a.message}
                </div>
              ))}
            </div>
          )}

          {/* Status */}
          {status && (
            <div className="user-card">
              <div className="user-card-title">ℹ️ System Status</div>
              <p className="user-status-msg">{status.message}</p>
              <p className="user-mode">Scenario: Hyderabad Operational Demo</p>
            </div>
          )}
        </aside>

        {/* Right Panel: Dual Mode Evacuation Map */}
        <div className="user-map-section">
          {/* Map Header Controls: Mode Switcher */}
          <div className="map-mode-bar">
            <div className="map-mode-switcher" role="group" aria-label="Map View Mode">
              <button
                className={`map-mode-btn ${mapMode === 'demo' ? 'active' : ''}`}
                onClick={() => setMapMode('demo')}
              >
                🗺️ DEMO — HYDERABAD
              </button>
              <button
                className={`map-mode-btn ${mapMode === 'real' ? 'active' : ''}`}
                onClick={() => setMapMode('real')}
              >
                🌍 REAL GIS (OpenStreetMap)
              </button>
            </div>

            <span className={`map-mode-badge badge-${mapMode}`}>
              {mapMode === 'demo' ? '⚡ HYDERABAD TOPOLOGY ACTIVE' : '🌐 REAL HYDERABAD GIS ACTIVE'}
            </span>
          </div>

          {/* Map Content View */}
          <div className="user-map-frame">
            {mapMode === 'demo' ? (
              <DemoMapView mapData={mapData} selectedZone={selectedZone} routeData={routeData} isActive={isActive} />
            ) : (
              <RealMapView mapData={mapData} isActive={isActive} />
            )}
          </div>
        </div>
      </main>
    </>
  )
}

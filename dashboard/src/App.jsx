import { useState, useEffect, useCallback } from 'react'
import { Routes, Route, useNavigate } from 'react-router-dom'
import RoleSelector from './RoleSelector'
import UserView from './UserView'

const API_BASE = '/api'

function usePolling(url, interval = 5000, enabled = true) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch(url)
      if (res.ok) {
        const json = await res.json()
        setData(json)
        setError(null)
      }
    } catch (e) {
      setError(e.message)
    }
  }, [url])

  useEffect(() => {
    if (!enabled) return
    fetchData()
    const id = setInterval(fetchData, interval)
    return () => clearInterval(id)
  }, [fetchData, interval, enabled])

  return { data, error, refetch: fetchData }
}

/* ============================================================ */

function StatsBar({ state }) {
  const s = state || {}
  const progress = (s.progress || 0) * 100

  return (
    <div className="stats-grid">
      <div className="stat-card">
        <div className="stat-label">Total People</div>
        <div className="stat-value accent">{(s.total_people || 0).toLocaleString()}</div>
        <div className="stat-sub">across all zones</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Evacuated</div>
        <div className="stat-value success">{(s.evacuated || 0).toLocaleString()}</div>
        <div className="stat-sub">{progress.toFixed(1)}% complete</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Assigned</div>
        <div className="stat-value warning">{(s.people_assigned || 0).toLocaleString()}</div>
        <div className="stat-sub">to routes</div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Replans</div>
        <div className="stat-value danger">{s.replan_count || 0}</div>
        <div className="stat-sub">dynamic adjustments</div>
      </div>
    </div>
  )
}

function ProgressBar({ progress }) {
  const pct = Math.min(100, (progress || 0) * 100)
  return (
    <div className="progress-bar-container">
      <div className="progress-bar-fill" style={{ width: `${pct}%` }} />
    </div>
  )
}

function ZonesPanel({ zones }) {
  const zoneEntries = Object.entries(zones || {})
  if (zoneEntries.length === 0) return <div className="card"><div className="card-header"><span className="card-title">📍 Zones</span></div><p style={{color:'var(--text-muted)', fontSize:'0.85rem'}}>Start an emergency to see zone data</p></div>

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">📍 Zones</span>
      </div>
      <div className="zone-list">
        {zoneEntries.map(([id, z]) => (
          <div key={id} className="zone-item">
            <span className="zone-name">{z.name || id}</span>
            <span className="zone-count">{(z.crowd_count || 0).toLocaleString()} people</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function RoadsPanel({ roads }) {
  const roadEntries = Object.entries(roads || {})
  if (roadEntries.length === 0) return <div className="card"><div className="card-header"><span className="card-title">🛣️ Roads</span></div><p style={{color:'var(--text-muted)', fontSize:'0.85rem'}}>Start an emergency to see road data</p></div>

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">🛣️ Roads</span>
      </div>
      <div className="zone-list">
        {roadEntries.map(([id, r]) => {
          const cong = (r.congestion || 0) * 100
          const badge = r.blocked ? 'critical' : cong > 70 ? 'high' : cong > 40 ? 'medium' : 'low'
          return (
            <div key={id} className="zone-item">
              <span className="zone-name">{r.name || id}</span>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{cong.toFixed(0)}%</span>
                <span className={`zone-badge badge-${badge}`}>
                  {r.blocked ? 'BLOCKED' : cong > 70 ? 'HIGH' : cong > 40 ? 'MEDIUM' : 'CLEAR'}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function AgentsPanel({ agents }) {
  const agentList = agents?.agents || [
    { name: 'crowd_agent', status: 'idle' },
    { name: 'risk_agent', status: 'idle' },
    { name: 'traffic_agent', status: 'idle' },
    { name: 'transport_agent', status: 'idle' },
    { name: 'route_agent', status: 'idle' },
    { name: 'coordinator_agent', status: 'idle' },
  ]

  const names = {
    crowd_agent: '👥 Crowd Agent',
    risk_agent: '⚠️ Risk Agent',
    traffic_agent: '🚦 Traffic Agent',
    transport_agent: '🚌 Transport Agent',
    route_agent: '🗺️ Route Agent',
    coordinator_agent: '🧠 Coordinator',
  }

  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">🤖 Agents</span>
      </div>
      <div className="agent-list">
        {agentList.map(a => (
          <div key={a.name} className="agent-item">
            <div className={`agent-dot ${a.status}`} />
            <span>{names[a.name] || a.name}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function ReasoningPanel({ reasoning }) {
  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">💭 Coordinator Reasoning</span>
      </div>
      <div className="reasoning-box">
        {reasoning || 'No reasoning available yet. Start an emergency to activate the agent workflow.'}
      </div>
    </div>
  )
}

function PlanPanel({ plan }) {
  if (!plan || !plan.status) return null
  return (
    <div className="card" style={{ gridColumn: '1 / -1' }}>
      <div className="card-header">
        <span className="card-title">📋 Evacuation Plan</span>
        <span className={`zone-badge badge-${plan.status === 'approved' ? 'low' : 'medium'}`}>
          {plan.status?.toUpperCase()}
        </span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
        <div>
          <div className="stat-label">Total People</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700 }}>{(plan.total_people || 0).toLocaleString()}</div>
        </div>
        <div>
          <div className="stat-label">Assigned</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--success)' }}>{(plan.people_assigned || 0).toLocaleString()}</div>
        </div>
        <div>
          <div className="stat-label">Unassigned</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: plan.people_unassigned > 0 ? 'var(--danger)' : 'var(--success)' }}>{(plan.people_unassigned || 0).toLocaleString()}</div>
        </div>
      </div>
      {plan.blocked_roads?.length > 0 && (
        <div style={{ marginTop: '8px' }}>
          {plan.blocked_roads.map(r => (
            <div key={r} className="alert-item">🚧 Blocked: {r}</div>
          ))}
        </div>
      )}
    </div>
  )
}

/* ============================================================ */

export function OperatorView() {
  const navigate = useNavigate()
  const [isActive, setIsActive] = useState(false)
  const [state, setState] = useState({})

  const { data: dashData, refetch } = usePolling(`${API_BASE}/dashboard/summary`, 3000, isActive)
  const { data: agentData } = usePolling(`${API_BASE}/agents/status`, 5000, isActive)

  useEffect(() => {
    if (dashData) {
      setState(dashData)
    }
  }, [dashData])

  const startEmergency = async () => {
    try {
      const res = await fetch(`${API_BASE}/emergency/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ emergency_type: 'chemical_spill', severity: 'high', scenario: 'default_demo' }),
      })
      if (res.ok) {
        setIsActive(true)
        refetch()
      }
    } catch (e) {
      console.error('Failed to start emergency:', e)
    }
  }

  const stepSimulation = async () => {
    try {
      await fetch(`${API_BASE}/emergency/step`, { method: 'POST' })
      refetch()
    } catch (e) {
      console.error('Step failed:', e)
    }
  }

  const blockRoad = async (roadId) => {
    try {
      await fetch(`${API_BASE}/emergency/block-road`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ road_id: roadId, reason: 'manual' }),
      })
      refetch()
    } catch (e) {
      console.error('Block road failed:', e)
    }
  }

  const stopEmergency = async () => {
    try {
      await fetch(`${API_BASE}/emergency/stop`, { method: 'POST' })
      setIsActive(false)
    } catch (e) {
      console.error('Stop failed:', e)
    }
  }

  const s = state?.state || {}
  const zones = state?.zones || {}
  const roads = state?.roads || {}
  const plan = state?.evacuation_plan || {}
  const reasoning = s.reasoning || ''

  return (
    <>
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <button className="btn" onClick={() => navigate('/')} style={{ fontSize: '0.8rem' }}>
            ← Roles
          </button>
          <span className="header-icon">🚨</span>
          <h1>Emergency Evacuation AI — Hyderabad Control Center</h1>
        </div>
        <div className="header-status">
          <div className={`status-dot ${isActive ? '' : 'inactive'}`} />
          <span>{isActive ? 'ACTIVE' : 'STANDBY'}</span>
          {s.simulation_step > 0 && <span>· Step {s.simulation_step}</span>}
        </div>
        <div className="controls">
          {!isActive ? (
            <button id="btn-start" className="btn btn-primary" onClick={startEmergency}>
              🚀 Start Emergency
            </button>
          ) : (
            <>
              <button id="btn-step" className="btn" onClick={stepSimulation}>
                ⏭️ Step
              </button>
              <button id="btn-block" className="btn btn-danger" onClick={() => blockRoad('road_r4')}>
                🚧 Block R4 (JBS-MGBS)
              </button>
              <button id="btn-stop" className="btn" onClick={stopEmergency}>
                ⏹️ Stop
              </button>
            </>
          )}
        </div>
      </header>

      {/* Demo notice */}
      <div className="user-demo-notice" style={{ margin: '8px 12px 0 12px' }}>
        🔬 DEMO MODE — Simulated emergency & crowd data on real Hyderabad geography (Miyapur, Raidurg, Nagole, LB Nagar, MGBS, JBS).
      </div>

      {/* Dashboard Grid */}
      <main className="dashboard">
        <StatsBar state={s} />
        <ProgressBar progress={s.progress} />

        <PlanPanel plan={plan} />

        <ZonesPanel zones={zones} />
        <RoadsPanel roads={roads} />

        <AgentsPanel agents={agentData} />
        <ReasoningPanel reasoning={reasoning} />
      </main>
    </>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<RoleSelector />} />
      <Route path="/operator" element={<OperatorView />} />
      <Route path="/user" element={<UserView />} />
    </Routes>
  )
}

/**
 * RoleSelector — Landing page for choosing Operator or Evacuee view.
 *
 * Renders at the root path "/" with two large cards that navigate
 * to /operator or /user respectively.
 */
import { useNavigate } from 'react-router-dom'

export default function RoleSelector() {
  const navigate = useNavigate()

  return (
    <div className="role-selector" role="main">
      <div className="role-header">
        <span className="role-icon" aria-hidden="true">🚨</span>
        <h1>Emergency Evacuation AI</h1>
        <p className="role-subtitle">Select your role to continue</p>
      </div>

      <div className="role-cards">
        <button
          id="role-operator"
          className="role-card role-card-operator"
          onClick={() => navigate('/operator')}
          aria-label="Open Operator Control Center"
        >
          <span className="role-card-icon" aria-hidden="true">🎛️</span>
          <h2>Operator Control Center</h2>
          <p>Monitor and manage emergency evacuations. View agent decisions, simulation state, and system controls.</p>
          <span className="role-card-badge">AUTHORIZED PERSONNEL</span>
        </button>

        <button
          id="role-evacuee"
          className="role-card role-card-evacuee"
          onClick={() => navigate('/user')}
          aria-label="Open Evacuee View"
        >
          <span className="role-card-icon" aria-hidden="true">🚶</span>
          <h2>Evacuee View</h2>
          <p>Get personalized evacuation instructions. See your route, destination, and real-time updates.</p>
          <span className="role-card-badge">PUBLIC ACCESS</span>
        </button>
      </div>

      <p className="role-footer">
        🔬 DEMO MODE — This system uses simulated data for demonstration purposes.
      </p>
    </div>
  )
}

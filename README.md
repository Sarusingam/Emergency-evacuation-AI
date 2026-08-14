# 🚨 Emergency Evacuation AI

**Agentic AI Framework for Distributed Emergency Evacuation Optimization**

A multi-agent system that uses LangGraph, computer vision, and real-time optimization to coordinate emergency evacuations. The system detects crowds via YOLO, assesses risk, monitors traffic, dispatches vehicles, computes optimal evacuation routes using Dijkstra + linear programming, and provides a real-time React dashboard.

---

## ✨ Key Features

| Feature | Technology |
|---------|-----------|
| 🤖 Multi-Agent Orchestration | LangGraph StateGraph with 6 specialized agents |
| 👁️ Computer Vision | YOLO person detection with demo fallback |
| 🗺️ Route Optimization | NetworkX Dijkstra + SciPy linear programming |
| 📊 Real-Time Dashboard | React + Vite + Leaflet + Recharts |
| 🔄 Dynamic Replanning | Agents detect changes and auto-replan |
| 🐳 Docker Ready | Full docker-compose deployment |
| 🎯 Demo Mode | Runs completely offline, no external deps |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Dashboard (React)                  │
│          Leaflet Map · Charts · Controls             │
└─────────────────────┬───────────────────────────────┘
                      │ HTTP/Polling
┌─────────────────────┴───────────────────────────────┐
│              FastAPI Backend (Python)                 │
│      REST API · Services · Database (SQLite)         │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────┐
│           LangGraph Agent Workflow                    │
│                                                       │
│  crowd_agent → risk_agent → traffic_agent            │
│       → transport_agent → route_agent                │
│            → coordinator_agent                        │
│                 ↓                                     │
│         [replan?] ──yes──→ loop back                 │
│            ↓ no                                       │
│           END                                         │
└─────────────────────────────────────────────────────┘
```

### Agents

| Agent | Responsibility |
|-------|---------------|
| **CrowdAgent** | Analyzes zone-level crowd density from CV or scenario data |
| **RiskAgent** | Computes composite risk scores (crowd + traffic + emergency) |
| **TrafficAgent** | Monitors road congestion, detects blocked roads |
| **TransportAgent** | Dispatches vehicles based on zone priority |
| **RouteAgent** | Deterministic Dijkstra routing + LP assignment |
| **CoordinatorAgent** | Final plan approval, strategic reasoning |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+ (for dashboard)

### 1. Clone & Install

```bash
git clone <repo-url>
cd emergency-evacuation-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env
```

### 2. Run Demo (No Server)

```bash
python run.py --demo
```

This runs the full agent workflow and simulates evacuation with a progress bar — no server, database, or external services needed.

### 3. Start Backend Server

```bash
python run.py
```

Server starts at: http://localhost:8000
API Docs at: http://localhost:8000/docs

### 4. Start Dashboard

```bash
cd dashboard
npm install
npm run dev
```

Dashboard at: http://localhost:5173

### 5. Run Tests

```bash
# Unit tests
pytest tests/ -v

# System test
python run.py --test
```

---

## 🐳 Docker Deployment

```bash
docker-compose up --build
```

- Backend: http://localhost:8000
- Dashboard: http://localhost:5173

---

## 📁 Project Structure

```
emergency-evacuation-ai/
├── agents/                 # Multi-agent system (LangGraph)
│   ├── base_agent.py       # Abstract base class
│   ├── agent_state.py      # LangGraph TypedDict state
│   ├── agent_messages.py   # Inter-agent messaging
│   ├── tools.py            # Deterministic tools (routing, optimization)
│   ├── crowd_agent.py      # Crowd density analysis
│   ├── risk_agent.py       # Risk assessment
│   ├── traffic_agent.py    # Road monitoring
│   ├── transport_agent.py  # Vehicle dispatch
│   ├── route_agent.py      # Route optimization
│   ├── coordinator_agent.py # Orchestration
│   └── graph.py            # LangGraph workflow definition
│
├── computer_vision/        # CV pipeline
│   ├── detector.py         # YOLO + synthetic fallback
│   ├── counter.py          # People counting
│   ├── tracker.py          # Centroid tracking
│   ├── density.py          # Grid density estimation
│   ├── zone_analyzer.py    # Zone-to-detection mapping
│   ├── video_processor.py  # OpenCV frame extraction
│   └── inference.py        # Full pipeline orchestrator
│
├── datasets/               # Dataset loaders for training
│   ├── dronecrowd_loader.py
│   ├── nwpu_loader.py
│   ├── ucf_qnrf_loader.py
│   ├── preprocessing.py
│   └── dataset_config.py
│
├── models/                 # ML models
│   ├── crowd_model.py      # Crowd counting CNN
│   └── model_manager.py    # Weight management
│
├── routing/                # Road network routing
│   ├── graph_builder.py    # NetworkX graph construction
│   ├── route_service.py    # Routing facade
│   ├── osrm_client.py      # Optional OSRM integration
│   └── map_data.py         # Demo road network
│
├── optimization/           # Route optimization
│   ├── cost_function.py    # Multi-criteria cost
│   ├── route_optimizer.py  # Dijkstra with custom cost
│   ├── evacuation_optimizer.py  # LP assignment
│   ├── assignment.py       # Zone-to-exit solver
│   └── constraints.py      # Capacity validation
│
├── simulation/             # Evacuation simulation
│   ├── scenario_manager.py # YAML scenario loading
│   ├── crowd_simulator.py  # Crowd movement
│   ├── traffic_simulator.py # Road conditions
│   ├── evacuation_simulator.py # Progress tracking
│   ├── fallback_simulator.py   # Complete demo simulator
│   └── sumo_client.py      # Optional SUMO integration
│
├── database/               # Data persistence
│   ├── database.py         # SQLAlchemy engine
│   ├── models.py           # ORM models
│   ├── repositories.py     # CRUD operations
│   └── seed.py             # Demo data seeder
│
├── communication/          # Event messaging
│   ├── event_bus.py        # Abstract protocol
│   ├── local_bus.py        # In-memory bus
│   └── redis_client.py     # Redis pub/sub
│
├── backend/                # FastAPI application
│   ├── main.py             # App factory + lifespan
│   ├── config.py           # Settings from env + YAML
│   ├── dependencies.py     # DI for FastAPI
│   ├── api/                # Route handlers
│   │   ├── emergency.py    # Emergency CRUD
│   │   ├── crowd.py        # Crowd data
│   │   ├── routes.py       # Evacuation routes
│   │   ├── traffic.py      # Traffic status
│   │   ├── agents.py       # Agent status
│   │   ├── simulation.py   # Simulation control
│   │   └── dashboard.py    # Aggregated view
│   ├── schemas/            # Pydantic models
│   └── services/           # Business logic
│
├── dashboard/              # React frontend
│   ├── src/
│   │   ├── App.jsx         # Main app
│   │   ├── components/     # UI components
│   │   └── hooks/          # Custom hooks
│   └── package.json
│
├── config/                 # Configuration files
│   ├── settings.yaml       # App settings
│   ├── scenarios.yaml      # Demo scenarios
│   └── thresholds.yaml     # Risk/density thresholds
│
├── tests/                  # Test suite
├── scripts/                # Utility scripts
├── run.py                  # Main entry point
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## 🔧 Configuration

### Environment Variables (.env)

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_MODE` | `demo` | `demo` or `production` |
| `DATABASE_URL` | `sqlite:///./data/evacuation.db` | Database connection |
| `OPENAI_API_KEY` | (empty) | For LLM-enhanced coordinator |
| `USE_REDIS` | `false` | Enable Redis event bus |
| `USE_OSRM` | `false` | Enable OSRM routing |

### Demo Mode (Default)

The system runs completely self-contained:
- ✅ Synthetic crowd detections (no YOLO weights needed)
- ✅ NetworkX routing (no OSRM needed)
- ✅ SQLite database (no PostgreSQL needed)
- ✅ In-memory event bus (no Redis needed)
- ✅ Rule-based coordinator (no LLM API key needed)

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/emergency/start` | Start new emergency |
| `GET` | `/api/emergency/status` | Get emergency status |
| `POST` | `/api/emergency/step` | Run simulation step |
| `POST` | `/api/emergency/block-road` | Block a road |
| `GET` | `/api/crowd/analysis` | Crowd analysis |
| `GET` | `/api/crowd/zones` | Zone data |
| `GET` | `/api/routes/` | Evacuation routes |
| `GET` | `/api/routes/plan` | Evacuation plan |
| `GET` | `/api/traffic/` | Traffic status |
| `GET` | `/api/agents/status` | Agent status |
| `GET` | `/api/agents/reasoning` | Coordinator reasoning |
| `GET` | `/api/dashboard/summary` | Full dashboard data |
| `POST` | `/api/simulation/step` | Simulation step |
| `GET` | `/api/simulation/history` | Step history |

---

## 🧪 Testing

```bash
# All unit tests
pytest tests/ -v

# Specific module
pytest tests/test_agents.py -v
pytest tests/test_routing.py -v

# End-to-end system test
python scripts/test_system.py

# API integration tests
pytest tests/test_api.py -v
```

---

## 📚 Supported Datasets

For training the crowd counting model:

| Dataset | Description | Type |
|---------|-------------|------|
| [DroneCrowd](https://github.com/VisDrone/DroneCrowd) | Drone-captured crowds | Detection + counting |
| [NWPU-Crowd](https://gjy3035.github.io/NWPU-Crowd-Sample-Code/) | Large-scale benchmark | Counting |
| [UCF-QNRF](https://www.crcv.ucf.edu/data/ucf-qnrf/) | Ultra-high density | Counting |

```bash
# Train model (requires dataset + PyTorch)
python scripts/train_model.py
```

---

## 🔑 Design Principles

1. **Deterministic Routing**: All numerical computations (Dijkstra, LP) are deterministic — never LLM-based
2. **Graceful Degradation**: Every external service has an in-process fallback
3. **Agent Autonomy**: Each agent independently processes its domain and communicates via shared state
4. **Dynamic Replanning**: System automatically detects changes and re-optimizes

---

## 📄 License

MIT License

---

## 🙏 Acknowledgments

- **LangGraph** — Multi-agent orchestration framework
- **NetworkX** — Graph algorithms for routing
- **SciPy** — Linear programming for optimal assignment
- **Ultralytics** — YOLO object detection
- **FastAPI** — High-performance Python web framework

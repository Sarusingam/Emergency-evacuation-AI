# 🚨 Emergency Evacuation AI

> **Agentic AI framework for distributed emergency evacuation optimization using multi-agent intelligence, computer vision, dynamic routing, simulation, and Hyderabad-based GIS visualization.**

---

## 📌 Table of Contents
1. [Overview & Problem Statement](#-overview--problem-statement)
2. [Key Objectives](#-key-objectives)
3. [System Architecture](#-system-architecture)
4. [Multi-Agent Intelligence System](#-multi-agent-intelligence-system)
5. [Computer Vision Pipeline](#-computer-vision-pipeline)
6. [Route Optimization & Dynamic Replanning](#-route-optimization--dynamic-replanning)
7. [Hyderabad Geographic Setting](#-hyderabad-geographic-setting)
8. [User Interfaces](#-user-interfaces)
9. [Project Screenshots](#-project-screenshots)
10. [Technology Stack](#-technology-stack)
11. [Project Directory Structure](#-project-directory-structure)
12. [Installation & Setup](#-installation--setup)
13. [How to Run](#-how-to-run)
14. [Running Tests](#-running-tests)
15. [API Overview](#-api-overview)
16. [Current Limitations](#-current-limitations)
17. [Future Enhancements](#-future-enhancements)
18. [License](#-license)

---

## 📖 Overview & Problem Statement

Urban emergency evacuations (triggered by chemical spills, industrial fires, floods, or infrastructure failures) often suffer from **severe bottleneck congestion**, **conflicting information**, and **uncoordinated exit assignments**. Traditional centralized systems cannot adapt quickly when primary evacuation corridors become blocked or compromised.

**Emergency Evacuation AI** is a distributed multi-agent system designed to optimize urban evacuations in real time. It continuously processes simulated crowd distributions, evaluates zone risk levels, dynamically computes optimal evacuation corridors using linear programming and graph routing, and pushes personalized evacuation instructions to both emergency operators and citizens.

> **Note on Demonstration Data**: The system uses **real Hyderabad geographical coordinates, zones, landmarks, and road networks** coupled with **simulated emergency conditions, crowd movements, vehicle states, and incident telemetry** for demonstration and testing.

---

## 🎯 Key Objectives

- **Distributed Agent Decision-Making**: Decompose emergency management across specialized AI agents (Crowd, Risk, Traffic, Transport, Route, Coordinator) orchestrated via LangGraph.
- **Global Evacuation Optimization**: Balance evacuee flow across peripheral safe exits using Scipy Linear Programming (`linprog`) to prevent exit overload.
- **Dynamic Replanning**: Instantly detect road blockages or high-risk hotspots and re-route affected zones through safe alternative corridors within seconds.
- **Dual-View Operations**: Provide an **Operator Command Center** for scenario control and real-time monitoring, alongside a streamlined **Citizen Evacuation Assistant** for route guidance.
- **Dual Map Visualization**: Toggle between an **Interactive Topological Grid** and a **Real OpenStreetMap Leaflet GIS View** centered on Hyderabad.

---

## 🏗️ System Architecture

```
                               ┌─────────────────────────────┐
                               │     Emergency Scenario      │
                               │  (Simulated Data / Sensors) │
                               └──────────────┬──────────────┘
                                              │
                                              ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                              Multi-Agent Intelligence Engine                              │
│                                                                                           │
│  ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐                  │
│  │   Crowd Agent   │──────▶│   Risk Agent    │──────▶│  Traffic Agent  │                  │
│  │ (Density & CV)  │       │ (Hazard Eval)   │       │(Congestion/Road)│                  │
│  └─────────────────┘       └─────────────────┘       └────────┬────────┘                  │
│                                                               │                           │
│  ┌─────────────────┐       ┌─────────────────┐                │                           │
│  │Transport Agent  │◀──────│   Route Agent   │◀───────────────┘                           │
│  │(Bus Allocation) │       │ (LP + Dijkstra) │                                            │
│  └────────┬────────┘       └────────┬────────┘                                            │
│           │                         │                                                     │
│           └───────────┬─────────────┘                                                     │
│                       ▼                                                                   │
│          ┌─────────────────────────┐                                                      │
│          │    Coordinator Agent    │◀──── Dynamic Replanning Loop                         │
│          │ (LangGraph Orchestration│                                                      │
│          └─────────────────────────┘                                                      │
└───────────────────────────────┬───────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                              FastAPI Backend & Event Bus                                  │
│  • /api/emergency/*   • /api/user/*   • /api/agents/*   • /api/simulation/*               │
└───────────────────────────────┬───────────────────────────────────────────────────────────┘
                                │
               ┌────────────────┴────────────────┐
               ▼                                 ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│    Operator Command Center  │   │  Citizen Evacuation View    │
│  • Incident control & steps │   │  • Zone selection / GPS     │
│  • Road blockage injection  │   │  • Step-by-step route steps │
│  • Multi-agent state logs   │   │  • Assigned safe exit & ETA │
│  • Dual Hyderabad Map       │   │  • Dual Hyderabad Map       │
└─────────────────────────────┘   └─────────────────────────────┘
```

---

## 🤖 Multi-Agent Intelligence System

The system implements a sequential and LangGraph-governed multi-agent workflow:

| Agent | Responsibility | Implementation Details |
| :--- | :--- | :--- |
| **Crowd Agent** | Monitors evacuee counts, crowd movement, and evacuation progress across all zones. | Integrates with CV density outputs, runs fallback Gaussian crowd motion models. |
| **Risk Agent** | Evaluates compound environmental and hazard risks (CRITICAL, HIGH, MEDIUM, LOW) per zone. | Evaluates distance to hazard epicenter, wind speed/direction, and crowd vulnerability. |
| **Traffic Agent** | Tracks road status, speeds, congestion levels, and closure states. | Calculates BPR congestion functions, flags blocked segments, and monitors bottleneck corridors. |
| **Route Agent** | Computes optimal evacuation corridors and citizen allocations. | Formulates a Linear Program (LP) for exit capacity constraints + NetworkX Dijkstra shortest feasible paths. |
| **Transport Agent**| Dispatches and schedules emergency evacuation buses and shuttles. | Solves vehicle allocation based on zone priority, vulnerability count, and turnaround times. |
| **Coordinator** | Orchestrates the agent cycle, synthesizes reports, and triggers replanning when blocked roads are reported. | Rule-based decision logic with optional LLM integration (OpenAI / Anthropic / Gemini). |

---

## 👁️ Computer Vision Pipeline

The `computer_vision/` module provides modular crowd analysis capabilities:

- **Detection**: Person detection using YOLOv8 (`ultralytics`) with bounding box confidence thresholding.
- **Density Estimation**: CSRNet / DM-Count style density map estimation for dense crowd scenes.
- **Tracking**: Optical flow tracker (`cv2.calcOpticalFlowFarneback`) to measure crowd velocity and directional flow.
- **Zone Analyzer**: Aggregates pixel-level density maps into zone-specific headcounts and congestion indices.
- **Demo Mode Generators**: Generates synthetic crowd frames and density tensors for testing when video cameras or GPUs are unavailable.

---

## 🛣️ Route Optimization & Dynamic Replanning

### 1. Global Evacuation Allocation (Linear Programming)
To prevent all evacuees from rushing to a single exit and causing deadly stampedes, the system solves a global assignment optimization problem:
$$\min \sum_{z \in Z} \sum_{e \in E} x_{z,e} \cdot C(z, e)$$
Subject to:
- $\sum_{e} x_{z,e} = \text{Crowd}(z) \quad \forall z \in Z$ (Every evacuee is assigned)
- $\sum_{z} x_{z,e} \le \text{Capacity}(e) \quad \forall e \in E$ (Exit capacities are respected)
- $x_{z,e} \ge 0$

Where $C(z, e)$ represents the multi-factor cost combining travel time, road congestion, and corridor risk.

### 2. Multi-Cost Shortest Path Routing (NetworkX)
Edge weights in the road graph are dynamically updated:
$$\text{Weight}(u, v) = \text{Length} \times (1 + \alpha \cdot \text{Congestion}^2) \times (1 + \beta \cdot \text{Risk})$$
If a road is marked `blocked: true`, its weight becomes $\infty$, removing it from the search space.

### 3. Dynamic Replanning
When an operator blocks a road (or high congestion occurs), the `CoordinatorAgent` automatically triggers an incremental replan cycle. The affected zones receive recalculated evacuation paths and updated ETAs, broadcasting a `⚡ ROUTE UPDATED` alert to evacuees.

---

## 📍 Hyderabad Geographic Setting

The scenario is mapped to **real Hyderabad urban geography and arterial road corridors**:

### Operational Zones
- **Z1 — Miyapur** (North-West) · Lat: `17.4968`, Lon: `78.3614`
- **Z2 — Raidurg / HITEC City** (West) · Lat: `17.4435`, Lon: `78.3772`
- **Z3 — Nagole** (East) · Lat: `17.3753`, Lon: `78.5583`
- **Z4 — LB Nagar** (South-East) · Lat: `17.3457`, Lon: `78.5522`
- **Z5 — MGBS / Old City** (Central) · Lat: `17.3786`, Lon: `78.4811`
- **Z6 — JBS / Secunderabad** (North-Central) · Lat: `17.4474`, Lon: `78.4984`

### Peripheral Evacuation Points (Exits)
- **North Evacuation Point** (Medchal / NH44) · Lat: `17.6297`, Lon: `78.4814`
- **East Evacuation Point** (Ghatkesar / NH163) · Lat: `17.4468`, Lon: `78.6835`
- **South Evacuation Point** (Shamshabad / ORR / NH44) · Lat: `17.2403`, Lon: `78.4294`
- **West Evacuation Point** (Patancheru / NH65) · Lat: `17.5332`, Lon: `78.2656`

### Arterial Connecting Corridors
- `R1`: Outer Ring Road (ORR West — Miyapur to Patancheru)
- `R2`: NH65 / Bombay Highway (Miyapur to MGBS)
- `R3`: Hitech City Main Road (Raidurg to Miyapur)
- `R4`: Inner Ring Road / Mehdipatnam Corridor (Raidurg to MGBS)
- `R5`: PVNR Expressway / NH44 South (MGBS to Shamshabad)
- `R6`: NH65 South-East (MGBS to LB Nagar)
- `R7`: Saroornagar Corridor (LB Nagar to Nagole)
- `R8`: Inner Ring Road East (Nagole to JBS)
- `R9`: NH163 Warangal Highway (Nagole to Ghatkesar)
- `R10`: SP Road / Secunderabad Link (MGBS to JBS)
- `R11`: NH44 North / Medchal Highway (JBS to Medchal)
- `R12`: Balanagar - Kukatpally Corridor (Miyapur to JBS)

---

## 🖥️ User Interfaces

The frontend dashboard provides two dedicated views:

### 1. Operator Control Center (`/operator`)
- **Simulation Control**: Start emergency scenarios, advance simulation steps, trigger replanning, and reset.
- **Incident Injection**: Dynamically block/unblock roads with reason tags (e.g. debris, structural damage, waterlogging).
- **Agent Intelligence Feed**: Real-time structured outputs from Crowd, Risk, Traffic, Route, and Transport agents.
- **Multi-Map Visualizer**: Toggle between SVG topology diagram and Leaflet GIS satellite/street map with live congestion heatmaps.

### 2. Citizen Evacuation Assistant (`/user`)
- **Zone Selector / GPS Locator**: Select current Hyderabad zone or auto-detect nearest zone via browser geolocation.
- **Evacuation Instructions**: Clear, unambiguous primary evacuation corridor, assigned peripheral exit, and calculated travel ETA.
- **Dynamic Re-Route Alerts**: Visual banner notifying citizens when an upstream blockage causes a route recalculation.
- **Incident Broadcasts**: Live list of active hazard zones and road closures to avoid.

---

## 📸 Project Screenshots

<!-- Screenshot Section Placeholders -->

### Operator View
> *Real-time emergency control center showing simulation controls, road blockage injector, agent state metrics, and dual map visualization.*

```
+-----------------------------------------------------------------------------------+
|  🚨 EMERGENCY EVACUATION COMMAND CENTER                                           |
|  [ Start Emergency ]  [ Step Simulation ]  [ Trigger Replan ]  [ Reset ]          |
|-----------------------------------------------------------------------------------|
|  SIMULATION METRICS       |  HYDERABAD MAP (Demo SVG / Real GIS)                  |
|  • Active Evacuees: 9,000 |  [ Z1 Miyapur ] ===== R2 ===== [ Z5 MGBS ]            |
|  • Evacuated: 3,420       |         ||                             ||             |
|  • Blocked Corridors: R4  |      R3 ||                             || R5          |
|  • High-Risk Zones: Z5    |         \/                             \/             |
|                           |  [ Z2 Raidurg ]                 [ Exit South ]        |
|---------------------------+-------------------------------------------------------|
|  AGENT INTELLIGENCE LOGS                                                          |
|  • [Route Agent] LP Solver assigned 3,200 people from Z1 to Exit West             |
|  • [Risk Agent] Elevated risk for Z5 (Chemical Cloud dispersion radius: 600m)     |
+-----------------------------------------------------------------------------------+
```

### Evacuee View
> *Streamlined citizen evacuation screen with zone selection, step-by-step route directions, estimated travel time, and safety status.*

```
+-----------------------------------------------------------------------------------+
|  🚨 Hyderabad Emergency Evacuation Assistant                                     |
|  📍 Your Location: [ Z1 - Miyapur (North-West) ]  [ 📡 GPS ]                      |
|-----------------------------------------------------------------------------------|
|  🏁 ASSIGNED DESTINATION: West Evacuation Point (Patancheru / NH65)               |
|  ⏱️ ESTIMATED TRAVEL TIME: 10.0 mins                                              |
|  🗺️ ROUTE SUMMARY: Proceed via R8 to West Evacuation Point                       |
|                                                                                   |
|  🚧 BLOCKED CORRIDORS TO AVOID:                                                   |
|  [ R4 - Inner Ring Road ]                                                         |
|                                                                                   |
|  HYDERABAD EVACUATION MAP:                                                        |
|  [ Leaflet GIS OpenStreetMap / SVG Topological Grid ]                             |
+-----------------------------------------------------------------------------------+
```

---

## 🛠️ Technology Stack

### Backend & Agents
- **Language**: Python 3.12+
- **API Framework**: FastAPI & Uvicorn (ASGI)
- **Agent Orchestration**: LangGraph, LangChain
- **Optimization & Graph Routing**: SciPy (`scipy.optimize.linprog`), NetworkX
- **Computer Vision & ML**: PyTorch, Ultralytics YOLOv8, OpenCV (`cv2`)
- **Database**: SQLite (default local) / PostgreSQL via SQLAlchemy
- **Data Validation**: Pydantic v2

### Frontend Dashboard
- **Framework**: React 18
- **Build Tool**: Vite
- **Mapping & GIS**: Leaflet, React-Leaflet, OpenStreetMap
- **Styling**: Modern Responsive CSS3 (Glassmorphic dark design system)
- **Routing**: React Router DOM

---

## 📁 Project Directory Structure

```
emergency-evacuation-ai/
├── agents/                      # AI Agent implementations
│   ├── coordinator_agent.py     # Master orchestrator & LangGraph graph
│   ├── crowd_agent.py           # Crowd estimation & headcount tracking
│   ├── risk_agent.py            # Hazard & environmental risk assessor
│   ├── traffic_agent.py         # Road status & congestion analyzer
│   ├── transport_agent.py       # Bus & emergency shuttle allocator
│   ├── route_agent.py           # LP optimizer & Dijkstra route planner
│   ├── tools.py                 # Graph builders & pathfinding algorithms
│   └── graph.py                 # LangGraph state machine definitions
├── backend/                     # FastAPI backend application
│   ├── api/                     # API routers (emergency, user, agents, routes)
│   ├── schemas/                 # Pydantic request/response schemas
│   ├── services/                # Emergency service singleton & state
│   ├── config.py                # App configuration & settings loader
│   └── main.py                  # FastAPI application entrypoint
├── computer_vision/             # Computer vision crowd analysis
│   ├── detector.py              # YOLOv8 person detector
│   ├── density.py               # CSRNet crowd density estimator
│   ├── tracker.py               # Optical flow motion tracker
│   └── video_processor.py       # Frame processing & zone aggregation
├── config/                      # Configuration files
│   ├── scenarios.yaml           # Hyderabad demo scenario definition
│   ├── settings.yaml            # Server & system parameters
│   └── thresholds.yaml         # Risk, congestion, and capacity limits
├── dashboard/                   # React + Vite frontend application
│   ├── src/
│   │   ├── App.jsx              # Main dashboard & operator interface
│   │   ├── UserView.jsx         # Citizen evacuation assistant view
│   │   ├── RoleSelector.jsx     # Landing portal role chooser
│   │   └── index.css            # Dark-mode styling and UI tokens
│   ├── package.json             # NPM dependencies
│   └── vite.config.js           # Vite development server configuration
├── database/                    # Database models and SQLite repository
│   ├── database.py              # Engine and session initialization
│   ├── models.py                # SQLAlchemy ORM models
│   └── seed.py                  # Initial seed data loader
├── optimization/                # Evacuation mathematical optimizers
│   ├── evacuation_optimizer.py  # SciPy Linear Programming solver
│   └── route_optimizer.py       # Multi-criteria path search
├── routing/                     # Routing network models & OSRM client
├── simulation/                  # Crowd and traffic simulation engines
│   ├── crowd_simulator.py       # Zone crowd flow simulator
│   └── fallback_simulator.py   # Self-contained ODE traffic runner
├── scripts/                     # Utility and test execution scripts
│   ├── run_demo.py              # CLI demo simulation runner
│   └── test_system.py           # End-to-end integration test
├── tests/                       # Pytest automated test suite
├── run.py                       # Unified project CLI launcher
├── requirements.txt             # Python package dependencies
├── .env.example                 # Environment configuration template
├── .gitignore                   # Git exclusion rules
├── LICENSE                      # MIT License
└── README.md                    # Project documentation
```

---

## ⚙️ Installation & Setup

### Prerequisites
- **Python**: Version `3.10`, `3.11`, or `3.12`
- **Node.js**: Version `18.0.0` or higher
- **Git**

### 1. Clone the Repository
```bash
git clone https://github.com/Sarusingam/Emergency-evacuation-AI.git
cd Emergency-evacuation-AI
```

### 2. Python Virtual Environment Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Frontend Dependencies Setup
```bash
cd dashboard
npm install
cd ..
```

### 4. Environment Configuration (Optional)
```bash
# Copy template configuration (defaults work out-of-the-box)
cp .env.example .env
```

---

## 🚀 How to Run

### Option A: Launch Everything Simultaneously
```bash
python run.py
```
This starts both the FastAPI backend (`http://localhost:8000`) and the Vite dashboard (`http://localhost:5174`).

### Option B: Run Backend & Frontend Separately

**Terminal 1 — Backend API:**
```bash
python run.py --backend
# or: uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend Dashboard:**
```bash
python run.py --dashboard
# or: cd dashboard && npm run dev
```

### Option C: Run the CLI Demonstration
To run a complete 50-step simulated evacuation directly in your terminal:
```bash
python run.py --demo
```

### Accessing the Applications:
- **Operator Command Center**: [http://localhost:5174/operator](http://localhost:5174/operator)
- **Citizen Evacuation Assistant**: [http://localhost:5174/user](http://localhost:5174/user)
- **FastAPI Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Running Tests

### 1. Fast End-to-End System Test
Validates scenario loading, agent pipeline, LangGraph workflow, simulation, CV fallback, database, and user routing:
```bash
python run.py --test
```
*Expected output: `Results: 7/7 passed`*

### 2. Full Pytest Test Suite
Runs all 49+ unit and integration tests across agents, APIs, routing, optimization, crowd models, and simulation:
```bash
pytest tests/ -v
```

### 3. Frontend Production Build Validation
```bash
cd dashboard && npm run build
```

---

## 🔌 API Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/emergency/start` | Initialize an emergency scenario (`chemical_spill`, `fire`, etc.). |
| `POST` | `/api/emergency/step` | Advance the simulation by one time step (runs agent cycle). |
| `POST` | `/api/emergency/block-road` | Dynamically close a road corridor (triggers auto replanning). |
| `POST` | `/api/emergency/unblock-road` | Re-open a previously closed road corridor. |
| `POST` | `/api/emergency/replan` | Manually trigger a full multi-agent re-optimization cycle. |
| `POST` | `/api/emergency/reset` | Reset simulation state to Standby. |
| `GET` | `/api/emergency/status` | Full operator emergency state and scenario metrics. |
| `GET` | `/api/user/route?zone_id=...` | Personalized citizen evacuation route, assigned exit, and ETA. |
| `GET` | `/api/user/map-data?zone_id=...` | Live map topology, route coordinates, and blocked corridors. |
| `GET` | `/api/user/zones` | List of available evacuation zones for selection. |
| `GET` | `/api/user/alerts` | Public emergency incident and hazard alerts. |
| `POST` | `/api/user/location` | Resolves GPS coordinates to the nearest evacuation zone. |
| `GET` | `/api/agents/state` | Current internal state of all multi-agent components. |

---

## ⚠️ Current Limitations

- **Simulated Demonstration Environment**: Crowd movements, road congestion curves, and sensor alerts are generated by simulated mathematical models rather than live municipal traffic feeds.
- **Topology Resolution**: The current Hyderabad scenario models 6 primary urban zones, 4 peripheral exits, and 12 connecting arterial corridors. Sub-arterial street-level routing is simplified.
- **Hardware Acceleration**: Deep learning computer vision models (YOLOv8, CSRNet) run on CPU with fallback synthetic generators when GPU hardware is unavailable.
- **Network Protocol**: Frontend polling is used for state synchronization; WebSocket streaming is planned for high-frequency updates.

---

## 🔮 Future Enhancements

- **Real-Time Sensor Integration**: Connect to live municipal traffic API feeds and CCTV camera RTMP streams.
- **Expanded Microscopic Routing**: Ingest full OpenStreetMap Hyderabad road networks using Open Source Routing Machine (OSRM) integration.
- **SUMO Micro-Traffic Coupling**: Full bidirectional coupling with Eclipse SUMO for vehicle-by-vehicle acceleration and intersection simulation.
- **Multi-Modal Transit**: Extended routing including Hyderabad Metro Rail stations and dedicated emergency bus priority lanes.
- **Mobile Push Notifications**: Web Push API for citizen evacuation alerts and live progress tracking.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

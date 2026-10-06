# PROJECT AUDIT — Food Delivery Simulator (NotArsal Base)

**Audit Date:** 2026-10-06  
**Auditor:** SmartRoute Engineering Team  
**Milestone:** 1 — Audit Only

---

## 1. Repository Overview

| Field | Value |
|---|---|
| Repository | https://github.com/NotArsal/Food-Delivery-Simulator |
| Local Path | `D:\DAA\CP\Food-Delivery-Simulator` |
| Python Version | 3.14.6 |
| Node.js Version | 24.18.0 |
| Backend Framework | FastAPI + Uvicorn |
| Frontend Framework | React 19 + Vite 7 |
| Map Library | Leaflet + React-Leaflet + OpenStreetMap |
| Road Network | OSMnx (OpenStreetMap) + NetworkX |
| ML Model | RandomForest (scikit-learn) for ETA prediction |

---

## 2. Project Structure

```
Food-Delivery-Simulator/
├── backend/                      # FastAPI backend
│   ├── main.py                   # API server, WebSocket, REST endpoints
│   ├── simulation.py             # SimulationEngine class (tick-based loop)
│   ├── routing.py                # All routing algorithm implementations
│   ├── route_optimizer.py        # Multi-stop route planner (constrained greedy TSP)
│   ├── batching.py               # K-Means order batching
│   ├── drivers.py                # Driver initialization + greedy assignment
│   ├── orders.py                 # Order generation (real OSM restaurant data)
│   ├── road_network.py           # OSMnx graph loading + synthetic fallback
│   ├── traffic.py                # Traffic simulation (random + time-of-day)
│   ├── pune_data.py              # Pune zone/restaurant/traffic data
│   ├── requirements.txt          # Python dependencies
│   ├── routing_algorithms/
│   │   ├── algorithm_router.py   # Dynamic algorithm selector (enum-based)
│   │   └── genetic_algorithm.py  # Genetic Algorithm (TSP, partially integrated)
│   └── cache/                    # (empty, reserved)
├── frontend/                     # React frontend
│   ├── src/
│   │   ├── App.jsx               # Root app: WS mgmt, start/stop/reset
│   │   ├── components/
│   │   │   ├── Dashboard.jsx     # Main dashboard layout
│   │   │   ├── MapView.jsx       # Leaflet map (riders, orders, routes)
│   │   │   ├── SimControls.jsx   # Simulation start/stop/config controls
│   │   │   ├── MetricsPanel.jsx  # Live metrics display
│   │   │   ├── AlgorithmChart.jsx # Algorithm comparison bar charts
│   │   │   └── AlgorithmSelector.jsx # Algorithm selection UI
│   │   ├── App.css               # Global styles
│   │   └── main.jsx              # React entry point
│   ├── package.json              # Frontend deps (leaflet, recharts, react-leaflet)
│   └── vite.config.js
├── data/
│   ├── pune_india_graph.graphml  # Cached Pune OSM road graph (~11 MB)
│   ├── pune_india_restaurants.csv
│   ├── mumbai_india_graph.graphml
│   ├── mumbai_india_restaurants.csv
│   ├── restaurants.csv           # Generic restaurants CSV
│   ├── eta_model.pkl             # Trained RandomForest ETA model (~24 MB)
│   ├── training_data.csv         # ML training data (synthetic)
│   └── cache/                    # OSMnx tile cache (14 JSON files)
├── ml/
│   ├── generate_training_data.py # Synthetic data generator
│   ├── train_model.py            # RandomForest trainer
│   └── predict.py                # ETA prediction API
├── simulation/
│   └── run_simulation.py         # Standalone simulation runner
└── docs/
    └── superpowers/
        ├── plans/                # Planning documents
        └── specs/                # Design spec documents
```

---

## 3. Backend Architecture

### 3.1 FastAPI Application (`main.py`)

**REST Endpoints:**

| Method | Path | Description |
|---|---|---|
| GET | `/` | Health check + ML availability |
| GET | `/api/network/stats` | Graph stats + traffic summary |
| GET | `/api/orders` | Current orders + statistics |
| GET | `/api/drivers` | Driver states + statistics |
| GET | `/api/metrics` | Simulation metrics |
| POST | `/api/simulation/start` | Start simulation with config |
| POST | `/api/simulation/stop` | Stop running simulation |
| POST | `/api/simulation/reset` | Reset + reinitialize |
| POST | `/api/simulation/config` | Update routing mode/algorithm |
| POST | `/api/predict-eta` | ML ETA prediction endpoint |
| GET | `/api/route` | Point-to-point route computation |
| GET | `/api/algorithms/compare` | Compare all algorithms on same route |
| WS | `/ws` | WebSocket for live state broadcast |

**Simulation Config Parameters:**
- `num_orders`: default 1000
- `num_drivers`: default 50
- `city`: default `"Pune, India"`
- `tick_delay`: default 2.0s

### 3.2 Simulation Engine (`simulation.py`)

**Tick-based loop:**
1. `_release_orders()` — releases 10 orders per tick
2. `update_traffic()` — every 5 ticks
3. `_run_batching()` — K-Means batching of pending orders
4. `_assign_drivers()` — greedy nearest-driver assignment
5. `_compute_routes()` — constrained greedy TSP per driver
6. `_move_drivers()` — advances drivers along routes (40 km/h / traffic)
7. `_update_metrics()` — aggregates metrics

**Routing modes:**
- `dynamic` — auto-selects algorithm based on distance/urgency/traffic
- `manual` — uses specified algorithm

**Simulation State (broadcast via WS):**
```json
{
  "tick": int,
  "metrics": {...},
  "drivers": [{driver_id, lat, lng, status, route_coords, progress, ...}],
  "orders": [{order_id, restaurant_lat/lng, customer_lat/lng, status}],
  "is_running": bool,
  "config": {routing_mode, manual_algorithm}
}
```

---

## 4. Existing Algorithms

### 4.1 Level 1 — Point-to-Point Routing (`routing.py`)

| Algorithm | Implementation | Correctness | Notes |
|---|---|---|---|
| **Dijkstra** | Custom (heapq) | ✅ Correct | Tracks explored nodes, calc_time_ms |
| **A\*** | Custom (heapq + haversine heuristic) | ✅ Correct | Same core as Dijkstra with is_astar flag |
| **BFS** | Custom (deque) | ✅ Correct | Unweighted shortest path |
| **DFS** | Custom (stack) | ✅ Correct | Not optimal, for comparison only |
| **Greedy Best-First** | Custom (heapq, heuristic only) | ✅ Correct | Demonstrates heuristic-only search |
| **Bellman-Ford** | NetworkX wrapper | ✅ Correct | Slow on large graphs as expected |
| **Floyd-Warshall** | NetworkX on subgraph (100 nodes) | ✅ Correct | Subgraph-only to avoid O(n³) on full graph |

All algorithms return:
- `path_nodes`, `path_coords`, `explored_coords`
- `total_distance_m`, `estimated_time_s`
- `num_nodes`, `nodes_explored`, `calc_time_ms`

**Dynamic Mode Selection** (`find_route` with `dynamic_mode=True`):
- urgent → A*
- dist > 5 km → A*
- traffic > 1.5 → Dijkstra
- dist < 1 km → Greedy
- else → Dijkstra

### 4.2 Level 2 — Multi-Stop Route Sequencing (`route_optimizer.py`)

| Component | Implementation | Status |
|---|---|---|
| **Constrained Greedy TSP** | Custom (pickup-before-delivery constraint) | ✅ Working |
| **Distance Matrix** | One-to-all Dijkstra (O(N·(E+V log V))) | ✅ Working |
| **Genetic Algorithm** | Custom (exists in `routing_algorithms/`) | ⚠️ Defined but NOT used (always falls to greedy) |

**Algorithm selector** (`algorithm_router.py`):
- Maps scenario params to algorithm enum
- Currently unused by main simulation loop

### 4.3 Batching (`batching.py`)

| Method | Status |
|---|---|
| **K-Means Clustering** | ✅ Working — sklearn KMeans on restaurant coords |
| Max batch size | 3 orders |
| Max batch radius | 2.0 km |
| Priority handling | ✅ Priority orders attract drivers faster |

### 4.4 Driver Assignment (`drivers.py`)

| Method | Status |
|---|---|
| **Nearest-Driver Greedy** | ✅ Working — min-heap scoring by distance |
| Priority batch bonus | ✅ −3 km equivalent for high-priority batches |
| Load balancing | ✅ +0.1 per completed delivery |

### 4.5 ML ETA (`ml/predict.py`, `ml/train_model.py`)

| Feature | Value |
|---|---|
| Model | RandomForest Regressor (100 trees) |
| Features | route_distance, traffic_level, num_stops, hour_of_day |
| Target | delivery_time_minutes |
| Model file | `data/eta_model.pkl` (~24 MB, pre-trained) |
| Status | ✅ Working — loaded on startup, fallback formula if unavailable |

### 4.6 Traffic Simulation (`traffic.py`)

| Feature | Status |
|---|---|
| Random traffic assignment | ✅ Low/Medium/High probabilities |
| Time-of-day adjustment | ✅ Rush hour increases high-traffic probability |
| Graph edge update | ✅ `travel_time = base_travel_time * multiplier` |
| Multipliers | Low: 1.0, Medium: 1.3, High: 1.8 |

---

## 5. Road Network (`road_network.py`)

| Feature | Status |
|---|---|
| OSMnx integration | ✅ Downloads and caches from OpenStreetMap |
| Graph caching | ✅ Saved as `.graphml`, reloaded on restart |
| Pune graph | ✅ Pre-cached (`pune_india_graph.graphml`, ~11 MB) |
| Mumbai graph | ✅ Pre-cached |
| Edge attributes | `length`, `distance`, `base_travel_time`, `travel_time`, `traffic_multiplier` |
| Synthetic fallback | ✅ 50×50 grid graph if OSMnx unavailable |
| Nearest-node lookup | ✅ via OSMnx or manual Euclidean fallback |

---

## 6. Frontend Architecture

| Component | File | Purpose |
|---|---|---|
| **App.jsx** | `src/App.jsx` | Root: WS connection, sim controls, state management |
| **Dashboard** | `Dashboard.jsx` | Layout: map + controls + metrics + charts |
| **MapView** | `MapView.jsx` | Leaflet map: riders, orders, routes, heatmap |
| **SimControls** | `SimControls.jsx` | Start/stop/reset + speed/config UI |
| **MetricsPanel** | `MetricsPanel.jsx` | Live KPI display |
| **AlgorithmChart** | `AlgorithmChart.jsx` | Bar/line charts for algorithm comparison |
| **AlgorithmSelector** | `AlgorithmSelector.jsx` | Algorithm picker UI |

**Frontend dependencies:**
- `react@19`, `react-dom@19`
- `leaflet@1.9.4`, `react-leaflet@5.0.0`
- `leaflet.heat@0.2.0` (heatmap overlay)
- `recharts@3.8.1` (charts)
- `vite@7.3.1` (bundler)

---

## 7. Data Models

### Order Object
```python
{
    "order_id": "ORD-0001",
    "restaurant_id": "...",
    "restaurant_name": "...",
    "restaurant_zone": "Kothrud",
    "restaurant_lat": float,
    "restaurant_lng": float,
    "customer_lat": float,
    "customer_lng": float,
    "restaurant_node": int,  # graph node id
    "customer_node": int,
    "order_time": ISO_string,
    "status": "pending|assigned|picked|delivered",
    "assigned_driver": str | None,
    "batch_id": str | None,
    "is_priority": bool
}
```

### Driver Object
```python
{
    "driver_id": "DRV-001",
    "lat": float,
    "lng": float,
    "current_node": int,
    "status": "idle|picking|delivering|returning",
    "active_batch": str | None,
    "route_coords": [(lat, lng), ...],
    "route_progress": int,
    "current_orders": [order_id, ...],
    "stats": {
        "deliveries_completed": int,
        "total_distance_m": float,
        "total_time_s": float
    }
}
```

### Batch Object
```python
{
    "batch_id": "BATCH-0001",
    "orders": [order_id, ...],
    "centroid_lat": float,
    "centroid_lng": float,
    "num_orders": int,
    "is_priority": bool,
    "assigned": bool,
    "assigned_driver": str | None
}
```

---

## 8. Existing Python Dependencies

From `requirements.txt`:
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
websockets>=12.0
osmnx>=1.9.0
networkx>=3.2
pandas>=2.2.0
numpy>=2.0.0
scikit-learn>=1.5.0
joblib>=1.3.0
geopy>=2.4.0
```

**Installed at audit time:**
- ✅ numpy 2.5.3
- ✅ pandas 3.0.6
- ✅ scikit-learn 1.9.1
- ✅ joblib 1.6.0
- ⚠️ fastapi — needs installation
- ⚠️ uvicorn — needs installation
- ⚠️ osmnx — needs installation
- ⚠️ networkx — needs installation
- ⚠️ websockets — needs installation
- ⚠️ geopy — needs installation

---

## 9. Git History (last 10 commits)

```
fe3c2a6 Fixed Backend Logic, Simulation, UI/UX
e5f972b Fixed Markers
cc42b8c Fixed Map, Sidebar, Routing issues
c9015d7 fix: resolve routing module naming conflict
9473e26 feat: add premium frontend components
5f82898 test: backend integration verified
4fd4ce1 feat: add algorithm compare and heatmap API endpoints
fdfaba7 chore: simulation already uses routing_mode for algorithm selection
9a56ae9 feat: add pune_data traffic zone integration
113e146 feat: integrate pune_data into orders module
```

---

## 10. Known Bugs and Limitations

| # | Issue | Severity | Location |
|---|---|---|---|
| 1 | Genetic algorithm defined but **never invoked** in `route_optimizer.py` (both branches use greedy) | Medium | `route_optimizer.py:130-135` |
| 2 | `algorithm_router.py` enum-based selector is **never called** by simulation | Medium | `algorithm_router.py` |
| 3 | Delivery time in `_complete_delivery` is **random** (600–2400s), not actually computed from route | High | `simulation.py:199` |
| 4 | `_path_stats()` uses flat `12` second fallback when `travel_time` is missing — unrealistic | Medium | `routing.py:44` |
| 5 | `get_edge_traffic_level()` uses `G.edges[u, v]` which fails on MultiDiGraph (must be `G.edges[u, v, 0]`) | Medium | `traffic.py:76` |
| 6 | `driver["stats"]["total_distance_m"]` accumulates `accumulated_dist` which can be zero if segment is large | Low | `simulation.py:189` |
| 7 | Floyd-Warshall uses `random.sample` — results non-deterministic, doesn't include source/target | Medium | `main.py:325` |
| 8 | CORS config has both `allow_origins=["*"]` comment about incompatibility but is already fixed | Info | `main.py:61` |
| 9 | No road closure simulation | High | Missing entirely |
| 10 | No dynamic re-routing on traffic change | High | Missing entirely |
| 11 | No time windows on orders | High | Missing entirely |
| 12 | No capacity constraints on drivers | Medium | Missing |
| 13 | No stochastic/demand scenarios | Medium | Missing |
| 14 | Delivery completion marks orders as "delivered" before driver actually reaches customer node | Medium | `simulation.py:196` |

---

## 11. Extension Points

| Extension Point | File | Current State | Required Extension |
|---|---|---|---|
| New routing algorithms | `routing.py` | 6 algorithms present | Add Held-Karp, 2-opt |
| Multi-stop sequencing | `route_optimizer.py` | Greedy TSP only | Add Held-Karp, 2-opt, OR-Tools |
| Driver assignment | `drivers.py` | Greedy nearest only | Add Hungarian, FoodMatch-inspired |
| Order batching | `batching.py` | K-Means only | Add no-batching, FoodMatch-inspired |
| Simulation engine | `simulation.py` | Basic tick loop | Add dynamic re-routing, order insertion |
| Traffic simulation | `traffic.py` | Random + time-of-day | Add road closures, targeted disruptions |
| Experiment engine | Missing | — | Create ExperimentManager |
| Metrics | `simulation.py` | Basic KPIs | Add lateness, utilization, optimality gap |
| Road closure | Missing | — | Add closure events + rerouting |
| CVRPTW | Missing | — | OR-Tools integration |
| ACS | Missing | — | Optional Ant Colony System |
| Algorithm explanation UI | Missing | — | Viva-ready explanation panel |

---

## 12. API Verification Checklist

| Endpoint | Expected Status | Notes |
|---|---|---|
| GET `/` | 200 OK | Returns version + ML availability |
| GET `/api/network/stats` | 200 OK | Returns graph nodes/edges + traffic |
| GET `/api/orders` | 200 OK | Returns order list + stats |
| GET `/api/drivers` | 200 OK | Returns driver states + stats |
| GET `/api/metrics` | 200 OK | Returns simulation metrics |
| POST `/api/simulation/start` | 200 OK | Starts background tick loop |
| POST `/api/simulation/stop` | 200 OK | Stops simulation |
| POST `/api/simulation/reset` | 200 OK | Re-initializes |
| POST `/api/simulation/config` | 200 OK | Updates routing mode |
| POST `/api/predict-eta` | 200 OK | Returns ETA prediction |
| GET `/api/route` | 200 OK | Returns path coords + metrics |
| GET `/api/algorithms/compare` | 200 OK | Returns all algorithm results |
| WS `/ws` | 101 Upgrade | Broadcasts tick state |

---

## 13. Missing Features vs. Project Specification

| Feature | Required | Status |
|---|---|---|
| BFS | ✅ | ✅ Present |
| DFS | ✅ | ✅ Present |
| Dijkstra | ✅ | ✅ Present |
| A* | ✅ | ✅ Present |
| Bellman-Ford | ✅ | ✅ Present |
| Floyd-Warshall | ✅ | ✅ Present (subgraph) |
| Greedy TSP | ✅ | ✅ Present (constrained) |
| **Held-Karp DP** | ✅ | ❌ Missing |
| **2-opt improvement** | ✅ | ❌ Missing |
| Greedy assignment | ✅ | ✅ Present |
| **Hungarian matching** | ✅ | ❌ Missing |
| **FoodMatch-inspired assignment** | ✅ | ❌ Missing |
| No-batching mode | ✅ | ❌ Missing |
| K-Means batching | ✅ | ✅ Present |
| **FoodMatch-inspired batching** | ✅ | ❌ Missing |
| **OR-Tools CVRPTW** | ✅ | ❌ Missing |
| **Dynamic re-routing** | ✅ | ❌ Missing |
| **Road closure simulation** | ✅ | ❌ Missing |
| **New order insertion** | ✅ | ❌ Missing |
| **ExperimentManager** | ✅ | ❌ Missing |
| **AlgorithmSelector (modular)** | ✅ | ⚠️ Partial (unused enum) |
| **Multi-objective scoring** | ✅ | ❌ Missing |
| **Environmental metrics** | ✅ | ❌ Missing |
| ML ETA | ✅ | ✅ Present (RandomForest) |
| WebSocket | ✅ | ✅ Present |
| Live dashboard | ✅ | ✅ Present |
| **Algorithm comparison table** | ✅ | ⚠️ Partial (chart only) |
| **Algorithm explanation UI** | ✅ | ❌ Missing |
| **Stochastic demand scenarios** | ✅ | ❌ Missing |
| **Time windows on orders** | ✅ | ❌ Missing |
| **Capacity constraints** | ✅ | ❌ Missing |
| Genetic Algorithm | Optional | ✅ Present but inactive |
| **ACS** | Optional | ❌ Missing |

---

## 14. How to Run the Existing Project

### Backend
```bash
# Install dependencies
pip install fastapi uvicorn websockets osmnx networkx geopy

# Start backend
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend
```bash
# Install dependencies
cd frontend
npm install

# Start dev server
npm run dev
# Opens at http://localhost:5173
```

### ML Model (pre-trained model already at data/eta_model.pkl)
```bash
# To retrain (optional)
cd ml
python train_model.py
```

### Verify
1. Open http://localhost:5173 — map should load with Pune centered
2. Click "Start Simulation" — drivers should begin moving
3. Check http://localhost:8000/docs — Swagger UI
4. WebSocket at ws://localhost:8000/ws — live state

---

## 15. Milestone 1 Conclusion

**What works:**
- FastAPI backend with full REST + WebSocket
- React frontend with live map
- 6 routing algorithms (Dijkstra, A*, BFS, DFS, Greedy, Bellman-Ford)
- Floyd-Warshall on subgraph
- Constrained Greedy TSP for multi-stop routing
- K-Means order batching
- Nearest-driver greedy assignment
- Random + time-based traffic simulation
- ML ETA (RandomForest, pre-trained)
- Pune OSM road network (cached)
- Mumbai OSM road network (cached)
- Algorithm comparison endpoint
- Live simulation dashboard

**What is missing for full project specification:**
- Held-Karp (DP TSP)
- 2-opt improvement
- Hungarian matching
- FoodMatch-inspired assignment + batching
- OR-Tools CVRPTW
- Dynamic re-routing on traffic/closure
- Road closure events
- New-order-during-simulation insertion
- ExperimentManager with CSV/JSON output
- Time windows and capacity constraints
- Stochastic demand scenarios
- Algorithm explanation UI (viva panel)
- Environmental metrics
- Comprehensive test suite

**Recommendation:**  
The existing codebase is a solid, working foundation. Do NOT rewrite. Extend it milestone by milestone per the specification. The next step (Milestone 2) should create modular strategy interfaces without changing existing behavior.

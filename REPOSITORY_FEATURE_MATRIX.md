# REPOSITORY FEATURE MATRIX

**Project:** SmartRoute — Dynamic Food Delivery Optimization Platform  
**Date:** 2026-10-06

This matrix compares all 10 reference repositories across key features relevant to the DAA project specification.

---

## Legend

| Symbol | Meaning |
|---|---|
| ✅ | Feature present and working |
| ⚠️ | Feature partially present or limited |
| ❌ | Feature absent |
| 📖 | Concept present (research/docs), no implementation |
| 🔌 | Via external dependency |

---

## Feature Matrix

| Feature | **NotArsal** (BASE) | **FoodMatch** (RESEARCH) | **Dhanoliya RouteOS** | **Mauros191** | **WalterWootz** | **Dungnotnull** | **Cha635** | **Noumanh11** | **DVRPTW_ACS** | **DVRPSR** |
|---|---|---|---|---|---|---|---|---|---|---|
| **INFRASTRUCTURE** | | | | | | | | | | |
| Language | Python | Python | Python | Python | Python | Python | Python | Python | Java | C++/CPLEX |
| Backend Framework | FastAPI | None | FastAPI | Python | FastAPI | Python | Streamlit | Flask | None | None |
| Frontend | React+Leaflet | None | React | None | React | None | None | None | None | None |
| WebSocket | ✅ | ❌ | ✅ | ❌ | ⚠️ | ❌ | ❌ | ❌ | ❌ | ❌ |
| REST API | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ⚠️ | ❌ | ❌ |
| **ROAD NETWORK** | | | | | | | | | | |
| OSMnx/OpenStreetMap | ✅ | ❌ | ❌ | 🔌 OSRM | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| NetworkX graph | ✅ | ✅ | ⚠️ | ❌ | ❌ | ❌ | ✅ | ⚠️ | ❌ | ❌ |
| Graph caching | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Synthetic graph fallback | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Pune/India support | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **ROUTING ALGORITHMS (L1 — Point-to-Point)** | | | | | | | | | | |
| BFS | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| DFS | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Dijkstra | ✅ | ✅ | ✅ | 🔌 | ✅ | 🔌 | ✅ | ✅ | ❌ | ❌ |
| A* | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Bellman-Ford | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Floyd-Warshall | ✅ (subgraph) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Greedy Best-First | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **SEQUENCING ALGORITHMS (L2 — Multi-Stop)** | | | | | | | | | | |
| Nearest Neighbor (Greedy TSP) | ✅ (constrained) | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Held-Karp (DP TSP)** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| **2-opt** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Or-opt | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Genetic Algorithm | ✅ (inactive) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Ant Colony System (ACS)** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| **VEHICLE ROUTING (CVRPTW)** | | | | | | | | | | |
| OR-Tools CVRPTW | ❌ | ❌ | ✅ | 🔌 | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Capacity constraints | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| Time windows | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| Multi-vehicle routing | ⚠️ (basic) | ❌ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| Gurobi support | ❌ | ❌ | ❌ | ❌ | ⚠️ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **ASSIGNMENT** | | | | | | | | | | |
| Greedy nearest assignment | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Priority-based assignment | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Hungarian matching** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 📖 | ❌ | ❌ |
| **Bipartite matching** | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **FoodMatch-style assignment** | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Best-first candidate search | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Graph clustering for batching | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **BATCHING** | | | | | | | | | | |
| No-batching mode | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Greedy proximity batching | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| K-Means batching | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **FoodMatch-inspired graph batching** | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Order rejection on infeasibility | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **SIMULATION** | | | | | | | | | | |
| Tick-based simulation loop | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Discrete-event simulation | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Dynamic order arrivals | ✅ (batched) | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Restaurant preparation time | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Driver movement simulation | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Traffic simulation | ✅ | ❌ | ⚠️ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Rush hour simulation | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Road closure simulation** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Dynamic re-routing** | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ |
| **New order insertion mid-sim** | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Stochastic demand | ❌ | ❌ | ❌ | ✅ | ❌ | ⚠️ | ❌ | ❌ | ✅ | ✅ |
| Rollout/policy-based decisions | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **ML / ETA** | | | | | | | | | | |
| ML ETA model | ✅ RandomForest | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Food prep time model | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Dynamic ETA buffer | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **METRICS** | | | | | | | | | | |
| Total distance | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Average delivery time | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| On-time delivery % | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Rider utilization | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Nodes explored | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Runtime (ms) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Optimality gap | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Environmental metrics | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Lateness / delay | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **EXPERIMENTS** | | | | | | | | | | |
| Algorithm comparison endpoint | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| CSV/JSON output | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Controlled experiment runner | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Multiple seeds | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **DOCUMENTATION** | | | | | | | | | | |
| README | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Algorithm complexity docs | ❌ | 📖 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | 📖 | 📖 |
| API docs (Swagger) | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| License | Unspecified | MIT | Unspecified | MIT | Unspecified | Unspecified | Unspecified | Unspecified | Academic | Academic |

---

## What We Inherit/Reuse from Each Repository

### 1. NotArsal (BASE)
**Reuse:** Entire codebase is our starting point.
- FastAPI server, WebSocket, all REST endpoints
- OSMnx road network with Pune + Mumbai cached graphs
- All 6 point-to-point routing algorithms
- Constrained Greedy TSP
- K-Means batching
- Greedy nearest assignment
- Tick-based simulation engine
- React + Leaflet frontend
- RandomForest ETA model (pre-trained)
- Traffic simulation

### 2. FoodMatch (RESEARCH — Primary Research Reference)
**Extract concepts:**
- Dynamic order-to-rider assignment as a bipartite matching problem
- Weighted edge construction: `(rider-to-restaurant + restaurant-to-customer)` travel cost
- Best-first candidate generation: filter riders by proximity before building full graph
- Batching as graph-clustering problem: cluster orders by proximity + restaurant locality
- Dynamic vehicle positions: use current driver positions, not static home bases
- Evaluation methodology: lateness, on-time %, utilization across multiple seeds

**Our adaptation:** `FoodMatchInspiredAssignment`, `FoodMatchInspiredBatching`

### 3. Dhanoliya RouteOS (ARCHITECTURE REFERENCE)
**Extract concepts:**
- OR-Tools CVRPTW model structure (capacity + time window constraints)
- Solver configuration: time limit, solution strategies (AUTOMATIC, PARALLEL_CHEAPEST_INSERTION)
- Dynamic re-sequencing on traffic disruption
- WebSocket streaming of optimization progress
- Analytics structure: distance, time, utilization per vehicle

### 4. Mauros191 (SIMULATION REFERENCE)
**Extract concepts:**
- Discrete-event simulation pattern (vs tick-based)
- Restaurant food preparation time as a distinct event
- Order queue management with rejection logic
- OSRM for real travel time lookups (we use Dijkstra/A* instead)

### 5. WalterWootz (CVRPTW REFERENCE)
**Extract concepts:**
- OR-Tools API usage patterns
- Time window modeling
- Vehicle capacity modeling
- Example dataset structure (benchmark instances)

### 6. Dungnotnull (MULTI-OBJECTIVE REFERENCE)
**Extract concepts:**
- 2-opt and Or-opt improvement algorithms
- Multi-objective scoring: distance + time + environmental cost
- Traffic + weather disruption modeling
- Fleet size analysis experiments
- Scenario analysis framework

### 7. Cha635 (BENCHMARK REFERENCE)
**Extract concepts:**
- Held-Karp exact TSP implementation
- Greedy vs Held-Karp comparison methodology
- Optimality gap calculation
- Real-road distance vs straight-line comparison
- Runtime growth O(n² · 2ⁿ) demonstration

### 8. Noumanh11 (DAA BASELINE)
**Extract concepts:**
- Priority-based order handling
- 2-opt improvement idea (reference implementation)
- Simple BFS-based assignment baseline
- Hungarian algorithm as conceptual reference

### 9. DVRPTW_ACS (OPTIONAL)
**Extract concepts:**
- Ant Colony System for DVRPTW
- Pheromone trail update rules
- Local search integration with metaheuristic
- Dynamic vehicle routing with time windows

### 10. DVRPSR (OPTIONAL)
**Extract concepts:**
- Stochastic request arrival models
- Accept/reject decision policies
- Rollout policy for online decision making
- Re-optimization triggers

---

## Priority for Integration

| Priority | Repository | Integration Type |
|---|---|---|
| 1 | **NotArsal** | Base — extend in-place |
| 2 | **FoodMatch** | Algorithm adaptation — new Python modules |
| 3 | **Dhanoliya RouteOS** | OR-Tools patterns — new optimizer module |
| 4 | **Mauros191** | Simulation concepts — improve simulation.py |
| 5 | **WalterWootz** | CVRPTW config patterns — supplement #3 |
| 6 | **Dungnotnull** | 2-opt + multi-objective — new modules |
| 7 | **Cha635** | Held-Karp reference — new module |
| 8 | **Noumanh11** | DAA baseline reference — documentation |
| 9 | **DVRPTW_ACS** | Optional ACS module |
| 10 | **DVRPSR** | Optional stochastic policies |

---

## Algorithms Sourced From Each Repository

| Algorithm | Source Repository | Our Module |
|---|---|---|
| BFS, DFS | NotArsal | `backend/routing.py` (existing) |
| Dijkstra, A*, Greedy, Bellman-Ford, Floyd-Warshall | NotArsal | `backend/routing.py` (existing) |
| K-Means batching | NotArsal | `backend/batching.py` (existing) |
| Constrained Greedy TSP | NotArsal | `backend/route_optimizer.py` (existing) |
| Genetic Algorithm | NotArsal | `backend/routing_algorithms/genetic_algorithm.py` (inactive) |
| Held-Karp (DP TSP) | **Cha635** (reference) | `backend/algorithms/sequencing/held_karp.py` (to add) |
| 2-opt improvement | **Dungnotnull** (reference) | `backend/algorithms/sequencing/two_opt.py` (to add) |
| Hungarian matching | **Noumanh11** (concept) + scipy | `backend/algorithms/assignment/hungarian.py` (to add) |
| FoodMatch assignment | **FoodMatch** (research) | `backend/algorithms/assignment/foodmatch_inspired.py` (to add) |
| FoodMatch batching | **FoodMatch** (research) | `backend/algorithms/batching/foodmatch_inspired.py` (to add) |
| OR-Tools CVRPTW | **Dhanoliya/WalterWootz** (reference) | `backend/algorithms/optimization/cvrptw.py` (to add) |
| ACS | **DVRPTW_ACS** (optional) | `backend/algorithms/optimization/acs.py` (optional) |

---

*This matrix will be updated as new algorithms and features are implemented.*

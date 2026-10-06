# System Architecture

## 1. High-Level Topology
SmartRoute follows a decoupled client-server architecture:
*   **Frontend**: React 19 + Vite + Leaflet mapping. Communicates via REST for controls and WebSockets for high-frequency state updates.
*   **Backend**: FastAPI + Uvicorn async server.
*   **Core Engine**: A tick-based discrete event simulation loop (`SimulationEngine`).

## 2. The Simulation Loop
The backend maintains a continuous loop governed by `self.tick_delay` (default 2s).
On each tick, the system executes:
1.  **Release Orders**: Moves newly generated orders to a "pending" queue.
2.  **Traffic Updates**: Modifies graph edge weights based on time-of-day distributions (every 5 ticks).
3.  **Batching**: Groups pending orders using `BatchingAlgorithm`.
4.  **Assignment**: Matches idle drivers to batches using `AssignmentAlgorithm`.
5.  **Sequencing & Routing**: Computes the optimal visit order (`SequencingAlgorithm`), then builds the physical path using `RoutingAlgorithm`.
6.  **Movement**: Advances driver `lat/lng` coordinates along the physical route array.

## 3. Strategy Pattern Modularization (Milestone 2)
The codebase strictly adheres to the Strategy Design Pattern. The core engine is decoupled from the algorithm implementations via abstract base classes in `backend/algorithms/interfaces.py`:
*   `BatchingAlgorithm` (e.g., `KMeansBatching`, `FoodMatchBatching`)
*   `AssignmentAlgorithm` (e.g., `GreedyNearestAssignment`, `HungarianAssignment`, `FoodMatchAssignment`)
*   `SequencingAlgorithm` (e.g., `GreedySequencing`, `HeldKarpSequencing`, `TwoOptSequencing`)
*   `RoutingAlgorithm` (e.g., `AStar`, `Dijkstra`)
*   `OptimizationAlgorithm` (e.g., `ORToolsCVRPTW`)

## 4. Graph Architecture
We utilize `NetworkX` combined with `OSMnx`. The physical road network is modeled as a `MultiDiGraph` where edges contain attributes like `travel_time` and `distance`.
Road closures dynamically rewrite the `travel_time` attribute of specific edges to `1000000.0`, ensuring algorithms naturally recalculate paths around the incident.

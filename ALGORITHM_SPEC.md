# Algorithm Specifications

This document defines the mathematical and algorithmic implementations used within SmartRoute.

## 1. Route Sequencing (Constrained TSP)
The problem involves ordering a set of Pickup (P) and Delivery (D) nodes for a driver such that total travel time is minimized, subject to the constraint that $P_i$ is visited before $D_i$.

### A. Held-Karp Dynamic Programming (`algorithms/sequencing/held_karp.py`)
*   **Approach**: Exact global minimum via Dynamic Programming.
*   **Time Complexity**: $O(N^2 2^N)$
*   **Implementation**: We iterate over bitmasks representing visited nodes. A state transition to a delivery node is only valid if its corresponding pickup node bit is already set in the current mask.

### B. 2-Opt Local Search (`algorithms/sequencing/two_opt.py`)
*   **Approach**: Iterative edge swapping.
*   **Time Complexity**: $O(K \cdot N^2)$, where K is the number of iterations until no improvements.
*   **Implementation**: Takes an initial greedy route, reverses sub-segments, and accepts the swap if the distance decreases AND the pickup-before-delivery validation function returns True.

## 2. Global Assignment
Matching $N$ idle drivers to $M$ order batches.

### A. Hungarian Algorithm (`algorithms/assignment/hungarian.py`)
*   **Approach**: Linear Sum Assignment / Bipartite Matching.
*   **Time Complexity**: $O(N^3)$
*   **Implementation**: Uses `scipy.optimize.linear_sum_assignment` on a cost matrix where $C_{i,j}$ is the distance from driver $i$ to batch $j$, minus a flat priority bonus, plus a load-balancing penalty.

### B. FoodMatch-Inspired Assignment (`algorithms/assignment/foodmatch_inspired.py`)
*   **Approach**: Candidate Filtration + Bipartite Matching.
*   **Implementation**: Prunes the complete bipartite graph by only considering edges where distance is $\le 7.0$ km (best-first). If a batch has no candidates, the constraint is relaxed. The Hungarian algorithm then runs on this highly sparse subgraph, significantly improving scalability.

## 3. Fleet Optimization (CVRPTW)
### Google OR-Tools (`algorithms/optimization/ortools_cvrptw.py`)
*   **Approach**: Constraint Programming.
*   **Implementation**: Folds batching, assignment, and sequencing into a single global step. Modeled using `pywrapcp.RoutingIndexManager`. Pickups and deliveries are tightly coupled via `AddPickupAndDelivery` and `VehicleVar` equality constraints. Handles graceful degradation via `ImportError` traps if the environment rejects protobuf binaries.

## 4. Graph Pathfinding (Level 1)
Implemented via `routing.py`.
*   **A\***: Uses Haversine distance divided by average vehicle speed as the admissible heuristic $h(n)$. Explores significantly fewer nodes than Dijkstra.
*   **Dijkstra**: Evaluates paths purely on cumulative edge weight $g(n)$.

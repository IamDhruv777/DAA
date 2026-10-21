# SmartRoute: Dynamic Food Delivery Optimization

SmartRoute is a Pune food-delivery simulation built around a real OpenStreetMap road graph. It assigns orders to riders, plans pickup and drop-off stops, animates riders along road routes, and supports traffic and road-closure rerouting.

## How a delivery is planned

1. **Batch orders.** The standard simulation uses K-Means to group nearby restaurant pickups (up to three orders per batch, with a 2 km clustering radius). Outliers remain individual batches.
2. **Assign riders.** The standard simulation uses Greedy Nearest to assign batches to available riders. The comparison simulation also offers Hungarian matching.
3. **Sequence stops.** Greedy sequencing chooses the next nearby stop while preserving pickup-before-delivery order. The comparison simulation uses 2-Opt to improve the stop sequence.
4. **Find road paths.** The routing engine calculates paths over the road graph and returns map waypoints. Riders advance along those points each simulation tick. Traffic events and road closures can trigger rerouting.

## Routing choices

| Algorithm | What it does | Rider-navigation notes |
| --- | --- | --- |
| Dijkstra | Finds the lowest travel-cost route through the graph. | Reliable weighted routing; the dynamic router can select it when traffic is high. |
| A* | Uses a goal-directed heuristic to search fewer roads while finding a shortest path. | The dynamic router uses it for most trips, including longer trips. |
| BFS | Finds a route with the fewest road segments. | Does not minimize travel time or physical distance. |
| DFS | Searches deeply along one branch before backtracking. | Does not optimize route length or travel time. |
| Greedy best-first | Chooses the next road using estimated closeness to the destination. | Fast, but may choose a longer route. |
| Floyd–Warshall | Calculates shortest paths between all pairs in a supplied subset of nodes. | The analysis helper exists, but the manual rider selector is not wired to it yet; selecting Floyd currently falls back to Dijkstra. |

In **Dynamic** routing mode, SmartRoute chooses A* or Dijkstra according to trip distance and traffic. In **Manual** mode, the selected algorithm is used when a route is calculated. BFS, DFS, and Greedy are included for comparison and are not generally good choices for fastest real-world delivery.

## Other algorithms

- **FoodMatch batching** groups orders with compatible pickup and delivery locations; it is used by the comparison simulation.
- **Hungarian assignment** considers rider-to-batch pairings together; it is used by the comparison simulation.
- **Held–Karp** computes an optimal stop order for small cases and is used in analysis/benchmarks.
- **CVRPTW (OR-Tools)** is available as an optional fleet optimizer, but is disabled by default in the standard simulation.
- **Bellman–Ford** and **Floyd–Warshall** are available for graph analysis; they are not the standard per-rider navigation algorithms.

## Distance and batching assumptions

Generated customer locations are placed 2–4 km from their restaurant. The 2 km K-Means radius only controls which restaurant pickups can share a batch; it is not a maximum rider-route distance. The standard simulation has no global route-distance cap.

## Run locally

### Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

The API is available at `http://127.0.0.1:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite prints the local URL, usually `http://127.0.0.1:5173`.

## Run benchmarks

```bash
cd backend
python experiments/benchmark_engine.py
```

## Delivery reliability behavior

- A rider stays assigned until all of its active orders are delivered.
- Route planning does not silently omit a failed road segment.
- Pickup and delivery stops are associated with their specific orders, including when orders share map nodes.
- If a route cannot be found, the rider keeps the delivery, retries routing, and the rider panel displays a warning.

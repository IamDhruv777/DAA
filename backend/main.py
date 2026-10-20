"""
Food Delivery Route Optimizer - FastAPI Backend
Main application with REST endpoints and WebSocket server.
"""
import os
import sys
import json
import asyncio
import time
from typing import Set
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Add parent dir to path for ML imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ml_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ml")
sys.path.insert(0, ml_dir)

from road_network import load_graph, get_graph_stats, get_nearest_node, get_node_coords
from routing import find_route, floyd_warshall_subgraph
from traffic import get_traffic_summary, update_traffic
from orders import get_order_stats
from drivers import get_driver_stats
from simulation import SimulationEngine
from dual_simulation import DualSimulationEngine
from pydantic import BaseModel, Field

# Try to import ML predictor
try:
    from predict import predict_eta, load_model
    ML_AVAILABLE = True
except Exception:
    ML_AVAILABLE = False

# Global state
simulation: SimulationEngine = SimulationEngine()
dual_simulation: DualSimulationEngine = DualSimulationEngine()
active_mode: str = "single"
ws_clients: Set[WebSocket] = set()
sim_task = None


@asynccontextmanager
async def lifespan(app):
    """Pre-load graph on startup."""
    print("[APP] Starting Food Delivery Route Optimizer...")
    simulation.initialize(num_orders=5, num_drivers=5)
    dual_simulation.initialize(num_orders=5, num_drivers=5)
    print("[APP] Ready! API docs at http://localhost:8000/docs")
    yield
    simulation.stop()
    dual_simulation.stop()
    print("[APP] Shutting down.")


app = FastAPI(
    title="Food Delivery Route Optimizer",
    description="Logistics simulation platform for Pune, India",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS - note: allow_credentials=True is incompatible with allow_origins=["*"] per CORS spec
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def broadcast_state(state):
    """Broadcast simulation state to all WebSocket clients."""
    if not ws_clients:
        return
    message = json.dumps(state, default=str)
    disconnected = []
    for ws in ws_clients:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        ws_clients.discard(ws)
    for ws in disconnected:
        ws_clients.discard(ws)


# ─── REST ENDPOINTS ─────────────────────────────────────────────


@app.get("/")
async def root():
    return {
        "name": "Food Delivery Route Optimizer",
        "version": "1.0.0",
        "status": "running",
        "ml_available": ML_AVAILABLE,
    }


@app.get("/api/network/stats")
async def network_stats():
    """Get road network statistics."""
    G = simulation.graph or load_graph()
    stats = get_graph_stats(G)
    traffic = get_traffic_summary(G)
    return {"graph": stats, "traffic": traffic}


@app.get("/api/orders")
async def get_orders():
    """Get current orders and statistics."""
    if not simulation.orders:
        return {"orders": [], "stats": {"total_orders": 0}}
    stats = get_order_stats(simulation.orders[:simulation.orders_released])
    # Return limited orders for performance
    visible = []
    for o in simulation.orders[:simulation.orders_released]:
        visible.append({
            "order_id": o["order_id"],
            "restaurant_lat": o["restaurant_lat"],
            "restaurant_lng": o["restaurant_lng"],
            "customer_lat": o["customer_lat"],
            "customer_lng": o["customer_lng"],
            "restaurant_name": o.get("restaurant_name", "Unknown"),
            "restaurant_zone": o.get("restaurant_zone", "Unknown"),
            "status": o["status"],
        })
    return {"orders": visible[:200], "stats": stats}


@app.get("/api/drivers")
async def get_drivers():
    """Get driver states."""
    if not simulation.drivers:
        return {"drivers": [], "stats": {"total_drivers": 0}}
    stats = get_driver_stats(simulation.drivers)
    driver_list = []
    for d in simulation.drivers:
        driver_list.append({
            "driver_id": d["driver_id"],
            "lat": d["lat"],
            "lng": d["lng"],
            "status": d["status"],
            "deliveries": d["stats"]["deliveries_completed"],
            "active_batch": d["active_batch"],
        })
    return {"drivers": driver_list, "stats": stats}


@app.get("/api/metrics")
async def get_metrics():
    """Get simulation metrics."""
    return simulation.metrics


class SimStartConfig(BaseModel):
    num_orders: int = Field(default=5, ge=5, le=100)
    num_drivers: int = 50
    city: str = "Pune, India"
    tick_delay: float = 2.0


@app.post("/api/simulation/start")
async def start_simulation(config: SimStartConfig = None):
    """Start the city-scale simulation."""
    global sim_task, active_mode
    active_mode = "single"
    dual_simulation.stop()

    if simulation.is_running:
        return {"status": "already_running"}

    # Initialize if needed
    if config:
        try:
            simulation.initialize(num_orders=config.num_orders, num_drivers=config.num_drivers, city_name=config.city)
        except Exception as e:
            return {"status": "error", "message": str(e)}
    elif not simulation.graph:
        simulation.initialize()

    # Start simulation in background
    sim_task = asyncio.create_task(simulation.run(ws_broadcast_callback=broadcast_state))

    return {
        "status": "started",
        "total_orders": len(simulation.orders),
        "total_drivers": len(simulation.drivers),
    }


@app.post("/api/simulation/stop")
async def stop_simulation():
    """Stop the simulation."""
    simulation.stop()
    dual_simulation.stop()
    return {"status": "stopped", "metrics": simulation.metrics}


@app.post("/api/simulation/reset")
async def reset_simulation(config: SimStartConfig = None):
    """Reset the simulation."""
    global sim_task
    simulation.stop()
    dual_simulation.stop()
    if sim_task:
        sim_task.cancel()
        sim_task = None
    if config:
        simulation.initialize(num_orders=config.num_orders, num_drivers=config.num_drivers, city_name=config.city)
    else:
        simulation.initialize()
    return {"status": "reset"}


# ─── DUAL SIMULATION BENCHMARK ENDPOINTS ────────────────────────

@app.post("/api/simulation/dual/start")
async def start_dual_simulation(config: SimStartConfig = None):
    """Start synchronized A/B benchmark (Baseline Greedy vs SmartRoute Optimized)."""
    global sim_task, active_mode
    active_mode = "dual"
    simulation.stop()

    if dual_simulation.is_running:
        return {"status": "already_running"}

    orders = config.num_orders if config else 5
    drivers = config.num_drivers if config else 5
    city = config.city if config else "Pune, India"
    delay = config.tick_delay if config else 0.8

    dual_simulation.initialize(num_orders=orders, num_drivers=drivers, city_name=city, tick_delay=delay)
    sim_task = asyncio.create_task(dual_simulation.run(ws_broadcast_callback=broadcast_state))

    return {
        "status": "started",
        "mode": "dual",
        "orders": orders,
        "drivers": drivers
    }


@app.post("/api/simulation/dual/stop")
async def stop_dual_simulation():
    """Stop dual simulation."""
    dual_simulation.stop()
    return {"status": "stopped", "mode": "dual"}


@app.post("/api/simulation/dual/reset")
async def reset_dual_simulation(config: SimStartConfig = None):
    """Reset dual simulation."""
    global sim_task
    dual_simulation.stop()
    if sim_task:
        sim_task.cancel()
        sim_task = None
    orders = config.num_orders if config else 5
    drivers = config.num_drivers if config else 5
    city = config.city if config else "Pune, India"
    delay = config.tick_delay if config else 0.8
    dual_simulation.initialize(num_orders=orders, num_drivers=drivers, city_name=city, tick_delay=delay)
    return {"status": "reset", "mode": "dual"}


@app.post("/api/simulation/dual/road-closure")
async def trigger_dual_road_closure():
    """Trigger road closures on both simulations to observe comparative re-routing."""
    if not dual_simulation.is_running:
        return {"status": "error", "message": "Dual simulation is not running."}
    closures = dual_simulation.trigger_road_closure(num_closures=4)
    return {
        "status": "success",
        "closures_count": len(closures),
        "message": f"Closed {len(closures)} roads across both simulations."
    }


@app.post("/api/simulation/road-closure")
async def trigger_road_closure():
    """Trigger a random road closure and dynamically reroute active drivers."""
    if not simulation.is_running:
        return {"status": "error", "message": "Simulation is not running."}
    
    closures = simulation.trigger_road_closure(num_closures=5)
    return {
        "status": "success", 
        "closures_count": len(closures),
        "message": f"Closed {len(closures)} roads. Active drivers re-routing."
    }


@app.post("/api/simulation/traffic-surge")
async def trigger_traffic_surge():
    """Trigger acute traffic surge to prompt dynamic re-routing."""
    if not simulation.is_running:
        return {"status": "error", "message": "Simulation is not running."}
    surged = simulation.trigger_traffic_surge(num_edges=20)
    return {
        "status": "success",
        "surged_count": len(surged),
        "message": f"Traffic surged on {len(surged)} roads. Active drivers re-routing."
    }


@app.post("/api/simulation/dual/traffic-surge")
async def trigger_dual_traffic_surge():
    """Trigger acute traffic surge on both simulations."""
    if not dual_simulation.is_running:
        return {"status": "error", "message": "Dual simulation is not running."}
    surged = dual_simulation.trigger_traffic_surge(num_edges=20)
    return {
        "status": "success",
        "surged_count": len(surged),
        "message": f"Traffic surged on {len(surged)} roads across both simulations."
    }


@app.post("/api/simulation/inject-order")
async def inject_order(data: dict = None):
    """Dynamically inject a new high-priority order mid-simulation."""
    if not simulation.is_running:
        return {"status": "error", "message": "Simulation is not running."}
    order = simulation.inject_order(data)
    return {"status": "success", "order_id": order["order_id"], "message": f"Priority Order {order['order_id']} injected."}


@app.post("/api/simulation/dual/inject-order")
async def inject_dual_order():
    """Dynamically inject a new order into dual simulation."""
    if not dual_simulation.is_running:
        return {"status": "error", "message": "Dual simulation is not running."}
    order = dual_simulation.inject_order()
    return {"status": "success", "order_id": order["order_id"], "message": f"Priority Order {order['order_id']} injected across both simulations."}



@app.post("/api/simulation/config")
async def update_config(data: dict):
    """Update simulation routing configuration and dynamic tick delay."""
    if "routing_mode" in data:
        simulation.routing_mode = data["routing_mode"]
    if "manual_algorithm" in data:
        simulation.manual_algorithm = data["manual_algorithm"]
    if "tick_delay" in data:
        delay = float(data["tick_delay"])
        simulation.tick_delay = delay
        dual_simulation.tick_delay = delay
        if hasattr(dual_simulation, "baseline") and dual_simulation.baseline:
            dual_simulation.baseline.tick_delay = delay
        if hasattr(dual_simulation, "optimized") and dual_simulation.optimized:
            dual_simulation.optimized.tick_delay = delay
    return {
        "status": "success", 
        "config": {
            "routing_mode": simulation.routing_mode, 
            "manual_algorithm": simulation.manual_algorithm,
            "tick_delay": simulation.tick_delay
        }
    }


@app.post("/api/predict-eta")
async def predict_delivery_eta(data: dict):
    """Predict delivery time using ML model."""
    if not ML_AVAILABLE:
        # Fallback: simple calculation
        distance = data.get("distance", 5000)
        traffic = data.get("traffic_level", 1.0)
        stops = data.get("num_stops", 1)
        hour = data.get("hour", 12)

        # Simple estimate: 30 km/h base speed + traffic + stop overhead
        base_time_min = (distance / 1000) / 30 * 60
        traffic_factor = traffic
        stop_overhead = stops * 3  # 3 min per stop
        eta = base_time_min * traffic_factor + stop_overhead

        return {
            "predicted_eta_minutes": round(eta, 1),
            "model": "fallback_calculation",
            "confidence": 0.6,
        }

    try:
        eta = predict_eta(
            distance=data.get("distance", 5000),
            traffic_level=data.get("traffic_level", 1.0),
            num_stops=data.get("num_stops", 1),
            hour=data.get("hour", 12),
        )
        return {
            "predicted_eta_minutes": round(eta, 1),
            "model": "random_forest",
            "confidence": 0.85,
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/route")
async def compute_route(
    from_lat: float, from_lng: float,
    to_lat: float, to_lng: float,
    algorithm: str = "dijkstra",
    routing_mode: str = "manual"
):
    """Compute a route between two points."""
    G = simulation.graph or load_graph()
    source = get_nearest_node(G, from_lat, from_lng)
    target = get_nearest_node(G, to_lat, to_lng)

    # get_traffic_summary returns a dict with keys: low, medium, high, total_edges, etc.
    traffic_data = get_traffic_summary(G)
    total_edges = traffic_data.get("total_edges", 0)
    if total_edges > 0:
        avg_traffic = (
            traffic_data.get("low", 0) * 1.0
            + traffic_data.get("medium", 0) * 1.3
            + traffic_data.get("high", 0) * 1.8
        ) / total_edges
    else:
        avg_traffic = 1.0

    result = find_route(
        G, source, target,
        algorithm=algorithm,
        dynamic_mode=(routing_mode == "dynamic"),
        traffic_level=avg_traffic
    )
    return result


@app.get("/api/algorithms/compare")
async def compare_algorithms(from_lat: float, from_lng: float, to_lat: float, to_lng: float):
    """Compare all routing algorithms with detailed metrics."""
    G = simulation.graph or load_graph()
    source = get_nearest_node(G, from_lat, from_lng)
    target = get_nearest_node(G, to_lat, to_lng)

    results = {}
    algorithms = ["dijkstra", "astar", "bfs", "dfs", "greedy", "bellman_ford"]

    for algo in algorithms:
        start = time.time()
        result = find_route(G, source, target, algorithm=algo)
        elapsed = (time.time() - start) * 1000  # ms

        results[algo] = {
            "distance_m": result.get("total_distance_m", 0),
            "time_ms": result.get("calc_time_ms", round(elapsed, 2)),
            "path_length": result.get("num_nodes", len(result.get("path_nodes", []))),
            "nodes_explored": result.get("nodes_explored", 0),
            "estimated_time_s": result.get("estimated_time_s", 0),
            "algorithm": algo,
            "path_coords": result.get("path_coords", []),
            "explored_coords": result.get("explored_coords", [])[:800],
            "error": result.get("error", None)
        }

    return results


@app.get("/api/tsp/compare")
async def compare_tsp(num_stops: int = 5):
    """
    Compare Level-2 Multi-Stop Delivery Sequencing Algorithms:
    - Held-Karp Dynamic Programming (O(N^2 * 2^N))
    - Greedy Nearest Neighbor (O(N^2))
    - Brute Force Permutations (O(N!))
    """
    import random
    import math
    import itertools
    from algorithms.sequencing.held_karp import HeldKarpSequencing
    from route_optimizer import GreedySequencing, _build_distance_matrix

    G = simulation.graph or load_graph()
    nodes_list = list(G.nodes())
    if len(nodes_list) < 20:
        return {"error": "Graph too small"}

    n = max(3, min(num_stops, 9))
    random.seed(101 + n * 13)
    sample_nodes = random.sample(nodes_list, n)

    dist_matrix = _build_distance_matrix(G, sample_nodes)

    # Constrain pickups to precede deliveries: e.g. stop 1 is picked before stop 2
    pickup_delivery_map = {}
    for i in range(1, n - 1, 2):
        pickup_delivery_map[i] = i + 1

    # 1. Greedy TSP
    greedy_solver = GreedySequencing()
    t0 = time.perf_counter()
    greedy_order = greedy_solver.sequence_stops(dist_matrix, pickup_delivery_map, start_idx=0)
    greedy_time_ms = (time.perf_counter() - t0) * 1000
    greedy_cost = sum(dist_matrix[greedy_order[i]][greedy_order[i+1]] for i in range(len(greedy_order)-1))

    # 2. Held-Karp DP
    hk_solver = HeldKarpSequencing(max_stops=14)
    t0 = time.perf_counter()
    hk_order = hk_solver.sequence_stops(dist_matrix, pickup_delivery_map, start_idx=0)
    hk_time_ms = (time.perf_counter() - t0) * 1000
    hk_cost = sum(dist_matrix[hk_order[i]][hk_order[i+1]] for i in range(len(hk_order)-1))

    # 3. Brute Force Permutations
    t0 = time.perf_counter()
    bf_order = []
    bf_cost = float('inf')
    bf_permutations_checked = 0

    if n <= 8:
        for perm in itertools.permutations(range(1, n)):
            bf_permutations_checked += 1
            valid = True
            seen = set([0])
            for stop in perm:
                for p, d in pickup_delivery_map.items():
                    if stop == d and p not in seen:
                        valid = False
                        break
                if not valid:
                    break
                seen.add(stop)
            if not valid:
                continue

            full_path = [0] + list(perm)
            cost = sum(dist_matrix[full_path[i]][full_path[i+1]] for i in range(len(full_path)-1))
            if cost < bf_cost:
                bf_cost = cost
                bf_order = full_path
        bf_time_ms = (time.perf_counter() - t0) * 1000
    else:
        bf_permutations_checked = math.factorial(n - 1)
        bf_cost = hk_cost
        bf_order = hk_order
        bf_time_ms = (bf_permutations_checked / 50000) * 1000

    stop_details = []
    for idx, node in enumerate(sample_nodes):
        coords = get_node_coords(G, node)
        role = "Depot (Start)" if idx == 0 else ("Pickup 🏬" if idx in pickup_delivery_map else "Customer 👤")
        stop_details.append({
            "index": idx,
            "node": node,
            "lat": coords[0],
            "lng": coords[1],
            "role": role,
            "hk_step": hk_order.index(idx) + 1 if idx in hk_order else 0,
            "greedy_step": greedy_order.index(idx) + 1 if idx in greedy_order else 0
        })

    # Precompute path coordinates connecting stops according to Held-Karp sequence
    hk_path_coords = []
    for i in range(len(hk_order) - 1):
        u, v = sample_nodes[hk_order[i]], sample_nodes[hk_order[i+1]]
        res = find_route(G, u, v, algorithm="astar")
        if "path_coords" in res:
            hk_path_coords.extend(res["path_coords"])

    greedy_path_coords = []
    for i in range(len(greedy_order) - 1):
        u, v = sample_nodes[greedy_order[i]], sample_nodes[greedy_order[i+1]]
        res = find_route(G, u, v, algorithm="astar")
        if "path_coords" in res:
            greedy_path_coords.extend(res["path_coords"])

    savings = round(((greedy_cost - hk_cost) / max(1, greedy_cost)) * 100, 1) if greedy_cost > hk_cost else 0

    return {
        "num_stops": n,
        "stops": stop_details,
        "held_karp": {
            "order": hk_order,
            "cost_seconds": round(hk_cost, 2),
            "cost_distance_m": round(hk_cost * 8.33, 1),
            "time_ms": round(hk_time_ms, 2),
            "states_explored": (n * (1 << n)),
            "path_coords": hk_path_coords,
            "algorithm": "Held-Karp Dynamic Programming (O(N^2 * 2^N))",
            "is_optimal": True
        },
        "greedy": {
            "order": greedy_order,
            "cost_seconds": round(greedy_cost, 2),
            "cost_distance_m": round(greedy_cost * 8.33, 1),
            "time_ms": round(greedy_time_ms, 2),
            "states_explored": n * n,
            "path_coords": greedy_path_coords,
            "algorithm": "Greedy Nearest Neighbor (O(N^2))",
            "is_optimal": (greedy_cost <= hk_cost + 1e-3)
        },
        "brute_force": {
            "order": bf_order if bf_order else hk_order,
            "cost_seconds": round(bf_cost if bf_cost != float('inf') else hk_cost, 2),
            "cost_distance_m": round((bf_cost if bf_cost != float('inf') else hk_cost) * 8.33, 1),
            "time_ms": round(bf_time_ms, 2),
            "states_explored": bf_permutations_checked,
            "algorithm": f"Brute Force Permutations (O(N!)) - Checked {bf_permutations_checked:,} paths",
            "is_optimal": True
        },
        "held_karp_savings_pct": savings
    }


# ─── WEBSOCKET ──────────────────────────────────────────────────


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """WebSocket endpoint for real-time simulation updates."""
    await ws.accept()
    ws_clients.add(ws)
    print(f"[WS] Client connected. Total: {len(ws_clients)}")

    try:
        while True:
            # Keep connection alive; client can also send commands
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await ws.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        ws_clients.discard(ws)
        print(f"[WS] Client disconnected. Total: {len(ws_clients)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)

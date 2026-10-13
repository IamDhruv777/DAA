"""
Dual Simulation Engine
Orchestrates two parallel simulations (Baseline Greedy vs SmartRoute Optimized)
running on the EXACT same initial orders, drivers, and road network for direct A/B benchmarking.
"""
import copy
import asyncio
import time
from simulation import SimulationEngine
from road_network import load_graph
from orders import generate_orders
from drivers import initialize_drivers, GreedyNearestAssignment
from batching import KMeansBatching
from route_optimizer import GreedySequencing
from algorithms.batching.foodmatch_inspired import FoodMatchBatching
from algorithms.assignment.hungarian import HungarianAssignment
from algorithms.sequencing.two_opt import TwoOptSequencing


class DualSimulationEngine:
    """Manages synchronized Baseline vs Optimized simulations side-by-side."""

    def __init__(self):
        self.is_running = False
        self.tick_delay = 2.0
        self.baseline = SimulationEngine()
        self.optimized = SimulationEngine()
        
        # Configure Baseline: Naive Traditional Heuristics
        self.baseline.batching_strategy = KMeansBatching()
        self.baseline.assignment_strategy = GreedyNearestAssignment()
        self.baseline.sequencing_strategy = GreedySequencing()
        self.baseline.routing_mode = "manual"
        self.baseline.manual_algorithm = "dijkstra"
        
        # Configure Optimized: Research / Global Combinatorial Algorithms
        self.optimized.batching_strategy = FoodMatchBatching()
        self.optimized.assignment_strategy = HungarianAssignment()
        self.optimized.sequencing_strategy = TwoOptSequencing()
        self.optimized.routing_mode = "dynamic"
        self.optimized.manual_algorithm = "astar"

    def initialize(self, num_orders=15, num_drivers=5, city_name="Pune, India", tick_delay=2.0):
        """Initializes both engines with IDENTICAL initial state."""
        print(f"[DUAL-SIM] Initializing A/B Benchmark for {city_name} with {num_drivers} drivers and {num_orders} orders...")
        self.tick_delay = tick_delay
        
        # Load master road network
        master_graph = load_graph(city_name)
        
        # Generate single source of truth for orders and drivers
        base_orders = generate_orders(master_graph, num_orders=num_orders, city_name=city_name)
        base_drivers = initialize_drivers(master_graph, num_drivers=num_drivers)
        
        # Setup Baseline Engine
        self.baseline.graph = master_graph.copy()
        self.baseline.tick_delay = tick_delay
        self.baseline.orders = copy.deepcopy(base_orders)
        self.baseline.drivers = copy.deepcopy(base_drivers)
        self.baseline.orders_released = 0
        self.baseline.tick_count = 0
        self.baseline._delivery_times = []
        self.baseline.batches = []
        self.baseline.routing_mode = "manual"
        self.baseline.manual_algorithm = "dijkstra"
        
        # Setup Optimized Engine
        self.optimized.graph = master_graph.copy()
        self.optimized.tick_delay = tick_delay
        self.optimized.orders = copy.deepcopy(base_orders)
        self.optimized.drivers = copy.deepcopy(base_drivers)
        self.optimized.orders_released = 0
        self.optimized.tick_count = 0
        self.optimized._delivery_times = []
        self.optimized.batches = []
        self.optimized.routing_mode = "dynamic"
        self.optimized.manual_algorithm = "astar"

        # Apply initial traffic to both graphs
        from traffic import update_traffic
        update_traffic(self.baseline.graph)
        update_traffic(self.optimized.graph)

        print("[DUAL-SIM] Initialization complete. Both engines synchronized.")

    def tick(self):
        """Advances both simulations by exactly one tick."""
        if self.baseline and self.optimized:
            self.baseline.tick()
            self.optimized.tick()

    def trigger_road_closure(self, num_closures=3):
        """Applies road closures to both graphs and observes differences in re-routing."""
        closures = self.optimized.trigger_road_closure(num_closures=num_closures)
        
        # Apply same closures to baseline graph, but baseline does NOT re-route dynamically
        from traffic import simulate_road_closures
        for u, v in closures:
            if self.baseline.graph.has_edge(u, v):
                # Baseline traffic suffers massive latency penalty
                for key in self.baseline.graph[u][v]:
                    self.baseline.graph[u][v][key]["travel_time"] = 1000000.0
                    self.baseline.graph[u][v][key]["weight"] = 1000000.0
        
        self.baseline.closed_roads = copy.deepcopy(self.optimized.closed_roads)
        return closures

    def trigger_traffic_surge(self, num_edges=25):
        """Applies traffic congestion surge across key corridors to test dynamic vs static response."""
        surged = self.optimized.trigger_traffic_surge(num_edges=num_edges)
        
        # Apply same traffic penalty to baseline edges (baseline does NOT re-route around congestion)
        for u, v in surged:
            if self.baseline.graph.has_edge(u, v):
                for key in self.baseline.graph[u][v]:
                    base_time = self.baseline.graph[u][v][key].get("base_travel_time", 12)
                    self.baseline.graph[u][v][key]["travel_time"] = base_time * 2.8
                    self.baseline.graph[u][v][key]["traffic_level"] = "high"
        return surged

    def inject_order(self):
        """Injects a VIP order into both simulations."""
        opt_order = self.optimized.inject_order()
        
        # Add to baseline as well so both simulations process the same workload
        base_order = copy.deepcopy(opt_order)
        self.baseline.orders.insert(self.baseline.orders_released, base_order)
        self.baseline.orders_released += 1
        self.baseline._run_batching()
        self.baseline._assign_drivers()
        self.baseline._compute_routes()
        return opt_order

    def get_state(self):
        """Calculates live comparative metrics and deltas for the dashboard."""
        base_state = self.baseline.get_state()
        opt_state = self.optimized.get_state()
        
        base_dist = base_state["metrics"].get("total_distance_km", 0.0)
        opt_dist = opt_state["metrics"].get("total_distance_km", 0.0)
        
        dist_saved_km = round(base_dist - opt_dist, 2)
        dist_saved_pct = round(((base_dist - opt_dist) / max(0.001, base_dist)) * 100, 1) if base_dist > 0.05 else 0.0
        
        base_time = base_state["metrics"].get("avg_delivery_time_min", 0.0)
        opt_time = opt_state["metrics"].get("avg_delivery_time_min", 0.0)
        time_saved_min = round(base_time - opt_time, 1)
        
        return {
            "mode": "dual",
            "tick": self.baseline.tick_count,
            "is_running": self.is_running,
            "baseline": base_state,
            "optimized": opt_state,
            "reroute_event": self.optimized.last_reroute_event,
            "delta": {
                "dist_saved_km": dist_saved_km,
                "dist_saved_pct": dist_saved_pct,
                "time_saved_min": time_saved_min,
                "base_dist_km": base_dist,
                "opt_dist_km": opt_dist,
                "base_time_min": base_time,
                "opt_time_min": opt_time,
                "delivered_base": base_state["metrics"].get("orders_delivered", 0),
                "delivered_opt": opt_state["metrics"].get("orders_delivered", 0),
                "active_drivers_base": base_state["metrics"].get("active_drivers", 0),
                "active_drivers_opt": opt_state["metrics"].get("active_drivers", 0)
            }
        }

    async def run(self, ws_broadcast_callback=None):
        """Runs synchronized simulation loop."""
        self.is_running = True
        self.baseline.is_running = True
        self.optimized.is_running = True
        print("[DUAL-SIM] Dual simulation loop started.")
        
        loop = asyncio.get_running_loop()
        
        while self.is_running:
            try:
                await loop.run_in_executor(None, self.tick)
                
                if ws_broadcast_callback:
                    state = self.get_state()
                    await ws_broadcast_callback(state)
                    
                await asyncio.sleep(self.tick_delay)
            except Exception as e:
                print(f"[DUAL-SIM] Error in tick loop: {e}")
                break

    def stop(self):
        """Stops both engines."""
        self.is_running = False
        if self.baseline:
            self.baseline.stop()
        if self.optimized:
            self.optimized.stop()
        print("[DUAL-SIM] Dual simulation stopped.")

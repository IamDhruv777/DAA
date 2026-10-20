"""
City-Scale Simulation Engine
Orchestrates the full delivery simulation lifecycle.
"""
import asyncio
import time
import random
import math
from datetime import datetime

from road_network import load_graph, get_node_coords
from traffic import update_traffic, get_traffic_summary
from orders import generate_orders, get_order_stats
from batching import batch_orders, KMeansBatching
from drivers import initialize_drivers, assign_drivers_to_batches, get_driver_stats, GreedyNearestAssignment
from route_optimizer import optimize_driver_route, GreedySequencing


class SimulationEngine:
    """Manages the full delivery simulation."""

    def __init__(self):
        self.graph = None
        self.orders = []
        self.drivers = []
        self.batches = []
        self.is_running = False
        self.tick_count = 0
        self.start_time = None
        self.orders_released = 0
        self.metrics = {
            "active_drivers": 0,
            "orders_pending": 0,
            "orders_delivered": 0,
            "orders_in_transit": 0,
            "avg_delivery_time_s": 0,
            "total_distance_km": 0,
            "tick": 0,
        }
        self._delivery_times = []
        self._ws_clients = set()
        self._orders_per_tick = 10  # Release 10 orders per tick
        
        # Instantiate Modular Strategy Algorithms
        self.batching_strategy = KMeansBatching()
        self.assignment_strategy = GreedyNearestAssignment()
        self.sequencing_strategy = GreedySequencing()
        
        # Optimizer
        from algorithms.optimization.ortools_cvrptw import ORToolsCVRPTW, ORTOOLS_AVAILABLE
        self.cvrptw_optimizer = ORToolsCVRPTW(time_limit_sec=1, max_capacity=3) if ORTOOLS_AVAILABLE else None
        self.use_cvrptw = False  # Toggleable via UI / API

        self.tick_delay = 0.8  # Fast smooth 800ms ticks
        self.closed_roads = []  # List of {nodes: [u, v], coords: [c1, c2]}
        self.last_reroute_event = None  # Live dynamic re-routing notification
        
        # New Routing Configuration
        self.routing_mode = "dynamic" # "dynamic" or "manual"
        self.manual_algorithm = "dijkstra" # "dijkstra", "astar", "bfs", "dfs", "greedy"

    def initialize(self, num_orders=5, num_drivers=5, city_name="Pune, India", tick_delay=0.8):
        """Load graph, generate orders and drivers."""
        print(f"[SIM] Initializing simulation for {city_name} with {num_drivers} drivers and {num_orders} orders...")
        self.graph = load_graph(city_name)
        self.tick_delay = tick_delay
        self.closed_roads = []
        self.last_reroute_event = None

        print(f"[SIM] Generating {num_orders} orders...")
        self.orders = generate_orders(self.graph, num_orders=num_orders, city_name=city_name)

        print(f"[SIM] Initializing {num_drivers} drivers...")
        self.drivers = initialize_drivers(self.graph, num_drivers=num_drivers)

        print("[SIM] Applying initial traffic conditions...")
        update_traffic(self.graph)

        self.orders_released = 0
        self.tick_count = 0
        self._delivery_times = []
        print("[SIM] Initialization complete.")

    def _release_orders(self):
        """Release a batch of orders (simulating orders coming in over time)."""
        start = self.orders_released
        end = min(start + self._orders_per_tick, len(self.orders))

        if start >= len(self.orders):
            return 0

        released = end - start
        self.orders_released = end
        return released

    def _run_cvrptw(self):
        """Global optimization for batching, assignment, and sequencing."""
        assignments = self.cvrptw_optimizer.optimize(self.drivers, self.orders[:self.orders_released])
        
        # Apply assignments
        for driver_id, route_seq in assignments.items():
            driver = next(d for d in self.drivers if d["driver_id"] == driver_id)
            
            # Map sequence to actual route coords
            order_ids = [order_id for _, order_id in route_seq if order_id not in driver["current_orders"]]
            driver["current_orders"].extend(order_ids)
            driver["status"] = "picking"
            
            driver_orders = [o for o in self.orders[:self.orders_released] if o["order_id"] in driver["current_orders"]]
            
            # Use GreedyTSP for pathing given the CVRPTW stop sequence
            # (In a full implementation we'd trace exactly the OR-Tools sequence)
            from route_optimizer import optimize_driver_route
            route_coords, stops, total_dist = optimize_driver_route(
                self.graph, driver, driver_orders,
                routing_mode=self.routing_mode,
                manual_algorithm=self.manual_algorithm
            )
            driver["route_coords"] = route_coords
            driver["route_progress"] = 0
            
            # Mark orders
            for order_id in order_ids:
                for order in self.orders[:self.orders_released]:
                    if order["order_id"] == order_id:
                        order["status"] = "assigned"
                        order["assigned_driver"] = driver_id
                        break

    def _run_batching(self):
        """Batch pending orders."""
        pending = [o for o in self.orders[:self.orders_released] if o["status"] == "pending"]
        if pending:
            self.batches = self.batching_strategy.batch(pending)
            return len(self.batches)
        return 0

    def _assign_drivers(self):
        """Assign idle drivers to batches."""
        unassigned = [b for b in self.batches if not b.get("assigned", False)]
        if unassigned:
            assignments = self.assignment_strategy.assign(
                self.drivers, unassigned, self.orders[:self.orders_released]
            )
            return len(assignments)
        return 0

    def _compute_routes(self):
        """Compute optimized routes for newly assigned drivers."""
        for driver in self.drivers:
            if driver["status"] == "picking" and not driver["route_coords"]:
                # Find the orders for this driver
                driver_orders = []
                for order in self.orders[:self.orders_released]:
                    if order["order_id"] in driver["current_orders"]:
                        driver_orders.append(order)

                if driver_orders:
                    # Get current traffic level
                    traffic_data = get_traffic_summary(self.graph)
                    total_edges = traffic_data.get("total_edges", 0)
                    if total_edges > 0:
                        avg_traffic = (traffic_data.get("low", 0) * 1.0 + 
                                       traffic_data.get("medium", 0) * 1.3 + 
                                       traffic_data.get("high", 0) * 1.8) / total_edges
                    else:
                        avg_traffic = 1.0

                    route_coords, stops, total_dist = optimize_driver_route(
                        self.graph, driver, driver_orders,
                        routing_mode=self.routing_mode,
                        manual_algorithm=self.manual_algorithm,
                        traffic_level=avg_traffic,
                        sequencing_strategy=self.sequencing_strategy
                    )
                    driver["route_coords"] = route_coords
                    driver["route_progress"] = 0
                    driver["total_route_distance"] = total_dist
                    driver["stops"] = stops

                    # If route contains pickup stops, driver starts in 'picking' mode
                    has_pickups = any(s.get("type") == "pickup" for s in stops)
                    if has_pickups:
                        driver["status"] = "picking"
                        for order in driver_orders:
                            if order.get("status") == "pending":
                                order["status"] = "assigned"
                    elif route_coords:
                        driver["status"] = "delivering"
                        for order in driver_orders:
                            order["status"] = "picked"

    def _move_drivers(self):
        """Advance drivers along their routes based on vehicle speed."""
        # 30 km/h base speed, adjusted by global traffic
        traffic_data = get_traffic_summary(self.graph)
        total_edges = traffic_data.get("total_edges", 0)
        traffic_mult = 1.0
        if total_edges > 0:
            sum_traffic = (traffic_data.get("low", 0) * 1.0 + 
                           traffic_data.get("medium", 0) * 1.3 + 
                           traffic_data.get("high", 0) * 1.8)
            traffic_mult = (sum_traffic / total_edges) if sum_traffic > 0 else 1.0
        
        if traffic_mult <= 0.1:
            traffic_mult = 1.0
        
        # Base speed 45 km/h adjusted by traffic conditions
        traffic_mult = max(0.6, min(2.5, traffic_mult))
        base_speed_mps = (45.0 / traffic_mult) * (1000.0 / 3600.0)
        
        # Target distance to cover per tick (dynamically scaled for city visualization)
        # At 1x speed (tick_delay ~0.8s), covers ~80-120m per tick (2-3 road intersections)
        sim_scale = max(1.0, 0.8 / max(0.05, self.tick_delay))
        target_dist_per_tick = max(60.0, base_speed_mps * 6.0 * sim_scale)

        for driver in self.drivers:
            if driver["status"] in ("delivering", "picking") and driver["route_coords"]:
                route = driver["route_coords"]
                progress = driver.get("route_progress", 0)
                
                if progress >= len(route) - 1:
                    self._complete_delivery(driver)
                    continue

                accumulated_dist = 0.0
                new_progress = progress

                # Step forward through waypoints until covering target_dist_per_tick
                while new_progress < len(route) - 1:
                    p1 = route[new_progress]
                    p2 = route[new_progress + 1]
                    dx = (p2[0] - p1[0]) * 111000.0
                    dy = (p2[1] - p1[1]) * 111000.0 * 0.95
                    seg_dist = math.hypot(dx, dy)

                    # If we already advanced at least 1 node and this next segment would overshoot, stop here
                    if accumulated_dist > 0.0 and (accumulated_dist + seg_dist) > target_dist_per_tick:
                        break

                    accumulated_dist += seg_dist
                    new_progress += 1

                    if accumulated_dist >= target_dist_per_tick:
                        break

                # CRITICAL GUARANTEE: Advance at least 1 node waypoint every single tick
                if new_progress == progress and progress < len(route) - 1:
                    p1 = route[progress]
                    p2 = route[progress + 1]
                    dx = (p2[0] - p1[0]) * 111000.0
                    dy = (p2[1] - p1[1]) * 111000.0 * 0.95
                    accumulated_dist += math.hypot(dx, dy)
                    new_progress = progress + 1

                # Update physical driver coordinates to the newly reached waypoint
                driver["route_progress"] = new_progress
                new_pos = route[new_progress]
                driver["lat"] = new_pos[0]
                driver["lng"] = new_pos[1]
                driver["stats"]["total_distance_m"] += accumulated_dist

                # Process stop milestones (restaurant pickups and customer deliveries)
                for stop in driver.get("stops", []):
                    stop_idx = stop.get("route_coord_idx", -1)
                    coords = stop.get("coords")
                    
                    # Stop reached either by waypoint index or physical distance <= 75m
                    dist_to_stop = 999999.0
                    if coords:
                        dx = (driver["lat"] - coords[0]) * 111000.0
                        dy = (driver["lng"] - coords[1]) * 111000.0 * 0.95
                        dist_to_stop = math.hypot(dx, dy)
                    
                    is_at_stop = (stop_idx >= 0 and new_progress >= stop_idx) or (dist_to_stop <= 75.0)
                    
                    if is_at_stop:
                        oid = stop.get("order_id")
                        if stop.get("type") == "pickup":
                            for o in self.orders[:self.orders_released]:
                                if (oid and o["order_id"] == oid) or (not oid and o["order_id"] in driver.get("current_orders", [])):
                                    if o["status"] in ("pending", "assigned"):
                                        o["status"] = "picked"
                        elif stop.get("type") == "delivery":
                            for o in self.orders[:self.orders_released]:
                                if (oid and o["order_id"] == oid) or (not oid and o["order_id"] in driver.get("current_orders", [])):
                                    if o["status"] != "delivered":
                                        o["status"] = "delivered"
                                        driver["stats"]["deliveries_completed"] += 1

                # Update driver lifecycle status based on active orders
                active_orders = [o for o in self.orders[:self.orders_released] if o["order_id"] in driver.get("current_orders", [])]
                has_unpicked = any(o["status"] in ("pending", "assigned") for o in active_orders)
                has_undelivered = any(o["status"] != "delivered" for o in active_orders)

                if has_unpicked:
                    driver["status"] = "picking"
                elif has_undelivered:
                    driver["status"] = "delivering"
                elif active_orders or new_progress >= len(route) - 1:
                    # All assigned orders are delivered or reached end of route!
                    self._complete_delivery(driver)

    def trigger_road_closure(self, num_closures=3):
        """Simulates unexpected road closures and forces active drivers to re-route."""
        from traffic import simulate_road_closures
        from road_network import get_node_coords
        closures = simulate_road_closures(self.graph, num_closures)
        
        for u, v in closures:
            c1 = get_node_coords(self.graph, u)
            c2 = get_node_coords(self.graph, v)
            self.closed_roads.append({
                "nodes": [u, v],
                "coords": [c1, c2]
            })
        
        print(f"[Simulation] Dynamic Event: {len(closures)} roads closed! Re-routing active drivers...")
        self.recalculate_active_routes(reason=f"{len(closures)} Road closures detected", traffic_level=1.8)
        return closures

    def trigger_traffic_surge(self, num_edges=25):
        """Simulates acute traffic surge on key road corridors and re-routes active drivers."""
        from traffic import simulate_traffic_surge
        surged = simulate_traffic_surge(self.graph, num_edges=num_edges, factor=2.8)
        print(f"[Simulation] Dynamic Event: Traffic surge on {len(surged)} roads! Re-routing...")
        self.recalculate_active_routes(reason="Acute traffic surge on road corridor", traffic_level=2.2)
        return surged

    def inject_order(self, order_data=None):
        """Dynamically injects a new high-priority order and re-evaluates delivery sequence."""
        import random
        from road_network import get_node_coords
        
        nodes = list(self.graph.nodes())
        p_node = random.choice(nodes)
        d_node = random.choice(nodes)
        p_coords = get_node_coords(self.graph, p_node)
        d_coords = get_node_coords(self.graph, d_node)
        order_id = f"VIP-{int(time.time() % 10000)}"
        
        new_order = {
            "order_id": order_id,
            "restaurant_node": p_node,
            "restaurant_lat": p_coords[0],
            "restaurant_lng": p_coords[1],
            "customer_node": d_node,
            "customer_lat": d_coords[0],
            "customer_lng": d_coords[1],
            "status": "pending",
            "is_priority": True
        }
        
        # Insert immediately into active released pool
        self.orders.insert(self.orders_released, new_order)
        self.orders_released += 1
        
        # Run batching and assignment for pending orders
        self._run_batching()
        self._assign_drivers()
        self._compute_routes()
        
        # Recalculate routes if any active driver was reassigned
        rerouted_drivers = self.recalculate_active_routes(
            reason=f"New VIP Order {order_id} arrived",
            traffic_level=1.2
        )
        if rerouted_drivers:
            reroute_status = "rerouted"
            message = f"📦 VIP ORDER {order_id}: recalculated routes for {len(rerouted_drivers)} rider(s). New paths are active."
        else:
            reroute_status = "no_reroute_needed"
            message = f"📦 VIP ORDER {order_id}: added to dispatch. No active rider routes needed rerouting."

        self.last_reroute_event = {
            "id": f"reroute-{int(time.time() * 1000)}",
            "timestamp": time.time(),
            "reason": f"New VIP Order {order_id} arrived",
            "message": message,
            "status": reroute_status,
            "drivers": rerouted_drivers,
        }
        return new_order

    def recalculate_active_routes(self, reason="Road Obstruction", traffic_level=1.5, only_affected=False):
        """Dynamically re-routes active drivers from their immediate positions."""
        from route_optimizer import optimize_driver_route
        from road_network import get_nearest_node
        
        rerouted_drivers = []
        for driver in self.drivers:
            if driver["status"] in ("picking", "delivering") and driver.get("current_orders"):
                # If only_affected is True, check if driver's upcoming path actually intersects a closed road
                if only_affected and self.closed_roads:
                    rem_coords = driver.get("route_coords", [])[driver.get("route_progress", 0):]
                    affected = False
                    for cr in self.closed_roads:
                        c_pair = cr.get("coords", [])
                        if len(c_pair) >= 2:
                            for rc in rem_coords[:25]:
                                if math.hypot((rc[0] - c_pair[0][0]) * 111000.0, (rc[1] - c_pair[0][1]) * 111000.0) < 80.0:
                                    affected = True
                                    break
                        if affected:
                            break
                    if not affected:
                        continue

                current_node = get_nearest_node(self.graph, driver["lat"], driver["lng"])
                driver["current_node"] = current_node
                
                # Fetch pending orders for this driver
                driver_orders = [o for o in self.orders[:self.orders_released] if o["order_id"] in driver["current_orders"]]
                if not driver_orders:
                    continue
                
                route_coords, stops, total_dist = optimize_driver_route(
                    self.graph, driver, driver_orders,
                    routing_mode=self.routing_mode,
                    manual_algorithm=self.manual_algorithm,
                    traffic_level=traffic_level,
                    sequencing_strategy=self.sequencing_strategy
                )
                
                # Apply new dynamically calculated route only if valid
                if route_coords and len(route_coords) > 1:
                    driver["route_coords"] = route_coords
                    driver["route_progress"] = 0
                    driver["stops"] = stops
                    driver["total_route_distance"] = total_dist
                    rerouted_drivers.append(driver["driver_id"])
        
        if rerouted_drivers:
            self.last_reroute_event = {
                "id": f"reroute-{int(time.time() * 1000)}",
                "timestamp": time.time(),
                "reason": reason,
                "message": f"⚠️ Dynamic Re-Route ({reason}): Recalculated paths for {len(rerouted_drivers)} active rider(s) using dynamic A* navigation.",
                "drivers": rerouted_drivers
            }
        return rerouted_drivers

    def _complete_delivery(self, driver):
        """Mark a driver's delivery as complete."""
        # Mark orders as delivered
        for order_id in driver.get("current_orders", []):
            for order in self.orders[:self.orders_released]:
                if order["order_id"] == order_id:
                    if order["status"] != "delivered":
                        order["status"] = "delivered"
                        driver["stats"]["deliveries_completed"] += 1
                        delivery_time = random.uniform(600, 2400)  # 10-40 minutes
                        self._delivery_times.append(delivery_time)
                    break

        driver["status"] = "idle"
        driver["active_batch"] = None
        driver["current_orders"] = []
        driver["route_coords"] = []
        driver["route_progress"] = 0
        driver["stops"] = []

    def _update_metrics(self):
        """Compute current simulation metrics."""
        order_stats = get_order_stats(self.orders[:self.orders_released])
        driver_stats = get_driver_stats(self.drivers)

        avg_time = 0
        if self._delivery_times:
            avg_time = sum(self._delivery_times) / len(self._delivery_times)

        self.metrics = {
            "tick": self.tick_count,
            "active_drivers": driver_stats["active_drivers"],
            "total_drivers": driver_stats["total_drivers"],
            "orders_pending": order_stats.get("pending", 0) + order_stats.get("assigned", 0),
            "orders_in_transit": order_stats.get("picked", 0),
            "orders_delivered": order_stats.get("delivered", 0),
            "total_orders_released": self.orders_released,
            "total_orders": len(self.orders),
            "avg_delivery_time_s": round(avg_time, 1),
            "avg_delivery_time_min": round(avg_time / 60, 1),
            "total_distance_km": driver_stats["total_distance_km"],
            "driver_statuses": driver_stats["status_breakdown"],
            "utilization_pct": driver_stats.get("utilization_pct", 0),
            "simulation_speed": round(2.0 / self.tick_delay, 1) if self.tick_delay > 0 else 1
        }

    def tick(self):
        """Execute one simulation tick."""
        self.tick_count += 1

        # 1. Release new orders
        self._release_orders()

        # 2. Update traffic (every 5 ticks)
        if self.tick_count % 5 == 0:
            traffic_counts = update_traffic(self.graph)
            # Recompute active routes dynamically only if road closures or obstructions directly affect active riders
            if self.routing_mode == "dynamic" and self.closed_roads:
                self.recalculate_active_routes(reason="Road Obstruction Encountered", traffic_level=1.4, only_affected=True)

        if self.use_cvrptw and self.cvrptw_optimizer:
            self._run_cvrptw()
        else:
            # 3. Batch pending orders
            self._run_batching()
            # 4. Assign drivers
            self._assign_drivers()
            # 5. Compute routes for new assignments
            self._compute_routes()

        # 6. Move drivers
        self._move_drivers()

        # 7. Update metrics
        self._update_metrics()

    def get_state(self):
        """Get current simulation state for WebSocket broadcast."""
        driver_positions = []
        for d in self.drivers:
            progress = d.get("route_progress", 0)
            raw_coords = d.get("route_coords", [])
            
            # Send the clean forward path from current position to customer (no stale tail)
            if raw_coords and progress < len(raw_coords) and d.get("status") != "idle":
                # Start at current rider position, then include all remaining forward waypoints to customer
                forward_coords = [[d["lat"], d["lng"]]] + raw_coords[progress + 1:]
            else:
                forward_coords = []

            # Detailed orders payload for rider HUD
            active_orders_payload = []
            for oid in d.get("current_orders", []):
                for o in self.orders[:self.orders_released]:
                    if o["order_id"] == oid:
                        active_orders_payload.append({
                            "order_id": o["order_id"],
                            "restaurant_name": o.get("restaurant_name", "Cafe Goodluck"),
                            "restaurant_zone": o.get("restaurant_zone", "Pune Core"),
                            "restaurant_lat": o["restaurant_lat"],
                            "restaurant_lng": o["restaurant_lng"],
                            "customer_lat": o["customer_lat"],
                            "customer_lng": o["customer_lng"],
                            "status": o["status"],
                            "is_priority": o.get("is_priority", False),
                            "items": o.get("items", ["Chicken Biryani", "Butter Naan", "Lassi"])
                        })
                        break

            # Filter remaining active delivery stops for this driver (only non-delivered)
            # Once rider reaches this point and finishes delivery, it immediately disappears
            remaining_delivery_stops = []
            for s in d.get("stops", []):
                if s.get("type") == "delivery":
                    oid = s.get("order_id")
                    is_delivered = False
                    if oid:
                        for o in self.orders[:self.orders_released]:
                            if o["order_id"] == oid and o.get("status") == "delivered":
                                is_delivered = True
                                break
                    if not is_delivered:
                        c = s.get("coords")
                        if c:
                            remaining_delivery_stops.append({
                                "order_id": oid,
                                "lat": c[0],
                                "lng": c[1],
                            })

            driver_positions.append({
                "driver_id": d["driver_id"],
                "name": f"Rider {d['driver_id']}",
                "lat": d["lat"],
                "lng": d["lng"],
                "status": d["status"],
                "route_coords": forward_coords,
                "progress": d["route_progress"],
                "active_batch": d["active_batch"],
                "deliveries": d["stats"]["deliveries_completed"],
                "total_dist_km": round(d["stats"].get("total_distance_m", 0) / 1000.0, 2),
                "speed_kmh": 38.0 if d["status"] != "idle" else 0.0,
                "battery_pct": max(15, 100 - (d["stats"]["deliveries_completed"] * 6)),
                "current_orders": active_orders_payload,
                "delivery_stops": remaining_delivery_stops,
            })

        # Get visible orders (restaurants & customers)
        visible_orders = []
        for o in self.orders[:self.orders_released]:
            if o["status"] != "delivered":
                visible_orders.append({
                    "order_id": o["order_id"],
                    "restaurant_lat": o["restaurant_lat"],
                    "restaurant_lng": o["restaurant_lng"],
                    "customer_lat": o["customer_lat"],
                    "customer_lng": o["customer_lng"],
                    "status": o["status"],
                    "is_priority": o.get("is_priority", False),
                })

        return {
            "tick": self.tick_count,
            "metrics": self.metrics,
            "drivers": driver_positions,
            "orders": visible_orders[:100],  # Limit for performance
            "closed_roads": self.closed_roads,
            "reroute_event": self.last_reroute_event,
            "is_running": self.is_running,
            "config": {
                "routing_mode": self.routing_mode,
                "manual_algorithm": self.manual_algorithm
            }
        }

    async def run(self, ws_broadcast_callback=None):
        """Run the simulation loop."""
        self.is_running = True
        self.start_time = time.time()
        print("[SIM] Simulation started!")

        loop = asyncio.get_running_loop()

        while self.is_running:
            try:
                # Run CPU-heavy tick in thread executor to not block the event loop
                await loop.run_in_executor(None, self.tick)

                # Broadcast state via WebSocket (now the event loop is free)
                if ws_broadcast_callback:
                    state = self.get_state()
                    await ws_broadcast_callback(state)

                if self.tick_count % 10 == 0:
                    m = self.metrics
                    print(
                        f"[SIM] Tick {m['tick']} | "
                        f"Released: {m.get('total_orders_released', 0)} | "
                        f"Pending: {m.get('orders_pending', 0)} | "
                        f"Transit: {m.get('orders_in_transit', 0)} | "
                        f"Delivered: {m.get('orders_delivered', 0)} | "
                        f"Active: {m.get('active_drivers', 0)}"
                    )

                # Check if all orders delivered
                delivered = sum(1 for o in self.orders if o["status"] == "delivered")
                if delivered >= len(self.orders):
                    print(f"[SIM] All {len(self.orders)} orders delivered!")
                    self.is_running = False
                    break

            except Exception as e:
                print(f"[SIM] Error in tick {self.tick_count}: {e}")
                import traceback
                traceback.print_exc()

            await asyncio.sleep(self.tick_delay)  # Dynamic speed

        elapsed = time.time() - self.start_time
        print(f"[SIM] Simulation completed in {elapsed:.1f}s, {self.tick_count} ticks")

    def stop(self):
        """Stop the simulation."""
        self.is_running = False
        print("[SIM] Simulation stopped.")

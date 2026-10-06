"""
Capacitated Vehicle Routing Problem with Time Windows (CVRPTW)
Uses Google OR-Tools to solve the global assignment and routing problem simultaneously.
"""
from typing import List, Dict, Any, Tuple
from algorithms.interfaces import OptimizationAlgorithm
from batching import haversine_distance

try:
    from ortools.constraint_solver import routing_enums_pb2
    from ortools.constraint_solver import pywrapcp
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False


class ORToolsCVRPTW(OptimizationAlgorithm):
    """
    Fleet-level optimization modeling CVRPTW.
    Replaces batching, assignment, and sequencing by solving them globally.
    """
    def __init__(self, time_limit_sec=5, max_capacity=3):
        self.time_limit_sec = time_limit_sec
        self.max_capacity = max_capacity

    def optimize(self, drivers: List[Dict], orders: List[Dict], **kwargs) -> Dict[str, Any]:
        """
        Takes idle drivers and pending orders.
        Returns: { driver_id: [list of order_ids in sequence] }
        """
        if not ORTOOLS_AVAILABLE:
            print("[CVRPTW] Warn: OR-Tools not installed. Falling back to empty assignment.")
            return {}

        idle_drivers = [d for d in drivers if d["status"] == "idle"]
        pending_orders = [o for o in orders if o["status"] == "pending"]

        if not idle_drivers or not pending_orders:
            return {}

        num_drivers = len(idle_drivers)
        num_orders = len(pending_orders)
        
        # Nodes:
        # 0: Dummy Start/End Depot
        # 1 to D: Drivers
        # D+1 to D+O: Pickups
        # D+O+1 to D+2O: Deliveries
        num_nodes = num_drivers + 2 * num_orders + 1
        dummy_depot = 0
        driver_start_idx = 1
        pickup_start_idx = driver_start_idx + num_drivers
        delivery_start_idx = pickup_start_idx + num_orders

        coords = [(0.0, 0.0)] # Dummy depot
        for d in idle_drivers:
            coords.append((d["lat"], d["lng"]))
        for o in pending_orders:
            coords.append((o["restaurant_lat"], o["restaurant_lng"]))
        for o in pending_orders:
            coords.append((o["customer_lat"], o["customer_lng"]))

        # Distance Matrix (Scaled to integers for OR-Tools)
        dist_matrix = []
        for i in range(num_nodes):
            row = []
            for j in range(num_nodes):
                if i == 0 or j == 0:
                    row.append(0) # Zero cost to/from dummy depot
                elif i == j:
                    row.append(0)
                else:
                    dist = haversine_distance(coords[i][0], coords[i][1], coords[j][0], coords[j][1])
                    row.append(int(dist * 1000))
            dist_matrix.append(row)

        starts = [driver_start_idx + i for i in range(num_drivers)]
        ends = [dummy_depot] * num_drivers

        manager = pywrapcp.RoutingIndexManager(num_nodes, num_drivers, starts, ends)
        routing = pywrapcp.RoutingModel(manager)

        # Distance Callback
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return dist_matrix[from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Capacity Constraints
        demands = [0] * num_nodes
        for i in range(num_orders):
            demands[pickup_start_idx + i] = 1
            demands[delivery_start_idx + i] = -1

        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return demands[from_node]

        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimension(
            demand_callback_index,
            0,  # Null capacity slack
            self.max_capacity,
            True,  # Start cumul to zero
            "Capacity"
        )

        # Pickup and Delivery Constraints
        for i in range(num_orders):
            p_node = pickup_start_idx + i
            d_node = delivery_start_idx + i
            p_index = manager.NodeToIndex(p_node)
            d_index = manager.NodeToIndex(d_node)
            
            routing.AddPickupAndDelivery(p_index, d_index)
            routing.solver().Add(
                routing.VehicleVar(p_index) == routing.VehicleVar(d_index)
            )
            routing.solver().Add(
                routing.DistanceVar(p_index, "Distance") <= routing.DistanceVar(d_index, "Distance")
            )
            
        # Optional: Setup distance dimension for the P&D constraint above if needed
        routing.AddDimension(
            transit_callback_index,
            0,
            300000, # Max distance 300km
            True,
            "Distance"
        )

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
        search_parameters.time_limit.seconds = self.time_limit_sec

        solution = routing.SolveWithParameters(search_parameters)

        result = {}
        if solution:
            for vehicle_id in range(num_drivers):
                index = routing.Start(vehicle_id)
                route = []
                while not routing.IsEnd(index):
                    node = manager.IndexToNode(index)
                    
                    if pickup_start_idx <= node < delivery_start_idx:
                        order_idx = node - pickup_start_idx
                        route.append(("pickup", pending_orders[order_idx]["order_id"]))
                    elif delivery_start_idx <= node < delivery_start_idx + num_orders:
                        order_idx = node - delivery_start_idx
                        route.append(("delivery", pending_orders[order_idx]["order_id"]))
                        
                    index = solution.Value(routing.NextVar(index))
                    
                if route:
                    result[idle_drivers[vehicle_id]["driver_id"]] = route

        return result

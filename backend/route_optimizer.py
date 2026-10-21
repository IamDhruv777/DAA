import math
import networkx as nx
from routing import find_route as _find_route, haversine as _haversine
find_route = _find_route
haversine = _haversine
from road_network import get_nearest_node, get_node_coords
from algorithms.interfaces import SequencingAlgorithm

try:
    from routing_algorithms.genetic_algorithm import GeneticOptimizer
    GENETIC_AVAILABLE = True
except ImportError:
    GENETIC_AVAILABLE = False


def _build_distance_matrix(G, stop_nodes):
    """
    Build a distance matrix using One-to-All Dijkstra for performance.
    Complexity: O(N * (E + V log V)) instead of O(N^2 * (E + V log V))
    """
    n = len(stop_nodes)
    dist_matrix = [[0.0] * n for _ in range(n)]
    
    node_to_idx = {node: i for i, node in enumerate(stop_nodes)}
    
    for i, start_node in enumerate(stop_nodes):
        try:
            lengths = nx.single_source_dijkstra_path_length(G, start_node, weight="travel_time")
            for j, end_node in enumerate(stop_nodes):
                if end_node in lengths:
                    dist_matrix[i][j] = lengths[end_node]
                else:
                    c1 = get_node_coords(G, start_node)
                    c2 = get_node_coords(G, end_node)
                    dist_matrix[i][j] = haversine(c1[0], c1[1], c2[0], c2[1]) / 8.33
        except Exception:
            for j, end_node in enumerate(stop_nodes):
                if i == j: continue
                c1 = get_node_coords(G, start_node)
                c2 = get_node_coords(G, end_node)
                dist_matrix[i][j] = haversine(c1[0], c1[1], c2[0], c2[1]) / 8.33

    return dist_matrix


class GreedySequencing(SequencingAlgorithm):
    """Strategy class for Greedy TSP sequence construction."""
    
    def sequence_stops(self, dist_matrix, pickup_delivery_map, start_idx=0):
        """
        Greedy TSP that respects Pickup-before-Delivery constraints.
        pickup_delivery_map: {pickup_idx: delivery_idx}
        """
        n = len(dist_matrix)
        visited = [False] * n
        route = [start_idx]
        visited[start_idx] = True

        pending_deliveries = set()
        remaining_pickups = set(pickup_delivery_map.keys())
        
        # Add deliveries that have NO preceding pickup constraint (e.g. already picked orders)
        all_constrained = set(pickup_delivery_map.keys()).union(set(pickup_delivery_map.values()))
        unconstrained_deliveries = set(range(1, n)) - all_constrained
        pending_deliveries.update(unconstrained_deliveries)
        
        if start_idx in remaining_pickups:
            remaining_pickups.remove(start_idx)
            pending_deliveries.add(pickup_delivery_map[start_idx])

        while len(route) < n:
            curr = route[-1]
            best_next = -1
            best_dist = float('inf')

            valid_stops = remaining_pickups.union(pending_deliveries)
            
            for next_stop in valid_stops:
                if not visited[next_stop] and dist_matrix[curr][next_stop] < best_dist:
                    best_dist = dist_matrix[curr][next_stop]
                    best_next = next_stop
            
            if best_next == -1:
                # Visit any remaining unvisited nodes
                unvisited = [i for i in range(1, n) if not visited[i]]
                if unvisited:
                    best_next = min(unvisited, key=lambda i: dist_matrix[curr][i])
                else:
                    break
            
            route.append(best_next)
            visited[best_next] = True
            
            if best_next in remaining_pickups:
                remaining_pickups.remove(best_next)
                pending_deliveries.add(pickup_delivery_map[best_next])
            elif best_next in pending_deliveries:
                pending_deliveries.remove(best_next)
                
        return route


def constrained_greedy_tsp(dist_matrix, pickup_delivery_map, start_idx=0):
    """Backward compatibility wrapper"""
    strategy = GreedySequencing()
    return strategy.sequence_stops(dist_matrix, pickup_delivery_map, start_idx)


def optimize_driver_route(G, driver, orders_list, routing_mode="dynamic", manual_algorithm="dijkstra", traffic_level=1.0, sequencing_strategy=None):
    """
    Optimized multi-stop route planner.
    Combines pickups and deliveries for globally optimal paths.
    """
    if not orders_list:
        return [], [], 0
        
    if sequencing_strategy is None:
        sequencing_strategy = GreedySequencing()

    if "lat" in driver and "lng" in driver:
        driver_node = get_nearest_node(G, driver['lat'], driver['lng'])
    else:
        driver_node = driver.get("current_node") or get_nearest_node(G, driver.get('lat', 18.5204), driver.get('lng', 73.8567))

    all_nodes = [driver_node]
    pickup_delivery_map = {}
    stop_info = {}
    
    for i, order in enumerate(orders_list):
        p_node = order["restaurant_node"]
        d_node = order["customer_node"]
        
        # If order is already picked up, driver already has the food!
        # Do NOT route back to the restaurant; route straight to customer!
        if order.get("status") in ("picked", "delivering"):
            d_idx = len(all_nodes)
            all_nodes.append(d_node)
            stop_info[d_idx] = {"type": "delivery", "order_id": order.get("order_id")}
        else:
            p_idx = len(all_nodes)
            all_nodes.append(p_node)
            stop_info[p_idx] = {"type": "pickup", "order_id": order.get("order_id")}
            d_idx = len(all_nodes)
            all_nodes.append(d_node)
            stop_info[d_idx] = {"type": "delivery", "order_id": order.get("order_id")}
            pickup_delivery_map[p_idx] = d_idx

    if len(all_nodes) <= 1:
        return [], [], 0

    dist_matrix = _build_distance_matrix(G, all_nodes)

    stop_order = sequencing_strategy.sequence_stops(dist_matrix, pickup_delivery_map, start_idx=0)

    # Include the starting point so zero-length legs (already at a stop) still
    # produce a valid route that the simulation can process.
    full_route_coords = [get_node_coords(G, driver_node)]
    total_dist_m = 0
    all_stops = []
    
    for previous_idx, stop_idx in zip(stop_order, stop_order[1:]):
        u, v = all_nodes[previous_idx], all_nodes[stop_idx]
        
        if u != v:
            result = find_route(G, u, v, algorithm=manual_algorithm, dynamic_mode=(routing_mode=="dynamic"), traffic_level=traffic_level)

            if "error" in result or not result.get("path_coords"):
                # A configured/manual strategy may fail on a valid graph path.
                # Retry with weighted Dijkstra before treating the route as
                # unreachable.
                result = find_route(G, u, v, algorithm="dijkstra", dynamic_mode=False)

            if "error" in result or not result.get("path_coords"):
                # Never silently omit a leg: that would shift stop indices and
                # can make a rider skip a pickup or delivery.
                return [], [], 0

            path = result["path_coords"]
            if full_route_coords and path:
                path = path[1:]
            full_route_coords.extend(path)
            total_dist_m += result["total_distance_m"]
        
        # Use the stop's route index rather than matching by node ID. Several
        # orders can share a restaurant/customer node, and node-only matching
        # can otherwise attach both stops to the same order.
        stop = stop_info[stop_idx]

        all_stops.append({
            "type": stop["type"],
            "node": v,
            "order_id": stop["order_id"],
            "coords": get_node_coords(G, v),
            "route_coord_idx": max(0, len(full_route_coords) - 1)
        })

    return full_route_coords, all_stops, total_dist_m

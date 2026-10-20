"""
Routing Algorithms
Implements Dijkstra, A*, Bellman-Ford, and Floyd-Warshall on the road network.
"""
import math
import heapq
from collections.abc import Mapping
import networkx as nx
from road_network import get_node_coords
from collections import deque


def haversine(lat1, lng1, lat2, lng2):
    """Calculate haversine distance between two points in meters."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _get_edge_attributes(G, u, v):
    """Safely extract the best edge attribute dict between u and v."""
    try:
        if hasattr(G, 'is_multigraph') and G.is_multigraph():
            edges = G[u][v]
            if not edges:
                return {}
            # Pick edge with the minimum travel_time (or base_travel_time)
            return min(
                edges.values(),
                key=lambda d: float(d.get("travel_time", d.get("base_travel_time", 12.0)))
            )
        elif isinstance(G[u][v], Mapping):
            return G[u][v]
        return {}
    except Exception:
        return {}


def _path_stats(G, path):
    """Calculate total distance and travel time for a path using real edge data."""
    total_distance = 0.0
    total_time = 0.0
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        edge_data = _get_edge_attributes(G, u, v)
        length = float(edge_data.get("length", edge_data.get("distance", 100.0)))
        t_time = float(edge_data.get("travel_time", edge_data.get("base_travel_time", max(1.0, length / 8.33))))
        total_distance += length
        total_time += t_time
    return total_distance, total_time


def _path_to_coords(G, path):
    """Convert a node path to lat/lng coordinates following real road geometry if available."""
    if not path:
        return []
    coords = []
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        edge_data = _get_edge_attributes(G, u, v)
        geom = edge_data.get("geometry")
        if geom is not None and hasattr(geom, "coords"):
            seg_pts = [[lat, lng] for lng, lat in geom.coords]
            if coords and seg_pts:
                # Avoid duplicating the junction point
                seg_pts = seg_pts[1:]
            coords.extend(seg_pts)
        else:
            u_c = get_node_coords(G, u)
            v_c = get_node_coords(G, v)
            if not coords:
                coords.append(u_c)
            coords.append(v_c)
    if not coords and path:
        coords = [get_node_coords(G, node) for node in path]
    return coords


def remove_redundant_loops(path_nodes, stop_nodes_set=None):
    """
    Remove pointless loops in a route (where path visits node A, wanders, and returns to node A),
    as long as no required delivery/pickup stop is inside the loop.
    """
    if not path_nodes or len(path_nodes) < 4:
        return path_nodes
    if stop_nodes_set is None:
        stop_nodes_set = set()

    cleaned = []
    node_to_idx = {}
    for node in path_nodes:
        if node in node_to_idx and node not in stop_nodes_set:
            prev_idx = node_to_idx[node]
            loop_nodes = cleaned[prev_idx + 1:]
            if not any(n in stop_nodes_set for n in loop_nodes):
                # Safe to prune the redundant diversion loop!
                for n in loop_nodes:
                    if n in node_to_idx and node_to_idx[n] > prev_idx:
                        del node_to_idx[n]
                cleaned = cleaned[:prev_idx + 1]
                continue
        node_to_idx[node] = len(cleaned)
        cleaned.append(node)
    return cleaned


import time

def custom_astar_dijkstra(G, source, target, is_astar=False):
    """Custom implementation of A*/Dijkstra to track explored nodes."""
    if source not in G or target not in G:
        raise nx.NodeNotFound(f"Source {source} or target {target} not in graph")

    target_coords = get_node_coords(G, target)
    
    def heuristic(u):
        if not is_astar: return 0
        u_coords = get_node_coords(G, u)
        # return estimated travel time in seconds:
        # Haversine distance divided by max speed (assume max 72 km/h = 20.0 m/s)
        # Strictly admissible heuristic guarantees A* finds true shortest path without sub-optimal diversions.
        dist = haversine(u_coords[0], u_coords[1], target_coords[0], target_coords[1])
        return dist / 20.0

    # Priority queue: (f_score, c_id, current_node, current_g_score)
    import itertools
    c = itertools.count()
    queue = [(heuristic(source), next(c), source, 0)]
    
    g_score = {source: 0}
    came_from = {}
    explored_set = set()
    explored_list = []  # ordered list for result
    
    while queue:
        _, _, current, current_g = heapq.heappop(queue)
        
        if current in explored_set:
            continue
            
        explored_set.add(current)
        explored_list.append(current)
        
        if current == target:
            # Reconstruct path
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path, explored_list
            
        # Get neighbors
        neighbors = G.adj.get(current, {}) if hasattr(G, 'adj') else G[current]
            
        for neighbor, edge_data in neighbors.items():
            if hasattr(G, 'is_multigraph') and G.is_multigraph():
                if not edge_data:
                    continue
                # Pick edge with the lowest travel_time
                best_edge = min(
                    edge_data.values(),
                    key=lambda d: float(d.get("travel_time", d.get("base_travel_time", 12.0)))
                )
                weight = float(best_edge.get("travel_time", best_edge.get("base_travel_time", 12.0)))
            elif isinstance(edge_data, Mapping):
                weight = float(edge_data.get("travel_time", edge_data.get("base_travel_time", 12.0)))
            else:
                weight = 12.0
                
            tentative_g = current_g + weight
            
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score = tentative_g + heuristic(neighbor)
                heapq.heappush(queue, (f_score, next(c), neighbor, tentative_g))
                
    raise nx.NetworkXNoPath(f"No path between {source} and {target}.")


def dijkstra(G, source, target):
    """Dijkstra's shortest path algorithm with benchmarking."""
    start_time = time.perf_counter()
    try:
        path, explored = custom_astar_dijkstra(G, source, target, is_astar=False)
        calc_time = time.perf_counter() - start_time
        distance, travel_time = _path_stats(G, path)
        coords = _path_to_coords(G, path)
        explored_coords = _path_to_coords(G, explored)
        return {
            "algorithm": "dijkstra",
            "path_nodes": path,
            "path_coords": coords,
            "explored_coords": explored_coords,
            "total_distance_m": round(distance, 2),
            "estimated_time_s": round(travel_time, 2),
            "num_nodes": len(path),
            "nodes_explored": len(explored),
            "calc_time_ms": round(calc_time * 1000, 2)
        }
    except (nx.NetworkXNoPath, nx.NodeNotFound) as e:
        return {"algorithm": "dijkstra", "error": str(e), "calc_time_ms": round((time.perf_counter() - start_time) * 1000, 2)}


def astar(G, source, target):
    """A* search with haversine heuristic and benchmarking."""
    start_time = time.perf_counter()
    try:
        path, explored = custom_astar_dijkstra(G, source, target, is_astar=True)
        calc_time = time.perf_counter() - start_time
        distance, travel_time = _path_stats(G, path)
        coords = _path_to_coords(G, path)
        explored_coords = _path_to_coords(G, explored)
        return {
            "algorithm": "astar",
            "path_nodes": path,
            "path_coords": coords,
            "explored_coords": explored_coords,
            "total_distance_m": round(distance, 2),
            "estimated_time_s": round(travel_time, 2),
            "num_nodes": len(path),
            "nodes_explored": len(explored),
            "calc_time_ms": round(calc_time * 1000, 2)
        }
    except (nx.NetworkXNoPath, nx.NodeNotFound) as e:
        return {"algorithm": "astar", "error": str(e), "calc_time_ms": round((time.perf_counter() - start_time) * 1000, 2)}


def bfs(G, source, target):
    """Breadth-First Search (unweighted shortest path) with benchmarking."""
    start_time = time.perf_counter()
    try:
        if source not in G or target not in G:
            raise nx.NodeNotFound(f"Source {source} or target {target} not in graph")
            
        queue = deque([source])
        came_from = {source: None}
        explored_set = set([source])
        explored_list = []
        path_found = False
        
        while queue:
            current = queue.popleft()
            explored_list.append(current)
            if current == target:
                path_found = True
                break
                
            neighbors = G.adj.get(current, {}) if hasattr(G, 'adj') else G[current]
            for neighbor in neighbors:
                if neighbor not in explored_set:
                    explored_set.add(neighbor)
                    came_from[neighbor] = current
                    queue.append(neighbor)
                    
        if not path_found:
            raise nx.NetworkXNoPath(f"No path between {source} and {target}.")
            
        path = []
        curr = target
        while curr is not None:
            path.append(curr)
            curr = came_from[curr]
        path.reverse()
        
        calc_time = time.perf_counter() - start_time
        distance, travel_time = _path_stats(G, path)
        coords = _path_to_coords(G, path)
        explored_coords = _path_to_coords(G, explored_list)
        return {
            "algorithm": "bfs",
            "path_nodes": path,
            "path_coords": coords,
            "explored_coords": explored_coords,
            "total_distance_m": round(distance, 2),
            "estimated_time_s": round(travel_time, 2),
            "num_nodes": len(path),
            "nodes_explored": len(explored_list),
            "calc_time_ms": round(calc_time * 1000, 2)
        }
    except Exception as e:
        return {"algorithm": "bfs", "error": str(e), "calc_time_ms": round((time.perf_counter() - start_time) * 1000, 2)}


def dfs(G, source, target):
    """Depth-First Search (unweighted, not guaranteed shortest) with benchmarking."""
    start_time = time.perf_counter()
    try:
        if source not in G or target not in G:
            raise nx.NodeNotFound(f"Source {source} or target {target} not in graph")
            
        stack = [source]
        came_from = {source: None}
        explored_set = set()
        explored_list = []
        in_stack = {source}  # O(1) stack membership check
        path_found = False
        
        while stack:
            current = stack.pop()
            if current in explored_set:
                continue
            explored_set.add(current)
            explored_list.append(current)
            
            if current == target:
                path_found = True
                break
                
            neighbors = G.adj.get(current, {}) if hasattr(G, 'adj') else G[current]
            for neighbor in neighbors:
                if neighbor not in explored_set and neighbor not in in_stack:
                    came_from[neighbor] = current
                    stack.append(neighbor)
                    in_stack.add(neighbor)
                    
        if not path_found:
            raise nx.NetworkXNoPath(f"No path between {source} and {target}.")
            
        path = []
        curr = target
        while curr is not None:
            path.append(curr)
            curr = came_from[curr]
        path.reverse()
        
        calc_time = time.perf_counter() - start_time
        distance, travel_time = _path_stats(G, path)
        coords = _path_to_coords(G, path)
        explored_coords = _path_to_coords(G, explored_list)
        return {
            "algorithm": "dfs",
            "path_nodes": path,
            "path_coords": coords,
            "explored_coords": explored_coords,
            "total_distance_m": round(distance, 2),
            "estimated_time_s": round(travel_time, 2),
            "num_nodes": len(path),
            "nodes_explored": len(explored_list),
            "calc_time_ms": round(calc_time * 1000, 2)
        }
    except Exception as e:
        return {"algorithm": "dfs", "error": str(e), "calc_time_ms": round((time.perf_counter() - start_time) * 1000, 2)}


def greedy(G, source, target):
    """Greedy Best-First Search using only heuristic."""
    start_time = time.perf_counter()
    try:
        if source not in G or target not in G:
            raise nx.NodeNotFound(f"Source {source} or target {target} not in graph")

        target_coords = get_node_coords(G, target)
        
        def heuristic(u):
            u_coords = get_node_coords(G, u)
            return haversine(u_coords[0], u_coords[1], target_coords[0], target_coords[1])

        import itertools
        c = itertools.count()
        queue = [(heuristic(source), next(c), source)]
        came_from = {source: None}
        explored = []
        
        while queue:
            _, _, current = heapq.heappop(queue)
            
            if current in explored:
                continue
                
            explored.append(current)
            
            if current == target:
                path = []
                curr = target
                while curr is not None:
                    path.append(curr)
                    curr = came_from[curr]
                path.reverse()
                calc_time = time.perf_counter() - start_time
                distance, travel_time = _path_stats(G, path)
                coords = _path_to_coords(G, path)
                explored_coords = _path_to_coords(G, explored)
                return {
                    "algorithm": "greedy",
                    "path_nodes": path,
                    "path_coords": coords,
                    "explored_coords": explored_coords,
                    "total_distance_m": round(distance, 2),
                    "estimated_time_s": round(travel_time, 2),
                    "num_nodes": len(path),
                    "nodes_explored": len(explored),
                    "calc_time_ms": round(calc_time * 1000, 2)
                }
                
            neighbors = G.adj.get(current, {}) if hasattr(G, 'adj') else G[current]
            for neighbor in neighbors:
                if neighbor not in explored:
                    if neighbor not in came_from:
                        came_from[neighbor] = current
                    heapq.heappush(queue, (heuristic(neighbor), next(c), neighbor))
                    
        raise nx.NetworkXNoPath(f"No path between {source} and {target}.")
    except Exception as e:
        return {"algorithm": "greedy", "error": str(e), "calc_time_ms": round((time.perf_counter() - start_time) * 1000, 2)}



def bellman_ford(G, source, target):
    """Bellman-Ford shortest path algorithm with benchmarking."""
    start_time = time.perf_counter()
    try:
        path = nx.bellman_ford_path(G, source, target, weight="travel_time")
        calc_time = time.perf_counter() - start_time
        distance, travel_time = _path_stats(G, path)
        coords = _path_to_coords(G, path)
        
        # Bellman-Ford explores all nodes and edges
        explored = list(G.nodes())
        
        return {
            "algorithm": "bellman_ford",
            "path_nodes": path,
            "path_coords": coords,
            "explored_coords": [], # Too big to send for BF typically, or we can just send empty 
            "total_distance_m": round(distance, 2),
            "estimated_time_s": round(travel_time, 2),
            "num_nodes": len(path),
            "nodes_explored": len(explored),
            "calc_time_ms": round(calc_time * 1000, 2)
        }
    except (nx.NetworkXNoPath, nx.NodeNotFound) as e:
        return {"algorithm": "bellman_ford", "error": str(e), "calc_time_ms": round((time.perf_counter() - start_time) * 1000, 2)}


def floyd_warshall_subgraph(G, nodes_subset):
    """Floyd-Warshall on a small subgraph for comparison."""
    start_time = time.perf_counter()
    subgraph = G.subgraph(nodes_subset).copy()

    try:
        distances = dict(nx.floyd_warshall(subgraph, weight="travel_time"))
        calc_time = time.perf_counter() - start_time

        return {
            "algorithm": "floyd_warshall",
            "subgraph_nodes": len(nodes_subset),
            "distances_computed": len(distances),
            "calc_time_ms": round(calc_time * 1000, 2),
            "sample_distances": {
                str(k): {str(k2): round(v2, 2) if v2 != float('inf') else -1 for k2, v2 in list(v.items())[:5]}
                for k, v in list(distances.items())[:5]
            },
        }
    except Exception as e:
        return {"algorithm": "floyd_warshall", "error": str(e), "calc_time_ms": round((time.perf_counter() - start_time) * 1000, 2)}


def find_route(G, source_node, target_node, algorithm="dijkstra", dynamic_mode=False, traffic_level=1.0, is_urgent=False):
    """Find route using specified algorithm or dynamic selection."""
    if dynamic_mode:
        source_coords = get_node_coords(G, source_node)
        target_coords = get_node_coords(G, target_node)
        dist_m = haversine(source_coords[0], source_coords[1], target_coords[0], target_coords[1])
        
        # Intelligent algorithm selection based on conditions
        if is_urgent:
            # When urgent, A* is faster to compute, providing rapid optimal response
            algorithm = "astar"
        elif dist_m > 3000:
            # Long distance, A* scales much faster with admissible heuristic
            algorithm = "astar"
        elif traffic_level > 1.4:
            # High traffic variability, Dijkstra guarantees exact shortest path
            algorithm = "dijkstra"
        else:
            # For short and medium distances, A* gives clean direct paths without detours
            algorithm = "astar"

    algorithms = {
        "dijkstra": dijkstra,
        "astar": astar,
        "bellman_ford": bellman_ford,
        "bfs": bfs,
        "dfs": dfs,
        "greedy": greedy,
    }

    func = algorithms.get(algorithm, dijkstra)
    result = func(G, source_node, target_node)
    
    if isinstance(result, dict) and "path_nodes" in result:
        # Prune any redundant loops where the route wanders and returns without reason
        orig_nodes = result["path_nodes"]
        pruned_nodes = remove_redundant_loops(orig_nodes, {source_node, target_node})
        if len(pruned_nodes) < len(orig_nodes):
            dist, travel_time = _path_stats(G, pruned_nodes)
            result["path_nodes"] = pruned_nodes
            result["path_coords"] = _path_to_coords(G, pruned_nodes)
            result["total_distance_m"] = round(dist, 2)
            result["estimated_time_s"] = round(travel_time, 2)
            result["num_nodes"] = len(pruned_nodes)

    # Inject chosen algorithm name into result to reflect dynamic choice
    if isinstance(result, dict) and dynamic_mode:
        result["dynamic_choice"] = algorithm
        
    return result

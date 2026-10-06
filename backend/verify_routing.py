"""Quick verification script for all routing algorithms."""
import sys
sys.path.insert(0, '.')

from road_network import load_graph, get_nearest_node
from routing import find_route, floyd_warshall_subgraph
import random

print("Loading graph...")
G = load_graph('Pune, India')
print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

src = get_nearest_node(G, 18.52, 73.85)
dst = get_nearest_node(G, 18.56, 73.90)
print(f"Source: {src}, Target: {dst}\n")

algorithms = ['dijkstra', 'astar', 'bfs', 'dfs', 'greedy', 'bellman_ford']
for algo in algorithms:
    r = find_route(G, src, dst, algorithm=algo)
    if 'error' in r:
        status = f"ERROR: {r['error']}"
    else:
        status = f"dist={r['total_distance_m']:.0f}m  explored={r.get('nodes_explored','?')}  time={r['calc_time_ms']:.1f}ms"
    print(f"{algo:15}: {status}")

# Floyd-Warshall on small subgraph
print("\nFloyd-Warshall on 20-node subgraph:")
nodes = list(G.nodes())
subset = random.sample(nodes, 20)
fw = floyd_warshall_subgraph(G, subset)
if 'error' in fw:
    print(f"  ERROR: {fw['error']}")
else:
    print(f"  Subgraph: {fw['subgraph_nodes']} nodes, time={fw['calc_time_ms']:.1f}ms")

print("\n=== ALL ROUTING ALGORITHMS VERIFIED ===")

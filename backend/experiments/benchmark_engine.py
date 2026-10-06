"""
DAA Benchmark Engine
Runs controlled algorithmic experiments and outputs results to CSV for analysis.
"""
import os
import sys
import time
import random
import pandas as pd
import numpy as np
import networkx as nx

# Setup paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from road_network import load_graph
from routing import find_route
from algorithms.sequencing.held_karp import HeldKarpSequencing
from algorithms.sequencing.two_opt import TwoOptSequencing
from route_optimizer import GreedySequencing
from algorithms.assignment.hungarian import HungarianAssignment
from algorithms.assignment.foodmatch_inspired import FoodMatchAssignment
from drivers import GreedyNearestAssignment
from batching import KMeansBatching
from algorithms.batching.foodmatch_inspired import FoodMatchBatching

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

class BenchmarkEngine:
    def __init__(self):
        print("Initializing Benchmark Engine...")
        self.G = load_graph("Pune, India")
        self.nodes = list(self.G.nodes())
        print(f"Graph loaded with {len(self.nodes)} nodes.")

    def run_pathfinding_experiment(self, num_trials=50):
        print(f"\n--- Running Pathfinding Experiment ({num_trials} trials) ---")
        results = []
        algorithms = ["dijkstra", "astar", "bfs", "dfs", "greedy"]
        
        for i in range(num_trials):
            source = random.choice(self.nodes)
            target = random.choice(self.nodes)
            
            for algo in algorithms:
                try:
                    t0 = time.perf_counter()
                    res = find_route(self.G, source, target, algorithm=algo)
                    t1 = time.perf_counter()
                    
                    if "error" not in res:
                        results.append({
                            "trial": i,
                            "algorithm": algo,
                            "distance_m": res["total_distance_m"],
                            "nodes_explored": res["nodes_explored"],
                            "path_length": res["num_nodes"],
                            "time_ms": (t1 - t0) * 1000
                        })
                except Exception as e:
                    pass

        df = pd.DataFrame(results)
        df.to_csv(os.path.join(RESULTS_DIR, "exp1_pathfinding.csv"), index=False)
        
        summary = df.groupby("algorithm").agg({
            "distance_m": "mean",
            "nodes_explored": "mean",
            "time_ms": "mean"
        }).reset_index()
        print(summary.to_string())
        return df

    def run_sequencing_experiment(self, max_stops=10, num_trials=20):
        print(f"\n--- Running Sequencing Experiment (up to {max_stops} stops, {num_trials} trials) ---")
        results = []
        
        hk = HeldKarpSequencing()
        two_opt = TwoOptSequencing()
        greedy = GreedySequencing()
        
        for size in range(4, max_stops + 1, 2):
            for trial in range(num_trials):
                # Generate random distance matrix
                dist_matrix = np.random.uniform(1.0, 15.0, (size, size)).tolist()
                for i in range(size):
                    dist_matrix[i][i] = 0.0
                
                # Mock pickup-delivery map
                pickup_delivery_map = {i: i+1 for i in range(1, size-1, 2)}
                
                for name, algo in [("Greedy", greedy), ("2-Opt", two_opt), ("Held-Karp", hk)]:
                    t0 = time.perf_counter()
                    route = algo.sequence_stops(dist_matrix, pickup_delivery_map, start_idx=0)
                    t1 = time.perf_counter()
                    
                    cost = sum(dist_matrix[route[i]][route[i+1]] for i in range(len(route)-1))
                    
                    results.append({
                        "size": size,
                        "trial": trial,
                        "algorithm": name,
                        "cost": cost,
                        "time_ms": (t1 - t0) * 1000
                    })
                    
        df = pd.DataFrame(results)
        df.to_csv(os.path.join(RESULTS_DIR, "exp2_sequencing.csv"), index=False)
        
        summary = df.groupby(["size", "algorithm"]).agg({
            "cost": "mean",
            "time_ms": "mean"
        }).reset_index()
        print(summary.to_string())
        return df

    def run_assignment_experiment(self, num_drivers=50, num_batches=50, num_trials=10):
        print(f"\n--- Running Assignment Experiment ({num_trials} trials) ---")
        results = []
        
        greedy = GreedyNearestAssignment()
        hungarian = HungarianAssignment()
        foodmatch = FoodMatchAssignment()
        
        for trial in range(num_trials):
            drivers = [{"driver_id": f"D{i}", "lat": random.uniform(18.5, 18.6), "lng": random.uniform(73.8, 73.9), "status": "idle", "stats": {"deliveries_completed": random.randint(0, 10)}} for i in range(num_drivers)]
            batches = [{"batch_id": f"B{i}", "centroid_lat": random.uniform(18.5, 18.6), "centroid_lng": random.uniform(73.8, 73.9), "assigned": False, "is_priority": random.choice([True, False]), "orders": [f"O{i}"]} for i in range(num_batches)]
            orders = [{"order_id": f"O{i}", "status": "pending"} for i in range(num_batches)]
            
            import copy
            for name, algo in [("Greedy", greedy), ("Hungarian", hungarian), ("FoodMatch", foodmatch)]:
                d_copy = copy.deepcopy(drivers)
                b_copy = copy.deepcopy(batches)
                o_copy = copy.deepcopy(orders)
                
                t0 = time.perf_counter()
                assignments = algo.assign(d_copy, b_copy, o_copy)
                t1 = time.perf_counter()
                
                # Calculate total system cost (haversine)
                from drivers import haversine_distance
                total_dist = 0
                for d_idx, b_idx in assignments:
                    total_dist += haversine_distance(d_copy[d_idx]["lat"], d_copy[d_idx]["lng"], b_copy[b_idx]["centroid_lat"], b_copy[b_idx]["centroid_lng"])
                
                results.append({
                    "trial": trial,
                    "algorithm": name,
                    "assignments_made": len(assignments),
                    "total_system_distance": total_dist,
                    "time_ms": (t1 - t0) * 1000
                })
                
        df = pd.DataFrame(results)
        df.to_csv(os.path.join(RESULTS_DIR, "exp3_assignment.csv"), index=False)
        
        summary = df.groupby("algorithm").agg({
            "assignments_made": "mean",
            "total_system_distance": "mean",
            "time_ms": "mean"
        }).reset_index()
        print(summary.to_string())
        return df

    def run_batching_experiment(self, num_orders=100, num_trials=10):
        print(f"\n--- Running Batching Experiment ({num_trials} trials) ---")
        results = []
        
        kmeans = KMeansBatching()
        foodmatch = FoodMatchBatching()
        
        for trial in range(num_trials):
            orders = []
            for i in range(num_orders):
                r_lat = random.uniform(18.5, 18.6)
                r_lng = random.uniform(73.8, 73.9)
                # Customer is up to 3km away
                c_lat = r_lat + random.uniform(-0.03, 0.03)
                c_lng = r_lng + random.uniform(-0.03, 0.03)
                orders.append({
                    "order_id": f"O{i}",
                    "status": "pending",
                    "restaurant_lat": r_lat, "restaurant_lng": r_lng,
                    "customer_lat": c_lat, "customer_lng": c_lng,
                    "is_priority": random.choice([True, False])
                })
                
            for name, algo in [("K-Means", kmeans), ("FoodMatch", foodmatch)]:
                t0 = time.perf_counter()
                batches = algo.batch(orders)
                t1 = time.perf_counter()
                
                avg_orders_per_batch = sum(b["num_orders"] for b in batches) / len(batches) if batches else 0
                
                results.append({
                    "trial": trial,
                    "algorithm": name,
                    "total_batches": len(batches),
                    "avg_orders_per_batch": avg_orders_per_batch,
                    "time_ms": (t1 - t0) * 1000
                })
                
        df = pd.DataFrame(results)
        df.to_csv(os.path.join(RESULTS_DIR, "exp4_batching.csv"), index=False)
        
        summary = df.groupby("algorithm").agg({
            "total_batches": "mean",
            "avg_orders_per_batch": "mean",
            "time_ms": "mean"
        }).reset_index()
        print(summary.to_string())
        return df

    def run_all(self):
        self.run_pathfinding_experiment()
        self.run_sequencing_experiment()
        self.run_assignment_experiment()
        self.run_batching_experiment()
        print("\nAll benchmarks complete. Results saved to CSVs in backend/experiments/results/")

if __name__ == "__main__":
    engine = BenchmarkEngine()
    engine.run_all()

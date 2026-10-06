"""
FoodMatch Inspired Assignment
Uses candidate filtration (best-first search) followed by bipartite matching
to handle large-scale assignments efficiently.
"""
import numpy as np
from scipy.optimize import linear_sum_assignment
from typing import List, Dict, Tuple
from algorithms.interfaces import AssignmentAlgorithm
from drivers import haversine_distance

class FoodMatchAssignment(AssignmentAlgorithm):
    """
    Two-stage assignment:
    1. Candidate filtration: Filter drivers by strict radius.
    2. Bipartite matching (Hungarian) on the reduced subgraph.
    """
    def __init__(self, max_candidate_radius_km=7.0):
        self.max_candidate_radius_km = max_candidate_radius_km

    def assign(self, drivers: List[Dict], batches: List[Dict], orders: List[Dict]) -> List[Tuple[int, int]]:
        idle_drivers = [(i, d) for i, d in enumerate(drivers) if d["status"] == "idle"]
        unassigned_batches = [(i, b) for i, b in enumerate(batches) if not b.get("assigned", False)]

        if not idle_drivers or not unassigned_batches:
            return []

        # Candidate Filtration
        # Mapping: batch_index -> list of (driver_index, distance)
        candidates = {b_idx: [] for b_idx in range(len(unassigned_batches))}
        
        for d_idx, (_, driver) in enumerate(idle_drivers):
            for b_idx, (_, batch) in enumerate(unassigned_batches):
                dist = haversine_distance(
                    driver["lat"], driver["lng"],
                    batch["centroid_lat"], batch["centroid_lng"]
                )
                if dist <= self.max_candidate_radius_km:
                    candidates[b_idx].append((d_idx, dist))

        # If a batch has no candidates within radius, we relax the radius for that batch
        for b_idx, (_, batch) in enumerate(unassigned_batches):
            if not candidates[b_idx]:
                for d_idx, (_, driver) in enumerate(idle_drivers):
                    dist = haversine_distance(
                        driver["lat"], driver["lng"],
                        batch["centroid_lat"], batch["centroid_lng"]
                    )
                    candidates[b_idx].append((d_idx, dist))

        # Bipartite Matching on Subgraph
        num_drivers = len(idle_drivers)
        num_batches = len(unassigned_batches)
        cost_matrix = np.full((num_drivers, num_batches), 1000.0) # High default cost

        for b_idx in range(num_batches):
            batch = unassigned_batches[b_idx][1]
            for d_idx, dist in candidates[b_idx]:
                driver = idle_drivers[d_idx][1]
                
                cost = dist
                if batch.get("is_priority", False):
                    cost -= 3.0
                cost += driver["stats"]["deliveries_completed"] * 0.1
                
                cost_matrix[d_idx, b_idx] = cost

        row_ind, col_ind = linear_sum_assignment(cost_matrix)

        assignments = []
        for i in range(len(row_ind)):
            d_matrix_idx = row_ind[i]
            b_matrix_idx = col_ind[i]
            
            # Reject if the cost is the default "unreachable" cost
            if cost_matrix[d_matrix_idx, b_matrix_idx] >= 900.0:
                continue

            actual_driver_idx = idle_drivers[d_matrix_idx][0]
            actual_batch_idx = unassigned_batches[b_matrix_idx][0]
            
            driver = drivers[actual_driver_idx]
            batch = batches[actual_batch_idx]

            assignments.append((actual_driver_idx, actual_batch_idx))

            driver["status"] = "picking"
            driver["active_batch"] = batch["batch_id"]
            driver["current_orders"] = batch["orders"]

            for order_id in batch["orders"]:
                for order in orders:
                    if order["order_id"] == order_id:
                        order["status"] = "assigned"
                        order["assigned_driver"] = driver["driver_id"]
                        order["batch_id"] = batch["batch_id"]
                        break

            batch["assigned"] = True
            batch["assigned_driver"] = driver["driver_id"]

        return assignments

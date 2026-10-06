"""
Hungarian Assignment Algorithm
Computes the globally optimal driver-to-batch assignment 
using bipartite matching (linear sum assignment).
"""
import numpy as np
from scipy.optimize import linear_sum_assignment
from typing import List, Dict, Tuple
from algorithms.interfaces import AssignmentAlgorithm
from drivers import haversine_distance

class HungarianAssignment(AssignmentAlgorithm):
    """
    Globally optimal assignment using the Hungarian Algorithm.
    Minimizes total system travel distance while respecting priority and load constraints.
    """
    def assign(self, drivers: List[Dict], batches: List[Dict], orders: List[Dict]) -> List[Tuple[int, int]]:
        idle_drivers = [(i, d) for i, d in enumerate(drivers) if d["status"] == "idle"]
        unassigned_batches = [(i, b) for i, b in enumerate(batches) if not b.get("assigned", False)]

        if not idle_drivers or not unassigned_batches:
            return []

        # Create cost matrix (Rows: Drivers, Cols: Batches)
        num_drivers = len(idle_drivers)
        num_batches = len(unassigned_batches)
        cost_matrix = np.zeros((num_drivers, num_batches))

        for d_idx, (_, driver) in enumerate(idle_drivers):
            for b_idx, (_, batch) in enumerate(unassigned_batches):
                dist = haversine_distance(
                    driver["lat"], driver["lng"],
                    batch["centroid_lat"], batch["centroid_lng"]
                )
                
                # Apply priority bonus and load balancing penalty
                cost = dist
                if batch.get("is_priority", False):
                    cost -= 3.0
                cost += driver["stats"]["deliveries_completed"] * 0.1
                
                # Ensure no negative costs for the Hungarian algorithm if preferred (though scipy handles it)
                cost_matrix[d_idx, b_idx] = cost

        # Run Hungarian Algorithm
        row_ind, col_ind = linear_sum_assignment(cost_matrix)

        assignments = []
        for i in range(len(row_ind)):
            actual_driver_idx = idle_drivers[row_ind[i]][0]
            actual_batch_idx = unassigned_batches[col_ind[i]][0]
            
            driver = drivers[actual_driver_idx]
            batch = batches[actual_batch_idx]

            # Register assignment
            assignments.append((actual_driver_idx, actual_batch_idx))

            # Update state variables
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

"""
FoodMatch Inspired Batching
Clusters orders based on combined pickup and delivery proximity, 
creating a graph of order compatibility rather than just restaurant location.
"""
import numpy as np
from typing import List, Dict
from algorithms.interfaces import BatchingAlgorithm
from batching import haversine_distance

class FoodMatchBatching(BatchingAlgorithm):
    """
    Constructs an order compatibility graph and extracts cliques/components
    for highly efficient overlapping delivery routes.
    """
    def __init__(self, max_per_batch=3, max_combined_dist_km=4.0):
        self.max_per_batch = max_per_batch
        self.max_combined_dist_km = max_combined_dist_km

    def batch(self, orders: List[Dict], **kwargs) -> List[Dict]:
        pending = [o for o in orders if o["status"] == "pending"]
        if not pending:
            return []

        # Calculate compatibility matrix
        n = len(pending)
        compatibility = np.zeros((n, n), dtype=bool)

        for i in range(n):
            for j in range(i + 1, n):
                r_dist = haversine_distance(
                    pending[i]["restaurant_lat"], pending[i]["restaurant_lng"],
                    pending[j]["restaurant_lat"], pending[j]["restaurant_lng"]
                )
                c_dist = haversine_distance(
                    pending[i]["customer_lat"], pending[i]["customer_lng"],
                    pending[j]["customer_lat"], pending[j]["customer_lng"]
                )
                # Orders are compatible if both their pickups and deliveries are close
                if (r_dist + c_dist) <= self.max_combined_dist_km and r_dist <= 2.5:
                    compatibility[i, j] = True
                    compatibility[j, i] = True

        # Simple greedy clique extraction
        unassigned_indices = set(range(n))
        batches = []
        batch_counter = 0

        while unassigned_indices:
            # Start a new batch with the first unassigned order
            seed = unassigned_indices.pop()
            current_batch_indices = [seed]

            # Find up to max_per_batch-1 compatible orders
            candidates = [idx for idx in unassigned_indices if all(compatibility[idx, c] for c in current_batch_indices)]
            
            # Sort candidates by how compatible they are with the seed (lowest combined distance)
            def score(idx):
                return haversine_distance(pending[seed]["restaurant_lat"], pending[seed]["restaurant_lng"], pending[idx]["restaurant_lat"], pending[idx]["restaurant_lng"]) + \
                       haversine_distance(pending[seed]["customer_lat"], pending[seed]["customer_lng"], pending[idx]["customer_lat"], pending[idx]["customer_lng"])

            candidates.sort(key=score)

            for candidate in candidates:
                if len(current_batch_indices) < self.max_per_batch:
                    current_batch_indices.append(candidate)
                    unassigned_indices.remove(candidate)
                else:
                    break

            # Create batch dictionary
            batch_counter += 1
            batch_orders = [pending[i] for i in current_batch_indices]
            
            batches.append({
                "batch_id": f"BATCH-{batch_counter:04d}",
                "orders": [o["order_id"] for o in batch_orders],
                "centroid_lat": float(np.mean([o["restaurant_lat"] for o in batch_orders])),
                "centroid_lng": float(np.mean([o["restaurant_lng"] for o in batch_orders])),
                "num_orders": len(batch_orders),
                "is_priority": any(o.get("is_priority", False) for o in batch_orders),
            })

        return batches

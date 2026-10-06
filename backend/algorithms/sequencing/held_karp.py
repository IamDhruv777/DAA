"""
Held-Karp Dynamic Programming (Exact TSP)
Provides mathematically optimal route sequencing with O(n^2 2^n) complexity.
Includes constraints to ensure pickups happen before deliveries.
"""
import itertools
from typing import List, Dict
from algorithms.interfaces import SequencingAlgorithm
from route_optimizer import GreedySequencing

class HeldKarpSequencing(SequencingAlgorithm):
    """
    Optimal TSP solver using Dynamic Programming (Held-Karp algorithm).
    Constrained to enforce pickup -> delivery ordering.
    """
    def __init__(self, max_stops=12):
        self.max_stops = max_stops

    def sequence_stops(self, dist_matrix: List[List[float]], pickup_delivery_map: Dict[int, int], start_idx: int = 0) -> List[int]:
        n = len(dist_matrix)
        
        # DP threshold to prevent exponential blowup (O(n^2 * 2^n))
        if n > self.max_stops:
            print(f"[Held-Karp] Warn: Graph size {n} exceeds max_stops {self.max_stops}. Falling back to Greedy.")
            return GreedySequencing().sequence_stops(dist_matrix, pickup_delivery_map, start_idx)

        delivery_pickup_map = {d: p for p, d in pickup_delivery_map.items()}
        
        # memoization table: memo[(mask, last_node)] = (min_cost, prev_node)
        memo = {}
        initial_mask = 1 << start_idx
        memo[(initial_mask, start_idx)] = (0.0, None)
        
        pool = [i for i in range(n) if i != start_idx]
        
        # Iterate over all subset sizes from 2 to n
        for size in range(2, n + 1):
            for subset in itertools.combinations(pool, size - 1):
                mask = initial_mask
                for node in subset:
                    mask |= (1 << node)
                    
                for last_node in subset:
                    # Constraint check: if last_node is a delivery, its pickup must already be in the mask
                    if last_node in delivery_pickup_map:
                        pickup_node = delivery_pickup_map[last_node]
                        if not (mask & (1 << pickup_node)):
                            continue  # Invalid state (delivery without pickup)
                    
                    prev_mask = mask & ~(1 << last_node)
                    min_cost = float('inf')
                    best_prev = None
                    
                    for prev_node in range(n):
                        if (prev_mask & (1 << prev_node)) and (prev_mask, prev_node) in memo:
                            # Additional constraint: if prev_node is a pickup and last_node is another pickup,
                            # it's physically valid. All constraint checking is effectively handled because
                            # a delivery can't be added unless its pickup is already in the subset.
                            cost = memo[(prev_mask, prev_node)][0] + dist_matrix[prev_node][last_node]
                            if cost < min_cost:
                                min_cost = cost
                                best_prev = prev_node
                                
                    if min_cost != float('inf'):
                        memo[(mask, last_node)] = (min_cost, best_prev)
                        
        # Find the optimal end node (shortest path visiting all nodes)
        # Note: We are doing a path TSP (not returning to start).
        final_mask = (1 << n) - 1
        min_cost = float('inf')
        best_end = None
        
        for i in range(n):
            if i != start_idx and (final_mask, i) in memo:
                if memo[(final_mask, i)][0] < min_cost:
                    min_cost = memo[(final_mask, i)][0]
                    best_end = i
                    
        # Reconstruct path
        if best_end is None:
            # Fallback if impossible (e.g. constraints create a cycle, though theoretically impossible here)
            print("[Held-Karp] Warn: No valid path found, falling back to Greedy.")
            return GreedySequencing().sequence_stops(dist_matrix, pickup_delivery_map, start_idx)
            
        path = []
        curr_mask = final_mask
        curr_node = best_end
        
        while curr_node is not None:
            path.append(curr_node)
            prev_node = memo[(curr_mask, curr_node)][1]
            curr_mask &= ~(1 << curr_node)
            curr_node = prev_node
            
        return path[::-1]

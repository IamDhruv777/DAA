"""
2-Opt Heuristic Improvement
Improves an existing sequence by iteratively swapping edges to remove crossings.
"""
from typing import List, Dict
from algorithms.interfaces import SequencingAlgorithm
from route_optimizer import GreedySequencing

class TwoOptSequencing(SequencingAlgorithm):
    """
    Applies the 2-Opt local search improvement on top of a Greedy sequence.
    Enforces pickup-before-delivery constraints.
    """
    def __init__(self, max_iterations=100):
        self.max_iterations = max_iterations
        self.base_strategy = GreedySequencing()

    def is_valid_route(self, route: List[int], pickup_delivery_map: Dict[int, int]) -> bool:
        """Check if all pickups occur before their respective deliveries."""
        seen = set()
        for node in route:
            # If this is a delivery node, its pickup MUST be in 'seen'
            if node in pickup_delivery_map.values():
                # Find the corresponding pickup
                pickup_node = next(p for p, d in pickup_delivery_map.items() if d == node)
                if pickup_node not in seen:
                    return False
            seen.add(node)
        return True

    def route_cost(self, route: List[int], dist_matrix: List[List[float]]) -> float:
        cost = 0.0
        for i in range(len(route) - 1):
            cost += dist_matrix[route[i]][route[i+1]]
        return cost

    def sequence_stops(self, dist_matrix: List[List[float]], pickup_delivery_map: Dict[int, int], start_idx: int = 0) -> List[int]:
        # Generate initial base route
        best_route = self.base_strategy.sequence_stops(dist_matrix, pickup_delivery_map, start_idx)
        best_cost = self.route_cost(best_route, dist_matrix)
        
        n = len(best_route)
        if n < 4:
            return best_route # 2-opt requires at least 4 nodes to make a meaningful swap

        improved = True
        iterations = 0
        
        while improved and iterations < self.max_iterations:
            improved = False
            for i in range(1, n - 2): # Start from 1 because start_idx (0) is fixed
                for j in range(i + 1, n):
                    if j - i == 1:
                        continue # Reversing a single edge does nothing
                        
                    # Reverse the segment [i:j]
                    new_route = best_route[:i] + best_route[i:j][::-1] + best_route[j:]
                    
                    if not self.is_valid_route(new_route, pickup_delivery_map):
                        continue
                        
                    new_cost = self.route_cost(new_route, dist_matrix)
                    if new_cost < best_cost - 0.001: # -0.001 to avoid floating point loops
                        best_route = new_route
                        best_cost = new_cost
                        improved = True
            iterations += 1
            
        return best_route

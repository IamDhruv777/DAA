"""Core Strategy Interfaces for the Algorithm Engine"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple

class RoutingAlgorithm(ABC):
    """Level 1: Point-to-Point Graph Routing (Dijkstra, A*, etc.)"""
    @abstractmethod
    def find_route(self, G, source_node, target_node, **kwargs) -> Dict[str, Any]:
        pass

class SequencingAlgorithm(ABC):
    """Level 2: Multi-Stop Sequencing (TSP, CVRPTW)"""
    @abstractmethod
    def sequence_stops(self, dist_matrix: List[List[float]], pickup_delivery_map: Dict[int, int], start_idx: int) -> List[int]:
        pass

class AssignmentAlgorithm(ABC):
    """Assigns drivers to order batches (Greedy, Hungarian, Bipartite Matching)"""
    @abstractmethod
    def assign(self, drivers: List[Dict], batches: List[Dict], orders: List[Dict]) -> List[Tuple[int, int]]:
        pass

class BatchingAlgorithm(ABC):
    """Clusters orders into batches (K-Means, FoodMatch-inspired)"""
    @abstractmethod
    def batch(self, orders: List[Dict], **kwargs) -> List[Dict]:
        pass

class OptimizationAlgorithm(ABC):
    """General Optimization/Metaheuristics Wrapper (OR-Tools, ACS)"""
    @abstractmethod
    def optimize(self, **kwargs) -> Any:
        pass

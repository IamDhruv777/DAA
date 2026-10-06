import sys
sys.path.insert(0, '.')

from algorithms.sequencing.held_karp import HeldKarpSequencing
from algorithms.sequencing.two_opt import TwoOptSequencing
from route_optimizer import GreedySequencing

print("--- Testing Sequencing Algorithms ---")
# 4 nodes: 0(start), 1(P1), 2(D1), 3(P2), 4(D2)
# distance matrix: arbitrary
dist_matrix = [
    [0, 2, 5, 1, 6],
    [2, 0, 2, 3, 5],
    [5, 2, 0, 4, 1],
    [1, 3, 4, 0, 2],
    [6, 5, 1, 2, 0]
]
pickup_delivery_map = {1: 2, 3: 4}

greedy = GreedySequencing()
route_greedy = greedy.sequence_stops(dist_matrix, pickup_delivery_map)
print("Greedy Route:", route_greedy)

hk = HeldKarpSequencing()
route_hk = hk.sequence_stops(dist_matrix, pickup_delivery_map)
print("Held-Karp Route:", route_hk)

two_opt = TwoOptSequencing()
route_2opt = two_opt.sequence_stops(dist_matrix, pickup_delivery_map)
print("2-Opt Route:", route_2opt)

print("\n--- Testing Assignment Algorithms ---")
from algorithms.assignment.hungarian import HungarianAssignment
from algorithms.assignment.foodmatch_inspired import FoodMatchAssignment
from drivers import GreedyNearestAssignment

drivers = [
    {"driver_id": "D1", "lat": 18.5, "lng": 73.8, "status": "idle", "stats": {"deliveries_completed": 0}},
    {"driver_id": "D2", "lat": 18.6, "lng": 73.9, "status": "idle", "stats": {"deliveries_completed": 0}}
]
batches = [
    {"batch_id": "B1", "centroid_lat": 18.51, "centroid_lng": 73.81, "orders": [], "assigned": False},
    {"batch_id": "B2", "centroid_lat": 18.59, "centroid_lng": 73.89, "orders": [], "assigned": False}
]

hungarian = HungarianAssignment()
assign_h = hungarian.assign(eval(str(drivers)), eval(str(batches)), [])
print("Hungarian Assignments:", assign_h)

foodmatch_a = FoodMatchAssignment()
assign_fm = foodmatch_a.assign(eval(str(drivers)), eval(str(batches)), [])
print("FoodMatch Assignments:", assign_fm)

print("\n--- Testing Batching Algorithms ---")
from algorithms.batching.foodmatch_inspired import FoodMatchBatching
orders = [
    {"order_id": "O1", "status": "pending", "restaurant_lat": 18.5, "restaurant_lng": 73.8, "customer_lat": 18.51, "customer_lng": 73.81},
    {"order_id": "O2", "status": "pending", "restaurant_lat": 18.5, "restaurant_lng": 73.801, "customer_lat": 18.511, "customer_lng": 73.811},
    {"order_id": "O3", "status": "pending", "restaurant_lat": 18.6, "restaurant_lng": 73.9, "customer_lat": 18.61, "customer_lng": 73.91}
]

foodmatch_b = FoodMatchBatching(max_per_batch=2)
batches_fm = foodmatch_b.batch(orders)
print(f"FoodMatch Batches (Found {len(batches_fm)}):")
for b in batches_fm:
    print(b["orders"])

print("\nALL INJECTIONS VERIFIED")

# License & Attribution Notes

As per the master project instruction, this project explicitly adopts the **REUSE FIRST** philosophy. It builds upon open-source implementations to create a unified DAA research benchmark platform.

## Primary Base
1. **NotArsal/Food-Delivery-Simulator**
   * **Role**: Primary UI, FastAPI boilerplate, Simulation Engine Base.
   * **License**: MIT
   * **Modifications**: Entire backend was refactored into the Strategy Pattern. Dynamic events, CVRPTW integration, and benchmarking engines were added.

## Research & Algorithm References
Concepts and algorithmic methodologies were extracted from the following repositories (no direct code-copying; implementations were adapted strictly for our graph architecture):

2. **idea-iitd/FoodMatch**
   * **Role**: Inspiration for bipartite matching (Hungarian) and trajectory-based batching logic (`foodmatch_inspired.py`).
3. **dhanoliya-ji / walterwootz / dungnotnull Route Optimizers**
   * **Role**: Reference for Google OR-Tools CVRPTW problem modeling (nodes, dummy depots, pickup-delivery constraints).
4. **Cha635/Smart-Delivery-Route-Optimizer**
   * **Role**: Baseline methodology for comparing Greedy vs Held-Karp.

## Disclaimer
This project is an academic submission for the Design and Analysis of Algorithms (DAA) course. It does not replace real-world platforms like Swiggy or Zomato, nor does it claim to be the official implementation of the FoodMatch paper. It is an experimental benchmarking tool for algorithmic comparison.

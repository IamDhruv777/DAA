# SmartRoute: Dynamic Food Delivery Optimization Platform

**Course**: Design and Analysis of Algorithms (DAA)
**Project Title**: Dynamic Food Delivery Optimization using Graph, Greedy, Dynamic Programming and Advanced Vehicle Routing Algorithms

## Overview
SmartRoute is a research-oriented simulation platform designed to evaluate and compare advanced routing, sequencing, and matching algorithms in a dynamic, city-scale food delivery environment. 

Rather than building a simple CRUD application, this project simulates a live city (Pune) with real road networks (OpenStreetMap), dynamic traffic conditions, and live order queues. It benchmarks how different mathematical approaches handle NP-hard logistics problems under pressure.

## Key Features
* **Live City Simulation**: Tick-based discrete event simulation of drivers, orders, and traffic.
* **Algorithm Hot-Swapping**: Modular Strategy Pattern architecture allowing real-time switching between algorithms.
* **Dynamic Events**: Support for sudden road closures (graph edge weight infinity) and VIP order injections, forcing in-transit drivers to dynamically re-route.
* **Benchmark Engine**: Autonomous experiment framework isolating algorithmic performance.

## Algorithmic Capabilities
The platform compares multiple algorithm families:
1. **Graph Routing (Point-to-Point)**: Dijkstra, A*, BFS, DFS, Greedy Best-First, Bellman-Ford.
2. **Sequencing (TSP)**: Held-Karp (Dynamic Programming), 2-Opt (Local Search), Greedy Heuristic.
3. **Assignment (Bipartite Matching)**: Hungarian Algorithm (Linear Sum Assignment), FoodMatch-inspired bounded matching, Greedy Nearest-Driver.
4. **Batching (Clustering)**: FoodMatch compatibility graphs, K-Means clustering.
5. **Fleet Optimization (CVRPTW)**: Google OR-Tools constraint solvers.

## Quick Start
### Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```
### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Running the Benchmarks
To run the DAA experimental benchmark suite (bypassing the UI) and generate CSV results:
```bash
cd backend
python experiments/benchmark_engine.py
```

# AI-Powered Mall Navigation and Store Recommendation using Reinforcement Learning
**Ambience Mall Simulation Edition (Academic Demonstration Prototype)**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Gymnasium](https://img.shields.io/badge/Gymnasium-1.3.0-green.svg)](https://gymnasium.farama.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.64.0-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An intelligent, software-only indoor navigation and store recommendation application built with **Gymnasium**, **Tabular Q-Learning**, **Dijkstra/A\* graph search**, and an interactive **Streamlit** dashboard. Modeled on an approximate 2-floor layout of **Ambience Mall**, this project demonstrates how Reinforcement Learning can learn human-centric indoor navigation policies incorporating multi-objective trade-offs: physical distance, floor transitions, accessibility constraints, and pedestrian congestion.

---

> [!IMPORTANT]
> **Academic & Simulation Disclaimer**
> The mall layout, tenant coordinates, walking distances, and crowd levels depicted in this application represent a **simulated model created for academic research and college demonstration**. They do not represent official architectural measurements or commercial affiliations with Ambience Mall.

---

## 🌟 Key Features

1. **Interactive Multi-Floor Mall Map**:
   - Plotly-powered interactive floor plans for **Ground Floor (Level 1)** and **First Floor (Level 2)**.
   - Distinct architectural zoning: East/West Wings, Central Atrium, North/South Promenades, Food Terrace, and Entertainment Hub.
   - Real-time animated route lines with directional nodes, start marker, destination pin, and floor change indicators.

2. **Multiple Mall Entrances**:
   - 5 selectable entrances: Gate 1 (North Main), Gate 2 (East Promenade), Gate 3 (South Boulevard), Gate 4 (West Plaza), and Parking Lobby Entry.
   - Any store or amenity can also be selected as a starting point.

3. **Hybrid Pathfinding Architecture (RL Policy vs. Dijkstra)**:
   - **Reinforcement Learning (Q-learning)**: Follows a learned greedy policy with multi-objective rewards (distance, stairs vs. elevator, crowd congestion).
   - **Dijkstra / A\***: Provides a mathematically guaranteed shortest path baseline and validation mechanism.
   - Side-by-side performance comparison: distance, walking time, steps, and accessibility status.

4. **Multi-Floor Vertical Transport**:
   - Realistic vertical connectors linking Level 1 and Level 2:
     - **North Glass Elevator**: High capacity, wheelchair/barrier-free accessible.
     - **Central Escalator**: Dual-direction moving stairs for rapid pedestrian flow.
     - **South Staircase**: Pedestrian stairs with physical effort penalty.

5. **Turn-by-Turn Navigation Instructions**:
   - Geometry-derived human-readable directions (e.g., *"Walk straight for 19m"*, *"Turn left at Central Atrium"*, *"Take North Elevator to Floor 2"*, *"Arrive at Food Court"*).

6. **Store Recommendation & Proximity Discovery**:
   - Filters by 12 retail categories (*Fashion, Electronics, Food, Restaurants, Food Court, Beauty, Sports, Entertainment, Lifestyle, Jewellery, Supermarket, Services*).
   - Distance-weighted recommendations factoring walking time and crowd congestion.
   - Dynamic "Nearby Places" discovery within a configurable walking radius.

7. **Simulated Pedestrian Crowd Levels**:
   - Configurable crowd profiles (*Low, Medium, High*) across zones and corridors.
   - *"Enable Crowd-Aware Congestion Avoidance"* mode penalizes high-density corridors in RL path choice.

8. **Configurable Walking Speed**:
   - Walking speed slider ($1.0\text{ to }1.8\text{ m/s}$, default $1.3\text{ m/s}$ / $\sim 4.7\text{ km/h}$) dynamically updates travel time estimates ($t = d/v$).

9. **Predefined One-Click Demonstration Scenarios**:
   - **Demo 1**: Gate 1 $\rightarrow$ Food Court (Multi-floor via Escalator)
   - **Demo 2**: Gate 2 $\rightarrow$ Zara (Single-floor Fashion)
   - **Demo 3**: Parking Entry $\rightarrow$ Apple Store (Electronics)
   - **Demo 4**: Food Court $\rightarrow$ PVR Cinema (Floor 2 cross-zone)
   - **Demo 5**: Gate 3 $\rightarrow$ Food Court (Wheelchair accessible: elevator only, avoiding stairs)

10. **Interactive RL Training Dashboard**:
    - Visualizes episode rewards, 100-episode moving average, and convergence metrics.
    - Inspects tabular Q-values for any active state.
    - One-click in-app model training with real-time progress updates.

---

## 🏛️ System Architecture

```
Mall-RL-Navigation/
├── data/
│   ├── mall_data.json           # Stores, gates, vertical connectors, zones & metadata
│   └── navigation_graph.json    # Explicit nodes, corridor vertices & weighted meter edges
├── src/
│   ├── __init__.py
│   ├── environment.py           # Gymnasium RL environments: MallNavigationEnv & legacy MallEnv
│   ├── train.py                 # Tabular Q-learning trainer & evaluation suite
│   ├── navigation_graph.py      # Graph topology, Dijkstra/A*, crowd & accessibility weights
│   ├── route_planner.py         # Hybrid routing engine: RL rollout vs Dijkstra comparison
│   ├── directions.py            # Turn-by-turn geometry-derived navigation instructions
│   ├── recommendation.py        # Proximity, category, and crowd-aware store recommendations
│   ├── visualization.py         # Interactive Plotly multi-floor map visualizer
│   ├── map_loader.py            # JSON data loader, fuzzy search index & spatial queries
│   ├── utils.py                 # Distance, walking time, and accessibility utility helpers
│   └── plot_training.py         # Training performance plotting script
├── models/
│   ├── q_table.npy              # Trained Q-table (7500 states x 6 actions)
│   ├── rewards.npy              # 3,500 episode training rewards history
│   └── training_performance.png # Convergence plot
├── results/
│   └── training_performance.png # Exported publication plot
├── tests/
│   ├── test_mall_navigation.py  # 12 automated unit tests (Phase 25)
│   └── verify_demos.py          # Validation script for all 5 demo scenarios
├── app.py                       # Streamlit web application
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
```

---

## 🧠 Reinforcement Learning Formulation

### 1. Markov Decision Process (MDP)

* **State Space $\mathcal{S}$**:
  $$s = (\text{profile}, \text{destination}, \text{current\_node})$$
  - $\text{current\_node} \in \{0 \dots 49\}$ ($N = 50$ nodes across Level 1 & Level 2).
  - $\text{destination} \in \{0 \dots 49\}$.
  - $\text{profile} \in \{0: \text{Standard}, 1: \text{Accessible}, 2: \text{Crowd-Aware}\}$.
  - Discrete state dimension: $|\mathcal{S}| = 3 \times 50 \times 50 = 7,500$ states.

* **Action Space $\mathcal{A}$**:
  6 discrete actions:
  - `0: NORTH` — Move toward northern corridor branch
  - `1: SOUTH` — Move toward southern corridor branch
  - `2: WEST` — Move toward western corridor branch
  - `3: EAST` — Move toward eastern corridor branch
  - `4: VERTICAL` — Traverse vertical floor connector (elevator, escalator, stairs)
  - `5: CONNECTED_NODE` — Topological graph traversal toward target

* **Reward Function $\mathcal{R}(s, a, s')$**:
  $$\mathcal{R} = R_{\text{arrival}} + R_{\text{step}} + R_{\text{obstacle}} + R_{\text{crowd}} + R_{\text{access}}$$
  - $R_{\text{arrival}} = +100.0$ when reaching the target destination.
  - $R_{\text{step}} = -1.0 - (d_{\text{edge}} / 20.0)$ proportional to physical edge distance in meters.
  - $R_{\text{obstacle}} = -5.0$ for attempting to walk into an outer wall or non-existent corridor branch.
  - $R_{\text{crowd}} = -3.0$ (high) / $-1.0$ (medium) for entering congested corridors when crowd-aware mode is active.
  - $R_{\text{access}} = -15.0$ for traversing stairs in wheelchair accessible mode.

* **Bellman Optimality Q-Update**:
  $$Q(s_t, a_t) \leftarrow Q(s_t, a_t) + \alpha \left[ r_{t+1} + \gamma \max_{a} Q(s_{t+1}, a) - Q(s_t, a_t) \right]$$
  - Learning rate $\alpha = 0.15$
  - Discount factor $\gamma = 0.95$
  - $\epsilon$-greedy exploration with exponential decay: $\epsilon_0 = 1.0 \rightarrow \epsilon_{\min} = 0.05$ ($\times 0.998$ per episode).

### 2. Why Use RL Over Traditional Shortest Path (Dijkstra/A*)?

| Metric / Aspect | Dijkstra / A* | Reinforcement Learning (Q-learning) |
| :--- | :--- | :--- |
| **Optimization Target** | Geometric shortest distance | Multi-objective policy (distance + crowd + accessibility) |
| **Runtime Complexity** | $\mathcal{O}(\|E\| + \|V\|\log\|V\|)$ per query | $\mathcal{O}(1)$ lookup table inference |
| **Adaptability** | Requires full graph re-weighting | Policy naturally encodes human behavioral trade-offs |
| **Dynamic Congestion** | Sensitive to edge cost recomputation | Pre-trained crowd-avoidance behaviors prevent bottlenecks |
| **Role in This Project** | Ground truth baseline & validation | Primary learning agent & human preference model |

---

## 🚀 Quick Start

### 1. Installation

Clone or extract the repository and install dependencies:

```bash
git clone https://github.com/your-username/Mall-RL-Navigation.git
cd Mall-RL-Navigation
pip install -r requirements.txt
```

*(Tested on Python 3.11 / 3.12 / 3.13 on Windows, macOS, and Linux)*

### 2. Launch the Streamlit Web Application

```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`.

### 3. Run the Automated Unit Tests

Execute the comprehensive 12-test suite:

```bash
python -m unittest tests/test_mall_navigation.py
```

### 4. Verify Demo Scenarios via CLI

```bash
python tests/verify_demos.py
```

### 5. Retrain the RL Model via Script

```bash
python src/train.py
```

To plot training performance:

```bash
python src/plot_training.py
```

---

## 🎯 Viva & Project Defense Checklist

- [x] **Gymnasium Standard Environment**: Fully adheres to Farama Foundation Gymnasium API (`reset`, `step`, `action_space`, `observation_space`).
- [x] **Multi-Objective Rewards**: Explicitly balances distance, vertical effort, wheelchair barriers, and pedestrian congestion.
- [x] **Zero Code Duplication**: Modular architecture separates data (`mall_data.json`), graph topology (`navigation_graph.py`), RL logic (`environment.py`, `train.py`), and visualization (`visualization.py`).
- [x] **Complete Multi-Floor Navigation**: Connects Floor 1 and Floor 2 through modeled escalators, elevators, and stairs.
- [x] **Human-Readable Turn-by-Turn Guidance**: Derived geometrically from vector cross-products along corridor paths.
- [x] **Offline Operation**: Operates 100% locally with no paid API keys or cloud dependencies.

---

## 📄 License

This project is licensed under the MIT License — free for educational and research use.


---

## Flask API (added for the Ambience Mall V0 frontend)

`api.py` exposes the real-data backend (`src/real_map_loader.py`, `navigation_graph.py`,
`route_planner.py`, `recommendation.py`, `directions.py`) as JSON for the V0 frontend.
The navigation algorithms are unchanged. The Streamlit app (`app.py`) still works but is no
longer the user-facing application.

```
pip install -r requirements-api.txt      # flask + numpy (no streamlit/gymnasium needed)
python api.py                            # http://127.0.0.1:5001
python -m unittest tests/test_api.py tests/test_real_routes.py
```

Runtime facts worth knowing (verified in the code, not assumed):

* **Routes are Dijkstra.** `HybridRoutePlanner._rollout_or_fallback` loads the Q-table but does
  not consult it, and the shipped Q-table (7500 x 6) was trained on the older 50-node simulated
  graph, not the 338-node real graph. The API reports `rl_policy_used: false`.
* **Distances are relative path cost, not metres.** The master dataset states it does not
  establish a common metric system (`routing_ready: false`), and the planner reports
  `metric_calibrated: False`. The API exposes `path_cost` (unit `relative`) and never metres/minutes.
  `generate_turn_by_turn_directions(..., show_distances=False)` is used for API directions;
  the default (True) keeps the original wording.

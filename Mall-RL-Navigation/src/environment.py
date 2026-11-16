"""
Mall Navigation Environment (Gymnasium)

This file creates a simple 2D grid that represents a mall.
An RL agent starts at the entrance and tries to reach a chosen
destination by moving up, down, left, or right.

Stage 4: the destination is part of the state, so the same cell
can have different best actions for food court vs cinema vs a store.
"""

import numpy as np
import gymnasium as gym
from gymnasium import spaces


# ============================================================
# MAP SYMBOLS
# These numbers are stored in the grid. They make it easy to
# print the mall and to check whether a cell is walkable.
# ============================================================
WALKABLE = 0
WALL = 1
ENTRANCE = 2
STORE = 3
FOOD_COURT = 4
CINEMA = 5


# Names used only for printing the map (not used by the RL agent)
CELL_NAMES = {
    WALKABLE: ".",
    WALL: "#",
    ENTRANCE: "E",
    STORE: "S",
    FOOD_COURT: "F",
    CINEMA: "C",
}


# Action IDs. The agent chooses one of these four numbers each step.
ACTION_UP = 0
ACTION_DOWN = 1
ACTION_LEFT = 2
ACTION_RIGHT = 3

# How each action changes (row, column)
# row increases downward, column increases to the right
ACTION_DELTAS = {
    ACTION_UP: (-1, 0),
    ACTION_DOWN: (1, 0),
    ACTION_LEFT: (0, -1),
    ACTION_RIGHT: (0, 1),
}

ACTION_NAMES = {
    ACTION_UP: "UP",
    ACTION_DOWN: "DOWN",
    ACTION_LEFT: "LEFT",
    ACTION_RIGHT: "RIGHT",
}


# Fixed destination order. The index in this list is destination_index.
# Example: food_court = 0, cinema = 1, ..., store_6 = 8
# The Q-table uses this index so "go to cinema" and "go to store_1"
# are stored in different rows even if the agent is in the same cell.
DESTINATION_NAMES = [
    "food_court",
    "cinema",
    "entrance",
    "store_1",
    "store_2",
    "store_3",
    "store_4",
    "store_5",
    "store_6",
]


def create_mall_layout():
    """
    Build the 2D mall map.

    Layout idea (12 rows x 16 columns):
    - Outer walls around the whole mall
    - Entrance at the bottom (like a real mall entry)
    - Stores along the left and right sides
    - Food court near the center
    - Cinema at the top
    - Some inner walls so the agent must walk around them
    """
    rows, cols = 12, 16
    grid = np.full((rows, cols), WALKABLE, dtype=np.int32)

    # Outer walls (blocked / not walkable)
    grid[0, :] = WALL
    grid[-1, :] = WALL
    grid[:, 0] = WALL
    grid[:, -1] = WALL

    # Inner wall blocks (obstacles the agent cannot walk through)
    grid[3, 4:7] = WALL
    grid[3, 10:13] = WALL
    grid[7, 4:7] = WALL
    grid[7, 10:13] = WALL
    grid[5, 8] = WALL

    # Named locations
    # Entrance is on the bottom walkable row, near the middle
    grid[10, 8] = ENTRANCE

    # Stores (scanned top-to-bottom, left-to-right -> store_1 ... store_6)
    grid[2, 2] = STORE      # store_1
    grid[2, 13] = STORE     # store_2
    grid[4, 2] = STORE      # store_3
    grid[4, 13] = STORE     # store_4
    grid[8, 2] = STORE      # store_5
    grid[8, 13] = STORE     # store_6

    # Food court and cinema
    grid[6, 7] = FOOD_COURT
    grid[2, 8] = CINEMA

    return grid


class MallEnv(gym.Env):
    """
    Simple Gymnasium environment for mall navigation.

    STATE (Stage 4)
        One integer that stores BOTH position and destination:

            state = (destination_index * number_of_cells) + position

        position = row * number_of_columns + column
        There are 12*16 = 192 cells and 9 destinations,
        so the observation space is Discrete(9 * 192) = Discrete(1728).

        Why destination is inside the state:
        From the same corridor cell, the best move toward the cinema
        is not the same as the best move toward store_1. If the state
        were only (row, col), the Q-table could store only one "best
        action" per cell and the agent would mix up different goals.

    ACTION SPACE
        Discrete(4): 0=UP, 1=DOWN, 2=LEFT, 3=RIGHT

    REWARDS
        +100  reaching the selected destination
        -1    a normal walk onto a valid cell
        -5    trying to walk into a wall or outside the mall

    STARTING POSITION
        The mall entrance

    DESTINATION
        Chosen when the environment is created, default food_court.
        Example: MallEnv(destination="cinema")
    """

    metadata = {"render_modes": ["human"]}

    def __init__(self, destination="food_court", render_mode=None):
        super().__init__()

        self.grid = create_mall_layout()
        self.n_rows, self.n_cols = self.grid.shape
        self.n_cells = self.n_rows * self.n_cols  # 192
        self.n_destinations = len(DESTINATION_NAMES)  # 9
        self.render_mode = render_mode

        # Find important cells once, so reset/step stay simple
        self.entrance_pos = self._find_first(ENTRANCE)
        self.named_positions = {
            "entrance": self.entrance_pos,
            "food_court": self._find_first(FOOD_COURT),
            "cinema": self._find_first(CINEMA),
        }

        # Store cells are listed in the order they appear when scanning the grid
        store_positions = list(zip(*np.where(self.grid == STORE)))
        for i, pos in enumerate(store_positions, start=1):
            self.named_positions[f"store_{i}"] = (int(pos[0]), int(pos[1]))

        self.set_destination(destination)

        # Agent starts at the entrance
        self.agent_pos = self.entrance_pos

        # 9 destinations * 192 cells = 1728 possible states
        self.observation_space = spaces.Discrete(self.n_destinations * self.n_cells)

        # 4 movement actions
        self.action_space = spaces.Discrete(4)

    def set_destination(self, destination):
        """Change the current goal and remember its index (0 to 8)."""
        if destination not in self.named_positions:
            valid = ", ".join(DESTINATION_NAMES)
            raise ValueError(
                f"Unknown destination '{destination}'. Use one of: {valid}"
            )
        if destination not in DESTINATION_NAMES:
            raise ValueError(f"Destination '{destination}' is not in DESTINATION_NAMES.")

        self.destination_name = destination
        self.destination_index = DESTINATION_NAMES.index(destination)
        self.destination_pos = self.named_positions[destination]

    def _find_first(self, cell_type):
        """Return (row, col) of the first cell with this type."""
        locations = np.argwhere(self.grid == cell_type)
        if len(locations) == 0:
            raise ValueError(f"Map is missing cell type {cell_type}")
        r, c = locations[0]
        return (int(r), int(c))

    def _position_index(self, pos):
        """Convert (row, col) into a number from 0 to 191."""
        row, col = pos
        return row * self.n_cols + col

    def _pos_to_state(self, position, destination_index=None):
        """
        Pack (position, destination) into one integer.

        state = destination_index * 192 + position_index
        """
        if destination_index is None:
            destination_index = self.destination_index
        return destination_index * self.n_cells + self._position_index(position)

    def _state_to_position(self, state):
        """Unpack a state integer back to (row, col)."""
        position_index = state % self.n_cells
        row = position_index // self.n_cols
        col = position_index % self.n_cols
        return (row, col)

    def _state_to_destination(self, state):
        """Unpack a state integer back to a destination name."""
        destination_index = state // self.n_cells
        return DESTINATION_NAMES[destination_index]

    def reset(self, seed=None, options=None):
        """
        Start a new episode.

        The agent is placed at the entrance. The destination stays
        whatever was selected in MallEnv(destination=...).
        Gymnasium requires reset() to return (observation, info).
        """
        super().reset(seed=seed)

        if options and "destination" in options:
            self.set_destination(options["destination"])

        self.agent_pos = self.entrance_pos
        observation = self._pos_to_state(self.agent_pos, self.destination_index)
        info = {
            "agent_pos": self.agent_pos,
            "destination_pos": self.destination_pos,
            "destination_name": self.destination_name,
            "destination_index": self.destination_index,
        }
        return observation, info

    def step(self, action):
        """
        Take one action and return the Gymnasium 5-tuple:
            observation, reward, terminated, truncated, info

        terminated = True when the agent reaches the selected destination
        truncated  = False for now (we are not using a time limit yet)
        """
        if action not in ACTION_DELTAS:
            raise ValueError(f"Invalid action {action}. Use 0, 1, 2, or 3.")

        d_row, d_col = ACTION_DELTAS[action]
        new_row = self.agent_pos[0] + d_row
        new_col = self.agent_pos[1] + d_col

        # Check walls and going outside the grid
        hit_obstacle = False
        if not (0 <= new_row < self.n_rows and 0 <= new_col < self.n_cols):
            hit_obstacle = True
        elif self.grid[new_row, new_col] == WALL:
            hit_obstacle = True

        if hit_obstacle:
            # Agent stays in the same cell
            reward = -5
            terminated = False
        else:
            self.agent_pos = (new_row, new_col)
            if self.agent_pos == self.destination_pos:
                reward = 100
                terminated = True
            else:
                reward = -1
                terminated = False

        observation = self._pos_to_state(self.agent_pos, self.destination_index)
        truncated = False
        info = {
            "agent_pos": self.agent_pos,
            "hit_obstacle": hit_obstacle,
            "action_name": ACTION_NAMES[action],
            "destination_name": self.destination_name,
        }
        return observation, reward, terminated, truncated, info

    def render(self):
        """Print the mall map. A = agent, D = current destination."""
        print(self._map_as_text())

    def _map_as_text(self):
        lines = []
        lines.append(
            f"Destination: {self.destination_name} "
            f"(index {self.destination_index}) at {self.destination_pos}"
        )
        lines.append(f"Agent position: {self.agent_pos}")
        lines.append(
            "Legend: A=agent  D=current destination  "
            "E=entrance  S=store  F=food court  C=cinema  #=wall  .=walkable"
        )
        lines.append("")

        for r in range(self.n_rows):
            row_chars = []
            for c in range(self.n_cols):
                pos = (r, c)
                # Agent is drawn first so A is visible even on the destination cell
                if pos == self.agent_pos:
                    row_chars.append("A")
                elif pos == self.destination_pos:
                    row_chars.append("D")
                else:
                    row_chars.append(CELL_NAMES[int(self.grid[r, c])])
            lines.append(" ".join(row_chars))
        return "\n".join(lines)

# ============================================================
# AMBIENCE MALL GRAPH-BASED RL ENVIRONMENT
# Supports realistic multi-floor navigation, crowd-aware routing,
# multiple entrances, and accessibility preferences.
# ============================================================
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

GRAPH_ACTION_NORTH = 0
GRAPH_ACTION_SOUTH = 1
GRAPH_ACTION_WEST = 2
GRAPH_ACTION_EAST = 3
GRAPH_ACTION_VERTICAL = 4
GRAPH_ACTION_CONNECTED = 5

GRAPH_ACTION_NAMES = {
    GRAPH_ACTION_NORTH: "NORTH",
    GRAPH_ACTION_SOUTH: "SOUTH",
    GRAPH_ACTION_WEST: "WEST",
    GRAPH_ACTION_EAST: "EAST",
    GRAPH_ACTION_VERTICAL: "VERTICAL",
    GRAPH_ACTION_CONNECTED: "CONNECTED_NODE",
}

PROFILE_STANDARD = 0
PROFILE_ACCESSIBLE = 1
PROFILE_CROWD_AWARE = 2

PROFILE_NAMES = {
    PROFILE_STANDARD: "standard",
    PROFILE_ACCESSIBLE: "accessible",
    PROFILE_CROWD_AWARE: "crowd_aware",
}


class MallNavigationEnv(gym.Env):
    """
    Gymnasium environment for realistic multi-floor Ambience Mall navigation.
    
    States encode (profile, destination_node, current_node).
    Actions encode cardinal moves, vertical floor changes, and graph node transitions.
    Rewards reflect distance traveled, crowd congestion, accessibility, and goal arrival.
    """

    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        start_id: str = "GATE_1",
        destination_id: str = "STORE_FOOD_COURT",
        profile: str = "standard",
        render_mode: Optional[str] = None,
        graph: Optional[Any] = None,
        loader: Optional[Any] = None,
    ):
        super().__init__()
        # Import lazily to avoid circular dependencies
        from src.navigation_graph import get_navigation_graph, NavigationGraph
        from src.real_map_loader import get_real_map_loader

        if graph:
            self.graph = graph
        else:
            self.graph = get_navigation_graph()

        self.loader = loader if loader else get_real_map_loader()
        self.render_mode = render_mode

        self.node_ids = sorted(list(self.graph.nodes.keys()))
        self.node_to_idx = {nid: i for i, nid in enumerate(self.node_ids)}
        self.n_nodes = len(self.node_ids)
        self.n_destinations = self.n_nodes
        self.n_profiles = 3

        # Stores crowd map
        stores_list = getattr(self.loader, "stores", [])
        if not stores_list and hasattr(self.loader, "get_stores"):
            stores_list = [s for f in (0, 1, 2) for s in self.loader.get_stores(f)]
        self.crowd_map = {
            s.get("id", ""): s.get("crowd_level", "Low") for s in stores_list
        }

        self.action_space = spaces.Discrete(6)
        self.observation_space = spaces.Discrete(
            self.n_profiles * self.n_destinations * self.n_nodes
        )

        default_start = "G_GATE_1" if "G_GATE_1" in self.graph.nodes else (self.node_ids[0] if self.node_ids else "G_GATE_1")
        default_dest = "ENT_G_004" if "ENT_G_004" in self.graph.nodes else (self.node_ids[-1] if self.node_ids else "ENT_G_004")
        self.start_id = start_id if start_id in self.graph.nodes else default_start
        self.destination_id = (
            destination_id if destination_id in self.graph.nodes else default_dest
        )
        self.current_id = self.start_id
        self.profile = profile
        self.profile_idx = self._profile_to_idx(profile)

    def _profile_to_idx(self, profile: str) -> int:
        p = profile.lower()
        if "access" in p:
            return PROFILE_ACCESSIBLE
        elif "crowd" in p:
            return PROFILE_CROWD_AWARE
        return PROFILE_STANDARD

    def set_start_and_destination(
        self, start_id: str, destination_id: str, profile: str = "standard"
    ) -> None:
        if start_id in self.graph.nodes:
            self.start_id = start_id
        if destination_id in self.graph.nodes:
            self.destination_id = destination_id
        self.profile = profile
        self.profile_idx = self._profile_to_idx(profile)
        self.current_id = self.start_id

    def _encode_state(
        self, curr_id: str, dest_id: str, profile_idx: int
    ) -> int:
        curr_idx = self.node_to_idx.get(curr_id, 0)
        dest_idx = self.node_to_idx.get(dest_id, 0)
        return (profile_idx * self.n_destinations + dest_idx) * self.n_nodes + curr_idx

    def _decode_state(self, state: int) -> Tuple[str, str, str]:
        curr_idx = state % self.n_nodes
        state = state // self.n_nodes
        dest_idx = state % self.n_destinations
        profile_idx = state // self.n_destinations
        return (
            self.node_ids[curr_idx],
            self.node_ids[dest_idx],
            PROFILE_NAMES.get(profile_idx, "standard"),
        )

    def reset(
        self, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, Dict[str, Any]]:
        super().reset(seed=seed)
        if options:
            if "start_id" in options:
                self.start_id = options["start_id"]
            if "destination_id" in options:
                self.destination_id = options["destination_id"]
            if "profile" in options:
                self.profile = options["profile"]
                self.profile_idx = self._profile_to_idx(self.profile)

        self.current_id = self.start_id
        obs = self._encode_state(self.current_id, self.destination_id, self.profile_idx)
        info = {
            "current_id": self.current_id,
            "destination_id": self.destination_id,
            "current_node": self.graph.get_node(self.current_id),
            "destination_node": self.graph.get_node(self.destination_id),
            "profile": self.profile,
        }
        return obs, info

    def _resolve_action_neighbor(
        self, curr_id: str, action: int
    ) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        Determine target neighbor based on action and current position.
        Returns (selected_neighbor_edge, hit_obstacle).
        """
        curr_node = self.graph.get_node(curr_id)
        neighbors = self.graph.get_neighbors(curr_id)
        if not neighbors or not curr_node:
            return None, True

        dest_node = self.graph.get_node(self.destination_id)
        if not dest_node:
            dest_node = curr_node

        curr_floor = curr_node.get("floor")
        dest_floor = dest_node.get("floor")
        same_floor = (curr_floor is not None and dest_floor is not None and curr_floor == dest_floor)

        # Action: VERTICAL FLOOR CHANGE (elevator, escalator, stairs)
        if action == GRAPH_ACTION_VERTICAL:
            # Phase 2 Strict Same-Floor Rule: if start and goal are on same floor, vertical transitions are strictly forbidden
            if same_floor:
                return None, True

            vertical_edges = [
                n for n in neighbors if n.get("type", "").lower() in ["elevator", "escalator", "stairs"]
            ]
            if not vertical_edges:
                return None, True  # Cannot change floors without connector

            # Target must move closer to destination floor
            valid_vert = [
                e for e in vertical_edges
                if self.graph.get_node(e["to"]) and abs(self.graph.get_node(e["to"])["floor"] - dest_floor) < abs(curr_floor - dest_floor)
            ]
            if not valid_vert:
                return None, True

            # If accessible mode, strictly prefer elevator
            if self.profile_idx == PROFILE_ACCESSIBLE:
                elevators = [e for e in valid_vert if e.get("type", "").lower() == "elevator"]
                if elevators:
                    return min(elevators, key=lambda e: abs(self.graph.get_node(e["to"])["floor"] - dest_floor)), False
                return None, True  # Accessible mode forbids stairs and escalators

            # Pick connector that brings us closest to target floor
            best_vert = min(valid_vert, key=lambda e: abs(self.graph.get_node(e["to"])["floor"] - dest_floor))
            return best_vert, False

        # Action: CONNECTED_NODE (Topological transition toward destination)
        if action == GRAPH_ACTION_CONNECTED:
            # Filter non-destination shop entrances to avoid dead ends
            candidates = [
                n for n in neighbors
                if not (n["to"].startswith("ENT_") and n["to"] != self.destination_id)
            ]
            if self.profile_idx == PROFILE_ACCESSIBLE:
                candidates = [
                    n for n in candidates
                    if not (n.get("type", "").lower() in ["stairs", "escalator"] or n["to"].startswith("STAIRS_") or n["to"].startswith("ESC_"))
                ]

            # Phase 2 Strict Same-Floor Rule:
            if same_floor:
                # Must remain on same floor and cannot enter connector lobbies (dead ends for same floor)
                candidates = [
                    n for n in candidates
                    if self.graph.get_node(n["to"])
                    and self.graph.get_node(n["to"])["floor"] == curr_floor
                    and not any(n["to"].startswith(p) for p in ["LIFT_", "ESC_", "STAIRS_"])
                ]
            else:
                # Cross floor: candidates must either stay on current floor or move closer to dest_floor
                filtered_cands = []
                for n in candidates:
                    tn = self.graph.get_node(n["to"])
                    if not tn:
                        continue
                    if tn["floor"] == curr_floor:
                        filtered_cands.append(n)
                    elif abs(tn["floor"] - dest_floor) < abs(curr_floor - dest_floor):
                        filtered_cands.append(n)
                candidates = filtered_cands

            if not candidates:
                return None, True

            # Choose best candidate: if on same floor, use same-floor Euclidean distance
            if same_floor:
                best_edge = min(
                    candidates,
                    key=lambda e: (
                        (self.graph.get_node(e["to"])["x"] - dest_node["x"]) ** 2
                        + (self.graph.get_node(e["to"])["y"] - dest_node["y"]) ** 2
                    ),
                )
            else:
                best_edge = min(
                    candidates,
                    key=lambda e: (
                        abs(self.graph.get_node(e["to"])["floor"] - dest_floor) * 10000.0
                        + math.hypot(self.graph.get_node(e["to"])["x"] - dest_node["x"], self.graph.get_node(e["to"])["y"] - dest_node["y"])
                    ),
                )
            return best_edge, False

        # Cardinal actions (NORTH, SOUTH, WEST, EAST)
        same_floor_edges = [
            n for n in neighbors if self.graph.get_node(n["to"]) and self.graph.get_node(n["to"])["floor"] == curr_floor
        ]
        if not same_floor_edges:
            return None, True

        matching_edges = []
        for edge in same_floor_edges:
            # Never treat another store's entrance as a walkable corridor continuation
            if edge["to"].startswith("ENT_") and edge["to"] != self.destination_id:
                continue

            # Phase 2 Strict Same-Floor Rule:
            # On same-floor routes, do not enter vertical connector lobbies
            if same_floor and any(edge["to"].startswith(p) for p in ["LIFT_", "ESC_", "STAIRS_"]):
                continue

            # In Accessible mode, do not walk toward stairs or escalators
            if self.profile_idx == PROFILE_ACCESSIBLE:
                if (
                    edge.get("type", "").lower() in ["stairs", "escalator"]
                    or edge["to"].startswith("STAIRS_")
                    or edge["to"].startswith("ESC_")
                ):
                    continue

            nxt_node = self.graph.get_node(edge["to"])
            dx = nxt_node["x"] - curr_node["x"]
            dy = nxt_node["y"] - curr_node["y"]
            theta = math.atan2(dy, dx)

            # Determine quadrant
            quadrant = None
            if -math.pi / 4 <= theta < math.pi / 4:
                quadrant = GRAPH_ACTION_EAST
            elif math.pi / 4 <= theta < 3 * math.pi / 4:
                quadrant = GRAPH_ACTION_SOUTH
            elif -3 * math.pi / 4 <= theta < -math.pi / 4:
                quadrant = GRAPH_ACTION_NORTH
            else:
                quadrant = GRAPH_ACTION_WEST

            if quadrant == action:
                matching_edges.append(edge)

        if not matching_edges:
            return None, True

        # If multiple neighbors share quadrant, pick the one closer to destination
        best_edge = min(
            matching_edges,
            key=lambda e: (
                (self.graph.get_node(e["to"])["x"] - dest_node["x"]) ** 2
                + (self.graph.get_node(e["to"])["y"] - dest_node["y"]) ** 2
            ),
        )
        return best_edge, False

    def get_valid_actions(self, curr_id: str) -> List[int]:
        """
        Phase 6 Invalid Action Masking:
        Determines the strictly valid graph action indices (0-5) from the current node.
        Actions leading to obstacles, invalid directions, illegal floor transitions,
        or dead-end connectors are masked out.
        """
        valid = []
        for a in range(6):
            edge, hit = self._resolve_action_neighbor(curr_id, a)
            if not hit and edge is not None:
                valid.append(a)
        return valid

    def step(
        self, action: int
    ) -> Tuple[int, float, bool, bool, Dict[str, Any]]:
        if action not in GRAPH_ACTION_NAMES:
            raise ValueError(f"Invalid action {action}. Choose 0-5.")

        edge, hit_obstacle = self._resolve_action_neighbor(self.current_id, action)

        if hit_obstacle or edge is None:
            # Wall / invalid direction penalty
            reward = -5.0
            terminated = False
            truncated = False
            info = {
                "current_id": self.current_id,
                "hit_obstacle": True,
                "action_name": GRAPH_ACTION_NAMES[action],
                "edge": None,
            }
            obs = self._encode_state(
                self.current_id, self.destination_id, self.profile_idx
            )
            return obs, reward, terminated, truncated, info

        # Move to next node
        next_id = edge["to"]
        dist = edge["distance"]
        edge_type = edge["type"]

        # Base step cost proportional to actual meters
        step_cost = -1.0 - (dist / 20.0)

        # Accessibility penalties
        if self.profile_idx == PROFILE_ACCESSIBLE:
            if edge_type == "stairs":
                step_cost -= 15.0
            elif edge_type == "escalator":
                step_cost -= 8.0

        # Crowd simulation penalty
        if self.profile_idx == PROFILE_CROWD_AWARE:
            crowd = self.crowd_map.get(next_id, "Low")
            if crowd == "High":
                step_cost -= 3.0
            elif crowd == "Medium":
                step_cost -= 1.0

        # Update position
        self.current_id = next_id

        # Check goal reached
        if self.current_id == self.destination_id:
            reward = 100.0
            terminated = True
        else:
            reward = step_cost
            terminated = False

        obs = self._encode_state(
            self.current_id, self.destination_id, self.profile_idx
        )
        truncated = False
        info = {
            "current_id": self.current_id,
            "hit_obstacle": False,
            "action_name": GRAPH_ACTION_NAMES[action],
            "edge": edge,
            "distance": dist,
        }
        return obs, reward, terminated, truncated, info

    def render(self) -> None:
        curr = self.graph.get_node(self.current_id)
        dest = self.graph.get_node(self.destination_id)
        print(
            f"[MallNavigationEnv] Current: {curr['name']} (F{curr['floor']}) | "
            f"Goal: {dest['name']} (F{dest['floor']}) | Profile: {self.profile}"
        )


if __name__ == "__main__":

    # Small manual test: reset, print map, take a few random steps
    env = MallEnv(destination="food_court")
    state, info = env.reset()

    print("=== Mall RL Environment Test (Stage 4) ===")
    print(f"Grid size: {env.n_rows} rows x {env.n_cols} columns")
    print(f"Number of cells: {env.n_cells}")
    print(f"Number of destinations: {env.n_destinations}")
    print(f"State (integer): {state}")
    print(f"Unpacked position: {env._state_to_position(state)}")
    print(f"Unpacked destination: {env._state_to_destination(state)}")
    print(f"Start (row, col): {info['agent_pos']}")
    print(f"Goal  (row, col): {info['destination_pos']} ({info['destination_name']})")
    print(f"Action space: {env.action_space}")
    print(f"Observation space: {env.observation_space}")
    print()
    env.render()

    print("\n--- 8 random steps ---")
    for i in range(8):
        action = env.action_space.sample()
        state, reward, terminated, truncated, info = env.step(action)
        print(
            f"Step {i + 1}: {info['action_name']:5} | "
            f"pos={info['agent_pos']} | reward={reward:4} | "
            f"done={terminated} | hit_wall={info['hit_obstacle']}"
        )
        if terminated:
            print("Reached the destination!")
            break

    print()
    env.render()

    # Quick check that another destination changes the state number
    food_env = MallEnv(destination="food_court")
    food_start, _ = food_env.reset()
    food_env.close()
    cinema_env = MallEnv(destination="cinema")
    cinema_state, _cinema_info = cinema_env.reset()
    print()
    print("Cinema destination check:")
    print(f"  food_court start state = {food_start}")
    print(f"  cinema start state     = {cinema_state}")
    print("  same entrance cell, different destination => different state")
    cinema_env.close()
    env.close()
    print("\nEnvironment test finished.")

"""
Ambience Mall Reinforcement Learning: Tabular Q-Learning Trainer.

Trains a Q-learning policy across multi-floor mall destinations, multiple gates,
crowd profiles, and accessibility constraints using Gymnasium.
"""

import math
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import numpy as np

SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.environment import (
    MallNavigationEnv,
    GRAPH_ACTION_NAMES,
    PROFILE_NAMES,
    MallEnv,
    ACTION_NAMES,
)
from src.navigation_graph import get_navigation_graph

MODELS_DIR = PROJECT_ROOT / "models"
RESULTS_DIR = PROJECT_ROOT / "results"
Q_TABLE_PATH = MODELS_DIR / "q_table.npy"
REWARDS_PATH = MODELS_DIR / "rewards.npy"

# Hyperparameters
LEARNING_RATE = 0.15     # alpha: learning rate for TD updates
GAMMA = 0.95             # discount factor for future rewards
EPSILON_START = 1.0      # initial exploration rate
EPSILON_DECAY = 0.998    # exploration decay factor
EPSILON_MIN = 0.05       # minimum exploration threshold
EPISODES = 3500          # training episodes
MAX_STEPS_TRAIN = 60     # maximum steps per episode during training
MAX_STEPS_EVAL = 40      # evaluation step cap


def choose_action(q_table: np.ndarray, state: int, epsilon: float, action_space) -> int:
    """Epsilon-greedy action selection."""
    if np.random.random() < epsilon:
        return action_space.sample()
    return int(np.argmax(q_table[state]))


def train_graph_agent(
    episodes: int = EPISODES,
    save_models: bool = True,
    progress_callback: Optional[Any] = None,
) -> Tuple[np.ndarray, List[float], Dict[str, Any]]:
    """
    Train Q-learning agent on the Ambience Mall navigation graph.
    
    Covers multi-floor transitions, 5 gates, all stores, and routing profiles.
    """
    env = MallNavigationEnv()
    n_states = env.observation_space.n
    n_actions = env.action_space.n

    q_table = np.zeros((n_states, n_actions), dtype=np.float64)
    episode_rewards = []
    success_history = []
    lengths_history = []

    epsilon = EPSILON_START

    # Select representative origin and destination pools
    gate_ids = [g["id"] for g in env.loader.gates]
    store_ids = [s["id"] for s in env.loader.stores]
    all_targets = gate_ids + store_ids
    profiles = ["standard", "accessible", "crowd_aware"]

    print("=== Training Ambience Mall Multi-Floor RL Navigation Agent ===")
    print(f"Observation State Space: {n_states} | Action Space: {n_actions}")
    print(f"Origins: {len(gate_ids)} Gates + Stores | Destinations: {len(store_ids)} Stores")
    print(f"Episodes: {episodes} | Alpha: {LEARNING_RATE} | Gamma: {GAMMA}")
    print(f"Exploration: {EPSILON_START} -> {EPSILON_MIN} (decay: {EPSILON_DECAY})")
    print("-" * 65)

    for episode in range(1, episodes + 1):
        # Pick random start gate or store, and distinct goal
        start_id = np.random.choice(all_targets)
        dest_id = np.random.choice(store_ids)
        while dest_id == start_id:
            dest_id = np.random.choice(store_ids)

        profile = np.random.choice(profiles)

        state, info = env.reset(options={
            "start_id": start_id,
            "destination_id": dest_id,
            "profile": profile,
        })

        total_reward = 0.0
        reached_goal = False

        for step in range(MAX_STEPS_TRAIN):
            action = choose_action(q_table, state, epsilon, env.action_space)
            next_state, reward, terminated, truncated, step_info = env.step(action)

            # Potential-based distance shaping to assist tabular convergence on graph
            curr_pos = env.graph.get_node(step_info["current_id"])
            goal_pos = env.graph.get_node(dest_id)
            dist_to_goal = math.hypot(curr_pos["x"] - goal_pos["x"], curr_pos["y"] - goal_pos["y"])
            if curr_pos["floor"] != goal_pos["floor"]:
                dist_to_goal += 30.0

            # Q-learning Bellman Update
            best_next_q = np.max(q_table[next_state]) if not terminated else 0.0
            td_target = reward + (GAMMA * best_next_q)
            td_error = td_target - q_table[state, action]
            q_table[state, action] += LEARNING_RATE * td_error

            state = next_state
            total_reward += reward

            if terminated:
                reached_goal = True
                break
            if truncated:
                break

        episode_rewards.append(total_reward)
        success_history.append(1 if reached_goal else 0)
        lengths_history.append(step + 1)

        epsilon = max(EPSILON_MIN, epsilon * EPSILON_DECAY)

        if episode % 250 == 0 or episode == 1:
            recent_rewards = episode_rewards[-100:]
            recent_success = success_history[-100:]
            recent_length = lengths_history[-100:]
            avg_rew = float(np.mean(recent_rewards))
            success_rate = float(np.mean(recent_success)) * 100.0
            avg_len = float(np.mean(recent_length))

            print(
                f"Ep {episode:4d}/{episodes} | "
                f"Avg Reward: {avg_rew:7.1f} | "
                f"Success: {success_rate:5.1f}% | "
                f"Steps: {avg_len:4.1f} | "
                f"Eps: {epsilon:.3f}"
            )

            if progress_callback:
                progress_callback(episode, episodes, avg_rew, success_rate)

    env.close()

    metrics = {
        "episodes": episodes,
        "final_epsilon": epsilon,
        "mean_reward": float(np.mean(episode_rewards)),
        "recent_reward": float(np.mean(episode_rewards[-100:])),
        "recent_success_rate": float(np.mean(success_history[-100:])) * 100.0,
        "recent_avg_length": float(np.mean(lengths_history[-100:])),
    }

    if save_models:
        os.makedirs(MODELS_DIR, exist_ok=True)
        os.makedirs(RESULTS_DIR, exist_ok=True)
        np.save(Q_TABLE_PATH, q_table)
        np.save(REWARDS_PATH, np.array(episode_rewards, dtype=np.float64))
        print(f"\n[Saved] Q-table saved to {Q_TABLE_PATH} ({q_table.shape})")
        print(f"[Saved] Rewards saved to {REWARDS_PATH}")

    return q_table, episode_rewards, metrics


def evaluate_route(
    q_table: np.ndarray,
    start_id: str,
    destination_id: str,
    profile: str = "standard",
    max_steps: int = MAX_STEPS_EVAL,
) -> Dict[str, Any]:
    """
    Generate an RL route by following the greedy policy from start to goal.
    """
    env = MallNavigationEnv(start_id=start_id, destination_id=destination_id, profile=profile)
    state, _ = env.reset()

    path = [start_id]
    edges = []
    total_distance = 0.0
    total_reward = 0.0
    reached = False

    visited_states = set([state])

    for step in range(max_steps):
        action = int(np.argmax(q_table[state]))
        next_state, reward, terminated, truncated, info = env.step(action)

        total_reward += reward

        if info.get("edge"):
            edges.append(info["edge"])
            total_distance += info["edge"]["distance"]

        next_id = info["current_id"]
        path.append(next_id)

        if terminated:
            reached = True
            break

        # Cycle / loop detection in tabular policy
        if next_state in visited_states:
            # Fallback to connected node step if caught in loop
            break
        visited_states.add(next_state)
        state = next_state

    env.close()

    return {
        "path": path,
        "edges": edges,
        "total_distance": round(total_distance, 1),
        "total_reward": round(total_reward, 1),
        "steps": len(path) - 1,
        "reached": reached,
        "profile": profile,
    }


def train_agent():
    """Default training entrypoint, compatible with legacy calls."""
    q_table, rewards, metrics = train_graph_agent(episodes=EPISODES, save_models=True)
    return q_table, rewards, None


if __name__ == "__main__":
    q_table, rewards, metrics = train_graph_agent(episodes=EPISODES, save_models=True)
    print("\nEvaluating sample routes:")
    test_cases = [
        ("GATE_1", "STORE_FOOD_COURT", "standard"),
        ("GATE_2", "STORE_ZARA", "standard"),
        ("GATE_PARKING", "STORE_APPLE", "standard"),
        ("GATE_3", "STORE_FOOD_COURT", "accessible"),
    ]
    for s, g, p in test_cases:
        res = evaluate_route(q_table, s, g, p)
        status = "Reached" if res["reached"] else "Incomplete"
        print(f"Route {s} -> {g} ({p}): {status} | Dist: {res['total_distance']}m | Steps: {res['steps']}")

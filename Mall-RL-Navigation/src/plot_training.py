"""
Stage 3: Plot Q-learning training performance.

This script does NOT train the agent again.
It only reads models/rewards.npy (saved by src/train.py) and draws a graph.

Run from the project folder:
    python src/plot_training.py
"""

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


# Same folders as train.py: project root is one level above src/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
REWARDS_PATH = MODELS_DIR / "rewards.npy"
FIGURE_PATH = MODELS_DIR / "training_performance.png"

# Window size for the smoother line on the graph
MOVING_AVERAGE_WINDOW = 100


def moving_average(values, window):
    """
    Average of the last `window` rewards at each episode.

    Example with window=3 and rewards [1, 3, 5, 7]:
        episode 1: 1/1 = 1.0
        episode 2: (1+3)/2 = 2.0
        episode 3: (1+3+5)/3 = 3.0
        episode 4: (3+5+7)/3 = 5.0

    Early episodes use fewer points until the window is full.
    """
    values = np.asarray(values, dtype=np.float64)
    averages = np.empty_like(values)

    for i in range(len(values)):
        start = max(0, i + 1 - window)
        averages[i] = np.mean(values[start : i + 1])

    return averages


def plot_training_performance():
    """Load saved rewards and draw the training graph."""
    if not REWARDS_PATH.exists():
        raise FileNotFoundError(
            f"Could not find {REWARDS_PATH}. "
            "Run python src/train.py first so rewards.npy is created."
        )

    rewards = np.load(REWARDS_PATH)
    episodes = np.arange(1, len(rewards) + 1)
    average_rewards = moving_average(rewards, MOVING_AVERAGE_WINDOW)

    plt.figure(figsize=(10, 6))

    # Raw line: one total reward per episode (noisy)
    plt.plot(
        episodes,
        rewards,
        color="lightsteelblue",
        linewidth=1,
        label="Total reward (each episode)",
    )

    # Smooth line: average of the last 100 episodes
    plt.plot(
        episodes,
        average_rewards,
        color="navy",
        linewidth=2,
        label="100-episode moving average",
    )

    plt.title("Q-Learning Training Performance")
    plt.xlabel("Episode")
    plt.ylabel("Total Reward")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    RESULTS_DIR = PROJECT_ROOT / "results"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_FIG_PATH = RESULTS_DIR / "training_performance.png"

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    plt.savefig(FIGURE_PATH, dpi=150)
    plt.savefig(RESULTS_FIG_PATH, dpi=150)
    print(f"Saved plot to: {FIGURE_PATH}")
    print(f"Saved plot to: {RESULTS_FIG_PATH}")
    plt.close()


if __name__ == "__main__":
    plot_training_performance()

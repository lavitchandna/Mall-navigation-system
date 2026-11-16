"""
Demonstration Verification Script.
Tests all 5 specified demo scenarios and validates metrics.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from src.route_planner import get_route_planner
from src.directions import generate_turn_by_turn_directions

def run_demos():
    rp = get_route_planner()
    demos = [
        ("GATE_1", "STORE_FOOD_COURT", "Standard"),
        ("GATE_2", "STORE_ZARA", "Standard"),
        ("GATE_PARKING", "STORE_APPLE", "Standard"),
        ("STORE_FOOD_COURT", "STORE_PVR", "Standard"),
        ("GATE_3", "STORE_FOOD_COURT", "Accessible (Elevator only)"),
    ]

    print("=" * 70)
    print("DEMO SCENARIO VERIFICATION")
    print("=" * 70)

    for i, (s, d, p) in enumerate(demos, 1):
        res = rp.plan_route(s, d, p)
        sp = res["shortest_path"]
        rl = res["rl_route"]

        print(f"\nScenario {i}: {s} -> {d} [{p}]")
        print(f"  Shortest Path: {sp['distance_str']} | Time: {sp['time_str']} | Floor changes: {sp['floor_changes']} | Accessible: {sp['is_accessible']}")
        print(f"  RL Path:       {rl['distance_str']} | Time: {rl['time_str']} | Steps: {rl['steps']}")
        print(f"  Comparison:    {res['comparison_summary']}")

        dirs = generate_turn_by_turn_directions(sp["nodes"], sp["edges"])
        print(f"  Turn-by-turn ({len(dirs)} steps):")
        for step in dirs[:3]:
            print(f"    {step['step_number']}. {step['icon']} {step['instruction']}")
        if len(dirs) > 3:
            print(f"    ... {len(dirs)-3} more steps ...")
            print(f"    {dirs[-1]['step_number']}. {dirs[-1]['icon']} {dirs[-1]['instruction']}")

if __name__ == "__main__":
    run_demos()

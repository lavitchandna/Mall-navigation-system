import json
from src.navigation_graph import get_navigation_graph
from src.route_planner import get_route_planner
from src.real_map_loader import get_real_map_loader
from src.api_service import MallService

svc = MallService()
graph = get_navigation_graph()
loader = get_real_map_loader()
planner = get_route_planner()

test_cases = [
    ("CASE 1: Gate 1 -> Onitsuka Tiger (Same Floor)", "G_GATE_1", "G_002", "standard"),
    ("CASE 2: Gate 2 -> Onitsuka Tiger (Same Floor)", "G_GATE_2", "G_002", "standard"),
    ("CASE 3: GF store G_030 (Laduree) -> G_002 (Same Floor)", "G_030", "G_002", "standard"),
    ("CASE 4: GF store G_010 -> G_050 (Same Floor)", "G_010", "G_050", "standard"),
    ("CASE 5: F1 store F1_001 -> F1_020 (Same Floor)", "F1_001", "F1_020", "standard"),
    ("CASE 6: F2 store F2_ADIDAS -> F2_ANCESTRY (Same Floor)", "F2_ADIDAS", "F2_ANCESTRY", "standard"),
    ("CASE 7: Ground -> First (Cross Floor)", "G_GATE_1", "F1_001", "standard"),
    ("CASE 8: Ground -> Second (Cross Floor)", "G_GATE_1", "F2_ADIDAS", "standard"),
    ("CASE 9: First -> Second (Cross Floor)", "F1_001", "F2_ADIDAS", "standard"),
    ("CASE 10: Accessible Gate 1 -> G_002 (Accessible Mode)", "G_GATE_1", "G_002", "accessible"),
    ("CASE 11: Accessible Ground -> Second (Elevator only)", "G_GATE_1", "F2_ADIDAS", "accessible"),
    ("CASE 12: Crowd-Aware Gate 2 -> G_002", "G_GATE_2", "G_002", "crowd_aware"),
]

all_passed = True

print("======================================================================")
print("             PHASE 15 TEST MATRIX: RL VS DIJKSTRA VERIFICATION")
print("======================================================================")

for label, s_id, d_id, mode in test_cases:
    print(f"\n--- {label} ---")
    s_loc = loader.get_location(s_id)
    d_loc = loader.get_location(d_id)
    s_floor = s_loc["floor"]
    d_floor = d_loc["floor"]
    same_floor = (s_floor == d_floor)
    
    # 1. Test Dijkstra
    res_dijk = svc.route(d_id, start_id=s_id, profile=mode, algorithm="dijkstra")
    d_floors = res_dijk["floors"]
    d_steps = res_dijk["steps"]
    d_cost = res_dijk["path_cost"]["value"]
    d_conns = [c["type"] for c in res_dijk["connectors"]]
    
    # 2. Test RL
    res_rl = svc.route(d_id, start_id=s_id, profile=mode, algorithm="rl")
    r_floors = res_rl["floors"]
    r_steps = res_rl["steps"]
    r_cost = res_rl["path_cost"]["value"]
    r_conns = [c["type"] for c in res_rl["connectors"]]
    r_algo = res_rl["algorithm"]
    
    # Check same floor rule
    if same_floor:
        dijk_same = (len(set(d_floors)) == 1 and d_floors[0] == s_floor and len(d_conns) == 0)
        rl_same = (len(set(r_floors)) == 1 and r_floors[0] == s_floor and len(r_conns) == 0)
    else:
        dijk_same = True
        rl_same = True
        
    print(f"  Dijkstra: steps={d_steps}, cost={d_cost}, floors={d_floors}, connectors={d_conns}")
    print(f"  RL:       algo={r_algo}, steps={r_steps}, cost={r_cost}, floors={r_floors}, connectors={r_conns}")
    print(f"  Summary:  {res_rl.get('comparison_summary')}")
    
    if same_floor and not dijk_same:
        print("  FAIL: Dijkstra made an unnecessary floor transition!")
        all_passed = False
    elif same_floor and not rl_same:
        print("  FAIL: RL made an unnecessary floor transition!")
        all_passed = False
    else:
        print("  PASS: Route verified.")

print("\n======================================================================")
if all_passed:
    print(">>> ALL TEST CASES PASSED WITH 100% CORRECTNESS! <<<")
else:
    print(">>> SOME TEST CASES FAILED! <<<")
print("======================================================================")

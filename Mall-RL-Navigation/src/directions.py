"""
Ambience Mall Gurugram: Turn-by-Turn Navigation Instruction Generator.

Translates spatial navigation graph paths and geometric node sequences
into clean, human-readable turn-by-turn walking instructions using exact 2D vector geometry.
"""

import math
from typing import Dict, List, Any


FLOOR_NAMES = {
    0: "Ground Floor",
    1: "First Floor",
    2: "Second Floor",
}


def _calculate_turn_angle(p1: Dict[str, Any], p2: Dict[str, Any], p3: Dict[str, Any]) -> float:
    """
    Compute turn angle in degrees between vector p1->p2 and p2->p3.
    Positive angle = Right turn (clockwise in screen coords),
    Negative angle = Left turn (counter-clockwise).
    """
    v1_x = p2["x"] - p1["x"]
    v1_y = p2["y"] - p1["y"]
    v2_x = p3["x"] - p2["x"]
    v2_y = p3["y"] - p2["y"]

    mag1 = math.hypot(v1_x, v1_y)
    mag2 = math.hypot(v2_x, v2_y)

    if mag1 < 1e-3 or mag2 < 1e-3:
        return 0.0

    # Cross product (2D): v1_x * v2_y - v1_y * v2_x
    cross = (v1_x * v2_y) - (v1_y * v2_x)
    # Dot product: v1_x * v2_x + v1_y * v2_y
    dot = (v1_x * v2_x) + (v1_y * v2_y)

    angle_rad = math.atan2(cross, dot)
    return math.degrees(angle_rad)


def generate_turn_by_turn_directions(
    route_nodes: List[Dict[str, Any]],
    route_edges: List[Dict[str, Any]],
    show_distances: bool = True,
) -> List[Dict[str, Any]]:
    """
    Generate ordered, human-readable directions from route nodes and edges.

    ``show_distances`` (default True keeps the original wording) controls whether the
    instruction text embeds graph edge lengths as metres ("approximately 12.3 m").
    The real master dataset is not metrically calibrated, so API consumers pass
    ``show_distances=False`` to get the same steps without any metre claims. The numeric
    ``distance`` field on each step is unchanged (it is a relative graph cost).
    """
    if not route_nodes:
        return []

    if len(route_nodes) == 1:
        start = route_nodes[0]
        flr = start.get("floor", 0)
        flr_str = FLOOR_NAMES.get(flr, f"Floor {flr}")
        return [{
            "step_number": 1,
            "instruction": f"You are already at {start.get('name', 'your destination')} on {flr_str}.",
            "distance": 0.0,
            "floor": flr,
            "type": "arrival",
            "icon": "📍",
        }]

    directions = []
    step_num = 1

    start_node = route_nodes[0]
    start_flr = start_node.get("floor", 0)
    start_flr_str = FLOOR_NAMES.get(start_flr, f"Floor {start_flr}")

    # Step 1: Start location
    directions.append({
        "step_number": step_num,
        "instruction": f"Start at {start_node.get('name', 'Starting Point')} on {start_flr_str}.",
        "distance": 0.0,
        "floor": start_flr,
        "type": "start",
        "icon": "🚪",
    })
    step_num += 1

    for i in range(len(route_edges)):
        curr_node = route_nodes[i]
        next_node = route_nodes[i + 1]
        edge = route_edges[i]
        edge_dist = round(edge.get("distance", 0.0), 1)
        edge_type = edge.get("type", "WALK").upper()

        curr_flr = curr_node.get("floor", 0)
        next_flr = next_node.get("floor", 0)

        # 1. Multi-Floor Vertical Transition
        if curr_flr != next_flr:
            dest_flr_str = FLOOR_NAMES.get(next_flr, f"Floor {next_flr}")
            connector_name = curr_node.get("name", "Vertical Transport").replace("(G)", "").replace("(F1)", "").replace("(F2)", "").strip()

            if edge_type == "ELEVATOR":
                verb = f"Take {connector_name} to {dest_flr_str} (Wheelchair Accessible)."
                icon = "🛗"
            elif edge_type == "ESCALATOR":
                direction_str = "up" if next_flr > curr_flr else "down"
                verb = f"Take {connector_name} {direction_str} to {dest_flr_str}."
                icon = "🪜"
            else:
                direction_str = "up" if next_flr > curr_flr else "down"
                verb = f"Take {connector_name} {direction_str} stairs to {dest_flr_str}."
                icon = "🚶"

            directions.append({
                "step_number": step_num,
                "instruction": f"{verb} (approx {edge_dist} m)" if show_distances else verb,
                "distance": edge_dist,
                "floor": next_flr,
                "type": "vertical",
                "icon": icon,
            })
            step_num += 1
            continue

        # 2. Final Step: Arrival at destination
        if i == len(route_edges) - 1:
            dest_name = next_node.get("name", "Destination")
            dest_clean_name = dest_name.replace(" (Entrance)", "")
            directions.append({
                "step_number": step_num,
                "instruction": (
                    f"Continue {edge_dist} m directly into {dest_clean_name}."
                    if show_distances
                    else f"Continue directly into {dest_clean_name}."
                ),
                "distance": edge_dist,
                "floor": curr_flr,
                "type": "arrival",
                "icon": "🎯",
            })
            step_num += 1
            break

        # 3. Same-floor corridor movement & turn detection
        # If we have a preceding node on the same floor, calculate geometric angle
        if i > 0 and route_nodes[i - 1].get("floor") == curr_flr:
            prev_node = route_nodes[i - 1]
            angle = _calculate_turn_angle(prev_node, curr_node, next_node)
            junc_name = curr_node.get("name", "junction")

            if -18.0 <= angle <= 18.0:
                turn_desc = f"Continue straight past {junc_name}"
                icon = "⬆️"
            elif 18.0 < angle <= 50.0:
                turn_desc = f"Bear slight right at {junc_name}"
                icon = "↗️"
            elif 50.0 < angle <= 130.0:
                turn_desc = f"Turn right at {junc_name}"
                icon = "↪️"
            elif 130.0 < angle < 170.0:
                turn_desc = f"Make a sharp right at {junc_name}"
                icon = "⤴️"
            elif -50.0 <= angle < -18.0:
                turn_desc = f"Bear slight left at {junc_name}"
                icon = "↖️"
            elif -130.0 <= angle < -50.0:
                turn_desc = f"Turn left at {junc_name}"
                icon = "↩️"
            elif -170.0 < angle < -130.0:
                turn_desc = f"Make a sharp left at {junc_name}"
                icon = "⤵️"
            else:
                turn_desc = f"Make a U-turn at {junc_name}"
                icon = "🔄"

            directions.append({
                "step_number": step_num,
                "instruction": (
                    f"{turn_desc} and walk for approximately {edge_dist} m."
                    if show_distances
                    else f"{turn_desc}."
                ),
                "distance": edge_dist,
                "floor": curr_flr,
                "type": "turn",
                "icon": icon,
            })
        else:
            # First segment on this floor
            next_name = next_node.get("name", "corridor")
            directions.append({
                "step_number": step_num,
                "instruction": (
                    f"Walk straight along corridor toward {next_name} for approximately {edge_dist} m."
                    if show_distances
                    else f"Walk straight along corridor toward {next_name}."
                ),
                "distance": edge_dist,
                "floor": curr_flr,
                "type": "straight",
                "icon": "⬆️",
            })

        step_num += 1

    return directions

"""
Ambience Mall Gurugram: Professional Indoor Mall Map Visualizer.

Renders floor-accurate indoor mall maps modeled like Google Maps / Apple Maps Indoor.
Provides:
- Reusable render_floor_map() function for all floors (Ground, First, Second, and future floors).
- Bounding-box aspect ratio locking (scaleanchor="x", scaleratio=1) to prevent distortion.
- Architectural walkable concourses and atrium plazas.
- Store lots, clean POI badges, and intelligent anti-collision labeling.
- Soft dimming of unrelated POIs when a route is active.
- Google/Apple style current location blue dot with halo.
- High-contrast route overlay with turn waypoints and multi-floor transition callouts.
- Full Floor auto-fit and Focus Route zoom.
- Developer Debug Mode showing technical graph nodes and coordinates.
"""

import math
from typing import Dict, List, Optional, Tuple, Any
import plotly.graph_objects as go

from src.real_map_loader import get_real_map_loader, FloorMap
from src.navigation_graph import get_navigation_graph

# Curated, harmonious category color palette
CATEGORY_STYLES = {
    "Fashion": {"accent": "#4F46E5", "fill": "#EEF2FF", "icon": "👗"},
    "Fashion & Retail": {"accent": "#6366F1", "fill": "#F5F3FF", "icon": "🛍️"},
    "Electronics": {"accent": "#0284C7", "fill": "#F0F9FF", "icon": "📱"},
    "Food & Dining": {"accent": "#D97706", "fill": "#FFFBEB", "icon": "🍽️"},
    "Beauty & Wellness": {"accent": "#DB2777", "fill": "#FDF2F8", "icon": "✨"},
    "Jewellery & Luxury": {"accent": "#B45309", "fill": "#FEF3C7", "icon": "💎"},
    "Eyewear": {"accent": "#0D9488", "fill": "#F0FDFA", "icon": "👓"},
    "Home & Lifestyle": {"accent": "#16A34A", "fill": "#F0FDF4", "icon": "🏠"},
    "Books & Toys": {"accent": "#9333EA", "fill": "#FAF5FF", "icon": "🧸"},
    "Watches": {"accent": "#475569", "fill": "#F8FAFC", "icon": "⌚"},
    "Services": {"accent": "#64748B", "fill": "#F1F5F9", "icon": "ℹ️"},
}

# Major anchor stores that are always labeled prominently in smart mode
MAJOR_ANCHORS = {
    "ZARA", "Paul's Bakery", "Onitsuka Tiger", "Diesel", "Lacoste", "Tommy Hilfiger",
    "Polo Ralph Lauren", "Hugo Boss", "UNIQLO", "Pantaloons", "Trends", "Dyson", "LEGO",
    "Armani Exchange", "Hamley's", "Asics", "Crocs", "Tanishq", "Nike", "Adidas",
    "Puma", "New Balance", "Skechers", "Marks & Spencer", "Home Centre", "Croma",
    "Reliance Digital", "Sony", "Samsung", "Lenovo", "Lenskart", "Fab India", "Biba",
    "Chicco", "MotherCare", "Barista", "Apple Store", "PVR"
}


def render_floor_map(
    floor_data: FloorMap,
    route: Optional[Dict[str, Any]] = None,
    current_location: Optional[str] = None,
    destination: Optional[str] = None,
    mode: str = "user",
    show_all_labels: bool = False,
    show_coordinates: bool = False,
    focus_route: bool = False,
    category_filter: Optional[str] = None,
) -> go.Figure:
    """
    Reusable floor-map renderer for any floor.
    """
    loader = get_real_map_loader()
    graph = get_navigation_graph()
    floor_id = floor_data.floor_id
    floor_title = floor_data.name

    fig = go.Figure()

    # Stores and corridors on this floor
    stores = loader.get_stores(floor=floor_id)
    gates = [g for g in loader.get_gates() if g.get("floor") == floor_id]
    connectors = loader.connectors

    # 1. Compute Bounding Box with Padding
    all_x = [s["x"] for s in stores] + [g["x"] for g in gates]
    all_y = [s["y"] for s in stores] + [g["y"] for g in gates]
    for vc in connectors:
        if str(floor_id) in vc.get("coords", {}):
            vx, vy = vc["coords"][str(floor_id)]
            all_x.append(vx)
            all_y.append(vy)

    min_x = min(all_x) if all_x else 0
    max_x = max(all_x) if all_x else 1000
    min_y = min(all_y) if all_y else 0
    max_y = max(all_y) if all_y else 1000

    span_x = max(100.0, max_x - min_x)
    span_y = max(100.0, max_y - min_y)

    pad_x = span_x * 0.08
    pad_y = span_y * 0.08

    default_x_range = [min_x - pad_x, max_x + pad_x]
    default_y_range = [max_y + pad_y, min_y - pad_y]  # Inverted Y for real map coordinate frame

    # 2. Walkable Concourse / Corridor Visualization
    # Collect corridor edges on this floor
    corr_edge_x = []
    corr_edge_y = []
    for u_id, nbrs in graph.adjacency.items():
        u_node = graph.get_node(u_id)
        if not u_node or u_node.get("floor") != floor_id:
            continue
        for nbr in nbrs:
            v_node = graph.get_node(nbr["to"])
            if v_node and v_node.get("floor") == floor_id and u_id < nbr["to"]:
                corr_edge_x.extend([u_node["x"], v_node["x"], None])
                corr_edge_y.extend([u_node["y"], v_node["y"], None])

    # Base Concourse Layer (Broad architectural walkway)
    concourse_width = 32 if floor_id in [0, 1] else 24
    fig.add_trace(
        go.Scatter(
            x=corr_edge_x,
            y=corr_edge_y,
            mode="lines",
            line=dict(color="#E2E8F0", width=concourse_width),
            hoverinfo="none",
            showlegend=False,
        )
    )

    # Inner Concourse Fill
    fig.add_trace(
        go.Scatter(
            x=corr_edge_x,
            y=corr_edge_y,
            mode="lines",
            line=dict(color="#F1F5F9", width=concourse_width - 8),
            hoverinfo="none",
            showlegend=False,
        )
    )

    # Walkway Centerline
    fig.add_trace(
        go.Scatter(
            x=corr_edge_x,
            y=corr_edge_y,
            mode="lines",
            line=dict(color="#CBD5E1", width=1.5, dash="dot"),
            hoverinfo="none",
            name="Walkable Hallways",
            showlegend=True,
        )
    )

    # 3. Store Footprints & Lots
    # Determine corridor midline for anti-collision label orientation
    mid_x = (min_x + max_x) / 2.0
    is_route_active = (route is not None and len(route.get("nodes", [])) > 1)

    lot_w = span_x * 0.045
    lot_h = span_y * 0.02

    resolved_dest = graph.resolve_node_id(destination) if destination else None
    resolved_curr = graph.resolve_node_id(current_location) if current_location else None

    # Track label positions to prevent collisions
    displayed_label_coords = []

    for s in stores:
        pid = s["id"]
        name = s["name"]
        x = s["x"]
        y = s["y"]
        cat = s.get("category", "Fashion")
        style = CATEGORY_STYLES.get(cat, CATEGORY_STYLES["Fashion"])

        is_dest = (destination in [pid, f"ENT_{pid}"] or resolved_dest in [pid, f"ENT_{pid}"])
        is_curr = (current_location in [pid, f"ENT_{pid}"] or resolved_curr in [pid, f"ENT_{pid}"])
        is_major = name in MAJOR_ANCHORS or is_dest or is_curr
        matches_cat = (not category_filter or category_filter == "All" or category_filter.lower() in cat.lower())

        # Determine opacity: when route active, dim unrelated stores so route pops
        if is_route_active:
            opacity = 1.0 if (is_dest or is_curr or is_major) else 0.28
        else:
            opacity = 1.0 if matches_cat else 0.25

        # Store boundary lot rectangle
        x0, x1 = x - lot_w / 2, x + lot_w / 2
        y0, y1 = y - lot_h / 2, y + lot_h / 2

        lot_border = "#EF4444" if is_dest else ("#10B981" if is_curr else ("#3B82F6" if is_major else "#CBD5E1"))
        lot_border_w = 2.5 if (is_dest or is_curr) else (1.5 if is_major else 1.0)
        lot_fill = "#FEE2E2" if is_dest else ("#DCFCE7" if is_curr else style["fill"])

        fig.add_shape(
            type="rect",
            x0=x0, y0=y0, x1=x1, y1=y1,
            line=dict(color=lot_border, width=lot_border_w),
            fillcolor=lot_fill,
            opacity=opacity,
        )

        # Anti-collision label positioning: left side vs right side of corridor spine
        pos = "middle left" if x < mid_x else "middle right"

        # Smart label decision
        show_this_label = show_all_labels or is_major or is_dest or is_curr

        # Collision avoidance: check if close to previously displayed label
        if show_this_label and not (is_dest or is_curr):
            collision = False
            for lx, ly in displayed_label_coords:
                if abs(x - lx) < lot_w * 0.8 and abs(y - ly) < lot_h * 1.5:
                    collision = True
                    break
            if collision and not show_all_labels:
                show_this_label = False

        if show_this_label:
            displayed_label_coords.append((x, y))

        label_font_color = "#991B1B" if is_dest else ("#065F46" if is_curr else "#1E293B")
        label_font_size = 11 if (is_dest or is_curr) else (9 if is_major else 8)
        label_text = f"<b>{name}</b>" if (is_dest or is_curr or is_major) else name
        if show_coordinates:
            label_text += f"<br><span style='font-size:7px; color:#64748B;'>({x:.0f},{y:.0f})</span>"

        hover_card = (
            f"<b>🏬 {name}</b><br>"
            f"Category: {cat}<br>"
            f"Floor: {floor_title}<br>"
            f"Zone: {s.get('zone', 'Mall')}<br>"
            f"Crowd Level: {s.get('crowd_level', 'Low')}"
        )
        if show_coordinates:
            hover_card += f"<br>Exact Coordinates: ({x:.1f}, {y:.1f})"

        fig.add_trace(
            go.Scatter(
                x=[x],
                y=[y],
                mode="markers+text" if show_this_label else "markers",
                marker=dict(
                    size=7 if not (is_dest or is_curr) else 10,
                    color=lot_border,
                    symbol="circle",
                    opacity=opacity,
                ),
                text=[label_text] if show_this_label else None,
                textposition=pos,
                textfont=dict(size=label_font_size, color=label_font_color),
                hovertext=hover_card,
                hoverinfo="text",
                showlegend=False,
            )
        )

    # 4. Entrance Gates (Ground Floor)
    if floor_id == 0:
        for g in gates:
            gx, gy = g["x"], g["y"]
            fig.add_trace(
                go.Scatter(
                    x=[gx],
                    y=[gy],
                    mode="markers+text",
                    marker=dict(size=14, color="#10B981", symbol="square", line=dict(color="#064E3B", width=2)),
                    text=[f"<b>🚪 {g['name']}</b>"],
                    textposition="bottom center" if gy > 3000 else "top center",
                    textfont=dict(size=10, color="#065F46"),
                    hovertext=f"<b>{g['name']}</b><br>{g.get('description', '')}",
                    hoverinfo="text",
                    name="Mall Entrance Gate",
                    showlegend=True,
                )
            )

    # 5. Vertical Transport (Lifts, Escalators, Stairs)
    added_connectors = set()
    for vc in connectors:
        flr_str = str(floor_id)
        if flr_str in vc.get("coords", {}):
            vx, vy = vc["coords"][flr_str]
            vc_type = vc["type"]
            if vc_type == "elevator":
                icon, color, sym = "🛗", "#0284C7", "diamond"
            elif vc_type == "escalator":
                icon, color, sym = "🪜", "#3B82F6", "cross"
            else:
                icon, color, sym = "🚶", "#64748B", "circle"

            # Avoid duplicated label text
            name_key = f"{vc['name']}_{floor_id}"
            show_txt = name_key not in added_connectors
            added_connectors.add(name_key)

            fig.add_trace(
                go.Scatter(
                    x=[vx],
                    y=[vy],
                    mode="markers+text" if show_txt else "markers",
                    marker=dict(size=15, color=color, symbol=sym, line=dict(color="#FFFFFF", width=2)),
                    text=[f"<b>{icon} {vc['name']}</b>"] if show_txt else None,
                    textposition="middle right",
                    textfont=dict(size=10, color="#0369A1"),
                    hovertext=f"<b>{vc['name']}</b><br>{vc.get('description', '')}",
                    hoverinfo="text",
                    showlegend=False,
                )
            )

    # 6. Current Location Marker (Apple/Google Style Blue Dot with Halo)
    if current_location:
        curr_node = graph.get_node(current_location)
        if curr_node and curr_node.get("floor") == floor_id:
            cx, cy = curr_node["x"], curr_node["y"]
            # Outer Halo
            fig.add_trace(
                go.Scatter(
                    x=[cx],
                    y=[cy],
                    mode="markers",
                    marker=dict(size=28, color="#93C5FD", opacity=0.45, symbol="circle"),
                    hoverinfo="none",
                    showlegend=False,
                )
            )
            # Inner Blue Dot
            fig.add_trace(
                go.Scatter(
                    x=[cx],
                    y=[cy],
                    mode="markers+text",
                    marker=dict(size=14, color="#2563EB", symbol="circle", line=dict(color="#FFFFFF", width=2.5)),
                    text=["<b>📍 You Are Here</b>"],
                    textposition="top center",
                    textfont=dict(size=11, color="#1D4ED8"),
                    hovertext=f"<b>Current Location:</b> {curr_node.get('name')}",
                    hoverinfo="text",
                    name="Current Location",
                    showlegend=True,
                )
            )

    # 7. Navigation Route Overlay
    route_on_this_floor = []
    if route and route.get("nodes"):
        all_nodes = route["nodes"]
        floor_nodes = [n for n in all_nodes if n.get("floor") == floor_id]
        route_on_this_floor = floor_nodes

        if len(floor_nodes) >= 1:
            rx = [n["x"] for n in floor_nodes]
            ry = [n["y"] for n in floor_nodes]

            # Route polyline with navigation glow
            fig.add_trace(
                go.Scatter(
                    x=rx,
                    y=ry,
                    mode="lines",
                    line=dict(color="#3B82F6", width=6),
                    opacity=0.35,
                    hoverinfo="none",
                    showlegend=False,
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=rx,
                    y=ry,
                    mode="lines+markers",
                    line=dict(color="#EF4444", width=4.5),
                    marker=dict(size=8, color="#EF4444", symbol="circle"),
                    name="Active Route",
                    hoverinfo="text",
                    hovertext=[f"Waypoint {i+1}: {n.get('name')}" for i, n in enumerate(floor_nodes)],
                    showlegend=True,
                )
            )

            # Start point pin (if route starts on this floor)
            if all_nodes[0].get("floor") == floor_id:
                fig.add_trace(
                    go.Scatter(
                        x=[all_nodes[0]["x"]],
                        y=[all_nodes[0]["y"]],
                        mode="markers+text",
                        marker=dict(size=18, color="#10B981", symbol="circle", line=dict(color="#064E3B", width=2.5)),
                        text=["<b>🟢 START</b>"],
                        textposition="top center",
                        textfont=dict(color="#047857", size=12),
                        name="Route Origin",
                        hoverinfo="text",
                        hovertext=f"Start: {all_nodes[0].get('name')}",
                        showlegend=False,
                    )
                )

            # Destination goal pin (if route ends on this floor)
            if all_nodes[-1].get("floor") == floor_id:
                fig.add_trace(
                    go.Scatter(
                        x=[all_nodes[-1]["x"]],
                        y=[all_nodes[-1]["y"]],
                        mode="markers+text",
                        marker=dict(size=22, color="#DC2626", symbol="star", line=dict(color="#7F1D1D", width=2.5)),
                        text=["<b>🎯 DESTINATION</b>"],
                        textposition="top center",
                        textfont=dict(color="#991B1B", size=12),
                        name="Destination Pin",
                        hoverinfo="text",
                        hovertext=f"Goal: {all_nodes[-1].get('name')}",
                        showlegend=False,
                    )
                )

            # Multi-floor transition connector badges
            for i in range(len(all_nodes) - 1):
                c_node = all_nodes[i]
                n_node = all_nodes[i + 1]
                if c_node.get("floor") == floor_id and n_node.get("floor") != floor_id:
                    target_floor = n_node.get("floor")
                    target_str = "Ground Floor" if target_floor == 0 else f"Floor {target_floor}"
                    conn_name = c_node.get('name', 'Elevator').replace("(G)", "").replace("(F1)", "").replace("(F2)", "").strip()
                    fig.add_annotation(
                        x=c_node["x"],
                        y=c_node["y"],
                        text=f"<b>⬆️ Take {conn_name}<br>to {target_str}</b>",
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=1.2,
                        arrowcolor="#2563EB",
                        font=dict(size=10, color="#1D4ED8"),
                        bgcolor="#EFF6FF",
                        bordercolor="#3B82F6",
                        borderwidth=1.5,
                    )

    # 8. Visual Debug Mode Overlays
    if mode == "debug":
        # Corridor nodes
        dbg_nodes = [n for n in graph.nodes.values() if n.get("floor") == floor_id]
        if dbg_nodes:
            fig.add_trace(
                go.Scatter(
                    x=[n["x"] for n in dbg_nodes],
                    y=[n["y"] for n in dbg_nodes],
                    mode="markers+text",
                    marker=dict(size=5, color="#D97706", symbol="cross"),
                    text=[n["id"] for n in dbg_nodes],
                    textposition="bottom center",
                    textfont=dict(size=7, color="#92400E"),
                    hovertext=[f"ID: {n['id']}<br>Name: {n.get('name')}<br>Type: {n.get('type')}<br>Coords: ({n['x']:.1f}, {n['y']:.1f})" for n in dbg_nodes],
                    hoverinfo="text",
                    name="Debug Nodes",
                    showlegend=True,
                )
            )

    # 9. Dynamic Zoom / Range Selection
    if focus_route and route_on_this_floor and len(route_on_this_floor) >= 2:
        rx = [n["x"] for n in route_on_this_floor]
        ry = [n["y"] for n in route_on_this_floor]
        f_span_x = max(60.0, max(rx) - min(rx))
        f_span_y = max(60.0, max(ry) - min(ry))
        f_pad_x = f_span_x * 0.25
        f_pad_y = f_span_y * 0.25
        x_range = [min(rx) - f_pad_x, max(rx) + f_pad_x]
        y_range = [max(ry) + f_pad_y, min(ry) - f_pad_y]
    else:
        x_range = default_x_range
        y_range = default_y_range

    # 10. Aspect Ratio Locked Layout
    fig.update_layout(
        title=dict(
            text=f"<b>Ambience Mall Gurugram — {floor_title}</b>",
            x=0.5,
            xanchor="center",
            font=dict(size=17, color="#0F172A"),
        ),
        xaxis=dict(
            range=x_range,
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            scaleanchor="y",
            scaleratio=1,  # Strictly locks 1:1 aspect ratio to never distort physical layout
        ),
        yaxis=dict(
            range=y_range,
            showgrid=False,
            zeroline=False,
            showticklabels=False,
        ),
        plot_bgcolor="#F8FAFC",
        paper_bgcolor="#FFFFFF",
        margin=dict(l=10, r=10, t=45, b=10),
        height=680,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.06,
            xanchor="center",
            x=0.5,
            font=dict(size=10, color="#475569"),
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#E2E8F0",
            borderwidth=1,
        ),
    )

    return fig


def create_mall_floor_map(
    floor_number: int = 0,
    route_data: Optional[Dict[str, Any]] = None,
    highlight_store_id: Optional[str] = None,
    category_filter: Optional[str] = None,
    show_graph: bool = False,
    show_coords: bool = False,
    focus_route: bool = False,
    show_all_labels: bool = False,
    current_location_id: Optional[str] = None,
) -> go.Figure:
    """Backward-compatible wrapper around render_floor_map()."""
    loader = get_real_map_loader()
    floor_map = loader.get_floor_map(floor_number)
    if not floor_map:
        floor_map = loader.get_floor_map(0)

    mode = "debug" if show_graph else "user"
    return render_floor_map(
        floor_data=floor_map,
        route=route_data,
        current_location=current_location_id,
        destination=highlight_store_id,
        mode=mode,
        show_all_labels=show_all_labels,
        show_coordinates=show_coords,
        focus_route=focus_route,
        category_filter=category_filter,
    )

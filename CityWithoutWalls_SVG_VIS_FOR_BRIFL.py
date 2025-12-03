# CityWithoutWalls_SVG_VIS_FOR_BRIFL.py
# Enhanced BRIFL SVG dashboard for CityWithoutWalls
# - Multi-panel summary with colored bars, gauges, and sparkline trends
# - Shows role panel, stakeholder supports, capacity gauges, and last action

import svgwrite
import math
import CityWithoutWalls as prob

GRAPHIC_W = 1000
GRAPHIC_H = 700
PADDING = 18

TITLE_FS = "20px"
HEADER_FS = "14px"
BODY_FS = "12px"
SM_FS = "10px"

def _bar(dwg, x, y, w, h, pct, fill="lightblue", back="#eee", stroke="black"):
    # draw background then filled portion
    dwg.add(dwg.rect((x, y), (w, h), fill=back, stroke=stroke, stroke_width=1))
    fw = max(0, min(w, w * (pct/100.0)))
    dwg.add(dwg.rect((x, y), (fw, h), fill=fill))

def _small_gauge(dwg, cx, cy, r, pct, label):
    # draw circular gauge (visual proxy)
    # background circle
    dwg.add(dwg.circle(center=(cx, cy), r=r+6, fill="#fafafa", stroke="none"))
    # wedge-like bar as proxy for gauge
    bar_w = 80
    bar_h = 10
    _bar(dwg, cx - bar_w/2, cy + r*0.6, bar_w, bar_h, pct, fill="#ffd366", back="#ddd")
    dwg.add(dwg.text(f"{label}: {pct:.0f}%", insert=(cx, cy + r*0.6 + 28),
                     text_anchor="middle", font_size=SM_FS))

def _sparkline(dwg, x, y, w, h, data, stroke="#0b3b4a"):
    if not data:
        return
    # normalize to min/max range
    mn = min(data)
    mx = max(data)
    rng = mx - mn if mx != mn else 1
    pts = []
    for i, v in enumerate(data):
        vx = x + (i/(len(data)-1)) * w if len(data) > 1 else x
        vy = y + h - ((v - mn)/rng) * h
        pts.append((vx, vy))
    # polyline
    dwg.add(dwg.polyline(points=pts, fill="none", stroke=stroke, stroke_width=1.5))

def render_state(s, roles=None):
    dwg = svgwrite.Drawing(size=(f"{GRAPHIC_W}px", f"{GRAPHIC_H}px"), debug=False)

    # Background panel
    dwg.add(dwg.rect((0,0), (GRAPHIC_W, GRAPHIC_H), fill="#f6f8fb"))

    # Title
    dwg.add(dwg.text("CityWithoutWalls — Current State Dashboard", insert=(GRAPHIC_W/2, 28),
                     text_anchor="middle", font_size=TITLE_FS, fill="#123040"))

    left_col_x = PADDING
    left_col_w = 360
    mid_col_x = left_col_x + left_col_w + PADDING
    right_col_x = mid_col_x + 360 + PADDING

    # -------- LEFT PANEL: ROLE, TURN, Last Action, Key Metrics --------
    panel_x = left_col_x
    panel_y = 60
    panel_w = left_col_w
    panel_h = 300
    dwg.add(dwg.rect((panel_x, panel_y), (panel_w, panel_h), fill="#ffffff", rx=8, ry=8, stroke="#d6e0ea"))

    # Panel header
    dwg.add(dwg.text("Role & Turn", insert=(panel_x + 12, panel_y + 22), font_size=HEADER_FS, fill="#0b3b4a"))
    # Role name box
    dwg.add(dwg.rect((panel_x + 12, panel_y + 34), (panel_w - 24, 44), fill="#e9f6ff", stroke="#9fcbe6"))
    dwg.add(dwg.text(f"Current: {prob.int_to_name(s.turn)}", insert=(panel_x + panel_w/2, panel_y + 34 + 28),
                     text_anchor="middle", font_size="18px", fill="#0b3b4a"))

    # Last action box (multi-line safe)
    dwg.add(dwg.text("Last action:", insert=(panel_x + 12, panel_y + 90), font_size=SM_FS, fill="#234f59"))
    action_text = s.last_action if s.last_action else "No recent action"
    # split into manageable lines
    action_lines = str(action_text).split("\n")[:6]
    ay = panel_y + 108
    for ln in action_lines:
        dwg.add(dwg.text(ln[:72], insert=(panel_x + 12, ay), font_size=SM_FS, fill="#234f59"))
        ay += 14

    # Key metrics list
    km_y = panel_y + 140
    spacing = 18
    dwg.add(dwg.text(f"Round: {s.round}", insert=(panel_x + 12, km_y), font_size=SM_FS))
    dwg.add(dwg.text(f"Total Homeless: {s.homeless_population}", insert=(panel_x + 12, km_y + spacing), font_size=SM_FS))
    dwg.add(dwg.text(f"Shelter cap: {s.shelter_capacity}", insert=(panel_x + 12, km_y + 2*spacing), font_size=SM_FS))
    dwg.add(dwg.text(f"Transitional: {s.transitional_units}", insert=(panel_x + 12, km_y + 3*spacing), font_size=SM_FS))
    dwg.add(dwg.text(f"Permanent units: {s.permanent_units}", insert=(panel_x + 12, km_y + 4*spacing), font_size=SM_FS))

    # Debt & momentum mini
    dwg.add(dwg.text(f"Debt (k$): {s.debt:.0f}", insert=(panel_x + 12, panel_y + panel_h - 40), font_size=SM_FS))
    dwg.add(dwg.text(f"Policy momentum: {s.policy_momentum:.1f}", insert=(panel_x + 12, panel_y + panel_h - 22), font_size=SM_FS))

    # -------- MIDDLE PANEL: Population Breakdown & Trend --------
    mp_x = mid_col_x
    mp_y = 60
    mp_w = 360
    mp_h = 300
    dwg.add(dwg.rect((mp_x, mp_y), (mp_w, mp_h), fill="#ffffff", rx=8, ry=8, stroke="#d6e0ea"))
    dwg.add(dwg.text("Population Breakdown", insert=(mp_x + 12, mp_y + 22), font_size=HEADER_FS, fill="#0b3b4a"))

    # bars for subpopulations
    sub_x = mp_x + 16
    max_bar_w = mp_w - 40
    total = max(1, s.homeless_population)
    def draw_sub(y_offset, label, value, color):
        pct = (value / total) * 100.0
        _bar(dwg, sub_x + 80, mp_y + y_offset - 10, max_bar_w - 80, 16, pct, fill=color, back="#f0f6fb")
        dwg.add(dwg.text(f"{label}", insert=(sub_x, mp_y + y_offset + 2), font_size=SM_FS))
        dwg.add(dwg.text(f"{value}", insert=(sub_x + max_bar_w + 2, mp_y + y_offset + 2), font_size=SM_FS))

    draw_sub(40, "Families", s.pop_families, "#7fb7ff")
    draw_sub(80, "Youth", s.pop_youth, "#ffd366")
    draw_sub(120, "Chronic", s.pop_chronic, "#ffa3a3")
    draw_sub(160, "Veterans", s.pop_veterans, "#c1f0c1")

    # sparkline trend
    dwg.add(dwg.text("Trend (last 10):", insert=(mp_x + 12, mp_y + 200), font_size=SM_FS))
    _sparkline(dwg, mp_x + 20, mp_y + 208, mp_w - 40, 60, getattr(s, "trend_history", []), stroke="#0b3b4a")

    # -------- RIGHT PANEL: Capacity & Support gauges --------
    rp_x = right_col_x
    rp_y = 60
    rp_w = 360
    rp_h = 300
    dwg.add(dwg.rect((rp_x, rp_y), (rp_w, rp_h), fill="#ffffff", rx=8, ry=8, stroke="#d6e0ea"))
    dwg.add(dwg.text("Capacity & Stakeholder Support", insert=(rp_x + 12, rp_y + 22), font_size=HEADER_FS, fill="#0b3b4a"))

    # capacity gauges: percent filled vs capacity approximations
    cap_x = rp_x + 20
    cap_y = rp_y + 44
    # approximate occupancy rate = homeless / total capacity (shelter+transitional+permanent)
    total_units = max(1, s.shelter_capacity + s.transitional_units + s.permanent_units)
    occ_pct = max(0.0, min(100.0, (s.homeless_population / total_units) * 100.0))
    _small_gauge(dwg, cap_x + 60, cap_y + 40, 50, occ_pct, "Occupancy")

    # stakeholder support bars (use fallback if attributes missing)
    supports = [
        ("Neighborhoods", getattr(s, "support_neighborhoods", getattr(s, "public_support", 0.0)), "#7fb7ff"),
        ("Business", getattr(s, "support_business", getattr(s, "public_support", 0.0)), "#ffd366"),
        ("Medical", getattr(s, "support_medical", getattr(s, "public_support", 0.0)), "#ffa3a3"),
        ("Shelters", getattr(s, "support_shelters", getattr(s, "public_support", 0.0)), "#c1f0c1"),
        ("University", getattr(s, "support_university", getattr(s, "public_support", 0.0)), "#d0b3ff")
    ]
    sb_x = cap_x + 140
    sb_y = cap_y
    for i, (label, val, color) in enumerate(supports):
        yoff = sb_y + i*34
        dwg.add(dwg.text(label, insert=(sb_x, yoff), font_size=SM_FS))
        _bar(dwg, sb_x + 80, yoff - 12, 160, 12, float(val), fill=color, back="#f4f6f9")

    # public support big bar
    dwg.add(dwg.text("Public support", insert=(rp_x + 16, rp_y + rp_h - 80), font_size=SM_FS))
    _bar(dwg, rp_x + 16, rp_y + rp_h - 68, rp_w - 32, 18, getattr(s, "public_support", 0.0), fill="#9fd3c7", back="#eaf6f2")
    dwg.add(dwg.text(f"{getattr(s, 'public_support', 0.0):.1f}%", insert=(rp_x + rp_w/2, rp_y + rp_h - 48), text_anchor="middle", font_size=SM_FS))

    # economy & legal small metrics
    dwg.add(dwg.text(f"Economy index: {getattr(s, 'economy_index', 0.0):.1f}", insert=(rp_x + 16, rp_y + rp_h - 28), font_size=SM_FS))
    dwg.add(dwg.text(f"Legal pressure: {getattr(s, 'legal_pressure', 0.0):.1f}", insert=(rp_x + rp_w/2 + 10, rp_y + rp_h - 28), font_size=SM_FS))

    # ------- Bottom: Operator area (role-specific hint) -------
    bottom_x = left_col_x
    bottom_y = mp_y + mp_h + 24
    bottom_w = GRAPHIC_W - 2*PADDING
    bottom_h = GRAPHIC_H - bottom_y - PADDING
    dwg.add(dwg.rect((bottom_x, bottom_y), (bottom_w, bottom_h), fill="#ffffff", rx=8, ry=8, stroke="#d6e0ea"))
    dwg.add(dwg.text("Available Operators (Only shown for your role when using role-specific UI):",
                     insert=(bottom_x + 12, bottom_y + 20), font_size=HEADER_FS, fill="#0b3b4a"))

    # Suggest some operators based on current role (for display; actual availability enforced server-side)
    suggested_x = bottom_x + 12
    suggested_y = bottom_y + 42
    ops = []
    for op in prob.OPERATORS:
        try:
            # if operator has is_applicable method, check using a shallow copy of state with same turn
            if hasattr(op, 'is_applicable'):
                try:
                    if op.is_applicable(s):
                        ops.append(op.name)
                except Exception:
                    # ignore operator errors
                    pass
        except Exception:
            pass
    # fallback: choose first 8 operator names
    ops = list(dict.fromkeys(ops))[:8]
    if not ops:
        ops = [o.name for o in prob.OPERATORS[:8]]

    # draw operator badges
    bx = suggested_x
    by = suggested_y
    for i, opname in enumerate(ops):
        rx = bx + (i%4) * 240
        ry = by + (i//4) * 48
        dwg.add(dwg.rect((rx, ry), (220, 36), rx=6, ry=6, fill="#f0f8ff", stroke="#cfe8ff"))
        dwg.add(dwg.text(opname, insert=(rx + 10, ry + 22), font_size=SM_FS, fill="#063447"))

    # Accessibility title
    dwg.add(svgwrite.base.Title(f"CityWithoutWalls: Turn {prob.int_to_name(s.turn)}, Homeless {s.homeless_population}, Public support {getattr(s,'public_support',0.0):.1f}%"))

    return dwg.tostring()

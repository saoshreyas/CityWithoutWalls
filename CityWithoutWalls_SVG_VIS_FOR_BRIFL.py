# CityWithoutWalls_SVG_VIS_FOR_BRIFL.py — FIXED
# - Removed operator panel
# - Expanded graphic width so right panel is not cut off

import svgwrite
import math
import CityWithoutWalls as prob

GRAPHIC_W = 1200   # ← widened from 1000
GRAPHIC_H = 500    # ← reduced height since operators are removed
PADDING = 18

TITLE_FS = "20px"
HEADER_FS = "14px"
BODY_FS = "12px"
SM_FS = "10px"

def _bar(dwg, x, y, w, h, pct, fill="lightblue", back="#eee", stroke="black"):
    dwg.add(dwg.rect((x, y), (w, h), fill=back, stroke=stroke, stroke_width=1))
    fw = max(0, min(w, w * (pct/100.0)))
    dwg.add(dwg.rect((x, y), (fw, h), fill=fill))

def _small_gauge(dwg, cx, cy, r, pct, label):
    dwg.add(dwg.circle(center=(cx, cy), r=r+6, fill="#fafafa", stroke="none"))
    bar_w = 80
    bar_h = 10
    _bar(dwg, cx - bar_w/2, cy + r*0.6, bar_w, bar_h, pct, fill="#ffd366", back="#ddd")
    dwg.add(dwg.text(f"{label}: {pct:.0f}%", insert=(cx, cy + r*0.6 + 28),
                     text_anchor="middle", font_size=SM_FS))

def _sparkline(dwg, x, y, w, h, data, stroke="#0b3b4a"):
    if not data:
        return
    mn = min(data)
    mx = max(data)
    rng = mx - mn if mx != mn else 1
    pts = []
    for i, v in enumerate(data):
        vx = x + (i/(len(data)-1)) * w if len(data) > 1 else x
        vy = y + h - ((v - mn)/rng) * h
        pts.append((vx, vy))
    dwg.add(dwg.polyline(points=pts, fill="none", stroke=stroke, stroke_width=1.5))

def render_state(s, roles=None):
    dwg = svgwrite.Drawing(size=(f"{GRAPHIC_W}px", f"{GRAPHIC_H}px"), debug=False)
    dwg.add(dwg.rect((0,0), (GRAPHIC_W, GRAPHIC_H), fill="#f6f8fb"))

    # Title
    dwg.add(dwg.text("CityWithoutWalls — Current State Dashboard",
                     insert=(GRAPHIC_W/2, 28),
                     text_anchor="middle", font_size=TITLE_FS, fill="#123040"))

    # Updated column layout — wider per panel
    PANEL_W = 370
    left_col_x = PADDING
    mid_col_x = left_col_x + PANEL_W + PADDING
    right_col_x = mid_col_x + PANEL_W + PADDING

    # --------------- LEFT PANEL ----------------
    panel_y = 60
    panel_h = 300

    dwg.add(dwg.rect((left_col_x, panel_y), (PANEL_W, panel_h),
                     fill="#ffffff", rx=8, ry=8, stroke="#d6e0ea"))

    dwg.add(dwg.text("Role & Turn", insert=(left_col_x + 12, panel_y + 22),
                     font_size=HEADER_FS, fill="#0b3b4a"))

    dwg.add(dwg.rect((left_col_x + 12, panel_y + 34), (PANEL_W - 24, 44),
                     fill="#e9f6ff", stroke="#9fcbe6"))

    dwg.add(dwg.text(f"Current: {prob.int_to_name(s.turn)}",
                     insert=(left_col_x + PANEL_W/2, panel_y + 62),
                     text_anchor="middle", font_size="18px"))

    dwg.add(dwg.text("Last action:", insert=(left_col_x + 12, panel_y + 90),
                     font_size=SM_FS))

    action_text = s.last_action if s.last_action else "No recent action"
    ay = panel_y + 108
    for ln in str(action_text).split("\n")[:6]:
        dwg.add(dwg.text(ln[:72], insert=(left_col_x + 12, ay),
                         font_size=SM_FS))
        ay += 14

    km_y = panel_y + 140
    spacing = 18
    dwg.add(dwg.text(f"Round: {s.round}", insert=(left_col_x + 12, km_y), font_size=SM_FS))
    dwg.add(dwg.text(f"Shelter cap: {s.shelter_capacity}", insert=(left_col_x + 12, km_y + spacing), font_size=SM_FS))
    dwg.add(dwg.text(f"Transitional: {s.transitional_units}", insert=(left_col_x + 12, km_y + 2*spacing), font_size=SM_FS))
    dwg.add(dwg.text(f"Permanent units: {s.permanent_units}", insert=(left_col_x + 12, km_y + 3*spacing), font_size=SM_FS))

    dwg.add(dwg.text(f"Debt (k$): {s.debt:.0f}", insert=(left_col_x + 12, panel_y + panel_h - 60), font_size=SM_FS))
    dwg.add(dwg.text(f"Policy momentum: {s.policy_momentum:.1f}", insert=(left_col_x + 12, panel_y + panel_h - 42), font_size=SM_FS))

    # --------------- MIDDLE PANEL ----------------
    mp_y = 60
    mp_h = 300

    dwg.add(dwg.rect((mid_col_x, mp_y), (PANEL_W, mp_h),
                     fill="#ffffff", rx=8, ry=8, stroke="#d6e0ea"))

    dwg.add(dwg.text("Population Breakdown", insert=(mid_col_x + 12, mp_y + 22),
                     font_size=HEADER_FS))

    dwg.add(dwg.text(f"Total Homeless: {s.homeless_population}",
                     insert=(mid_col_x + 12, mp_y + 38), font_size=BODY_FS, style="font-weight:bold"))

    sub_x = mid_col_x + 16
    max_bar_w = PANEL_W - 40
    total = max(1, s.homeless_population)

    def draw_sub(y_offset, label, value, color):
        pct = (value / total) * 100.0
        _bar(dwg, sub_x + 80, mp_y + y_offset - 10,
             max_bar_w - 80, 16, pct, fill=color, back="#f0f6fb")
        dwg.add(dwg.text(label, insert=(sub_x, mp_y + y_offset + 2), font_size=SM_FS))
        dwg.add(dwg.text(f"{value}", insert=(sub_x + max_bar_w + 2, mp_y + y_offset + 2), font_size=SM_FS))

    draw_sub(60, "Families", s.pop_families, "#7fb7ff")
    draw_sub(100, "Youth", s.pop_youth, "#ffd366")
    draw_sub(140, "Chronic", s.pop_chronic, "#ffa3a3")
    draw_sub(180, "Veterans", s.pop_veterans, "#c1f0c1")

    dwg.add(dwg.text("Population Trend (last 10 moves):", insert=(mid_col_x + 12, mp_y + 200), font_size=SM_FS))
    _sparkline(dwg, mid_col_x + 20, mp_y + 208, PANEL_W - 40, 60,
               getattr(s, "trend_history", []))

    # --------------- RIGHT PANEL (NO MORE CUTOFF) ----------------
    rp_y = 60
    rp_h = 300

    dwg.add(dwg.rect((right_col_x, rp_y), (PANEL_W, rp_h),
                     fill="#ffffff", rx=8, ry=8, stroke="#d6e0ea"))

    dwg.add(dwg.text("Capacity & Stakeholder Support", insert=(right_col_x + 12, rp_y + 22),
                     font_size=HEADER_FS))

    # capacity gauge
    cap_x = right_col_x + 20
    cap_y = rp_y + 44
    total_units = max(1, s.shelter_capacity + s.transitional_units + s.permanent_units)
    occ_pct = max(0.0, min(100.0, (s.homeless_population / total_units) * 100.0))
    _small_gauge(dwg, cap_x + 60, cap_y + 40, 50, occ_pct, "Occupancy")

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

    dwg.add(dwg.text("Public support", insert=(right_col_x + 16, rp_y + rp_h - 80),
                     font_size=SM_FS))
    _bar(dwg, right_col_x + 16, rp_y + rp_h - 68,
         PANEL_W - 32, 18, getattr(s, "public_support", 0.0),
         fill="#9fd3c7", back="#eaf6f2")
    dwg.add(dwg.text(f"{getattr(s,'public_support',0.0):.1f}%",
                     insert=(right_col_x + PANEL_W/2, rp_y + rp_h - 48),
                     text_anchor="middle", font_size=SM_FS))

    dwg.add(dwg.text(f"Economy index: {getattr(s,'economy_index',0.0):.1f}",
                     insert=(right_col_x + 16, rp_y + rp_h - 28), font_size=SM_FS))
    dwg.add(dwg.text(f"Legal pressure: {getattr(s,'legal_pressure',0.0):.1f}",
                     insert=(right_col_x + PANEL_W/2 + 10, rp_y + rp_h - 28),
                     font_size=SM_FS))

    return dwg.tostring()

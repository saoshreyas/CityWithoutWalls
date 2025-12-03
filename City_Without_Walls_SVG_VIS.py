'''City_Without_Walls_SVG_VIS.py

SVG visualization for City Without Walls game.
Renders city state with metrics dashboards for each stakeholder role.
'''

import svgwrite

def render_state(state, roles=None):
    """Generate SVG visualization of current city state
    
    Args:
        state: Current game state
        roles: List of role numbers for the viewing player (for role-specific views)
    
    Returns:
        SVG string
    """
    
    # Determine viewing role (if any)
    viewing_role = roles[0] if roles and len(roles) > 0 else None
    
    # Create SVG document
    dwg = svgwrite.Drawing(size=('1000px', '800px'))
    
    # Background
    dwg.add(dwg.rect(insert=(0, 0), size=('100%', '100%'), fill='#f8f9fa'))
    
    # Title
    title_text = f"City Without Walls - Turn {state.turn}/24 ({state.season})"
    dwg.add(dwg.text(title_text, insert=(500, 30), text_anchor='middle',
                     font_size='24px', font_weight='bold', fill='#2c3e50'))
    
    # Main metrics panel (left side)
    render_main_metrics(dwg, state)
    
    # Homeless population visualization (center)
    render_population_viz(dwg, state)
    
    # Stakeholder status (right side)
    render_stakeholder_status(dwg, state, viewing_role)
    
    # Progress toward goal (bottom)
    render_goal_progress(dwg, state)
    
    # Role-specific information
    if viewing_role is not None:
        render_role_specific_info(dwg, state, viewing_role)
    
    return dwg.tostring()


def render_main_metrics(dwg, state):
    """Render main city metrics panel"""
    x, y = 20, 60
    
    # Panel background
    dwg.add(dwg.rect(insert=(x, y), size=(280, 200), fill='white', 
                     stroke='#dee2e6', stroke_width=2, rx=8))
    
    # Title
    dwg.add(dwg.text("City Metrics", insert=(x+140, y+25), text_anchor='middle',
                     font_size='16px', font_weight='bold', fill='#495057'))
    
    # Metrics
    metrics = [
        ("Homeless Population:", f"{state.homeless_total:,}"),
        ("  Unsheltered:", f"{state.unsheltered:,}"),
        ("  Sheltered:", f"{state.sheltered:,}"),
        ("  Transitional:", f"{state.transitional:,}"),
        ("", ""),
        ("Public Support:", f"{state.public_support}%"),
        ("Trust Index:", f"{state.trust_index}"),
        ("Coordination:", f"{state.service_coordination}%"),
    ]
    
    current_y = y + 50
    for label, value in metrics:
        if label:  # Skip empty lines
            dwg.add(dwg.text(label, insert=(x+15, current_y),
                           font_size='12px', fill='#495057'))
            
            # Color code values
            color = '#495057'
            if 'Support' in label or 'Trust' in label or 'Coordination' in label:
                val = int(value.rstrip('%')) if '%' in value else int(value)
                color = '#28a745' if val >= 60 else '#ffc107' if val >= 40 else '#dc3545'
            
            dwg.add(dwg.text(value, insert=(x+265, current_y), text_anchor='end',
                           font_size='12px', font_weight='bold', fill=color))
        current_y += 20


def render_population_viz(dwg, state):
    """Render homeless population visualization"""
    x, y = 320, 60
    width, height = 360, 200
    
    # Panel background
    dwg.add(dwg.rect(insert=(x, y), size=(width, height), fill='white',
                     stroke='#dee2e6', stroke_width=2, rx=8))
    
    # Title
    dwg.add(dwg.text("Homeless Population Breakdown", insert=(x+width/2, y+25),
                     text_anchor='middle', font_size='16px', font_weight='bold',
                     fill='#495057'))
    
    # Stacked bar chart
    bar_x = x + 40
    bar_y = y + 60
    bar_width = width - 80
    bar_height = 60
    
    total = state.homeless_total
    if total > 0:
        unsheltered_width = (state.unsheltered / total) * bar_width
        sheltered_width = (state.sheltered / total) * bar_width
        transitional_width = (state.transitional / total) * bar_width
        
        # Unsheltered (red)
        dwg.add(dwg.rect(insert=(bar_x, bar_y), 
                        size=(unsheltered_width, bar_height),
                        fill='#dc3545'))
        
        # Sheltered (yellow)
        dwg.add(dwg.rect(insert=(bar_x + unsheltered_width, bar_y),
                        size=(sheltered_width, bar_height),
                        fill='#ffc107'))
        
        # Transitional (green)
        dwg.add(dwg.rect(insert=(bar_x + unsheltered_width + sheltered_width, bar_y),
                        size=(transitional_width, bar_height),
                        fill='#28a745'))
    
    # Legend
    legend_y = bar_y + bar_height + 30
    legends = [
        ('#dc3545', 'Unsheltered', state.unsheltered),
        ('#ffc107', 'Sheltered', state.sheltered),
        ('#28a745', 'Transitional', state.transitional),
    ]
    
    for i, (color, label, count) in enumerate(legends):
        legend_x = x + 40 + (i * 110)
        
        dwg.add(dwg.rect(insert=(legend_x, legend_y-10), size=(15, 15), fill=color))
        dwg.add(dwg.text(f"{label}:", insert=(legend_x+20, legend_y),
                        font_size='11px', fill='#495057'))
        dwg.add(dwg.text(f"{count:,}", insert=(legend_x+20, legend_y+15),
                        font_size='11px', font_weight='bold', fill=color))


def render_stakeholder_status(dwg, state, viewing_role):
    """Render stakeholder resources and status"""
    x, y = 700, 60
    width, height = 280, 480
    
    # Panel background
    dwg.add(dwg.rect(insert=(x, y), size=(width, height), fill='white',
                     stroke='#dee2e6', stroke_width=2, rx=8))
    
    # Title
    dwg.add(dwg.text("Stakeholders", insert=(x+width/2, y+25),
                     text_anchor='middle', font_size='16px', font_weight='bold',
                     fill='#495057'))
    
    # List each stakeholder
    from City_Without_Walls import ROLE_NAMES
    
    current_y = y + 50
    for role_num, role_name in enumerate(ROLE_NAMES):
        # Highlight if this is the viewing role
        if role_num == viewing_role:
            dwg.add(dwg.rect(insert=(x+10, current_y-15), size=(width-20, 75),
                           fill='#e7f3ff', stroke='#0066cc', stroke_width=2, rx=4))
        
        # Role name
        name_display = role_name if len(role_name) <= 20 else role_name[:17] + "..."
        dwg.add(dwg.text(name_display, insert=(x+15, current_y),
                        font_size='13px', font_weight='bold', fill='#2c3e50'))
        
        # Budget
        budget_color = '#28a745' if state.budgets[role_num] >= 200 else '#ffc107' if state.budgets[role_num] >= 100 else '#dc3545'
        dwg.add(dwg.text(f"Budget: ${state.budgets[role_num]}K",
                        insert=(x+15, current_y+18),
                        font_size='11px', fill=budget_color))
        
        # Influence
        influence_color = '#28a745' if state.influence[role_num] >= 60 else '#ffc107' if state.influence[role_num] >= 40 else '#dc3545'
        dwg.add(dwg.text(f"Influence: {state.influence[role_num]}",
                        insert=(x+15, current_y+33),
                        font_size='11px', fill=influence_color))
        
        # Turn indicator
        if role_num == state.current_role_num:
            dwg.add(dwg.text("â—€ CURRENT TURN", insert=(x+15, current_y+48),
                           font_size='11px', font_weight='bold', fill='#0066cc'))
        
        current_y += 85


def render_goal_progress(dwg, state):
    """Render progress toward goal"""
    x, y = 20, 280
    width = 660
    
    # Panel background
    dwg.add(dwg.rect(insert=(x, y), size=(width, 120), fill='white',
                     stroke='#dee2e6', stroke_width=2, rx=8))
    
    # Title
    dwg.add(dwg.text("Goal: Reduce homelessness to 9,095 (15% reduction)",
                     insert=(x+width/2, y+25), text_anchor='middle',
                     font_size='16px', font_weight='bold', fill='#495057'))
    
    # Progress bar
    bar_x = x + 40
    bar_y = y + 50
    bar_width = width - 80
    bar_height = 30
    
    from City_Without_Walls import INITIAL_HOMELESS, GOAL_HOMELESS
    
    # Background bar
    dwg.add(dwg.rect(insert=(bar_x, bar_y), size=(bar_width, bar_height),
                     fill='#e9ecef', stroke='#ced4da', stroke_width=1, rx=4))
    
    # Progress fill
    progress = max(0, (INITIAL_HOMELESS - state.homeless_total) / (INITIAL_HOMELESS - GOAL_HOMELESS))
    progress_width = min(bar_width, progress * bar_width)
    
    # Color based on progress
    if progress >= 1.0:
        fill_color = '#28a745'  # Green - goal achieved
    elif progress >= 0.75:
        fill_color = '#20c997'  # Teal - great progress
    elif progress >= 0.5:
        fill_color = '#ffc107'  # Yellow - moderate progress
    else:
        fill_color = '#fd7e14'  # Orange - limited progress
    
    dwg.add(dwg.rect(insert=(bar_x, bar_y), size=(progress_width, bar_height),
                     fill=fill_color, rx=4))
    
    # Goal marker
    goal_x = bar_x + bar_width
    dwg.add(dwg.line(start=(goal_x, bar_y-5), end=(goal_x, bar_y+bar_height+5),
                     stroke='#28a745', stroke_width=3))
    dwg.add(dwg.text("GOAL", insert=(goal_x, bar_y-10), text_anchor='middle',
                     font_size='10px', font_weight='bold', fill='#28a745'))
    
    # Progress text
    reduction_pct = ((INITIAL_HOMELESS - state.homeless_total) / INITIAL_HOMELESS) * 100
    progress_text = f"{reduction_pct:.1f}% reduction achieved  â€¢  Current: {state.homeless_total:,}  â€¢  Goal: {GOAL_HOMELESS:,}"
    dwg.add(dwg.text(progress_text, insert=(x+width/2, bar_y+bar_height+25),
                     text_anchor='middle', font_size='12px', fill='#495057'))


def render_role_specific_info(dwg, state, role_num):
    """Render role-specific metrics and information"""
    x, y = 20, 420
    width = 660
    
    # Panel background
    dwg.add(dwg.rect(insert=(x, y), size=(width, 120), fill='#e7f3ff',
                     stroke='#0066cc', stroke_width=2, rx=8))
    
    from City_Without_Walls import ROLE_NAMES, NEIGHBORHOODS, BUSINESS, MEDICAL, SHELTERS, UNIVERSITY
    
    role_name = ROLE_NAMES[role_num]
    
    # Title
    dwg.add(dwg.text(f"Your Role: {role_name}", insert=(x+width/2, y+25),
                     text_anchor='middle', font_size='16px', font_weight='bold',
                     fill='#0066cc'))
    
    # Role-specific metrics
    metrics = []
    
    if role_num == NEIGHBORHOODS:
        metrics = [
            ("Property Value Index:", f"{state.property_value_index}"),
            ("Safety Perception:", f"{state.safety_perception}/100"),
            ("Your Goal:", "Maintain property values, reduce visible homelessness"),
        ]
    elif role_num == BUSINESS:
        metrics = [
            ("Customer Traffic:", f"{state.customer_traffic}"),
            ("Cleanliness Index:", f"{state.cleanliness_index}/100"),
            ("Your Goal:", "Maintain business environment, demonstrate compassion"),
        ]
    elif role_num == MEDICAL:
        metrics = [
            ("Health Outcomes:", f"{state.health_outcome_index}/100"),
            ("Clinic Capacity:", f"{state.clinic_capacity} patients/month"),
            ("Your Goal:", "Improve health outcomes, provide quality care"),
        ]
    elif role_num == SHELTERS:
        metrics = [
            ("Bed Capacity:", f"{state.bed_capacity} beds"),
            ("Waitlist:", f"{state.waitlist} people"),
            ("Housing Placements:", f"{state.housing_placements} people"),
            ("Your Goal:", "Reduce waitlist, increase capacity, house people"),
        ]
    elif role_num == UNIVERSITY:
        metrics = [
            ("Reputation:", f"{state.reputation_score}/100"),
            ("Community Engagement:", f"{state.community_engagement}/100"),
            ("Volunteers:", f"{state.volunteer_count} active"),
            ("Your Goal:", "Research solutions, engage community, maintain reputation"),
        ]
    
    # Display metrics
    current_y = y + 55
    for label, value in metrics:
        dwg.add(dwg.text(label, insert=(x+30, current_y),
                        font_size='13px', fill='#0066cc'))
        dwg.add(dwg.text(value, insert=(x+width-30, current_y), text_anchor='end',
                        font_size='13px', font_weight='bold', fill='#004085'))
        current_y += 22


def render_recent_actions(dwg, state):
    """Render recent actions taken"""
    if not state.actions_taken:
        return
    
    x, y = 20, 560
    width = 660
    
    # Panel background
    dwg.add(dwg.rect(insert=(x, y), size=(width, 100), fill='white',
                     stroke='#dee2e6', stroke_width=2, rx=8))
    
    # Title
    dwg.add(dwg.text("Recent Actions", insert=(x+15, y+25),
                     font_size='14px', font_weight='bold', fill='#495057'))
    
    # List last 3 actions
    current_y = y + 50
    for action in state.actions_taken[-3:]:
        # Truncate if too long
        display_action = action if len(action) <= 90 else action[:87] + "..."
        dwg.add(dwg.text(f"â€¢ {display_action}", insert=(x+15, current_y),
                        font_size='11px', fill='#6c757d'))
        current_y += 20

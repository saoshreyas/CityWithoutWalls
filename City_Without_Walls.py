'''City_Without_Walls.py

A SOLUZION5 educational strategy game simulating urban homelessness policy.
Players assume stakeholder roles with competing interests to collaboratively
address a homelessness crisis, learning about wicked problems and trade-offs.

Based on the City Without Walls design document.
Compatible with Web_SOLUZION5 multi-session system.
'''

#<METADATA>
SOLUZION_VERSION = "5.0"
PROBLEM_NAME = "City Without Walls"
PROBLEM_VERSION = "1.0"
PROBLEM_AUTHORS = ['Design Doc Team']
PROBLEM_CREATION_DATE = "19-Nov-2025"
PROBLEM_DESC = '''City Without Walls is an educational strategy game simulating 
the complexity of addressing urban homelessness. Players assume roles of different 
city stakeholdersâ€”each with competing interests, limited resources, and conflicting 
valuesâ€”to collectively address a homelessness crisis. The game illustrates the 
"wicked problem" nature of homelessness through gameplay that reveals how 
individual decisions create system-wide consequences, often with unintended outcomes.

Goal: Reduce homelessness from 10,700 to 9,095 (15% reduction) over 24 turns 
while maintaining public support and balancing stakeholder interests.'''
#</METADATA>

#<COMMON_DATA>
# Stakeholder role constants
NEIGHBORHOODS = 0
BUSINESS = 1
MEDICAL = 2
SHELTERS = 3
UNIVERSITY = 4

ROLE_NAMES = ["Neighborhoods Coalition", "Business District", "Medical Quarter", 
              "Shelters & Services", "University Consortium"]

# Initial city statistics
INITIAL_HOMELESS = 10700
INITIAL_UNSHELTERED = 4500
INITIAL_SHELTERED = 3800
INITIAL_TRANSITIONAL = 2400
INITIAL_AT_RISK = 38000
GOAL_HOMELESS = 9095  # 15% reduction

# Budget constants (in thousands)
INITIAL_BUDGETS = {
    NEIGHBORHOODS: 750,
    BUSINESS: 900,
    MEDICAL: 600,
    SHELTERS: 500,
    UNIVERSITY: 400
}

INITIAL_INFLUENCE = {
    NEIGHBORHOODS: 65,
    BUSINESS: 70,
    MEDICAL: 55,
    SHELTERS: 50,
    UNIVERSITY: 45
}
#</COMMON_DATA>

#<COMMON_CODE>
DEBUG = True

from soluzion5 import Basic_State, Basic_Operator as Operator, ROLES_List, add_to_next_transition
import Select_Roles as sr
import random

class State(Basic_State):
    def __init__(self, old=None):
        if old == None:
            # Initial state
            self.turn = 1
            self.season = "Winter"
            
            # Homeless population tracking
            self.homeless_total = INITIAL_HOMELESS
            self.unsheltered = INITIAL_UNSHELTERED
            self.sheltered = INITIAL_SHELTERED
            self.transitional = INITIAL_TRANSITIONAL
            self.at_risk = INITIAL_AT_RISK
            
            # Citywide metrics
            self.public_support = 50  # Percentage
            self.trust_index = 42
            self.stigma_index = 68
            self.service_coordination = 35  # Percentage
            
            # Stakeholder resources
            self.budgets = INITIAL_BUDGETS.copy()
            self.influence = INITIAL_INFLUENCE.copy()
            
            # Stakeholder-specific metrics
            self.property_value_index = 100
            self.safety_perception = 45
            self.customer_traffic = 100
            self.cleanliness_index = 52
            self.health_outcome_index = 38
            self.clinic_capacity = 240
            self.bed_capacity = 3800
            self.waitlist = 420
            self.volunteer_count = 280
            self.reputation_score = 75
            self.community_engagement = 40
            
            # Turn management
            self.current_role_num = NEIGHBORHOODS
            self.current_role = ROLE_NAMES[self.current_role_num]
            self.whose_turn = self.current_role_num
            
            # Game progress tracking
            self.actions_taken = []
            self.major_events = []
            self.housing_placements = 0
            
            # Win tracking
            self.win = ""
            self.winner = -1
            
        else:
            # Copy from old state
            self.turn = old.turn
            self.season = old.season
            
            self.homeless_total = old.homeless_total
            self.unsheltered = old.unsheltered
            self.sheltered = old.sheltered
            self.transitional = old.transitional
            self.at_risk = old.at_risk
            
            self.public_support = old.public_support
            self.trust_index = old.trust_index
            self.stigma_index = old.stigma_index
            self.service_coordination = old.service_coordination
            
            self.budgets = old.budgets.copy()
            self.influence = old.influence.copy()
            
            self.property_value_index = old.property_value_index
            self.safety_perception = old.safety_perception
            self.customer_traffic = old.customer_traffic
            self.cleanliness_index = old.cleanliness_index
            self.health_outcome_index = old.health_outcome_index
            self.clinic_capacity = old.clinic_capacity
            self.bed_capacity = old.bed_capacity
            self.waitlist = old.waitlist
            self.volunteer_count = old.volunteer_count
            self.reputation_score = old.reputation_score
            self.community_engagement = old.community_engagement
            
            self.current_role_num = old.current_role_num
            self.current_role = old.current_role
            self.whose_turn = old.whose_turn
            
            self.actions_taken = old.actions_taken.copy()
            self.major_events = old.major_events.copy()
            self.housing_placements = old.housing_placements
            
            self.win = old.win
            self.winner = old.winner
    
    def __str__(self):
        txt = f"=== CITY WITHOUT WALLS - Turn {self.turn}/24 ({self.season}) ===\n\n"
        
        txt += f"HOMELESS POPULATION: {self.homeless_total:,} (Goal: {GOAL_HOMELESS:,})\n"
        txt += f"  Unsheltered: {self.unsheltered:,} | Sheltered: {self.sheltered:,}\n"
        txt += f"  At Risk: {self.at_risk:,}\n\n"
        
        txt += f"CITYWIDE METRICS:\n"
        txt += f"  Public Support: {self.public_support}% | Trust: {self.trust_index}\n"
        txt += f"  Service Coordination: {self.service_coordination}%\n\n"
        
        txt += f"CURRENT TURN: {self.current_role}\n\n"
        
        txt += f"STAKEHOLDER STATUS:\n"
        for role_num, role_name in enumerate(ROLE_NAMES):
            txt += f"  {role_name}:\n"
            txt += f"    Budget: ${self.budgets[role_num]}K | Influence: {self.influence[role_num]}\n"
        
        if self.actions_taken:
            txt += f"\nRECENT ACTIONS: {len(self.actions_taken)}\n"
            for action in self.actions_taken[-3:]:
                txt += f"  - {action}\n"
        
        return txt
    
    def __eq__(self, s):
        return self.turn == s.turn and self.homeless_total == s.homeless_total
    
    def __hash__(self):
        return hash((self.turn, self.homeless_total))
    
    def advance_turn(self):
        """Move to next role's turn or next month"""
        news = State(self)
        
        # Cycle through roles
        news.current_role_num = (self.current_role_num + 1) % len(ROLE_NAMES)
        news.current_role = ROLE_NAMES[news.current_role_num]
        news.whose_turn = news.current_role_num
        
        # If we've cycled back to first role, advance the turn
        if news.current_role_num == 0:
            news.turn = self.turn + 1
            news.apply_monthly_updates()
        
        return news
    
    def apply_monthly_updates(self):
        """Apply automatic updates at start of new month"""
        # Update season
        season_map = {1: "Winter", 4: "Spring", 7: "Summer", 10: "Fall"}
        month = ((self.turn - 1) % 12) + 1
        for start_month, season in season_map.items():
            if month >= start_month:
                self.season = season
        
        # Natural decay
        self.public_support = max(0, self.public_support - 1)
        
        # Random small fluctuations
        self.at_risk += random.randint(-200, 300)
        self.at_risk = max(30000, min(45000, self.at_risk))
    
    def can_afford(self, role_num, cost, influence_cost):
        """Check if role can afford an action"""
        return (self.budgets[role_num] >= cost and 
                self.influence[role_num] >= influence_cost)
    
    def spend_resources(self, role_num, cost, influence_cost):
        """Deduct resources for an action"""
        self.budgets[role_num] -= cost
        self.influence[role_num] -= influence_cost
    
    def is_goal(self):
        """Check if game is complete"""
        return self.turn >= 24 or self.public_support <= 25
    
    def goal_message(self):
        """Generate end game message"""
        if self.turn >= 24:
            reduction = ((INITIAL_HOMELESS - self.homeless_total) / INITIAL_HOMELESS) * 100
            
            if self.homeless_total <= GOAL_HOMELESS and self.public_support >= 45:
                return f"SUCCESS! You reduced homelessness by {reduction:.1f}% to {self.homeless_total:,} while maintaining public support at {self.public_support}%. The city has made meaningful progress through collaborative policy."
            elif self.homeless_total <= GOAL_HOMELESS:
                return f"Partial Success. You reached the numerical goal ({self.homeless_total:,}) but public support fell to {self.public_support}%. The political viability of these policies is uncertain."
            elif reduction > 0:
                return f"Incomplete Progress. You reduced homelessness by {reduction:.1f}% but fell short of the 15% goal. Final count: {self.homeless_total:,}. The complexity of this wicked problem remains."
            else:
                return f"Challenge Unmet. Homelessness increased to {self.homeless_total:,}. This demonstrates why homelessness is called a 'wicked problem' - there are no simple solutions."
        else:
            return f"Game Over. Public support collapsed to {self.public_support}%. Political backlash has made further intervention impossible."

SESSION = None

def update_turn(news, role_num):
    """Update whose turn it is"""
    news.current_role_num = role_num
    news.current_role = ROLE_NAMES[role_num]
    news.whose_turn = role_num

#</COMMON_CODE>

#<OPERATORS>

# NEIGHBORHOODS COALITION OPERATORS
def neighborhoods_can_media_campaign(s):
    return s.can_afford(NEIGHBORHOODS, 100, 10) and s.public_support < 70

def neighborhoods_media_campaign(s):
    news = State(s)
    news.spend_resources(NEIGHBORHOODS, 100, 10)
    
    # Primary effects
    news.public_support = min(100, news.public_support + 8)
    news.stigma_index = min(100, news.stigma_index + 5)
    
    # Secondary effects
    news.unsheltered = int(news.unsheltered * 0.99)  # Slight reduction via government response
    news.homeless_total = news.unsheltered + news.sheltered + news.transitional
    
    news.actions_taken.append(f"Turn {s.turn}: Neighborhoods launched media campaign")
    add_to_next_transition(
        "Neighborhoods Coalition launches 'Community Voices for Safe Streets' campaign. " +
        "Public support increases but some worry about stigmatizing messaging.",
        news
    )
    
    return news.advance_turn()

def neighborhoods_can_outreach(s):
    return s.can_afford(NEIGHBORHOODS, 60, 8) and s.public_support > 45

def neighborhoods_outreach(s):
    news = State(s)
    news.spend_resources(NEIGHBORHOODS, 60, 8)
    
    # Primary effects
    news.trust_index = min(100, news.trust_index + 6)
    news.volunteer_count += 25
    news.public_support = min(100, news.public_support + 3)
    
    # Delayed effect - reduce homelessness over time
    reduction = int(news.homeless_total * 0.03)
    news.homeless_total -= reduction
    news.unsheltered -= int(reduction * 0.7)
    news.sheltered += int(reduction * 0.3)
    
    news.actions_taken.append(f"Turn {s.turn}: Neighborhoods sponsored outreach program")
    add_to_next_transition(
        "Neighborhood Ambassadors program begins weekly rounds with coffee and resource guides. " +
        "Trust building takes time but connections are forming.",
        news
    )
    
    return news.advance_turn()

# BUSINESS DISTRICT OPERATORS
def business_can_job_training(s):
    return s.can_afford(BUSINESS, 180, 8) and s.turn > 3

def business_job_training(s):
    news = State(s)
    news.spend_resources(BUSINESS, 180, 8)
    
    # Primary effects
    news.public_support = min(100, news.public_support + 6)
    news.at_risk = int(news.at_risk * 0.97)  # Prevention
    
    # Delayed homelessness reduction
    reduction = int(news.homeless_total * 0.025)
    news.homeless_total -= reduction
    news.transitional += int(reduction * 0.5)
    news.unsheltered -= int(reduction * 0.5)
    
    news.customer_traffic = min(150, news.customer_traffic + 3)
    
    news.actions_taken.append(f"Turn {s.turn}: Business funded job-readiness programs")
    add_to_next_transition(
        "Business District launches 'Pathways to Work' offering resume help, interview coaching, " +
        "and job placement. Early participants show promise.",
        news
    )
    
    return news.advance_turn()

def business_can_ambassadors(s):
    return s.can_afford(BUSINESS, 90, 6)

def business_ambassadors(s):
    news = State(s)
    news.spend_resources(BUSINESS, 90, 6)
    
    # Primary effects
    news.trust_index = min(100, news.trust_index + 8)
    news.volunteer_count += 40
    news.cleanliness_index = min(100, news.cleanliness_index + 8)
    
    # Better service connections
    news.sheltered += 50
    news.unsheltered -= 50
    news.waitlist = max(0, news.waitlist - 30)
    
    news.actions_taken.append(f"Turn {s.turn}: Business deployed street ambassadors")
    add_to_next_transition(
        "Street ambassadors in branded jackets patrol downtown with resource maps and " +
        "non-judgmental presence. Some develop trusted relationships.",
        news
    )
    
    return news.advance_turn()

# MEDICAL QUARTER OPERATORS
def medical_can_clinic(s):
    return s.can_afford(MEDICAL, 200, 0) and s.turn > 2

def medical_clinic(s):
    news = State(s)
    news.spend_resources(MEDICAL, 200, 0)
    
    # Primary effects
    news.clinic_capacity += 120
    news.health_outcome_index = min(100, news.health_outcome_index + 12)
    news.public_support = min(100, news.public_support + 5)
    news.trust_index = min(100, news.trust_index + 8)
    
    # Health stability enables housing stability
    reduction = int(news.homeless_total * 0.03)
    news.homeless_total -= reduction
    news.transitional += reduction
    
    news.actions_taken.append(f"Turn {s.turn}: Medical opened low-barrier health clinic")
    add_to_next_transition(
        "Walk-in clinic opens treating infections, managing chronic conditions without judgment. " +
        "'We meet people where they are,' says the director.",
        news
    )
    
    return news.advance_turn()

def medical_can_mental_health(s):
    return s.can_afford(MEDICAL, 280, 0) and s.turn > 4

def medical_mental_health(s):
    news = State(s)
    news.spend_resources(MEDICAL, 280, 0)
    
    # Primary effects
    news.health_outcome_index = min(100, news.health_outcome_index + 18)
    news.public_support = min(100, news.public_support + 7)
    
    # Addresses root causes - significant long-term impact
    reduction = int(news.homeless_total * 0.04)
    news.homeless_total -= reduction
    news.transitional += int(reduction * 0.6)
    news.sheltered += int(reduction * 0.3)
    news.unsheltered -= int(reduction * 0.9)
    
    news.housing_placements += 60
    
    news.actions_taken.append(f"Turn {s.turn}: Medical launched mental health & addiction services")
    add_to_next_transition(
        "Integrated treatment teams provide therapy, psychiatric care, and peer support. " +
        "Trauma-informed approach recognizes root causes of homelessness.",
        news
    )
    
    return news.advance_turn()

# SHELTERS & SERVICES OPERATORS
def shelters_can_volunteers(s):
    return s.can_afford(SHELTERS, 50, 5) and s.public_support > 45

def shelters_volunteers(s):
    news = State(s)
    news.spend_resources(SHELTERS, 50, 5)
    
    # Primary effects
    news.volunteer_count = int(news.volunteer_count * 1.10)
    news.public_support = min(100, news.public_support + 5)
    news.service_coordination = min(100, news.service_coordination + 5)
    
    # Increased capacity
    reduction = int(news.homeless_total * 0.02)
    news.homeless_total -= reduction
    news.sheltered += reduction
    news.unsheltered -= reduction
    
    news.actions_taken.append(f"Turn {s.turn}: Shelters launched volunteer recruitment")
    add_to_next_transition(
        "'Be the Change' campaign brings new volunteers into shelters. " +
        "They discover the complexity behind headlines.",
        news
    )
    
    return news.advance_turn()

def shelters_can_expand_beds(s):
    return s.can_afford(SHELTERS, 150, 0)

def shelters_expand_beds(s):
    news = State(s)
    news.spend_resources(SHELTERS, 150, 0)
    
    # Primary effects
    news.bed_capacity += 180
    news.waitlist = max(0, news.waitlist - 90)
    news.public_support = max(0, news.public_support - 3)  # Some see as "enabling"
    
    # Move people from unsheltered to sheltered
    news.sheltered += 180
    news.unsheltered = max(0, news.unsheltered - 180)
    news.homeless_total = news.unsheltered + news.sheltered + news.transitional
    
    news.actions_taken.append(f"Turn {s.turn}: Shelters expanded bed capacity")
    add_to_next_transition(
        "New shelter beds fill immediately. Families no longer sleeping in cars. " +
        "But demand continues to exceed supply.",
        news
    )
    
    return news.advance_turn()

def shelters_can_housing_navigation(s):
    return s.can_afford(SHELTERS, 120, 10) and s.turn > 3

def shelters_housing_navigation(s):
    news = State(s)
    news.spend_resources(SHELTERS, 120, 10)
    
    # Primary effects - helps people exit homelessness
    news.public_support = min(100, news.public_support + 6)
    news.waitlist = max(0, news.waitlist - 60)
    news.service_coordination = min(100, news.service_coordination + 8)
    
    # Significant reduction through housing placements
    reduction = int(news.homeless_total * 0.03)
    news.homeless_total -= reduction
    news.sheltered -= int(reduction * 0.5)
    news.transitional -= int(reduction * 0.3)
    news.unsheltered -= int(reduction * 0.2)
    news.housing_placements += reduction
    
    news.actions_taken.append(f"Turn {s.turn}: Shelters implemented housing navigation")
    add_to_next_transition(
        "Housing navigators have relationships with landlords willing to rent to high-barrier tenants. " +
        "They troubleshoot problems before eviction occurs.",
        news
    )
    
    return news.advance_turn()

# UNIVERSITY CONSORTIUM OPERATORS
def university_can_outreach(s):
    return s.can_afford(UNIVERSITY, 40, 5)

def university_outreach(s):
    news = State(s)
    news.spend_resources(UNIVERSITY, 40, 5)
    
    # Primary effects
    news.volunteer_count += 60
    news.community_engagement = min(100, news.community_engagement + 12)
    news.public_support = min(100, news.public_support + 3)
    news.service_coordination = min(100, news.service_coordination + 5)
    
    # Better connections to services
    news.sheltered += 30
    news.unsheltered -= 30
    
    news.actions_taken.append(f"Turn {s.turn}: University launched student outreach")
    add_to_next_transition(
        "Social work and public health students staff resource tables and build relationships. " +
        "Service learning deepens understanding.",
        news
    )
    
    return news.advance_turn()

def university_can_research(s):
    return s.can_afford(UNIVERSITY, 90, 10) and s.turn > 4

def university_research(s):
    news = State(s)
    news.spend_resources(UNIVERSITY, 90, 10)
    
    # Primary effects - improves all interventions
    news.service_coordination = min(100, news.service_coordination + 15)
    news.reputation_score = min(100, news.reputation_score + 8)
    
    # Better evidence base improves effectiveness
    news.public_support = min(100, news.public_support + 4)
    
    # All stakeholders gain influence from better information
    for role in range(len(ROLE_NAMES)):
        news.influence[role] = min(100, news.influence[role] + 5)
    
    news.actions_taken.append(f"Turn {s.turn}: University conducted policy research")
    add_to_next_transition(
        "Research teams analyze outcomes and publish findings. Evidence shows Housing First " +
        "reduces costs by $15K/person/year. Policymakers take note.",
        news
    )
    
    return news.advance_turn()

def university_can_pilot(s):
    return s.can_afford(UNIVERSITY, 150, 20) and s.turn > 6

def university_pilot(s):
    news = State(s)
    news.spend_resources(UNIVERSITY, 150, 20)
    
    # Primary effects - tests innovative approach
    news.reputation_score = min(100, news.reputation_score + 12)
    news.community_engagement = min(100, news.community_engagement + 10)
    
    # Successful pilot (60% chance represented by moderate impact)
    news.public_support = min(100, news.public_support + 5)
    reduction = int(news.homeless_total * 0.025)
    news.homeless_total -= reduction
    news.transitional += reduction
    
    news.actions_taken.append(f"Turn {s.turn}: University piloted innovative intervention")
    add_to_next_transition(
        "Pilot program tests new approach with rigorous evaluation. Early results promising - " +
        "may unlock new strategies for entire city.",
        news
    )
    
    return news.advance_turn()

# Create all operators
OPERATORS = [
    # Neighborhoods Coalition
    Operator("Launch Media Campaign (+8% public support, -1% homelessness)",
             neighborhoods_can_media_campaign,
             neighborhoods_media_campaign),
    
    Operator("Sponsor Neighborhood Outreach (+6 trust, +25 volunteers, -3% homelessness)",
             neighborhoods_can_outreach,
             neighborhoods_outreach),
    
    # Business District
    Operator("Fund Job-Readiness Programs (+6% support, -2.5% homelessness long-term)",
             business_can_job_training,
             business_job_training),
    
    Operator("Deploy Street Ambassadors (+8 trust, +40 volunteers, better connections)",
             business_can_ambassadors,
             business_ambassadors),
    
    # Medical Quarter
    Operator("Open Low-Barrier Health Clinic (+12 health outcomes, -3% homelessness)",
             medical_can_clinic,
             medical_clinic),
    
    Operator("Launch Mental Health Services (+18 health, -4% homelessness, addresses root causes)",
             medical_can_mental_health,
             medical_mental_health),
    
    # Shelters & Services
    Operator("Launch Volunteer Recruitment (+10% volunteers, +5% support, -2% homelessness)",
             shelters_can_volunteers,
             shelters_volunteers),
    
    Operator("Expand Emergency Shelter Capacity (+180 beds, -90 waitlist)",
             shelters_can_expand_beds,
             shelters_expand_beds),
    
    Operator("Implement Housing Navigation (-3% homelessness, +placements, +6% support)",
             shelters_can_housing_navigation,
             shelters_housing_navigation),
    
    # University Consortium
    Operator("Launch Student Outreach (+60 volunteers, +12 engagement, better connections)",
             university_can_outreach,
             university_outreach),
    
    Operator("Conduct Policy Research (+15% coordination, +5 influence all, better evidence)",
             university_can_research,
             university_research),
    
    Operator("Pilot Innovative Intervention (test new approach, +12 reputation, -2.5% homelessness)",
             university_can_pilot,
             university_pilot),
]

#</OPERATORS>

#<INITIAL_STATE>
def create_initial_state():
    return State()
#</INITIAL_STATE>

#<ROLES>
ROLES = ROLES_List([
    {'name': 'Neighborhoods Coalition', 'min': 1, 'max': 1},
    {'name': 'Business District', 'min': 1, 'max': 1},
    {'name': 'Medical Quarter', 'min': 1, 'max': 1},
    {'name': 'Shelters & Services', 'min': 1, 'max': 1},
    {'name': 'University Consortium', 'min': 1, 'max': 1},
    {'name': 'Observer', 'min': 0, 'max': 10}
])
ROLES.min_num_of_roles_to_play = 5
ROLES.max_num_of_roles_to_play = 15
#</ROLES>

#<STATE_VIS>
BRIFL_SVG = True
render_state = None

def use_BRIFL_SVG():
    global render_state
    from City_Without_Walls_SVG_VIS import render_state

DEBUG_VIS = False  # Set to True to auto-launch browser tabs for testing
#</STATE_VIS>

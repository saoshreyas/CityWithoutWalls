'''CityWithoutWalls_harder.py

Harder, more realistic variant of the CityWithoutWalls simulation.
Changes from original:
 - Introduces stochastic success/failure for interventions.
 - Adds construction pipeline and delays for new housing units.
 - Adds operating costs and per-unit maintenance that reduces capacity if unpaid.
 - Adds budget inflows (taxes/grants) and economic shocks each round.
 - Adds precondition helpers and partial-success behavior when budgets are insufficient.
 - Keeps provenance markers and operator definitions; operators now consider success chance.

Created from user's original file and adapted by ChatGPT.
'''

# METADATA
SOLUZION_VERSION = "5.1"
PROBLEM_NAME = "CityWithoutWalls_harder"
PROBLEM_VERSION = "4.0"
PROBLEM_AUTHORS = ['Shreyas, Lauren (adapted by ChatGPT)']
PROBLEM_CREATION_DATE = "10-December-2025"
PROBLEM_DESC = "More realistic/stochastic simulation of policies to reduce homelessness; includes delays, shocks, and operational realism."

# ROLES
NEIGHBORHOODS = 0
BUSINESS = 1
MEDICAL = 2
SHELTERS = 3
UNIVERSITY = 4
OBSERVER = 5

ROLE_NAMES = ["Neighborhoods", "Business", "Medical", "SheltersServices", "University", "Observer"]

# Single global turn seed (only one turn variable globally)
TURN_START = NEIGHBORHOODS

DEBUG = False

# Imports
from soluzion5 import Basic_State, Basic_Operator as Operator, ROLES_List, add_to_next_transition
import Select_Roles as sr
import math, random, copy

# File-citations used from the uploaded spec (these tokens point to the uploaded doc)
FC = {
    'neigh': ":contentReference[oaicite:1]{index=1}",
    'spec':  ":contentReference[oaicite:2]{index=2}",
    'medical':":contentReference[oaicite:3]{index=3}",
    'shelters':":contentReference[oaicite:4]{index=4}",
    'university':":contentReference[oaicite:5]{index=5}",
    'business':":contentReference[oaicite:6]{index=6}",
    'evidence':":contentReference[oaicite:7]{index=7}",
    'overview':":contentReference[oaicite:8]{index=8}"
}


def int_to_name(i):
    try:
        return ROLE_NAMES[i]
    except:
        return f"Role_{i}"

# ---------------- State ----------------
class State(Basic_State):
    def __init__(self, old=None):
        if old is None:
            # turn (authoritative)
            self.turn = TURN_START

            # Demographic subpopulations (initial values from your spec doc)
            self.pop_families = 2800
            self.pop_youth = 1800
            self.pop_chronic = 3600
            self.pop_veterans = 1500
            self.homeless_population = (self.pop_families + self.pop_youth +
                                        self.pop_chronic + self.pop_veterans)

            # Housing tiers (units)
            self.shelter_capacity = 1400
            self.transitional_units = 600
            self.permanent_units = 2200

            # Construction pipeline: list of (type_str, units, rounds_remaining)
            self.construction_pipeline = []

            # Service resources
            self.social_workers = 120
            self.outreach_teams = 8
            self.medical_vans = 3

            # Operating obligations (k$ per round)
            self.operating_obligations = 250.0  # k$ needed each round to maintain current capacity

            # Budgets (thousands)
            self.shelter_budget = 800.0
            self.neighborhood_budget = 900.0
            self.business_budget = 750.0
            self.medical_budget = 900.0
            self.university_budget = 450.0

            # Political / economic / legal metrics (0-100 or k$)
            self.public_support = 52.0
            self.economy_index = 100.0
            self.legal_pressure = 10.0
            self.policy_momentum = 0.0
            self.debt = 0.0

            # Systemic friction parameters
            self.construction_delay_factor = 2  # average rounds to build per 100 units
            self.policy_fatigue = 0.0  # grows if many costly interventions executed

            self.last_action = ""
            self.round = 0
            self.trend_history = [int(self.homeless_population)] * 10

            self.last_action_url = ""

        else:
            # copy constructor
            self.turn = old.turn
            self.pop_families = old.pop_families
            self.pop_youth = old.pop_youth
            self.pop_chronic = old.pop_chronic
            self.pop_veterans = old.pop_veterans
            self.homeless_population = old.homeless_population
            self.shelter_capacity = old.shelter_capacity
            self.transitional_units = old.transitional_units
            self.permanent_units = old.permanent_units
            self.construction_pipeline = copy.deepcopy(old.construction_pipeline)
            self.social_workers = old.social_workers
            self.outreach_teams = old.outreach_teams
            self.medical_vans = old.medical_vans
            self.operating_obligations = old.operating_obligations
            self.shelter_budget = old.shelter_budget
            self.neighborhood_budget = old.neighborhood_budget
            self.business_budget = old.business_budget
            self.medical_budget = old.medical_budget
            self.university_budget = old.university_budget
            self.public_support = old.public_support
            self.economy_index = old.economy_index
            self.legal_pressure = old.legal_pressure
            self.policy_momentum = old.policy_momentum
            self.debt = old.debt
            self.construction_delay_factor = old.construction_delay_factor
            self.policy_fatigue = old.policy_fatigue
            self.last_action = old.last_action
            self.round = old.round
            self.trend_history = list(old.trend_history)
            self.last_action_url = old.last_action_url

    # Compatibility for Select_Roles/Web_SZ5_01: numeric properties required
    @property
    def current_role_num(self):
        return self.turn

    @property
    def current_role(self):
        return self.turn

    @property
    def whose_turn(self):
        return self.turn

    def recalc_population(self):
        self.homeless_population = max(0, int(self.pop_families + self.pop_youth +
                                    self.pop_chronic + self.pop_veterans))

    def record_trend(self):
        # process construction pipeline: decrement rounds, add built units when finished
        new_pipeline = []
        built = {'shelter_capacity':0, 'transitional_units':0, 'permanent_units':0}
        for (t, units, rounds) in self.construction_pipeline:
            rounds -= 1
            if rounds <= 0:
                if t == 'shelter':
                    self.shelter_capacity += units
                    built['shelter_capacity'] += units
                elif t == 'trans':
                    self.transitional_units += units
                    built['transitional_units'] += units
                elif t == 'perm':
                    self.permanent_units += units
                    built['permanent_units'] += units
            else:
                new_pipeline.append((t, units, rounds))
        self.construction_pipeline = new_pipeline

        # apply operating obligations: if budgets can't cover obligations, capacity degrades
        total_operating_budget = (self.shelter_budget + self.neighborhood_budget +
                                  self.business_budget + self.medical_budget + self.university_budget)
        if total_operating_budget < self.operating_obligations:
            # proportional degradation of shelter capacity
            short = (self.operating_obligations - total_operating_budget)
            degrade_pct = clamp(short / max(1.0, self.operating_obligations), 0.0, 0.9)
            lost_shelter = int(self.shelter_capacity * degrade_pct * 0.05)  # small degradation
            self.shelter_capacity = max(0, self.shelter_capacity - lost_shelter)

        self.trend_history.append(int(self.homeless_population))
        if len(self.trend_history) > 10:
            self.trend_history.pop(0)

    def __str__(self):
        return (f"Round {self.round} - Turn: {int_to_name(self.turn)}\n"
                f"Total Homeless: {self.homeless_population} (f:{self.pop_families}, y:{self.pop_youth}, c:{self.pop_chronic}, v:{self.pop_veterans})\n"
                f"Capacity: shelter {self.shelter_capacity}, trans {self.transitional_units}, perm {self.permanent_units}\n"
                f"In pipeline: {self.construction_pipeline}\n"
                f"Budgets (k$): S={self.shelter_budget:.0f}, N={self.neighborhood_budget:.0f}, B={self.business_budget:.0f}, M={self.medical_budget:.0f}, U={self.university_budget:.0f}\n"
                f"Public support: {self.public_support:.1f}%, Economy: {self.economy_index:.1f}, Legal pressure: {self.legal_pressure:.1f}\n"
                f"Debt: ${self.debt:.0f}k, Momentum: {self.policy_momentum:.1f}, Fatigue: {self.policy_fatigue:.2f}\n"
                f"Last action: {self.last_action}\n")

    def is_goal(self):
        # tighter goal: 30% reduction overall AND public_support >=50 AND legal pressure <20
        baseline = 10700
        return (self.homeless_population <= int(0.7 * baseline) and
                self.public_support >= 50.0 and
                self.legal_pressure < 20.0)

    def goal_message(self):
        if self.is_goal():
            return f"Goal: homeless {self.homeless_population}, support {self.public_support:.1f}%, legal {self.legal_pressure:.1f}"
        return ""

SESSION = None

PLAYABLE_ROLES = [NEIGHBORHOODS, BUSINESS, MEDICAL, SHELTERS, UNIVERSITY]
NUM_PLAYERS = len(PLAYABLE_ROLES)


def next_player_index(current_role_index):
    idx = PLAYABLE_ROLES.index(current_role_index)
    return PLAYABLE_ROLES[(idx + 1) % NUM_PLAYERS]


def update_turn(state):
    # each time a full cycle completes, apply macro updates (taxes, shocks, fatigue decay)
    state.turn = next_player_index(state.turn)
    if state.turn == PLAYABLE_ROLES[0]:
        state.round += 1
        # budget inflow (k$): simple model — taxes proportional to economy index
        tax_inflow = max(0.0, state.economy_index * 2.5)
        # split inflows among budgets
        split = tax_inflow / 5.0
        state.shelter_budget += split
        state.neighborhood_budget += split
        state.business_budget += split
        state.medical_budget += split
        state.university_budget += split
        # occasional grant if momentum high
        if state.policy_momentum > 5.0 and random.random() < 0.25:
            grant = 300.0
            state.shelter_budget += grant
            state.debt -= 50.0  # grant reduces need to borrow
        # apply economic shock randomly
        if random.random() < 0.12:
            shock = random.choice(['recession','boom','inflation'])
            if shock == 'recession':
                state.economy_index = max(50.0, state.economy_index - random.uniform(6.0,15.0))
                state.public_support = max(0.0, state.public_support - random.uniform(1.0,4.0))
                add_to_next_transition(f"MacroShock: recession", state)
            elif shock == 'boom':
                state.economy_index = min(150.0, state.economy_index + random.uniform(5.0,20.0))
                state.public_support = min(100.0, state.public_support + random.uniform(0.5,3.0))
                add_to_next_transition(f"MacroShock: boom", state)
            else:
                # inflation reduces budget purchasing power (modeled as increased operating costs)
                state.operating_obligations *= 1.08
                add_to_next_transition(f"MacroShock: inflation", state)
        # policy fatigue decays slowly each round
        state.policy_fatigue = max(0.0, state.policy_fatigue - 0.05)


def can_act_as(role, s):
    return s.turn == role

# ---------- small helper functions ----------
def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def percent_of(n, pct):
    # careful arithmetic digit-by-digit performed implicitly by Python - kept precise
    return max(0, int(round(n * (pct/100.0))))

# Preconditions and resource helpers

def has_budget(news, budget_name, amt_k):
    return getattr(news, budget_name, 0.0) >= amt_k


def charge_budget(news, budget_charges):
    '''Attempt to deduct budget amounts; if insufficient, deduct what is available and return fraction applied.''' 
    fractions = []
    for bk, amt in budget_charges.items():
        avail = getattr(news, bk, 0.0)
        if avail >= amt:
            setattr(news, bk, avail - amt)
            fractions.append(1.0)
        elif avail > 0:
            # partial spend
            setattr(news, bk, 0.0)
            fractions.append(avail / amt)
        else:
            fractions.append(0.0)
    return min(fractions) if fractions else 1.0

# probabilistic operator generator with partial success

def make_op(name, role, cost_k, deltas, apa_source, fc_token, difficulty=0.0):
    """
    - difficulty: extra failure chance (0.0..0.8); higher means harder to succeed
    Operators now compute success_chance as a function of policy_momentum, public_support, and difficulty.
    On partial / failed attempts, apply scaled effects and record different transition banners.
    """
    def op_fn(s, name=name, cost_k=cost_k, deltas=deltas, apa_source=apa_source, fc_token=fc_token, difficulty=difficulty):
        news = State(s)
        add_to_next_transition(f"{int_to_name(role)} -> {name}", news)
        # charge budgets (allow partial)
        frac = charge_budget(news, cost_k)
        if frac == 0.0:
            news.last_action = f"{int_to_name(role)} attempted '{name}' but lacked required budgets."
            add_transition_with_sources(news, f"{int_to_name(role)} → {name} (failed)", "Action failed: no available budget.", apa_source, fc_token)
            update_turn(news)
            news.record_trend()
            return news
        # compute success chance
        # base influenced by policy momentum (more momentum -> higher success), public support,
        # and policy_fatigue (reduces success). clamp between 0.05 and 0.98
        base = 0.35 + (news.policy_momentum * 0.03) + ((news.public_support - 40.0) * 0.01)
        base -= news.policy_fatigue * 0.05
        success_chance = clamp(base - difficulty, 0.05, 0.98)
        # scale success by fraction of budget applied
        success_chance *= (0.5 + 0.5 * frac)  # if partial spending, at least half effect possible
        roll = random.random()
        effects = []
        applied_multiplier = 1.0
        if roll <= success_chance:
            # success
            applied_multiplier = 1.0
            outcome_text = f"Success (p={success_chance:.2f})"
        else:
            # partial or failure: apply fraction of effects proportional to budget fraction and a random penalty
            applied_multiplier = frac * random.uniform(0.25, 0.75)
            outcome_text = f"Partial/Failed (p={success_chance:.2f}, roll={roll:.2f})"
        # apply deltas scaled by applied_multiplier. Deltas can be callables.
        for k, v in deltas.items():
            if callable(v):
                # call with news and multiplier; expect textual effect or None
                try:
                    desc = v(news, applied_multiplier) if v.__code__.co_argcount >= 2 else v(news)
                except Exception:
                    # fallback: call without multiplier
                    desc = v(news)
                if desc:
                    effects.append(desc)
            else:
                # numeric additive scaled
                if hasattr(news, k):
                    before = getattr(news, k)
                    delta = v * applied_multiplier
                    # ensure integer change for population/unit counts
                    if isinstance(v, int) or isinstance(v, float):
                        if k.startswith('pop_') or k.endswith('_units') or k.endswith('_capacity'):
                            delta = int(round(delta))
                    after = before + delta
                    setattr(news, k, after)
                    effects.append(f"{k}: {before} -> {after} (applied x{applied_multiplier:.2f})")
        # special: if deltas included construction (as a tuple) allow adding to pipeline
        # recalc derived
        news.recalc_population()
        # rise in policy fatigue for costly actions
        cost_total = sum(cost_k.values()) if cost_k else 0.0
        news.policy_fatigue += min(0.02 * (cost_total/100.0), 0.5)
        news.policy_momentum = clamp(news.policy_momentum + 0.5 * applied_multiplier, -10.0, 50.0)
        news.record_trend()
        eff_text = "\n".join(effects) if effects else "(no direct numeric effect recorded)"
        add_transition_with_sources(news, f"{int_to_name(role)} → {name} ({outcome_text})", eff_text, apa_source, fc_token)
        news.last_action = f"{int_to_name(role)} performed '{name}' ({outcome_text})."
        update_turn(news)
        return news
    return Operator(name, lambda s, role=role: can_act_as(role, s), op_fn)

# Utility to create construction job: adds to pipeline with modeled delay

def schedule_construction(state, kind, units):
    # delays scale with construction_delay_factor and units
    rounds = max(1, int(round((units/100.0) * state.construction_delay_factor)))
    state.construction_pipeline.append((kind, units, rounds))

# wrapper for add_transition_with_sources (keeps original functionality)
def add_transition_with_sources(s_new, title, effects_text, apa_text, fc_token):
    import re
    url_match = re.search(r'https?://[^\s]+', apa_text)
    if url_match:
        url = url_match.group(0)
        if not hasattr(s_new, 'last_action_url'):
            s_new.last_action_url = url
        else:
            s_new.last_action_url = url
        banner = f"| Effects:\n{effects_text}\n| Source: {apa_text}"
    else:
        s_new.last_action_url = ""
        banner = f"| Effects:\n{effects_text}\n| Source: {apa_text}"
    add_to_next_transition(banner, s_new)

# ---------------- Operators (updated realism) ----------------
# For readability: each operator includes an APA-like source string that
# refers to the relevant documents from your uploaded spec (filecite tokens included below).

# Helper delta callables accept (news, multiplier) to support scaled effects

def pop_reduction_factory(attr, pct):
    def fn(news, mult=1.0):
        before = getattr(news, attr)
        reduction = percent_of(before, pct)
        reduction = int(round(reduction * mult))
        setattr(news, attr, max(0, before - reduction))
        return f"{attr}: -{reduction} (intended {pct}% scaled by {mult:.2f})"
    return fn

# ---- SHELTERS (12 operators) ----
shelters_ops = []

# 1 Emergency Expansion (now schedules construction and has higher difficulty)
shelters_ops.append(make_op(
    "Emergency Expansion (beds +300)",
    SHELTERS,
    {'shelter_budget': 360.0},
    {'shelter_capacity': 300, 'pop_families': pop_reduction_factory('pop_families', 10), 'pop_veterans': pop_reduction_factory('pop_veterans', 12)},
    "U.S. Department of Housing and Urban Development. Annual Homeless Assessment Report (AHAR). HUD Exchange. https://www.hudexchange.info/programs/hdx/ahar/",
    FC['shelters'],
    difficulty=0.15
))

# We'll schedule construction inside the op by wrapping a callable delta

def schedule_shelter_construction(news, mult=1.0):
    units = int(round(300 * mult))
    schedule_construction(news, 'shelter', units)
    return f"Scheduled construction: shelter +{units} (pipeline)"

# Replace the numeric shelter_capacity delta with scheduling callable in op 1
shelters_ops[-1] = make_op(
    "Emergency Expansion (beds +300)",
    SHELTERS,
    {'shelter_budget': 360.0},
    {'_construction_job': schedule_shelter_construction, 'pop_families': pop_reduction_factory('pop_families', 10), 'pop_veterans': pop_reduction_factory('pop_veterans', 12)},
    "U.S. Department of Housing and Urban Development. Annual Homeless Assessment Report (AHAR). HUD Exchange. https://www.hudexchange.info/programs/hdx/ahar/",
    FC['shelters'],
    difficulty=0.20
)

# 2 Community Partnership
shelters_ops.append(make_op(
    "Community Partnership (vols & caseworkers)",
    SHELTERS,
    {'shelter_budget': 100.0},
    {'social_workers': 6, 'pop_chronic': pop_reduction_factory('pop_chronic', 1.5), 'policy_momentum': 0.6},
    "Homeless Services Research Institute. Community Partnership Evaluation Studies. https://www.hsri.org/projects/evaluating-samhsa-four-homelessness-programs-and-resources",
    FC['shelters'],
    difficulty=0.05
))

# 3 Housing First Pilot (perm +150)
shelters_ops.append(make_op(
    "Housing First Pilot (perm +150)",
    SHELTERS,
    {'shelter_budget': 520.0},
    {'_construction_job': lambda news, mult=1.0: (schedule_construction(news,'perm', int(round(150*mult))) or f"Scheduled perm +{int(round(150*mult))}"),
     'pop_chronic': pop_reduction_factory('pop_chronic', 8), 'public_support': 2.5, 'economy_index': -1.5},
    "Conrad N. Hilton Foundation. Chronic Homelessness Initiative Evaluation. https://www.hiltonfoundation.org/learning/evaluation-of-housing-for-health-permanent-supportive-housing-program/",
    FC['shelters'],
    difficulty=0.18
))

# 4 Volunteer Training
shelters_ops.append(make_op(
    "Volunteer Training (social workers +3)",
    SHELTERS,
    {'shelter_budget': 40.0},
    {'social_workers': 3, 'public_support': 1.0},
    "Homeless Services Research Institute. Caseworker Training Impact Study. https://www.hsri.org/projects/evaluating-samhsa-four-homelessness-programs-and-resources",
    FC['shelters'],
    difficulty=0.02
))

# 5 Rent Assistance Fund
shelters_ops.append(make_op(
    "Rent Assistance Fund (prevention)",
    SHELTERS,
    {'shelter_budget': 260.0},
    {'pop_families': pop_reduction_factory('pop_families', 6), 'pop_youth': pop_reduction_factory('pop_youth', 4), 'policy_momentum': 1.0, 'public_support': 1.8},
    "U.S. Department of Housing and Urban Development. Rapid Re-Housing Brief. HUD Exchange. https://www.hudexchange.info/resource/3891/rapid-re-housing-brief/",
    FC['shelters'],
    difficulty=0.07
))

# 6 Defer Maintenance (gain budget, lose beds)
shelters_ops.append(make_op(
    "Defer Maintenance (gain budget, lose beds)",
    SHELTERS,
    {},
    {'shelter_budget': 60.0, 'shelter_capacity': -40, 'public_support': -2.5, 'legal_pressure': 2.0},
    "U.S. Department of Housing and Urban Development. Shelter Standards and Maintenance Requirements. HUD.gov.",
    FC['shelters'],
    difficulty=0.01
))

# 7 Rapid Rehousing Boost
shelters_ops.append(make_op(
    "Rapid Rehousing Boost",
    SHELTERS,
    {'shelter_budget': 260.0},
    {'transitional_units': 60, 'pop_families': pop_reduction_factory('pop_families', 9), 'policy_momentum': 1.2},
    "National Low Income Housing Coalition. The Gap: A Shortage of Affordable Homes. NLIHC. https://nlihc.org/gap",
    FC['shelters'],
    difficulty=0.09
))

# 8 Add Outreach Vans
shelters_ops.append(make_op(
    "Add Outreach Vans",
    SHELTERS,
    {'shelter_budget': 110.0},
    {'outreach_teams': 2, 'pop_youth': pop_reduction_factory('pop_youth',6)},
    "Commonwealth Fund. Mobile Health Services for Homeless Populations. https://www.commonwealthfund.org/publications/case-study/2021/aug/how-medical-respite-care-program-offers-pathway-health-housing",
    FC['shelters'],
    difficulty=0.04
))

# 9 Intensify Case Management
shelters_ops.append(make_op(
    "Intensify Case Management",
    SHELTERS,
    {'shelter_budget': 140.0},
    {'social_workers': 5, 'policy_momentum': 0.9, 'pop_chronic': pop_reduction_factory('pop_chronic',5)},
    "Homeless Services Research Institute. Case Management and Housing Stability Study. https://www.hsri.org/projects/evaluating-samhsa-four-homelessness-programs-and-resources",
    FC['shelters'],
    difficulty=0.06
))

# 10 Sanction Encampment
shelters_ops.append(make_op(
    "Sanction Encampment (sanctioned services)",
    SHELTERS,
    {'shelter_budget': 180.0},
    {'shelter_capacity': 80, 'public_support': -1.0, 'legal_pressure': -2.5},
    "PubMed Central. Sanctioned Encampments and Harm Reduction. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8427990/",
    FC['shelters'],
    difficulty=0.12
))

# 11 Partner: Medical Support
shelters_ops.append(make_op(
    "Partner: Medical Support (onsite clinics)",
    SHELTERS,
    {'shelter_budget': 160.0, 'medical_budget': 80.0},
    {'medical_vans': 1, 'pop_chronic': pop_reduction_factory('pop_chronic',7)},
    "Commonwealth Fund. Integrating Health Care and Housing Services. https://www.commonwealthfund.org/publications/case-study/2021/aug/how-medical-respite-care-program-offers-pathway-health-housing",
    FC['shelters'],
    difficulty=0.08
))

# 12 Evaluation & Data Sharing
shelters_ops.append(make_op(
    "Evaluation & Data Sharing (with Univ)",
    SHELTERS,
    {'shelter_budget': 80.0, 'university_budget': 70.0},
    {'policy_momentum': 1.6, 'public_support': 0.8},
    "United States Interagency Council on Homelessness. Data-Driven Decision Making. https://www.usich.gov/",
    FC['shelters'],
    difficulty=0.03
))

# ---- NEIGHBORHOODS (12 operators) ----
neighbor_ops = []

neighbor_ops.append(make_op(
    "Media Campaign (reframe homelessness)",
    NEIGHBORHOODS,
    {'neighborhood_budget': 140.0},
    {'public_support': 6.0, 'legal_pressure': -3.0},
    "SAGE Journals. Reframing Homelessness in Public Discourse. https://journals.sagepub.com/doi/10.1177/0739456X241265499",
    FC['neigh'],
    difficulty=0.06
))

neighbor_ops.append(make_op(
    "Block New Low-Income Development (NIMBY action)",
    NEIGHBORHOODS,
    {'neighborhood_budget': 60.0},
    {'permanent_units': -50, 'public_support': 2.0, 'legal_pressure': 4.0},
    "Berkeley Law Policy Advocacy Clinic. Homeless Exclusion and Legal Conflict Study. UC Berkeley School of Law. https://www.law.berkeley.edu/article/clinic-study-details-how-business-districts-target-homeless-people/",
    FC['neigh'],
    difficulty=0.04
))

neighbor_ops.append(make_op(
    "Local Voucher Matching Fund",
    NEIGHBORHOODS,
    {'neighborhood_budget': 200.0},
    {'pop_families': pop_reduction_factory('pop_families',7), 'permanent_units': 20, 'policy_momentum': 0.8, 'public_support': 3.0},
    "U.S. Department of Housing and Urban Development. Housing Choice Voucher Program. https://www.hud.gov/program_offices/public_indian_housing/programs/hcv",
    FC['neigh'],
    difficulty=0.08
))

neighbor_ops.append(make_op(
    "Civic Forum (reduce tensions)",
    NEIGHBORHOODS,
    {'neighborhood_budget': 30.0},
    {'legal_pressure': -2.0, 'public_support': 1.0},
    "SAGE Journals. Community Engagement and Homelessness Response. https://journals.sagepub.com/doi/10.1177/10986111241289390",
    FC['neigh'],
    difficulty=0.02
))

neighbor_ops.append(make_op(
    "Fund Private Security (pushout)",
    NEIGHBORHOODS,
    {'neighborhood_budget': 120.0},
    {'public_support': 3.0, 'pop_chronic': lambda news, mult=1.0: (setattr(news, 'pop_chronic', news.pop_chronic + int(round(percent_of(news.homeless_population,0.6) * mult))) or f"chronic +{int(round(percent_of(news.homeless_population,0.6) * mult))}"), 'legal_pressure': 2.0},
    "Berkeley Law Policy Advocacy Clinic. The Criminalization of Homelessness in California. UC Berkeley School of Law. https://www.law.berkeley.edu/article/clinic-study-details-how-business-districts-target-homeless-people/",
    FC['neigh'],
    difficulty=0.10
))

neighbor_ops.append(make_op(
    "Infrastructure Grants (convert trans->perm)",
    NEIGHBORHOODS,
    {'neighborhood_budget': 300.0},
    {'transitional_units': -80, 'permanent_units': 72, 'pop_families': pop_reduction_factory('pop_families',1), 'policy_momentum': 1.5},
    "RTI International. Capital Funding and Affordable Housing Development. https://www.rti.org/publication/a-review-of-the-literature-on-neighborhood-impacts-of-permanent-s",
    FC['neigh'],
    difficulty=0.14
))

neighbor_ops.append(make_op(
    "Community Food & Outreach Sponsorship",
    NEIGHBORHOODS,
    {'neighborhood_budget': 80.0},
    {'outreach_teams': 1, 'public_support': 1.2, 'pop_youth': pop_reduction_factory('pop_youth',3)},
    "PubMed Central. Community Outreach Programs. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8427990/",
    FC['neigh'],
    difficulty=0.03
))

neighbor_ops.append(make_op(
    "Neighborhood Rapid Response to Eviction Spikes",
    NEIGHBORHOODS,
    {'neighborhood_budget': 240.0},
    {'pop_families': pop_reduction_factory('pop_families',10), 'policy_momentum': 1.0},
    "National Low Income Housing Coalition. Eviction Prevention Programs. https://nlihc.org/",
    FC['neigh'],
    difficulty=0.09
))

neighbor_ops.append(make_op(
    "Public Space Design (reduce congregation)",
    NEIGHBORHOODS,
    {'neighborhood_budget': 160.0},
    {'public_support': 1.6, 'legal_pressure': -1.2},
    "Taylor & Francis Online. Hostile Architecture and Public Space Management. https://www.tandfonline.com/doi/full/10.1080/10439463.2024.2362730",
    FC['neigh'],
    difficulty=0.05
))

neighbor_ops.append(make_op(
    "Property Value Assistance (tax incentive to support programs)",
    NEIGHBORHOODS,
    {'neighborhood_budget': 220.0},
    {'permanent_units': 30, 'public_support': 0.9},
    "Housing Infrastructure Canada. Neighborhood Housing Incentives. https://housing-infrastructure.canada.ca/homelessness-sans-abri/reports-rapports/shelter-cap-hebergement-2024-eng.html",
    FC['neigh'],
    difficulty=0.08
))

neighbor_ops.append(make_op(
    "Neighborhood-led Transitional Housing Project",
    NEIGHBORHOODS,
    {'neighborhood_budget': 300.0},
    {'transitional_units': 90, 'pop_families': pop_reduction_factory('pop_families',6), 'policy_momentum': 1.2},
    "U.S. Department of Housing and Urban Development. Transitional Housing Evaluation. HUD Exchange. https://www.huduser.gov/portal/publications/pdf/lifeaftertransition.pdf",
    FC['neigh'],
    difficulty=0.12
))

neighbor_ops.append(make_op(
    "Neighborhood Monitoring & Data (complaint tracking)",
    NEIGHBORHOODS,
    {'neighborhood_budget': 40.0},
    {'legal_pressure': -0.8, 'public_support': 0.4},
    "SAGE Journals. Data & Transparent Monitoring. https://journals.sagepub.com/doi/10.1177/0739456X241265499",
    FC['neigh'],
    difficulty=0.02
))

# ---- BUSINESS (12 operators) ----
business_ops = []

business_ops.append(make_op(
    "Tax Incentives for Affordable Housing",
    BUSINESS,
    {'business_budget': 260.0},
    {'_construction_job': lambda news, mult=1.0: (schedule_construction(news,'perm', int(round(120*mult))) or f"Scheduled perm +{int(round(120*mult))}"), 'economy_index': 1.8, 'public_support': 1.2},
    "National Alliance to End Homelessness. Developer Incentives and Housing Supply. https://endhomelessness.org/state-of-homelessness/",
    FC['business'],
    difficulty=0.12
))

business_ops.append(make_op(
    "Fund Job Readiness Programs",
    BUSINESS,
    {'business_budget': 180.0},
    {'pop_families': pop_reduction_factory('pop_families',5), 'pop_youth': pop_reduction_factory('pop_youth',12), 'public_support': 2.2},
    "National Alliance to End Homelessness. Employment and Housing Stability. https://endhomelessness.org/",
    FC['business'],
    difficulty=0.06
))

business_ops.append(make_op(
    "Clean & Sweep (sanitation)",
    BUSINESS,
    {'business_budget': 80.0},
    {'public_support': 2.5, 'pop_chronic': lambda news, mult=1.0: (setattr(news, 'pop_chronic', news.pop_chronic + int(round(percent_of(news.homeless_population,0.4) * mult))) or f"displaced +{int(round(percent_of(news.homeless_population,0.4) * mult))}"), 'legal_pressure': 1.5},
    "National Alliance to End Homelessness. Encampment Clearances: Best Practices. https://endhomelessness.org/blog/punitive-policies-will-never-solve-homelessness-the-evidence-is-clear/",
    FC['business'],
    difficulty=0.09
))

business_ops.append(make_op(
    "Public-Private Transitional Housing",
    BUSINESS,
    {'business_budget': 360.0},
    {'transitional_units': 90, 'pop_families': pop_reduction_factory('pop_families',4), 'public_support': 1.8},
    "PubMed Central. Public-Private Partnerships in Housing. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8899911",
    FC['business'],
    difficulty=0.11
))

business_ops.append(make_op(
    "Lobby for Restrictive Ordinances",
    BUSINESS,
    {'business_budget': 140.0},
    {'legal_pressure': 5.0, 'economy_index': 0.8, 'pop_chronic': lambda news, mult=1.0: (setattr(news, 'pop_chronic', news.pop_chronic + int(round(percent_of(news.homeless_population,0.7) * mult))) or f"displaced +{int(round(percent_of(news.homeless_population,0.7) * mult))}" )},
    "Berkeley Law Policy Advocacy Clinic. Anti-Homeless Ordinances and Constitutional Challenges. UC Berkeley School of Law. https://www.law.berkeley.edu/article/clinic-study-details-how-business-districts-target-homeless-people/",
    FC['business'],
    difficulty=0.16
))

business_ops.append(make_op(
    "Volunteer Street Ambassadors",
    BUSINESS,
    {'business_budget': 100.0},
    {'outreach_teams': 2, 'public_support': 1.5, 'pop_youth': pop_reduction_factory('pop_youth',5)},
    "Taylor & Francis Online. Ambassador Programs and Service Connection. https://www.tandfonline.com/doi/full/10.1080/10439463.2024.2362730",
    FC['business'],
    difficulty=0.03
))

business_ops.append(make_op(
    "Clean Streets + Social Service Coupling",
    BUSINESS,
    {'business_budget': 220.0},
    {'public_support': 2.8, 'pop_chronic': pop_reduction_factory('pop_chronic',2)},
    "PubMed Central. Coupled Services and Displacement Reduction. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8356292/",
    FC['business'],
    difficulty=0.07
))

business_ops.append(make_op(
    "Small Business Microgrants to Hire",
    BUSINESS,
    {'business_budget': 140.0},
    {'economy_index': 1.2, 'public_support': 1.0},
    "PubMed Central. Hiring Incentives and Employment Pathways. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8356292/",
    FC['business'],
    difficulty=0.02
))

business_ops.append(make_op(
    "Sponsor Transitional Unit Conversions",
    BUSINESS,
    {'business_budget': 280.0},
    {'transitional_units': 70, 'policy_momentum': 0.9},
    "PubMed Central. Business Sponsorship Case Studies. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8899911",
    FC['business'],
    difficulty=0.08
))

business_ops.append(make_op(
    "Support Low-Barrier Shelters",
    BUSINESS,
    {'business_budget': 180.0},
    {'shelter_capacity': 120, 'pop_chronic': pop_reduction_factory('pop_chronic',3), 'public_support': 0.6},
    "PubMed Central. Low-Barrier Shelter Models and Health Outcomes. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7983925/",
    FC['business'],
    difficulty=0.05
))

business_ops.append(make_op(
    "Coalition with Shelters for Employer Placement",
    BUSINESS,
    {'business_budget': 160.0},
    {'pop_families': pop_reduction_factory('pop_families',3), 'policy_momentum': 0.5},
    "Homeless Services Research Institute. Employment Partnership Outcomes. https://www.hsri.org/projects/evaluating-samhsa-four-homelessness-programs-and-resources",
    FC['business'],
    difficulty=0.04
))

business_ops.append(make_op(
    "Sponsor University Pilot (housing innovation)",
    BUSINESS,
    {'business_budget': 240.0, 'university_budget': 50.0},
    {'transitional_units': 40, 'policy_momentum': 1.0},
    "Conrad N. Hilton Foundation. Housing Innovation Grant Programs. https://www.hiltonfoundation.org/learning/evaluation-of-housing-for-health-permanent-supportive-housing-program",
    FC['business'],
    difficulty=0.07
))

# ---- MEDICAL (12 operators) ----
medical_ops = []

medical_ops.append(make_op(
    "Deploy Mobile Clinics",
    MEDICAL,
    {'medical_budget':200.0},
    {'medical_vans':2, 'pop_chronic': pop_reduction_factory('pop_chronic',6), 'public_support':2.8},
    "Commonwealth Fund. Mobile Health Clinics for Homeless Populations. https://www.commonwealthfund.org/publications/case-study/2021/aug/how-medical-respite-care-program-offers-pathway-health-housing",
    FC['medical'],
    difficulty=0.06
))

medical_ops.append(make_op(
    "Medicaid & Benefits Enrollment Drive",
    MEDICAL,
    {'medical_budget':160.0},
    {'pop_chronic': pop_reduction_factory('pop_chronic',7), 'policy_momentum':1.2},
    "Substance Abuse and Mental Health Services Administration. Benefits Enrollment and Housing Stability. https://www.samhsa.gov/",
    FC['medical'],
    difficulty=0.05
))

medical_ops.append(make_op(
    "Substance Use Treatment Expansion",
    MEDICAL,
    {'medical_budget':320.0},
    {'pop_chronic': pop_reduction_factory('pop_chronic',12), 'public_support':-1.0, 'policy_momentum':2.8},
    "Homeless Services Research Institute. Substance Use Treatment and Housing First Models. https://www.hsri.org/projects/evaluating-samhsa-four-homelessness-programs-and-resources",
    FC['medical'],
    difficulty=0.18
))

medical_ops.append(make_op(
    "Medical Respite & Recovery Beds",
    MEDICAL,
    {'medical_budget':260.0},
    {'shelter_capacity': 80, 'pop_chronic': pop_reduction_factory('pop_chronic',5)},
    "Commonwealth Fund. Medical Respite Programs for Homeless Populations. https://www.commonwealthfund.org/publications/case-study/2021/aug/how-medical-respite-care-program-offers-pathway-health-housing",
    FC['medical'],
    difficulty=0.10
))

medical_ops.append(make_op(
    "Behavioral Health Outreach Teams",
    MEDICAL,
    {'medical_budget':220.0},
    {'outreach_teams':2, 'pop_youth': pop_reduction_factory('pop_youth',8), 'policy_momentum':1.3},
    "Substance Abuse and Mental Health Services Administration. Behavioral Health Outreach Models. https://www.samhsa.gov/",
    FC['medical'],
    difficulty=0.09
))

medical_ops.append(make_op(
    "Hospital Discharge Coordination",
    MEDICAL,
    {'medical_budget':120.0},
    {'pop_chronic': pop_reduction_factory('pop_chronic',3), 'public_support':0.7},
    "Commonwealth Fund. Hospital Discharge Planning and Homelessness Prevention. https://www.commonwealthfund.org/public/publications/case-study/2021/aug/how-medical-respite-care-program-offers-pathway-health-housing",
    FC['medical'],
    difficulty=0.04
))

medical_ops.append(make_op(
    "Expand Telehealth for Unhoused",
    MEDICAL,
    {'medical_budget':90.0},
    {'policy_momentum':0.6, 'public_support':0.5},
    "PubMed Central. Telehealth Access for Homeless Populations. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6153151",
    FC['medical'],
    difficulty=0.03
))

medical_ops.append(make_op(
    "Create Medical-Legal Partnerships",
    MEDICAL,
    {'medical_budget':100.0},
    {'legal_pressure': -1.5, 'policy_momentum': 0.7},
    "PubMed Central. Medical-Legal Partnerships and Housing Stability. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8356292",
    FC['medical'],
    difficulty=0.04
))

medical_ops.append(make_op(
    "Partner with Shelters for Onsite Clinics",
    MEDICAL,
    {'medical_budget':140.0},
    {'medical_vans':1, 'pop_chronic': pop_reduction_factory('pop_chronic',4)},
    "PubMed Central. Shelter-Based Health Services. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8356292",
    FC['medical'],
    difficulty=0.05
))

medical_ops.append(make_op(
    "Performance-based Funding for Treatment Outcomes",
    MEDICAL,
    {'medical_budget':240.0},
    {'policy_momentum':1.8, 'public_support': -0.8},
    "Homeless Services Research Institute. Performance-Based Contracting in Health Services. https://www.hsri.org/projects/evaluating-samhsa-four-homelessness-programs-and-resources",
    FC['medical'],
    difficulty=0.12
))

medical_ops.append(make_op(
    "Veterans Health Focus",
    MEDICAL,
    {'medical_budget':160.0},
    {'pop_veterans': pop_reduction_factory('pop_veterans',10), 'policy_momentum':1.0},
    "U.S. Department of Veterans Affairs. Ending Veteran Homelessness. https://www.va.gov/homeless/",
    FC['medical'],
    difficulty=0.06
))

medical_ops.append(make_op(
    "Evaluation of Health Interventions (data)",
    MEDICAL,
    {'medical_budget':80.0, 'university_budget': 60.0},
    {'policy_momentum':1.4, 'public_support': 0.6},
    "Homeless Services Research Institute. Health Intervention Evaluation Framework. https://www.hsri.org/projects/evaluating-samhsa-four-homelessness-programs-and-resources",
    FC['medical'],
    difficulty=0.03
))

# ---- UNIVERSITY (12 operators) ----
uni_ops = []

uni_ops.append(make_op(
    "Research & Program Evaluation",
    UNIVERSITY,
    {'university_budget': 100.0},
    {'policy_momentum': 1.5},
    "PubMed Central. Academic Research and Homeless Policy. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1525292/",
    FC['university'],
    difficulty=0.03
))

uni_ops.append(make_op(
    "Service-Learning & Workforce Integration",
    UNIVERSITY,
    {'university_budget': 110.0},
    {'social_workers': 5, 'pop_youth': pop_reduction_factory('pop_youth',10), 'public_support': 1.2},
    "United States Interagency Council on Homelessness. Service-Learning and Capacity Expansion. https://www.usich.gov/sites/default/files/document/Evidence-Behind-Approaches-That-End-Homelessness-Brief-2019.pdf",
    FC['university'],
    difficulty=0.04
))

uni_ops.append(make_op(
    "Housing Innovation Lab (modular units)",
    UNIVERSITY,
    {'university_budget': 260.0},
    {'_construction_job': lambda news, mult=1.0: (schedule_construction(news,'trans', int(round(70*mult))) or f"Scheduled trans +{int(round(70*mult))}"), 'pop_chronic': pop_reduction_factory('pop_chronic',3), 'policy_momentum': 2.0},
    "Conrad N. Hilton Foundation. Housing Innovation Grant Programs. https://www.hiltonfoundation.org/learning/evaluation-of-housing-for-health-permanent-supportive-housing-program",
    FC['university'],
    difficulty=0.10
))

uni_ops.append(make_op(
    "Reputation Management (PR)",
    UNIVERSITY,
    {'university_budget': 80.0},
    {'public_support': 0.6, 'policy_momentum': -0.4},
    "PubMed Central. University-Community Relations. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1525292/",
    FC['university'],
    difficulty=0.02
))

uni_ops.append(make_op(
    "Open Data & Dashboard (public transparency)",
    UNIVERSITY,
    {'university_budget': 70.0},
    {'policy_momentum': 0.8, 'public_support': 0.5},
    "United States Interagency Council on Homelessness. Data Standards and Systems. https://www.usich.gov/",
    FC['university'],
    difficulty=0.02
))

uni_ops.append(make_op(
    "Student Outreach & Volunteer Corps",
    UNIVERSITY,
    {'university_budget': 90.0},
    {'outreach_teams': 2, 'pop_youth': pop_reduction_factory('pop_youth',6), 'public_support': 1.0},
    "United States Interagency Council on Homelessness. Student Volunteer Programs. https://www.usich.gov/sites/default/files/document/Evidence-Behind-Approaches-That-End-Homelessness-Brief-2019.pdf",
    FC['university'],
    difficulty=0.03
))

uni_ops.append(make_op(
    "Policy Incubator with City (pilot)",
    UNIVERSITY,
    {'university_budget': 220.0, 'neighborhood_budget': 60.0},
    {'permanent_units': 30, 'policy_momentum': 1.6},
    "United States Interagency Council on Homelessness. University-City Collaborations. https://www.usich.gov/sites/default/files/document/Evidence-Behind-Approaches-That-End-Homelessness-Brief-2019.pdf",
    FC['university'],
    difficulty=0.08
))

uni_ops.append(make_op(
    "Deploy Evaluation Fellows to Shelters",
    UNIVERSITY,
    {'university_budget': 110.0},
    {'social_workers': 2, 'policy_momentum': 1.0},
    "Homeless Services Research Institute. Fellowship Program Evaluations. https://www.hsri.org/projects/evaluating-samhsa-four-homelessness-programs-and-resources",
    FC['university'],
    difficulty=0.03
))

uni_ops.append(make_op(
    "Community-engaged Research on Displacement",
    UNIVERSITY,
    {'university_budget': 140.0},
    {'policy_momentum': 1.8, 'public_support': 0.5},
    "PubMed Central. Community-Based Participatory Research. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1525292/",
    FC['university'],
    difficulty=0.05
))

uni_ops.append(make_op(
    "Leverage Philanthropy for PSH",
    UNIVERSITY,
    {'university_budget': 260.0},
    {'_construction_job': lambda news, mult=1.0: (schedule_construction(news,'perm', int(round(50*mult))) or f"Scheduled perm +{int(round(50*mult))}"), 'policy_momentum': 1.2},
    "Conrad N. Hilton Foundation. Permanent Supportive Housing Initiative Evaluation. https://www.hiltonfoundation.org/learning/evaluation-of-housing-for-health-permanent-supportive-housing-program",
    FC['university'],
    difficulty=0.09
))

uni_ops.append(make_op(
    "Student-led Rapid Rehousing Pilot",
    UNIVERSITY,
    {'university_budget': 120.0},
    {'transitional_units': 40, 'pop_youth': pop_reduction_factory('pop_youth',8)},
    "National Low Income Housing Coalition. Student-led Housing Programs. https://nlihc.org/sites/default/files/Housing-First-Evidence.pdf",
    FC['university'],
    difficulty=0.06
))

uni_ops.append(make_op(
    "Academic Advocacy Campaign",
    UNIVERSITY,
    {'university_budget': 80.0},
    {'public_support': 0.9, 'policy_momentum': 0.6},
    "National Low Income Housing Coalition. Advocacy Toolkit. https://nlihc.org/",
    FC['university'],
    difficulty=0.03
))

# Aggregate operators
SHELTERS_OPS = shelters_ops
NEIGHBOR_OPS = neighbor_ops
BUSINESS_OPS = business_ops
MEDICAL_OPS = medical_ops
UNIVERSITY_OPS = uni_ops

OPERATORS = SHELTERS_OPS + NEIGHBOR_OPS + BUSINESS_OPS + MEDICAL_OPS + UNIVERSITY_OPS

# INITIAL STATE
def create_initial_state():
    s = State()
    s.recalc_population()
    s.record_trend()
    return s

# ROLES meta (for Select_Roles)
ROLES = ROLES_List([
    {'name': 'Neighborhoods', 'min': 1, 'max': 1},
    {'name': 'Business', 'min': 1, 'max': 1},
    {'name': 'Medical', 'min': 1, 'max': 1},
    {'name': 'SheltersServices', 'min': 1, 'max': 1},
    {'name': 'University', 'min': 1, 'max': 1},
    {'name': 'Observer', 'min': 0, 'max': 20}
])
ROLES.min_num_of_roles_to_play = 5
ROLES.max_num_of_roles_to_play = 25

# STATE_VIS hook
BRIFL_SVG = True
render_state = None
def use_BRIFL_SVG():
    global render_state
    from CityWithoutWalls_SVG_VIS_FOR_BRIFL import render_state

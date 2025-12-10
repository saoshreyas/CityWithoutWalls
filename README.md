City Without Walls: README
Overview

City Without Walls is a turn-based, multi-stakeholder strategy simulation about homelessness in a midsized American city. It reflects the real-world complexity, uncertainty, and political trade-offs inherent to addressing homelessness. Inspired by the concept of wicked problems, the game integrates economic pressures, public sentiment, institutional incentives, and competing stakeholder agendas.

This README serves both players and developers. The first half explains how to understand and play the game. The second half explains how the game works under the hood, including its architecture, state variables, operator structure, and turn logic.

PART I — PLAYER-FRIENDLY GUIDE
1. Setting

You are part of a dynamic, politically tense city attempting to solve the wicked problem of homelessness. Public outcry has generated momentum for change, but stakeholders disagree sharply on what ‘change’ means.

The city:

Population: 750,000 (metro: 2.2M)

People experiencing homelessness: 10,700

Rent burden extremely high; public frustration rising

Major zones include business districts, neighborhoods, medical quarter, shelters, university, and grey zones

You take on one of five roles, each representing a powerful stakeholder with their own incentives and tools:

Neighborhood Coalitions

Business District Alliance

Medical Quarter Leadership

Shelters & Service Providers

University / Research Institution

Each role wants homelessness reduced — but also wants to protect their own reputation, budget, and interests.

2. Game Objective

The city’s crisis is too large for any one group. You must collectively (and competitively) influence the system so that:

Homelessness decreases by 30%

Public Support stays above 50%

Legal Pressure stays below 20

You win if the city achieves these simultaneously.

You lose if:

Public Support collapses

Legal Pressure triggers lawsuits or federal takeover

Homelessness significantly rises due to poor decisions

3. Turn Order

Each turn:

A stakeholder acts.

Their operator triggers changes in the city state.

Background systems (economy, construction, fatigue, budget flows) update.

Next stakeholder takes a turn.

Order is semi-random at game start, but stabilizes based on political influence.

4. What Players Can Do (Operators)

Operators are policy actions. Each role has exclusive access to certain operators.

Examples:

Neighborhoods

Launch Media Campaign

Fund Private Security

Sponsor Local Outreach

Business District

Partner on Sanitation Sweeps

Run Job Readiness Programs

Deploy Street Ambassadors

Medical Quarter

Open Health Clinics

Expand Mental Health Services

Mobile Medical Teams

Shelters & Services

Volunteer Drives

Expand Bed Capacity

Partner with Medical or University actors

University

Conduct Research Studies

Run Pilot Projects with City

Reputation Management Operations

Each operator affects:

Public Support

Homeless Population (sheltered/unsheltered)

Budgets

Institutional variables

Construction pipeline (if relevant)

Stakeholder reputation

Policy momentum or fatigue

Not all operators help — punitive ones may backfire and increase chronic homelessness.

5. Difficulty & Realism Features

The game is intentionally challenging.

Uncertainty:

Actions can succeed, partially succeed, or fail.

Construction delays:

New housing takes multiple rounds to complete.

Operating costs:

Shelters deteriorate if underfunded.

Economic volatility:

Random events like recessions or booms affect budget and support.

Policy fatigue:

The public grows tired of expensive or repeated interventions.

Role interdependence:

No stakeholder can win alone; competing but coordinated strategies are required.

PART II — DEVELOPER GUIDE
6. Code Architecture

The game is built using an object-oriented Python framework structured around:

State class

Operator classes

Role definitions

Turn engine

Random event & background systems

SVG visualizer (separate file)

7. State Variables

The State object tracks all dynamic information:

Global Metrics

homeless_total

unsheltered

sheltered

at_risk_population

public_support

legal_pressure

policy_fatigue

economy_strength

policy_momentum

Budgets

Individual budgets for:

Neighborhoods

Business District

Medical Quarter

Shelters/Services

University

Infrastructure

bed_capacity

construction_queue (multi-turn projects)

Role Rotation

Current role

Turn counter

Political influence weights

8. Operators (Technical Overview)

Each operator is an object with:

name

precondition(state, role) → bool

apply(state) → modifies state

Cost helpers: partial spending, dynamic scaling

Failure/partial-success probabilities

Risk levels / unintended consequences

Operators are grouped by role and stored in an operator registry.

9. Turn Logic

Each turn:

Select Role based on influence mapping.

Get Available Operators (check preconditions).

Player Chooses Operator.

Operator Executes with realistic randomness.

Construction Queue Updates.

Budgets Adjust (inflows, grants, economic effect).

Policy Fatigue and Momentum Update.

Win/Loss Conditions Checked.

10. Background Systems

These systems activate automatically each turn:

Construction Pipeline

Reduces remaining time on housing projects; adds capacity when done.

Operating Cost Deduction

Shelters require upkeep; shortages degrade capacity.

Random Events

Recessions

Booms

Weather events

Political scandals

Chronic Homelessness Drift

Punitive strategies can increase chronic homelessness long-term.

11. Visualization

A separate Python file generates an SVG dashboard showing:

Current homelessness breakdown

Budget bars

Public support gauge

Legal pressure gauge

Construction progress timers

Turn and role indicators

This file reads from the State object and exports updated visuals each turn.

12. Extending the Game

Developers can add:

New roles

Additional operators

Deeper economic modeling

AI-controlled stakeholders

Narrative events

Adding a new operator requires only:

Writing a new class instance

Defining cost, effects, preconditions

Registering it under a role

The engine handles the rest.

13. Credits

Concept, research, and specifications by Shreyas and Lauren.

Development includes:

Wicked problem analysis

Stakeholder modeling

Policy simulation logic

Turn-based systems

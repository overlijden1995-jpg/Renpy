# Default values for every persistent game variable.
#
# Act scripts must not create these variables on the fly. Every value the
# game reads is declared here exactly once, so that rollback, save/load, and
# starting mid-game all operate on a fully-formed state. Script code assigns
# transitions (and phase-local derivations), never the initial existence of a
# variable.

# Calendar and act structure.
default day = 1
default act = 1
default phase = "dawn"

# Cold open / gate outcome.
default coldopen_labour = False
default coldopen_water = False
default coldopen_silence = False
default probation = False

# Colony resources.
# water starts as the one mouthful in the stranger's canteen when he reaches
# the gate; act1_day1_dawn carries it into the cistern baseline (5 + canteen).
# scrap, meds and food are the colony's Day 1 stores.
default water = 1
default scrap = 12
default meds = 1
default food = 8

# People.
default trust = {"alice": 0, "denice": 0, "sophia": 0, "tory": 0, "sable": 0}
default companion_unavailable = {"alice": False, "denice": False, "sophia": False, "tory": False, "sable": False}
default assignments = {"alice": "pump duty", "denice": "medical", "sophia": "stores", "tory": "the gate", "sable": "salvage"}
default trusted_companion = None
default helping_companion = None
default helping_name = None
default helping_trust = 0
default wounded_companion = None
default wounded_companion_return_day = None
default wounded_name = None

# Colony condition flags.
default colony_hungry = False
default colony_thirsty = False
default cut_trade = False
default cistern_below_reserve = False
default water_crisis_plan = "unresolved"
default colony_value = 0
default raid_pressure = 0
default raid_triggered = False
default line_resolution = "unresolved"

# Standing and outcome of the Line levy arc.
default line_standing = 0

# Day 1 work outcomes.
default pump_spent = False
default mc_injured = False
default salvage_with_tory = False
default salvage_yield = 0
default colonist_hand = "untreated"

# Day 3 raid losses.
default med_loss = 0
default food_loss = 0

# Act 1 close commitment.
default act1_commit = "unresolved"
default convoy_scout_risk = 0.0

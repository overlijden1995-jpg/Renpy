# Colony simulation engine: the phase loop.
#
# Act 1 is a three-day probation. The engine owns the calendar; each day
# runs dawn, day, evening and night in order. Every phase applies its own
# consumption (and the dawn slate assignments) before handing off to the
# content dispatcher in phase_event. Scripted event labels call no
# phase-scaffolding of their own.

define COLONY_PHASES = ("dawn", "day", "evening", "night")

label colony_loop:
    # Days 1-3 are Act 1. act1_close hands off to Act 2.
    while day <= 3:
        call colony_day
        $ day += 1
    jump act1_close


label colony_day:
    $ phase_index = 0
    while phase_index < len(COLONY_PHASES):
        $ phase = COLONY_PHASES[phase_index]
        call colony_phase
        $ phase_index += 1
    return


label colony_phase:
    if phase == "dawn":
        call meal("dawn")
        call slate_assignments
    elif phase == "evening":
        call meal("evening")
    elif phase == "night":
        call night_upkeep
    call phase_event
    return


label meal(which):
    # The colony eats one food at the day's two meals, if it has it.
    if food >= 1:
        $ food -= 1
    else:
        $ colony_hungry = True
        if which == "dawn":
            "Breakfast was skipped. There was nothing to skip."
        else:
            "Dinner was skipped. The colony worked on the memory of food."
    return


label night_upkeep:
    # The colony washes down and settles for the night; the cistern pays a
    # little more than anyone drinks.
    if water >= 1:
        $ water -= 1
    else:
        $ colony_thirsty = True
        "Night — the cistern had nothing to give. The colony settled for the taste of dust."
    return


label slate_assignments:
    # The dawn slate: whoever is not excused works. Wounded companions are
    # left off the slate and noted for the record.
    python:
        roster = []
        excused = []
        for name in ("alice", "denice", "sophia", "tory", "sable"):
            if companion_unavailable.get(name):
                excused.append(name.capitalize())
            else:
                roster.append(name.capitalize() + " — " + assignments[name])
        slate_line = ", ".join(roster)
        excused_line = ", ".join(excused)
    "The slate read: [slate_line]."
    if excused_line:
        "Left in Denice's care today: [excused_line]."
    return


label phase_event:
    if day == 1:
        if phase == "dawn":
            call act1_day1_dawn
        elif phase == "day":
            call act1_day1_day
        elif phase == "evening":
            call act1_day1_evening
        elif phase == "night":
            call act1_day1_night
    elif day == 2:
        if phase == "dawn":
            call act1_day2_dawn
        elif phase == "day":
            call act1_day2_day
        elif phase == "evening":
            call act1_day2_evening
        elif phase == "night":
            call act1_day2_night
    elif day == 3:
        if phase == "dawn":
            call act1_day3_dawn
        elif phase == "day":
            call act1_day3_day
        elif phase == "evening":
            call act1_day3_evening
        elif phase == "night":
            call act1_day3_night
    return

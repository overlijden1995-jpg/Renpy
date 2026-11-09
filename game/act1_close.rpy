# Act I closes on Sable's intelligence and the player's response to it.

label act1_close:
    scene black
    show sable work smile at center
    "After the Day 3 watch, Sable came through the sally port with road dust in every seam and a salvage pack that was much too light. She had left before the stranger reached the gate. She had been nine days out."
    "Sable" "Good news. I found a patrol. Tiny patrol. Very spread out."
    "Tory" "Count it."
    show tory idle neutral at left
    "Sable's smile went away. She set the light pack down and used twelve stones to make a road on the gate step."
    "Sable" "A convoy. Not a patrol. Eight trucks, two outriders, water-militia markings. Small convoy, if we are being optimistic. Barely a convoy, if we are being liars."
    "Denice" "Direction? Speed? Distance?"
    show denice work neutral at right
    "Sable" "Toward us. Slow enough to arrive organized. Close enough that I ran the last hour and only mostly got lost."
    "She had under-reported the first sighting because saying patrol had made the walk home feel shorter. The stones on the step did not make it shorter now."
    "Sable" "So. Fortify, let me look again before they close, or talk. Fast choice, but it is still a choice."
    $ act1_commit = "unresolved"
    $ convoy_scout_risk = 0.0
    menu:
        "Fortify the colony. (Costs 10 scrap; Tory approval +10.)" if scrap >= 10:
            $ scrap -= 10
            $ act1_commit = "fortify"
            $ trust["tory"] += 10
            "Tory" "Ten scrap into the wall. Better than ten bodies under it."
            "Approval: Tory +10."
        "Scout the convoy first. (Sable approval +10; 35% injury risk on the approach.)":
            $ act1_commit = "scout"
            $ convoy_scout_risk = 0.35
            $ trust["sable"] += 10
            "Sable" "I can be quick. I can be careful. I cannot promise both, which is annoyingly honest of me."
            "Approval: Sable +10."
        "Open talks. (-4 Line standing; Sophia approval +10.)":
            $ line_standing -= 4
            $ act1_commit = "talks"
            $ trust["sophia"] += 10
            "Sophia" "I will state what we can pay, what we will not pay, and exactly what their answer costs."
            "Approval: Sophia +10."
    $ act = 2
    jump act2_stub


label act2_stub:
    # Act 2 opens on the chosen response to the approaching convoy.
    return

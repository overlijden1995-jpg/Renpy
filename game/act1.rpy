# Act I story events. The cold open enters through colony_loop (colony.rpy).
# The colony engine owns the calendar and the phase dispatch; these labels
# contain the scene content only.

label act1_day1_dawn:
    # Carry the stranger's canteen into the cistern baseline: five colony
    # water plus whatever of his mouthful he kept (zero if he handed it
    # over at the gate).
    $ water = 5 + water
    scene black
    show alice work neutral at center
    "Day 1 — dawn. The yard woke in stages: a shutter, a kettle, then the first bucket striking stone. The colony kept no bell. It kept a rota, a slate, and a habit of listening for the cistern to sound wrong."
    "Alice had a pump bolt in one hand and a bucket under a leak that was not there."
    if coldopen_labour:
        "Alice" "You offered labour at the gate. Good. The pump heard you."
    elif coldopen_water:
        "Alice" "You gave up your last mouthful. I remember. It still doesn't buy a seal."
    elif coldopen_silence:
        "Alice" "You wait well. Let's find out if you can work while you wait."
    else:
        "Alice" "The gate is done talking. The pump isn't."
    "Alice" "This tank has outlived two governments and a flood of bad decisions. It can manage one more mouth."
    "Alice" "Help me seat a replacement seal. Sophia counted four scrap's worth of sound metal in the bins."
    menu:
        "Replace the seal. (Costs 4 scrap; partial repair tonight.)" if scrap >= 4:
            $ scrap -= 4
            $ pump_spent = True
            $ trust["alice"] += 10
            "He paid four scrap into Alice's parts tray before she touched the pump. They worked until the seal sat true."
            "Alice" "Not fixed. Less broken. That's most of my trade."
            "Trust: Alice +10."
        "Leave the pump for now. (No cost.)":
            $ pump_spent = False
            "He kept the four scrap in the colony bins. Alice wrapped the bolt in cloth and put it away for another attempt."
            "Alice" "All right. I read the cistern tonight. Numbers before promises."
    return


label act1_day1_day:
    scene black
    show tory idle neutral at right
    "Day — the scrap yard. Beyond the south wall the old depot's yard lay in heaps: sheet metal, bedframes, cable, the ribs of a bus. Everything in the colony had been somebody else's finished job, and most of it was still waiting to be finished again."
    "Tory" "Two ways. I go, you come back with less. You go alone, you come back with more. Usually."
    menu:
        "Take Tory. (Gain 4 scrap; no injury chance.)":
            $ salvage_with_tory = True
            $ salvage_yield = 4
            $ scrap += 4
            $ trust["tory"] += 10
            "Tory watched the approaches while he loaded four scrap. She fired nothing. They both came back through the gate."
            "Tory" "Four scrap. Two bodies home. Good yield."
            "Trust: Tory +10."
        "Go alone. (Gain 7 scrap; 25%% chance of injury.)":
            $ salvage_with_tory = False
            $ salvage_yield = 7
            $ scrap += 7
            "He brought back seven scrap, both hands full before he reached the wall."
            if renpy.random.random() < 0.25:
                $ mc_injured = True
                show mc hurt neutral at left
                "A sheet edge opened his forearm on the last load. Denice bound it at the gate. The cut was ugly, shallow, and would slow him for a day; it would not stop him working."
            else:
                "The yard stayed quiet. He returned with seven scrap and no new bandages."
    return


label act1_day1_evening:
    scene black
    show denice work neutral at center
    "Evening — a colonist sat beside Denice's scanner with one hand wrapped in stained cloth. The fever reading held steady at the edge of red."
    "Meds were the one stock nobody argued about. You did not trade them. You counted the doses and hoped the count was wrong in your favour."
    "Denice" "Infected laceration. I have one med dose that can buy the fever down. Or clean cloth, boiled water, and more time."
    menu:
        "Assist Denice. (Costs 1 med.)" if meds >= 1:
            $ meds -= 1
            $ colonist_hand = "treated"
            $ trust["denice"] += 10
            "He held the dressing basin while Denice used the dose and closed the clean wrap. The colonist's hand stopped shaking first."
            "Denice" "Temperature falling. Dressing stays dry. You can let go now."
            "Trust: Denice +10."
        "Stay out of her way. (No cost.)":
            $ colonist_hand = "recovering"
            "He stayed out of the light. Denice used boiled water and clean cloth, changing the dressing twice without asking for help."
            "Denice" "Slower route. Still a route. Fever is easing."
    return


label act1_day1_night:
    scene black
    show alice work neutral at right
    "Water was the only number the colony said out loud every night."
    "The yard had stopped staring at his arm by the second day. Two colonists had asked, politely, whether it hurt. He told them it did, which was true, and which closed the subject faster than anything else he had tried."
    if pump_spent:
        $ water += 2
        "Night — the repaired seal held when Alice lifted the handle. The pump produced a thin, uneven stream, enough to add two water to the cistern before the handle stiffened again."
        "Alice" "Partial repair. Two water. I'm writing down two, not the lake you were hoping for."
    else:
        "Night — Alice lowered the measuring cord into the cistern, brought it up, and checked the mark twice."
        "Alice" "Cistern reads [water] water. That's [water], not plenty. Nobody rounds up while I'm holding the cord."
    return


label act1_day2_dawn:
    scene black
    show alice idle angry at left
    show sophia work neutral at right
    "Day 2 — dawn. The breakfast queue used less water, and everyone noticed. Alice stood at the cistern with one finger on the untouched reserve mark."
    "The Cut were the caravans that ran sealed cans along the old roads. They were not kind and not cruel. They were punctual, and they remembered every price anyone had ever paid them."
    "Sophia" "Stores read [water] water and [scrap] scrap. Three answers. None is free, and none closes the colony tomorrow."
    menu:
        "Cut rations. (Save 4 water; the colony goes thirsty.)":
            $ water_crisis_plan = "rations"
            $ water += 4
            $ colony_thirsty = True
            "Sophia marked four water as saved. The cost walked away with the queue: dry mouths, shortened tempers, and another day still running."
        "Trade scrap with the Cut. (Costs 3 scrap; gain 6 water.)" if scrap >= 3:
            $ water_crisis_plan = "trade"
            $ scrap -= 3
            $ water += 6
            $ cut_trade = True
            $ trust["sophia"] += 10
            "Denice sent the terms by radio. Sophia paid three scrap against six sealed water due that day."
            "Trust: Sophia +10."
        "Draw the cistern below reserve. (Gain 5 water; cistern falls below reserve.)":
            $ water_crisis_plan = "reserve"
            $ water += 5
            $ cistern_below_reserve = True
            "Alice opened the lower valve and released five water into the colony tanks. The wet line sank below the reserve mark. Nobody called it permanent damage; nobody called it safe."
    return


label act1_day2_day:
    scene black
    "Day — the crisis stopped being a number on Sophia's slate."
    if water_crisis_plan == "rations":
        show alice work neutral at center
        "At the water queue, each colonist received half a cup. Four saved water stayed sealed under Alice's hand. The colony remained on its feet, thirsty and working."
    elif water_crisis_plan == "trade":
        show sophia work neutral at center
        "A Cut carrier delivered six sealed water and collected the three scrap. Sophia checked every seal before signing. The empty space in the scrap rack remained visible beside the full cans."
    else:
        show alice work neutral at center
        "Five drawn water filled the colony tanks. At the cistern, the reserve line stood dry above the water. Alice read the lower measure aloud so nobody could mistake it later."

    if salvage_with_tory:
        show tory idle neutral at right
        "By noon, the four scrap from Tory's run sat sorted in the rack. She counted the gate detail and found the same number alive as at breakfast."
    else:
        "The seven scrap from the solo run made a taller stack in the rack."
        if mc_injured:
            show mc hurt neutral at left
            "He worked more slowly with Denice's bandage visible, but the injury kept him from no essential task."
    if colonist_hand == "treated":
        "The colonist with the infected hand returned to light duty, fingers flexing inside the clean wrap."
    else:
        "The colonist with the infected hand rested in shade while Denice changed another boiled dressing. The fever continued to recede."
    if pump_spent:
        "The partially repaired pump ran for twenty minutes before needing rest. It did not solve the crisis; it helped."
    else:
        "The dead pump kept its silence, but the chosen water plan carried the colony through the workday."
    return


label act1_day2_evening:
    scene black
    show tory idle neutral at left
    show denice idle neutral at right
    "Evening — a Cut caravan scout waited outside the gate with both hands visible. Tory's crossbow stayed lowered."
    "Cut scout" "No speech. Your water trouble has a shape, and my caravan already knows it."
    if water_crisis_plan == "rations":
        "Cut scout" "Half cups at breakfast. Four cans put back. Your queue walks slower when it thinks nobody is counting."
    elif water_crisis_plan == "trade":
        "Cut scout" "Three scrap for six water. Terms were spoken on an open frequency. My ledger has the same numbers as yours."
    else:
        "Cut scout" "You drew under your reserve line. My outrider read the wet mark through the service hatch this morning."
    "Denice" "Who watched us? From where? Since when?"
    "The scout answered only the first question, and not with a name. Denice put the other two away for later."
    "Tory" "One scout came. One scout leaves. No bolt tonight."
    return


label act1_day2_night:
    $ trusted_companion = max(("alice", "denice", "sophia", "tory", "sable"), key=trust.get)
    if trusted_companion == "alice":
        call act1_day2_night_alice
    elif trusted_companion == "denice":
        call act1_day2_night_denice
    elif trusted_companion == "sophia":
        call act1_day2_night_sophia
    elif trusted_companion == "tory":
        call act1_day2_night_tory
    else:
        call act1_day2_night_sable
    return


label act1_day2_night_alice:
    scene black
    show alice idle soft at center
    # Routine beat 1: mending equipment.
    "Alice folded a bucket cloth while he held the torn edge straight. She talked through every stitch, mostly about buckets, once about him holding still."
    # Routine beat 2: checking the jars.
    "They turned the water jars so their chalk marks faced the wall. Alice tapped each lid, said good night to the levels, and left the last jar for morning."
    # Routine beat 3: what the cistern remembers.
    "She told him, without looking up, that the tank had been full when the colony took the yard, and that the people who filled it had written every level in a book. The book was in her bunk. She had read it until the pages softened. Nobody else was allowed to touch it."
    return


label act1_day2_night_denice:
    scene black
    show denice idle soft at center
    # Routine beat 1: maintaining the scanner.
    "Denice cleaned the scanner contacts with a dry swab. He held the lamp. She asked whether the light was steady, then whether he always held his breath when asked that."
    # Routine beat 2: keeping the radio schedule.
    "They listened through the scheduled radio silence. Denice marked the time, switched the set off, and left whatever she had heard in the static unspoken."
    # Routine beat 3: what the radio is for.
    "The colony's radio was the only thing that reached past the next ridge. The Cut used it. So did the Line, on a frequency Denice had never been able to fully lock. She did not say which one she was more afraid of hearing from."
    return


label act1_day2_night_sophia:
    scene black
    show sophia idle soft at center
    # Routine beat 1: balancing the ledger.
    "Sophia read the next day's column while he rubbed old pencil marks from the slate. She stated the cost of lamp oil, then turned the lamp one notch lower."
    # Routine beat 2: mending the ledger.
    "They stitched a loose ledger page back into place. Sophia put the better pencil beside his hand and kept the stub for herself without mentioning it."
    # Routine beat 3: what the ledger keeps.
    "Every colonist had a line in the book: what they ate, what they were owed, what they had brought in. Sophia said a ledger was a promise you could check. She added, very quietly, that it was also the only record of who had come in at a gate and who had been sent back out."
    return


label act1_day2_night_tory:
    scene black
    show tory idle soft at center
    # Routine beat 1: maintaining the crossbow.
    "Tory counted six crossbow bolts onto a cloth, cleaned them, and counted six back into the case. He kept the oil tin from tipping."
    # Routine beat 2: sharing the watch.
    "They oiled the gate hinge together. Tory counted two people on the wall, left the crossbow unloaded, and let the quiet finish its shift."
    # Routine beat 3: what the wall cost.
    "She had stood a wall for the Line before she stood one for herself. She did not explain the difference, except to say that the Line counted bodies and this wall counted names, and that the names were the reason she slept."
    return


label act1_day2_night_sable:
    scene black
    show sable idle soft at center
    # Routine beat 1: sorting salvage.
    "Sable sorted screws from a salvage tin at reckless speed while he caught the ones she flicked toward the wrong pile. She called his aim tragic and moved the tin closer."
    # Routine beat 2: airing bedrolls.
    "They shook dust from two bedrolls over the wall. Sable said the road home had been boring, then laughed too quickly and admitted the ravine had only been a little on fire."
    # Routine beat 3: what the roads are like.
    "Sable could tell a road by its dead trucks. The old highways had been the first things the wars broke and the last things anyone repaired. She knew which ones still had water under them, and she had never once told anyone how much that knowledge had cost her to get."
    return

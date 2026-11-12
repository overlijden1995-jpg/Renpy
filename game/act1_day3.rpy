# Act I, Day 3: the Line levy and its consequences.
# The colony engine owns the calendar; this file contains the scene content.

label act1_day3_dawn:
    # Levy stakes are derived from the colony's current position, so they
    # are recomputed each time the dawn plays out.
    $ colony_value = scrap + water + food + meds
    $ raid_pressure = colony_value
    $ helping_companion = max(("alice", "denice", "sophia", "tory", "sable"), key=trust.get)
    $ helping_name = helping_companion.capitalize()
    $ helping_trust = trust[helping_companion]
    scene black
    show tory idle neutral at left
    show denice work neutral at right
    "Day 3 — dawn. Tory watched the road through the gate slit and counted without raising her voice."
    "Tory" "Six bodies. Water-militia marks. The Line."
    "Their officer stopped beyond bow range with five carriers behind her. Every carrier had a rifle and an empty water can."

    if line_standing >= 10:
        "Line officer" "Your standing buys a table, not exemption. We can negotiate the measure before we discuss collection."
    else:
        "Line officer" "Levy first. Six water or eight scrap. Refusal gets an answer tonight."
    "Line officer" "Your colony got worth taking. That is why the Line came."

    if cut_trade:
        "The Cut caravan scout from the previous evening stood beside the Line carriers, close enough for the officer to notice his ledger."
        "Cut scout" "They already met one water price this week. Check the seal count before you set another."
        "Line officer" "Cut paper does not pay a Line levy. It does prove you know how to trade."
        "Tory" "Six Line. One Cut scout. Everybody still breathing."

    menu:
        "Pay the levy. (Choose 6 water or 8 scrap.)" if water >= 6 or scrap >= 8:
            menu:
                "Pay 6 water." if water >= 6:
                    $ water -= 6
                    $ line_resolution = "paid_water"
                    $ line_standing += 2
                    "Sophia measured six water into the Line's cans. The officer signed the slate and made no apology."
                "Pay 8 scrap." if scrap >= 8:
                    $ scrap -= 8
                    $ line_resolution = "paid_scrap"
                    $ line_standing += 2
                    "The Line carriers loaded eight scrap from the rack. Sophia counted every piece before she signed."
            $ colony_value = scrap + water + food + meds
            $ raid_pressure = colony_value
        "Refuse the levy. (-2 Line standing; raid at [raid_pressure] pressure: med/food loss, 1 companion wounded.)":
            $ line_resolution = "refused"
            $ line_standing -= 2
            $ raid_triggered = True
            "Line officer" "Then keep your cans. We will collect after dark."
            "Tory" "Six leave. More may come back. Raid pressure: [raid_pressure]."
        "Stall with [helping_name]. (Trust [helping_trust]/10; failure: -1 Line standing and the same night raid.)":
            if helping_trust >= 10:
                $ line_resolution = "stalled"
                $ line_standing += 1
                $ raid_triggered = False
                "[helping_name] stepped beside the officer with exact stores, names, and collection times. The answer was specific enough to be believed."
                "Line officer" "One day. I return for the measure tomorrow."
            else:
                $ line_resolution = "stall_failed"
                $ line_standing -= 1
                $ raid_triggered = True
                "[helping_name] tried to slow the officer with questions about weights and collection times. With only [helping_trust] trust, the help came late and the gaps showed."
                "Line officer" "You do not know your own stores well enough to bargain. Tonight, then."
    return


label act1_day3_day:
    scene black
    if line_resolution in ("paid_water", "paid_scrap"):
        show sophia work neutral at center
        "Day — six Line bodies marched back down the road with the levy. Sophia struck the payment from the slate in plain sight."
        if line_resolution == "paid_water":
            "Six empty spaces stood in the water rack. The colony was poorer, intact, and under no night-raid order."
        else:
            "The scrap rack leaned with its remaining load. The colony was poorer, intact, and under no night-raid order."
    elif line_resolution == "stalled":
        "Day — [helping_name] copied the agreed collection time while the Line waited. Six bodies left without a levy and without a promise of mercy beyond tomorrow."
    else:
        show tory work neutral at left
        show denice work neutral at right
        "Day — Tory braced the gate while Denice marked approach lanes on the scanner. The colony prepared for the pressure its value had drawn."
    return


label act1_day3_evening:
    scene black
    show tory work neutral at left
    show denice work neutral at right
    if raid_triggered:
        "Evening — Tory took the wall with her bolt-action crossbow. Denice set the scanner to motion and laid out the medical kit before anyone was bleeding."
        "Denice" "Two approaches. North ditch is faster. East cut is quieter. Scanner cannot see through the wall."
        "Tory" "One wall. Two watchers. Hold both."
    elif line_resolution == "stalled":
        "Evening — the reprieve held. Denice logged the Line's promised return and put the scanner back on its ordinary watch cycle."
    else:
        "Evening — Denice logged six Line signatures leaving scanner range. No return signal followed them."
    return


label act1_day3_night:
    if raid_triggered:
        call act1_day3_night_raid
    elif line_resolution == "stalled":
        "Night — the road stayed empty. Stalling had bought one day, not settled the levy."
    else:
        "Night — the paid levy bought a quiet road. Tory kept watch anyway."
    return


label act1_day3_night_raid:
    scene black
    show tory work neutral at left
    show denice work neutral at right
    "Night — Denice's scanner caught movement in the north ditch before the first stone struck the wall."
    "Denice" "Contact. Four low, two standing. North side. Thirty metres and closing."
    "Tory stayed on the wall, crossbow braced against the steel. Her shots were flat reports in the dark, each one answered by Denice's corrected range."
    "Tory" "Two climbing. Four carrying. Count them, not the noise."
    "The Line reached the stores before the wall held. The raiders withdrew with torn packaging behind them, and nobody pursued past the light."

    $ med_loss = min(meds, 1 + raid_pressure // 60)
    $ food_loss = min(max(0, food - 1), 1 + raid_pressure // 40)
    $ meds -= med_loss
    $ food -= food_loss
    $ wounded_companion = helping_companion
    $ companion_unavailable[wounded_companion] = True
    $ wounded_companion_return_day = day + 2
    $ wounded_name = wounded_companion.capitalize()
    "Raid losses: [med_loss] meds and [food_loss] food, scaled from [raid_pressure] raid pressure."
    "[wounded_name] was wounded during the defense and will be unavailable for one full day, returning on Day [wounded_companion_return_day]."
    "The wall held. The colony still had water, shelter, and enough food to answer the morning."
    return

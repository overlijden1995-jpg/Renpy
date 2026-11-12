# During engine test runs nothing animates once dialogue text finishes
# revealing, and Ren'Py only advances the test runner when a frame is drawn.
# Ask for a redraw every frame while a test suite is active so the runner
# keeps making progress even in a fully static scene. Outside of tests the
# callback returns False and has no effect.
init python:
    def _ashfall_test_redraw():
        try:
            from renpy.test.testexecution import is_in_test
            return is_in_test()
        except Exception:
            return False
    renpy.config.needs_redraw_callbacks.append(_ashfall_test_redraw)

# Engine verification for Act 1: a full playthrough to the act break, with
# engine save, load and rollback across the Day 2 water choice.
#
# Run with: ./run.sh . test ashfall
#
# The playthrough is deterministic by construction: every menu choice taken
# has a fixed outcome (no injury rolls, no raid outcome depends on RNG).

testsuite ashfall:
    description "Act 1 engine verification: playthrough to the act break, save/load/rollback across the Day 2 choice."

    setup:
        $ _test.screenshot_directory = "screenshots"

    # The project has no main menu: the game boots straight into the story.
    # Restart before every testcase so each one observes fresh default state.
    # The session flag is consumed by the restart and restored afterwards, so
    # the reboot cannot loop (renpy.session survives full_restart in-process).
    before testcase:
        if eval renpy.session.pop("ashfall_reset", False):
            run MainMenu(confirm=False)
        else:
            $ renpy.session["ashfall_reset"] = True

    teardown:
        exit

    testcase playthrough_to_act2:
        description "Labours at the gate, takes the Day 2 trade, pays the levy in water, opens talks; the act breaks at act2_stub."

        # Cold open: offer labour at the gate.
        advance until "Offer labour"
        click "Offer labour"
        assert eval (coldopen_labour)

        # Day 1, dawn: the seal. Scrap 12 -> 8.
        advance until "Replace the seal"
        assert eval (probation)
        assert eval (day == 1)
        assert eval (water == 6)   # 5 cistern + 1 for the unspent canteen
        click "Replace the seal"
        assert eval (scrap == 8)
        assert eval (pump_spent)

        # Day 1, day: salvage with Tory. Scrap 8 -> 12.
        advance until "Take Tory"
        click "Take Tory"
        assert eval (scrap == 12)
        assert eval (salvage_with_tory)

        # Day 1, evening: assist Denice. Meds 1 -> 0.
        advance until "Assist Denice"
        click "Assist Denice"
        assert eval (meds == 0)
        assert eval (colonist_hand == "treated")

        # Day 2, dawn: the water crisis. Trade 3 scrap for 6 water.
        advance until "Trade scrap"
        assert eval (day == 2)
        assert eval (water == 7)   # carry 6, night upkeep 5, pump +2
        assert eval (food == 5)    # breakfast at days 1 and 2 consumed
        click "Trade scrap"
        assert eval (scrap == 9)
        assert eval (water == 13)
        assert eval (cut_trade)

        # Day 3, dawn: the Line levy. Pay 6 water through the outer menu.
        advance until "Pay the levy"
        assert eval (day == 3)
        assert eval (water == 12)  # 13 less night upkeep at the Day 2 -> 3 boundary
        click "Pay the levy"
        advance until "Pay 6 water"
        click "Pay 6 water"
        assert eval (water == 6)
        assert eval (line_resolution == "paid_water")
        assert eval (line_standing == 2)

        # Act 1 close: open talks; the act breaks at act2_stub.
        advance until "Open talks"
        # "act = 2" executes after the branch dialogue, then the script
        # ends; the engine then reboots into a fresh game (Ren'Py's normal
        # end-of-start behavior), resetting stores. Assert the branch state
        # synchronously, then prove the act break by reaching act2_stub.
        click "Open talks"
        assert eval (act1_commit == "talks")
        assert eval (line_standing == -2)
        advance until label act2_stub

    testcase save_load_rollback_day2:
        description "Engine save at the Day 2 crisis menu, load into the rations branch, roll back, and take the reserve branch instead."

        advance until "Offer labour"
        click "Offer labour"

        advance until "Replace the seal"
        click "Replace the seal"
        advance until "Take Tory"
        click "Take Tory"
        advance until "Assist Denice"
        click "Assist Denice"

        # Day 2, dawn: the crisis menu. This is the save point.
        advance until "Trade scrap"
        assert eval (day == 2)
        assert eval (water == 7)
        run FileSave(7, confirm=False)

        # Trade branch, checked through to the Day 3 levy menu.
        click "Trade scrap"
        assert eval (water == 13)
        assert eval (scrap == 9)
        advance until "Pay the levy"
        assert eval (day == 3)
        assert eval (water == 12)

        # Engine load back into the Day 2 crisis menu.
        run FileLoad(7, confirm=False)
        assert eval (day == 2)
        assert eval (water == 7)
        assert eval (scrap == 12)
        assert eval (cut_trade == False)

        # Take the rations branch, then roll the choice back.
        click "Cut rations"
        assert eval (water == 11)
        assert eval (colony_thirsty)
        run Rollback()
        pause until "Trade scrap"
        assert eval (water == 7)
        assert eval (colony_thirsty == False)
        assert eval (water_crisis_plan == "unresolved")

        # Take the reserve branch instead; the raid fires on refusal.
        click "Draw the cistern"
        assert eval (water == 12)
        assert eval (cistern_below_reserve)
        advance until "Pay the levy"   # Day 3 levy menu
        assert eval (day == 3)
        assert eval (water == 11)       # 12 less night upkeep at the boundary
        click "Refuse the levy"
        advance until "Open talks"   # act1_close menu after the raid
        assert eval (raid_triggered == True)
        assert eval (wounded_companion == "alice")
        assert eval (med_loss == 0)
        assert eval (food_loss == 1)

        click "Open talks"
        assert eval (probation)
        assert eval (line_standing == -6)
        assert eval (act1_commit == "talks")
        advance until label act2_stub

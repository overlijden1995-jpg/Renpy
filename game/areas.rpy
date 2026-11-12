## Ashfall — field areas (route stops 21–30).
##
## Art masters live in assets/env/ and are registered in MANIFEST.json and
## data/hotspots.json; the game copies are in game/images/env/. Each area is a
## background plate plus a short narrated description. Areas are reached through
## visit_area, or through the area_survey menu, which is not yet part of the
## day loop.

image bg orchard_ruin = "images/env/21_orchard_ruin.png"
image bg grain_silo = "images/env/22_grain_silo.png"
image bg fuel_depot = "images/env/23_fuel_depot.png"
image bg schoolhouse = "images/env/24_schoolhouse.png"
image bg solar_array = "images/env/25_solar_array.png"
image bg dam_spillway = "images/env/26_dam_spillway.png"
image bg bus_depot = "images/env/27_bus_depot.png"
image bg chapel_hall = "images/env/28_chapel_hall.png"
image bg lookout_ridge = "images/env/29_lookout_ridge.png"
image bg seed_bank = "images/env/30_seed_bank.png"

# Survey order follows the route numbering in MANIFEST.json.
define ASHFALL_AREA_ORDER = (
    "orchard_ruin",
    "grain_silo",
    "fuel_depot",
    "schoolhouse",
    "solar_array",
    "dam_spillway",
    "bus_depot",
    "chapel_hall",
    "lookout_ridge",
    "seed_bank",
)

define ASHFALL_AREAS = {
    "orchard_ruin": {
        "title": "Orchard Ruin",
        "image": "bg orchard_ruin",
        "desc": "Eighteen apple trees, dead since the second dry summer. Someone pruned them anyway, and the cuts are still clean. The irrigation channel runs past them to a pump house with no pump.",
    },
    "grain_silo": {
        "title": "Grain Silos",
        "image": "bg grain_silo",
        "desc": "Four silos stand over a cracked loading dock, and the gantry still carries its cable reels. Grain sacks have split on the concrete and been picked clean by birds long ago.",
    },
    "fuel_depot": {
        "title": "Fuel Depot",
        "image": "bg fuel_depot",
        "desc": "Three tanks behind a fence that has been cut and mended more than once. The hand pump still works, if you are willing to crank it for a long time. The ground is black with old spills.",
    },
    "schoolhouse": {
        "title": "Schoolhouse",
        "image": "bg schoolhouse",
        "desc": "Half the roof is gone. The blackboard survived. Someone has wiped it clean, carefully, and left the chalk in the tray.",
    },
    "solar_array": {
        "title": "Solar Array",
        "image": "bg solar_array",
        "desc": "Acres of broken panels catch the last of the light. Cables hang from a leaning pole. The turbine blade in the dirt would make a good roof, if anyone could lift it.",
    },
    "dam_spillway": {
        "title": "Dam Spillway",
        "image": "bg dam_spillway",
        "desc": "The dam holds back a muddy pool and a great deal of quiet. The spillway has been dry for years. Someone still walks the catwalk each morning to check the cracks.",
    },
    "bus_depot": {
        "title": "Bus Depot",
        "image": "bg bus_depot",
        "desc": "Three coach buses under a corrugated canopy. The repair pit is half full of rainwater and old tyres. The buses have seats and glass, and nothing else worth taking.",
    },
    "chapel_hall": {
        "title": "Chapel Hall",
        "image": "bg chapel_hall",
        "desc": "A stone chapel with a stove, a row of benches, and a noticeboard of lost-and-found notes. Lanterns burn here after dark. Nobody asks you to pray. They ask you to sit near the stove.",
    },
    "lookout_ridge": {
        "title": "Lookout Ridge",
        "image": "bg lookout_ridge",
        "desc": "A timber hut on stilts, and a flag that tells the valley who is watching. Below, the road bends past the ruined town. From up here you can see visitors an hour before they arrive.",
    },
    "seed_bank": {
        "title": "Seed Bank",
        "image": "bg seed_bank",
        "desc": "A steel vault door set into a concrete hillside, the one thing in the region built to outlast the war. Outside, raised beds are tested in the open. Inside, labelled packets wait. Keep the door shut.",
    },
}


init python:
    def ashfall_area_menu():
        options = [(ASHFALL_AREAS[key]["title"], key) for key in ASHFALL_AREA_ORDER]
        options.append(("Leave", None))
        return options


label visit_area(area_id):
    $ area_entry = ASHFALL_AREAS[area_id]
    $ area_title = area_entry["title"]
    $ area_desc = area_entry["desc"]
    scene black
    scene expression area_entry["image"] with dissolve
    centered "[area_title]"
    "[area_desc]"
    return


label area_survey:
    # Repeatable survey of the ten field areas. Returns when the player leaves.
    while True:
        $ area_pick = renpy.display_menu(ashfall_area_menu())
        if area_pick is None:
            return
        call visit_area(area_pick)

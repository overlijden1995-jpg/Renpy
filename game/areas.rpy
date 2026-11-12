## Ashfall — field areas (route stops 21–40).
##
## Art masters live in assets/env/ and are registered in MANIFEST.json and
## data/hotspots.json; the game copies are in game/env/ (kept outside
## game/images/ so the character and layer tools do not scan them). Each area is
## a background plate plus a short narrated description. Areas are reached
## through visit_area, or through the area_survey menu, which is not yet part of
## the day loop.

image bg orchard_ruin = "env/21_orchard_ruin.png"
image bg grain_silo = "env/22_grain_silo.png"
image bg fuel_depot = "env/23_fuel_depot.png"
image bg schoolhouse = "env/24_schoolhouse.png"
image bg solar_array = "env/25_solar_array.png"
image bg dam_spillway = "env/26_dam_spillway.png"
image bg bus_depot = "env/27_bus_depot.png"
image bg chapel_hall = "env/28_chapel_hall.png"
image bg lookout_ridge = "env/29_lookout_ridge.png"
image bg seed_bank = "env/30_seed_bank.png"
image bg post_office = "env/31_post_office.png"
image bg old_hospital_ward = "env/32_old_hospital_ward.png"
image bg public_library = "env/33_public_library.png"
image bg hotel_lobby = "env/34_hotel_lobby.png"
image bg bakery_kitchen = "env/35_bakery_kitchen.png"
image bg public_baths = "env/36_public_baths.png"
image bg substation_control = "env/37_substation_control.png"
image bg root_cellar = "env/38_root_cellar.png"
image bg tailor_workshop = "env/39_tailor_workshop.png"
image bg abandoned_cinema = "env/40_abandoned_cinema.png"

# Survey groups follow the route numbering in MANIFEST.json.
define ASHFALL_AREA_GROUPS = {
    "outdoors": (
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
    ),
    "indoors": (
        "post_office",
        "old_hospital_ward",
        "public_library",
        "hotel_lobby",
        "bakery_kitchen",
        "public_baths",
        "substation_control",
        "root_cellar",
        "tailor_workshop",
        "abandoned_cinema",
    ),
}

define ASHFALL_AREA_ORDER = ASHFALL_AREA_GROUPS["outdoors"] + ASHFALL_AREA_GROUPS["indoors"]

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
    "post_office": {
        "title": "Post Office",
        "image": "bg post_office",
        "desc": "Pigeonholes for every street in the old district, most of them empty. The sacks by the counter were sorted by street, and then nobody came to collect them.",
    },
    "old_hospital_ward": {
        "title": "Old Hospital Ward",
        "image": "bg old_hospital_ward",
        "desc": "Iron beds with bare mattresses, and drip stands no one has needed in years. The shutters were nailed over the windows, but light still comes through the gaps. Someone kept this room swept.",
    },
    "public_library": {
        "title": "Public Library",
        "image": "bg public_library",
        "desc": "The dome lets in a pale square of sky. Half the shelves are bare, and the rest hold books that water has swollen shut. Paper is kindling now, so the shelves are mostly kept for the sake of the room.",
    },
    "hotel_lobby": {
        "title": "Hotel Lobby",
        "image": "bg hotel_lobby",
        "desc": "A reception desk, a cracked chandelier, and a staircase that climbs toward a floor nobody visits. The key board has no keys. Boarded windows let the morning in through the gaps.",
    },
    "bakery_kitchen": {
        "title": "Bakery Kitchen",
        "image": "bg bakery_kitchen",
        "desc": "The brick oven is still warm on cold nights. Flour dust sits on everything, including the bread knife nobody has moved. Copper pans hang where the last baker left them.",
    },
    "public_baths": {
        "title": "Public Baths",
        "image": "bg public_baths",
        "desc": "The pool has not held clean water since the pumps died. A puddle of rain sits in the deep end, and the tiles are cold. Changing cubicles line the wall, each with its own bolt and hook.",
    },
    "substation_control": {
        "title": "Substation Control",
        "image": "bg substation_control",
        "desc": "The gauges read zero, the switches sit at off, and the monitors have been dark since the grid failed. The window looks out on the old road. Someone still checks the cable runs every week, out of habit.",
    },
    "root_cellar": {
        "title": "Root Cellar",
        "image": "bg root_cellar",
        "desc": "Jars of preserves line the shelves, and potatoes sit in sacks beside last season's onions in crates. The stairs lead up to a hatch and daylight. Keep the lantern lit, or the cellar goes dark fast.",
    },
    "tailor_workshop": {
        "title": "Tailor's Workshop",
        "image": "bg tailor_workshop",
        "desc": "Bolts of patched canvas and wool sit on the shelves. Three treadle machines still turn if you push hard enough. The cutting table is covered in pattern paper and pins, and the dress form wears a coat someone has been mending.",
    },
    "abandoned_cinema": {
        "title": "Abandoned Cinema",
        "image": "bg abandoned_cinema",
        "desc": "Red seats slope toward a blank screen. The chandelier has come loose at one end, and the projection booth door swings on one hinge. Nobody has shown a film here for years, but people still gather for the quiet.",
    },
}


init python:
    def ashfall_group_menu():
        return [
            ("Outdoors", "outdoors"),
            ("Indoors", "indoors"),
            ("Leave", None),
        ]

    def ashfall_area_menu(group):
        options = [(ASHFALL_AREAS[key]["title"], key) for key in ASHFALL_AREA_GROUPS[group]]
        options.append(("Back", "back"))
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
    # Repeatable survey of the twenty field areas. Returns when the player leaves.
    while True:
        $ group_pick = renpy.display_menu(ashfall_group_menu())
        if group_pick is None:
            return
        while True:
            $ area_pick = renpy.display_menu(ashfall_area_menu(group_pick))
            if area_pick == "back":
                break
            call visit_area(area_pick)

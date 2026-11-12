################################################################################
## Ashfall — GUI palette, borders and shared defines.
##
## Art direction: rusted olive-drab metal, bone and brass. The generated UI
## plates referenced by screens.rpy live in game/images/ui/ (keyed and
## trimmed; regenerate with tools/alphakey.py and the manifest).
##
# This file deliberately only defines plain data. Screen layouts, styles and
# frame assembly live in screens.rpy, which runs after this file.

init offset = -2

## -- Palette -----------------------------------------------------------------

## Primary text on dark metal.
define ASHFALL_BONE = "#E9E2D0"
## Secondary / inactive text.
define ASHFALL_BONE_DIM = "#B0A892"
## Brass accent: titles, section labels, focus highlights.
define ASHFALL_ACCENT = "#D8A24A"
## Hovered text.
define ASHFALL_HOVER = "#FFFFFF"
## Disabled text.
define ASHFALL_INSENSITIVE = "#E9E2D044"
## Low-resource warning colour (HUD).
define ASHFALL_LOW = "#E05B3A"

## Dark ink on light (bone) panels, e.g. the dialogue plate.
define ASHFALL_INK = "#26201A"
## Rust used for the speaker name on the dialogue plate.
define ASHFALL_RUST = "#8F3B1B"

## Sheet-metal tones derived from the panel art (for bars and chips).
define ASHFALL_IRON = "#2B2721"
define ASHFALL_IRON_LIGHT = "#3B362E"
define ASHFALL_OLIVE = "#6B7042"

## Full-screen dimming overlay used behind menus and the main menu.
define ASHFALL_SCRIM = "#000000a8"

## -- Borders -----------------------------------------------------------------
# Nine-slice insets for the generated plates. Ren'Py scales the edge centres
# and keeps the corners untouched.

define ash_panel_borders = Borders(34, 30, 34, 30)
define ash_button_borders = Borders(30, 26, 30, 26)
define ash_dialogue_borders = Borders(36, 32, 36, 32)
define ash_chip_borders = Borders(20, 15, 20, 15)

## -- Screen geometry -----------------------------------------------------------

define ash_screen_width = 1280
define ash_screen_height = 720

## -- Low-resource thresholds (HUD) --------------------------------------------

define ASHFALL_LOW_WATER = 2
define ASHFALL_LOW_SCRAP = 4
define ASHFALL_LOW_FOOD = 2
define ASHFALL_LOW_MEDS = 1

## -- Menu background ----------------------------------------------------------
# The colony gate at dawn, baked at exactly 1280x720 so the renderer never has
# to rescale it (master: assets/env/01_colony_gate.png). Also used (dimmed)
# behind in-game menus.

define ash_menu_background = "images/ui/menu_gate.png"

## -- HUD icons ----------------------------------------------------------------
# Pre-baked at their display sizes; masters remain in this directory.

define ash_icon_water = "images/ui/hud_water.png"
define ash_icon_scrap = "images/ui/hud_scrap.png"
define ash_icon_food = "images/ui/hud_food.png"
define ash_icon_meds = "images/ui/hud_meds.png"

## -- Bars ---------------------------------------------------------------------

define ash_bar_height = 26
define ash_vbar_width = 26

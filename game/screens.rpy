################################################################################
## Ashfall — screens.
##
## The look is rusted olive-drab metal with bone and brass (see gui.rpy for
## the palette and plate borders). Screens here cover:
##
##   say / choice / input     — in-game dialogue and branch choices
##   hud                      — persistent resource overlay (Water/Scrap/
##                              Food/Meds/Day/Phase) with low warnings
##   quick_menu               — persistent button bar (H key area)
##   main_menu / game_menu    — title screen and the shared game-menu frame
##   save / load              — slot grid backed by engine saves
##   preferences              — display/skip/rollback/audio preferences
##   history                  — dialogue history
##   confirm                  — modal yes/no used by quit/main menu/delete
##   skip_indicator / notify  — skip banner and toast messages
##
## Do not introduce colour literals in this file; extend gui.rpy instead.

init offset = -1


################################################################################
## Base styles
################################################################################

style default:
    font "DejaVuSans.ttf"

style input is default
style hyperlink_text is default
style gui_text is default

style button is default
style button_text is default
style window is default
style frame is default
style label is default
style label_text is default
style vbox is default
style hbox is default
style viewport is default
style grid is default
style fixed is default

## Text properties for buttons: bone on dark metal plates.
style ash_button_text:
    color ASHFALL_BONE
    hover_color ASHFALL_HOVER
    selected_color ASHFALL_ACCENT
    insensitive_color ASHFALL_INSENSITIVE
    size 22
    yalign 0.5

## Image-framed button chrome (02 normal / 03 hover / 04 pressed).
style ash_button:
    background Frame("images/ui/02_button_normal.png", ash_button_borders)
    hover_background Frame("images/ui/03_button_hover.png", ash_button_borders)
    selected_background Frame("images/ui/04_button_pressed.png", ash_button_borders)
    insensitive_background Frame("images/ui/02_button_normal.png", ash_button_borders)
    xpadding 28
    ypadding 12
    focus_mask None

style bar:
    ysize ash_bar_height
    left_bar Solid(ASHFALL_ACCENT)
    right_bar Solid(ASHFALL_IRON)

style vbar:
    xsize ash_vbar_width
    top_bar Solid(ASHFALL_IRON)
    bottom_bar Solid(ASHFALL_ACCENT)
    bar_vertical True

style slider is bar
style vslider is vbar

style scrollbar:
    thumb Solid(ASHFALL_ACCENT)
    base_bar Solid(ASHFALL_IRON)
    unscrollable "hide"

style vscrollbar is scrollbar


################################################################################
## Say screen — the dialogue plate (10_dialogue_box.png)
################################################################################

screen say(who, what):

    window:
        id "window"
        style "say_window"

        vbox:
            style "say_vbox"

            if who is not None:
                text who id "who" style "say_name"

            text what id "what" style "say_dialogue"

    ## Speaker portraits / side images, when the script supplies them. Do not
    ## display on the small variant — there is no room.
    if not renpy.variant("small"):
        add SideImage() xalign 0.0 yalign 1.0


style say_window:
    background Frame("images/ui/10_dialogue_box.png", ash_dialogue_borders)
    xalign 0.5
    yalign 1.0
    yoffset -12
    xsize 1150
    ysize 180
    padding (46, 18, 46, 18)

style say_vbox is vbox

style say_vbox:
    xfill True
    yalign 0.5
    spacing 6

style say_name:
    font "DejaVuSans.ttf"
    size 19
    bold True
    color ASHFALL_RUST

style say_dialogue:
    font "DejaVuSans.ttf"
    size 22
    color ASHFALL_INK
    xfill True
    adjust_spacing False


################################################################################
## Choice screen — the branch-point menu
################################################################################

screen choice(items):
    style_prefix "choice"

    vbox:
        style "choice_vbox"
        for i in items:
            textbutton i.caption action i.action


style choice_vbox is vbox
style choice_button is ash_button
style choice_button_text is ash_button_text

style choice_vbox:
    xalign 0.5
    ypos 300
    yanchor 0.5
    spacing 14

style choice_button:
    xminimum 660
    padding (34, 12)

style choice_button_text:
    textalign 0.5
    size 23


################################################################################
## Input screen
################################################################################

screen input(prompt):
    style_prefix "input"

    window:
        style "say_window"

        vbox:
            spacing 8

            text prompt style "input_prompt"
            input id "input"

style input_prompt is default
style input_prompt:
    color ASHFALL_INK
    size 20

style input is default
style input:
    color ASHFALL_INK
    size 22


################################################################################
## HUD — persistent colony readout
##
## Water / Scrap / Food / Meds with icons, plus Day / Phase. Resource values
## at or below their warning threshold render in the low colour and gain a
## "!" marker (ids hud_<name>_low).
################################################################################

screen hud():
    zorder 40

    ## Hidden on the title screen; shown during play and in-game menus.
    if not main_menu:

        $ phase_label = str(phase).capitalize()

        hbox:
            style_prefix "hud"
            xalign 0.5
            ypos 10
            spacing 8

            frame:
                style "hud_chip"
                hbox:
                    spacing 6
                    text "Day" style "hud_chip_label"
                    text "[day]" id "hud_day" style "hud_chip_value"

            frame:
                style "hud_chip"
                hbox:
                    spacing 6
                    text "Phase" style "hud_chip_label"
                    text "[phase_label]" id "hud_phase" style "hud_chip_value"

            frame:
                style "hud_chip"
                hbox:
                    spacing 6
                    add ash_icon_water yalign 0.5
                    text "Water" style "hud_chip_label"
                    if water <= ASHFALL_LOW_WATER:
                        text "[water]" id "hud_water" color ASHFALL_LOW style "hud_chip_value"
                        text "!" id "hud_water_low" color ASHFALL_LOW style "hud_chip_alert"
                    else:
                        text "[water]" id "hud_water" style "hud_chip_value"

            frame:
                style "hud_chip"
                hbox:
                    spacing 6
                    add ash_icon_scrap yalign 0.5
                    text "Scrap" style "hud_chip_label"
                    if scrap <= ASHFALL_LOW_SCRAP:
                        text "[scrap]" id "hud_scrap" color ASHFALL_LOW style "hud_chip_value"
                        text "!" id "hud_scrap_low" color ASHFALL_LOW style "hud_chip_alert"
                    else:
                        text "[scrap]" id "hud_scrap" style "hud_chip_value"

            frame:
                style "hud_chip"
                hbox:
                    spacing 6
                    add ash_icon_food yalign 0.5
                    text "Food" style "hud_chip_label"
                    if food <= ASHFALL_LOW_FOOD:
                        text "[food]" id "hud_food" color ASHFALL_LOW style "hud_chip_value"
                        text "!" id "hud_food_low" color ASHFALL_LOW style "hud_chip_alert"
                    else:
                        text "[food]" id "hud_food" style "hud_chip_value"

            frame:
                style "hud_chip"
                hbox:
                    spacing 6
                    add ash_icon_meds yalign 0.5
                    text "Meds" style "hud_chip_label"
                    if meds <= ASHFALL_LOW_MEDS:
                        text "[meds]" id "hud_meds" color ASHFALL_LOW style "hud_chip_value"
                        text "!" id "hud_meds_low" color ASHFALL_LOW style "hud_chip_alert"
                    else:
                        text "[meds]" id "hud_meds" style "hud_chip_value"


style hud_chip is default
style hud_chip_label is default
style hud_chip_value is default
style hud_chip_alert is default

style hud_chip:
    background Frame("images/ui/01_nine_slice_panel.png", ash_chip_borders)
    xpadding 16
    ypadding 6

style hud_chip_label:
    font "DejaVuSans.ttf"
    size 15
    color ASHFALL_BONE_DIM
    yalign 0.5

style hud_chip_value:
    font "DejaVuSans.ttf"
    size 18
    bold True
    color ASHFALL_BONE
    yalign 0.5

style hud_chip_alert:
    font "DejaVuSans.ttf"
    size 18
    bold True
    yalign 0.5


init python:
    config.overlay_screens.append("hud")
    config.overlay_screens.append("quick_menu")


################################################################################
## Quick menu — persistent in-game button bar
################################################################################

screen quick_menu():

    zorder 100

    if quick_menu and not main_menu:

        hbox:
            style_prefix "quick"
            xalign 0.5
            yalign 1.0
            yoffset -6
            spacing 6

            textbutton _("Back") action Rollback()
            textbutton _("History") action ShowMenu("history")
            textbutton _("Skip") action Skip() alternate Skip(fast=True, confirm=True)
            textbutton _("Auto") action Preference("auto-forward", "toggle")
            textbutton _("Save") action ShowMenu("save")
            textbutton _("Quick Save") action QuickSave()
            textbutton _("Quick Load") action QuickLoad()
            textbutton _("Prefs") action ShowMenu("preferences")
            textbutton _("Hide") action HideInterface()
            textbutton _("Quit") action Quit()


default quick_menu = True

style quick_button is ash_button
style quick_button_text is ash_button_text

style quick_button:
    xpadding 12
    ypadding 6
    background Frame("images/ui/01_nine_slice_panel.png", ash_chip_borders)
    hover_background Frame("images/ui/03_button_hover.png", ash_chip_borders)

style quick_button_text:
    size 16
    color ASHFALL_BONE_DIM
    hover_color ASHFALL_HOVER


################################################################################
## Navigation — shared menu column (main menu and game menus)
################################################################################

screen navigation():

    vbox:
        style_prefix "navigation"
        spacing 12

        if main_menu:

            textbutton _("Start") action Start()

        else:

            textbutton _("History") action ShowMenu("history")

            textbutton _("Save") action ShowMenu("save")

        textbutton _("Load") action ShowMenu("load")

        textbutton _("Prefs") action ShowMenu("preferences")

        if _in_replay:

            textbutton _("End Replay") action EndReplay(confirm=True)

        elif not main_menu:

            textbutton _("Main Menu") action MainMenu()

        textbutton _("Quit") action Quit()


style navigation_button is default
style navigation_button_text is default
style navigation_vbox is vbox

style navigation_button:
    background Frame("images/ui/02_button_normal.png", ash_button_borders)
    hover_background Frame("images/ui/03_button_hover.png", ash_button_borders)
    insensitive_background Frame("images/ui/02_button_normal.png", ash_button_borders)
    focus_mask None
    xminimum 190
    xpadding 20
    ypadding 10

style navigation_button_text:
    font "DejaVuSans.ttf"
    size 24
    color ASHFALL_BONE
    hover_color ASHFALL_HOVER
    selected_color ASHFALL_ACCENT
    insensitive_color ASHFALL_INSENSITIVE
    xalign 0.0

style navigation_vbox:
    xminimum 210
    yalign 0.5


################################################################################
## Main menu
################################################################################

label main_menu:
    call screen main_menu
    return


screen main_menu():

    ## Replaces any other menu screen.
    tag menu

    style_prefix "main_menu"

    add ash_menu_background

    ## Left scrim to seat the title and buttons.
    add Solid(ASHFALL_SCRIM) xysize (660, 720)

    vbox:
        xpos 84
        yalign 0.60
        spacing 20

        text "ASHFALL" style "main_menu_title"
        text "A colony at the end of the world." style "main_menu_subtitle"

        null height 26

        use navigation

    text "v[config.version]" style "main_menu_version" xalign 0.985 yalign 0.97


style main_menu_title is default
style main_menu_subtitle is default
style main_menu_version is default

style main_menu_title:
    font "DejaVuSans.ttf"
    bold True
    size 96
    color ASHFALL_BONE
    outlines [ (2, "#000000", 4, 4) ]

style main_menu_subtitle:
    font "DejaVuSans.ttf"
    italic True
    size 20
    color ASHFALL_BONE_DIM
    xpos 4

style main_menu_version:
    font "DejaVuSans.ttf"
    size 15
    color ASHFALL_BONE_DIM


################################################################################
## Game menu — shared frame for save / load / preferences / history
################################################################################

screen game_menu(title, scroll=None):

    style_prefix "game_menu"

    add ash_menu_background
    add Solid(ASHFALL_SCRIM)

    frame:
        style "game_menu_panel"

        hbox:
            spacing 34

            frame:
                style "game_menu_nav_frame"
                use navigation

            frame:
                style "game_menu_content_frame"

                vbox:
                    style "game_menu_content_vbox"

                    if title:
                        label title style "game_menu_title"

                    if scroll == "viewport":

                        viewport:
                            style "game_menu_viewport"
                            scrollbars "vertical"
                            mousewheel True
                            draggable True
                            pagekeys True

                            vbox:
                                style "game_menu_transclude_vbox"
                                transclude

                    elif scroll == "vpgrid":

                        vpgrid:
                            cols 1
                            yinitial 1.0

                            scrollbars "vertical"
                            mousewheel True
                            draggable True
                            pagekeys True

                            style "game_menu_vpgrid"
                            transclude

                    else:

                        transclude

    textbutton _("Return"):
        style "return_button"

        action Return()

    if main_menu:
        key "game_menu" action ShowMenu("main_menu")
    else:
        key "game_menu" action Return()


style game_menu_panel is default
style game_menu_nav_frame is default
style game_menu_content_frame is default
style game_menu_viewport is viewport
style game_menu_transclude_vbox is vbox
style game_menu_content_vbox is vbox
style game_menu_vpgrid is vpgrid
style game_menu_title is default
style return_button is navigation_button
style return_button_text is navigation_button_text

style game_menu_panel:
    background Frame("images/ui/01_nine_slice_panel.png", ash_panel_borders)
    xalign 0.5
    yalign 0.5
    xsize 1130
    ysize 610
    padding (40, 26)

style game_menu_nav_frame:
    xminimum 220
    yfill True
    yalign 0.5
    background None

style game_menu_content_frame:
    xfill True
    yfill True
    xminimum 780
    background None

style game_menu_viewport:
    xsize 750
    ysize 445

style game_menu_vpgrid:
    xsize 750
    ysize 445

style game_menu_transclude_vbox:
    spacing 8

style game_menu_content_vbox:
    spacing 10
    yfill True

style game_menu_title:
    font "DejaVuSans.ttf"
    bold True
    size 34
    color ASHFALL_ACCENT
    outlines [ (1, "#000000", 2, 2) ]
    top_margin 4
    bottom_margin 2

style return_button:
    xalign 0.5
    xoffset 430
    yalign 0.5
    yoffset 232


################################################################################
## Save / Load
################################################################################

screen save():

    tag menu

    use file_slots(_("Save"))


screen load():

    tag menu

    use file_slots(_("Load"))


screen file_slots(title):

    default page_name_value = FilePageNameInputValue(pattern=_("Page {}"), auto=_("Automatic saves"), quick=_("Quick saves"))

    use game_menu(_(title)):

        fixed:

            ## The page name input gets the enter event before the buttons.
            order_reverse True

            ## The current page name; clicking toggles its editability.
            button:
                style "page_label"

                key_events True
                xalign 0.5
                action page_name_value.Toggle()

                input:
                    style "page_label_text"
                    value page_name_value

            ## The slot grid.
            grid 3 2:
                style_prefix "slot"

                xalign 0.5
                yalign 0.5
                yoffset 12
                spacing 14

                for i in range(6):

                    $ slot = i + 1

                    button:
                        action FileAction(slot)

                        has vbox

                        add FileScreenshot(slot) xalign 0.5 yalign 0.0

                        hbox:
                            spacing 10
                            text "Slot [slot]" style "slot_number_text"

                            text FileTime(slot, format=_("{#file_time}%A, %B %d %Y, %H:%M"), empty=_("empty slot")):
                                style "slot_time_text"

                        key "save_delete" action FileDelete(slot)

            ## Page navigation.
            hbox:
                style_prefix "page"

                xalign 0.5
                yalign 1.0
                spacing 6

                textbutton _("<") action FilePagePrevious()
                key "save_page_prev" action FilePagePrevious()

                if config.has_autosave:
                    textbutton _("{#auto_page}A") action FilePage("auto")

                if config.has_quicksave:
                    textbutton _("{#quick_page}Q") action FilePage("quick")

                for page in range(1, 10):
                    textbutton "[page]" action FilePage(page)

                textbutton _(">") action FilePageNext()
                key "save_page_next" action FilePageNext()


style page_label is default
style page_label_text is default
style page_button is ash_button
style page_button_text is ash_button_text
style slot_button is ash_button
style slot_button_text is ash_button_text
style slot_time_text is slot_button_text
style slot_number_text is slot_button_text

style page_label:
    xpadding 40
    ypadding 2
    background None

style page_label_text:
    font "DejaVuSans.ttf"
    size 18
    color ASHFALL_BONE_DIM
    textalign 0.5
    layout "subtitle"
    hover_color ASHFALL_ACCENT

style page_button:
    xpadding 8
    ypadding 2
    xminimum 44

style page_button_text:
    size 20

style slot_button:
    xpadding 10
    ypadding 8
    xsize 250
    ysize 216

style slot_button_text:
    size 15

style slot_number_text:
    color ASHFALL_BONE_DIM
    size 13
    yalign 0.5

style slot_time_text:
    size 13
    yalign 0.5


################################################################################
## Preferences
################################################################################

screen preferences():

    tag menu

    use game_menu(_("Preferences"), scroll="viewport"):

        vbox:
            style "preferences_vbox"

            hbox:
                box_wrap True
                spacing 60

                if renpy.variant("pc") or renpy.variant("web"):

                    vbox:
                        style_prefix "radio"
                        label _("Display")
                        textbutton _("Window") action Preference("display", "window")
                        textbutton _("Fullscreen") action Preference("display", "fullscreen")

                vbox:
                    style_prefix "check"
                    label _("Skip")
                    textbutton _("Unseen Text") action Preference("skip", "toggle")
                    textbutton _("After Choices") action Preference("after choices", "toggle")
                    textbutton _("Transitions") action InvertSelected(Preference("transitions", "toggle"))

                vbox:
                    style_prefix "radio"
                    label _("Rollback Side")
                    textbutton _("Left") action Preference("rollback side", "left")
                    textbutton _("Right") action Preference("rollback side", "right")
                    textbutton _("Disable") action Preference("rollback side", "disable")

            null height 28

            hbox:
                style_prefix "slider"
                spacing 60

                vbox:
                    xsize 470

                    label _("Text Speed")
                    bar value Preference("text speed")

                    null height 8

                    label _("Auto-Forward Time")
                    bar value Preference("auto-forward time")

                vbox:
                    xsize 470

                    label _("Music Volume")
                    bar value Preference("music volume")

                    null height 26

                    label _("Audio")

                    textbutton _("Mute All"):
                        action Preference("all mute", "toggle")
                        style "mute_all_button"


style preferences_vbox is vbox
style preferences_vbox:
    spacing 4

style pref_label is default
style pref_label_text is default
style pref_vbox is vbox

style radio_label is pref_label
style radio_label_text is pref_label_text
style radio_button is ash_button
style radio_button_text is ash_button_text
style radio_vbox is pref_vbox

style check_label is pref_label
style check_label_text is pref_label_text
style check_button is ash_button
style check_button_text is ash_button_text
style check_vbox is pref_vbox

style slider_label is pref_label
style slider_label_text is pref_label_text
style slider_slider is slider
style slider_button is ash_button
style slider_button_text is ash_button_text
style slider_vbox is pref_vbox

style mute_all_button is check_button
style mute_all_button_text is check_button_text

style pref_label:
    top_margin 10
    bottom_margin 4

style pref_label_text:
    font "DejaVuSans.ttf"
    size 26
    bold True
    color ASHFALL_ACCENT
    yalign 1.0

style pref_vbox:
    xsize 225
    spacing 4

style radio_button:
    xpadding 20
    ypadding 8
    xminimum 170

style radio_button_text:
    size 20

style check_button:
    xpadding 20
    ypadding 8
    xminimum 170

style check_button_text:
    size 20

style slider_label_text:
    yalign 1.0

style slider_slider:
    xsize 380

style slider_button:
    yalign 0.5


################################################################################
## History
################################################################################

define gui_history_allow_tags = { "alt", "noalt", "rt", "rb", "art" }

screen history():

    tag menu

    predict False

    use game_menu(_("History"), scroll="vpgrid"):

        style_prefix "history"

        for h in _history_list:

            window:

                has fixed:
                    yfit True

                if h.who:

                    label h.who:
                        style "history_name"
                        substitute False

                        if "color" in h.who_args:
                            text_color h.who_args["color"]

                $ what = renpy.filter_text_tags(h.what, allow=gui_history_allow_tags)
                text what:
                    substitute False

        if not _history_list:
            label _("The dialogue history is empty.")


style history_window is default
style history_name is default
style history_name_text is default
style history_text is default
style history_label is default
style history_label_text is default

style history_window:
    xfill True
    bottom_margin 10
    background None

style history_name:
    xfill True
    color ASHFALL_ACCENT

style history_name_text:
    font "DejaVuSans.ttf"
    size 18
    bold True

style history_text:
    font "DejaVuSans.ttf"
    size 19
    color ASHFALL_BONE
    xsize 700

style history_label:
    color ASHFALL_BONE_DIM

style history_label_text:
    size 20
    italic True


################################################################################
## Confirm — modal yes/no
################################################################################

screen confirm(message, yes_action, no_action):

    modal True
    zorder 200
    style_prefix "confirm"

    add Solid("#000000cc")

    frame:
        style "confirm_frame"

        vbox:
            xalign 0.5
            yalign 0.5
            spacing 36

            label message style "confirm_label"

            hbox:
                xalign 0.5
                spacing 60

                textbutton _("Yes") action yes_action
                textbutton _("No") action no_action

    key "game_menu" action no_action


style confirm_frame is default
style confirm_label is default
style confirm_label_text is default
style confirm_button is ash_button
style confirm_button_text is ash_button_text

style confirm_frame:
    background Frame("images/ui/01_nine_slice_panel.png", ash_panel_borders)
    xalign 0.5
    yalign 0.5
    xminimum 420
    padding (48, 30)

style confirm_label:
    xalign 0.5

style confirm_label_text:
    font "DejaVuSans.ttf"
    size 24
    color ASHFALL_BONE
    textalign 0.5

style confirm_button:
    xminimum 130
    padding (26, 10)

style confirm_button_text:
    textalign 0.5


################################################################################
## Skip indicator
################################################################################

screen skip_indicator():

    zorder 100
    style_prefix "skip"

    frame:
        hbox:
            spacing 6

            text _("Skipping") style "skip_text"

            text "▸" at delayed_blink(0.0, 1.0) style "skip_text"
            text "▸" at delayed_blink(0.2, 1.0) style "skip_text"
            text "▸" at delayed_blink(0.4, 1.0) style "skip_text"


transform delayed_blink(delay, cycle):
    alpha .5

    pause delay

    block:
        linear .2 alpha 1.0
        pause .2
        linear .2 alpha 0.5
        pause (cycle - .4)
        repeat


style skip_frame is default
style skip_text is default
style skip_triangle is skip_text

style skip_frame:
    ypos 48
    xpos 16
    background Frame("images/ui/01_nine_slice_panel.png", ash_chip_borders)
    padding (18, 8)

style skip_text:
    font "DejaVuSans.ttf"
    size 16
    color ASHFALL_BONE


################################################################################
## Notify — toast messages
################################################################################

screen notify(message):

    zorder 100
    style_prefix "notify"

    frame at notify_appear:
        text "[message!tq]"

    timer 3.25 action Hide("notify")


transform notify_appear:
    on show:
        alpha 0
        linear .25 alpha 1.0
    on hide:
        linear .5 alpha 0.0


style notify_frame is default
style notify_text is default

style notify_frame:
    ypos 64
    xalign 0.5
    background Frame("images/ui/01_nine_slice_panel.png", ash_chip_borders)
    padding (24, 10)

style notify_text:
    font "DejaVuSans.ttf"
    size 17
    color ASHFALL_BONE

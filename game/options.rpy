## Ashfall — project configuration.

# The game's title. This is shown in the window title and menus.
define config.name = "Ashfall"

# The game's version.
define config.version = "0.1.0"

# Ren'Py script language compatibility pin.
define config.script_version = (8, 3, 0)

# Saves stay isolated from other projects using the same Ren'Py installation.
define config.save_directory = "ashfall-1"

# Enable developer conveniences during development.
define config.developer = True
define config.console = True

init python:
    # Package the game source and assets for each supported build.
    build.classify("game/**", "all")

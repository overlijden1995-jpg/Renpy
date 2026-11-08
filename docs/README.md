# Ashfall project notes

Ashfall is a Ren'Py 8.3 project written for the Ren'Py Python 3 runtime. The script-language compatibility pin is `(8, 3, 0)` in `game/options.rpy`. Use the Ren'Py 8.3 SDK/toolchain for development and builds; do not silently upgrade the project baseline without testing scripts, saves, and distribution builds.

## Build order

1. Establish the project shell: configuration, entry point, and stub modules.
2. Add shared definitions and state (resources, companions, trust, factions, and day phases).
3. Implement the colony loop: navigation imagemap, inventory, phase transitions, building placement, companion assignment, and resource accounting.
4. Add threats, raid pressure, and faction interactions; then tune the colony-value scaling and economy.
5. Write the P17 cold open and the main narrative, integrating choices with the colony systems.
6. Author companion trust-gated bond scenes, then gallery and presentation polish.
7. Run the project in the pinned Ren'Py 8.3 SDK, lint it, test fresh and continued saves, and verify distributable builds.

The current script deliberately jumps to a returning P17 cold-open stub. The empty `.rpy` modules mark future implementation boundaries; bond-scene labels are present as empty placeholders.

## Content and asset policy

**Image prompts stay SFW. Adult content is text-only for now.** Keep generated and commissioned visual assets non-explicit. See [STYLE.md](STYLE.md) for the full style and prompt guidance.

See [WORLD.md](WORLD.md), [MECHANICS.md](MECHANICS.md), and [ROSTER.md](ROSTER.md) for the setting, systems, and companion baseline.

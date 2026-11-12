# Whole-project QA report

**Status: PASS for derived assets, reference runtime, lint, and the Ren'Py engine playthrough (headless).** The former 72/80 sprite-count blocker is retracted because the derived raw-source count passes: 6 characters × 10 frames = 60 frames. The twelve derived blush overlays remain declared assets but are not counted as raw source frames. See `docs/CANON.md`.

## Results

| Check | Result | Evidence / notes |
| --- | --- | --- |
| Character frame anchors | **PASS** | `tools/validate.py` compares foot-midline anchors across base frames; measured maximum drift is below the 6 px limit for all six characters. Alice 0.5 px; Denice 0 px; MC 0.5 px; Sable 0.5 px; Sophia 1.118 px; Tory 0 px. |
| Manifest assets | **PASS** | All 92 declared assets resolve to project-contained files and their image data verifies. No duplicate asset paths or unresolved manifest IDs were reported. |
| Sprite-frame requirement | **PASS** | Raw source count is 60: Alice 10, Denice 10, MC 10, Sable 10, Sophia 10, and Tory 10. `spriteFrames.expectedCount` is 60, `assetIds` contains 60 IDs, and all 60 unique files exist. The additional twelve blush overlays remain available through `assets` and are excluded from this raw-source contract. |
| Act 1 playthrough to act break | **PASS (Ren'Py engine, headless)** | `./run.sh . test ashfall` runs the Ren'Py 8.6 test suite in `game/tests/playthrough.rpy`: `playthrough_to_act2` (full Act 1 to the act break), `save_load_rollback_day2` (engine save at the Day 2 water crisis, engine load into the rations branch, rollback to the crisis menu, the reserve branch, the raid, act break), and `hud_overlay` (HUD render + low-resource warnings). 3/3 testcases, 5/5 hooks, 73/73 assertions pass. See the 2026-11-09 engine-evidence addendum. |
| Act break canon state | **PASS (static and state model)** | `probation` has one assignment, `$ probation = True`, and remained true at the modeled act break. A dialogue-string scan of `game/*.rpy` found zero references to Mara, Vesper, Ren, Iona, Brick, Tamsin, or Juno. |
| Ren'Py lint | **PASS** | `./run.sh . lint --error-code` exits 0: 170 dialogue blocks, 2,904 words, 16,280 characters. Requires the Python 3.12 uv environment (`uv sync`); the sandbox system Python 3.11 is not sufficient. |
| Hotspots | **PASS (static reachability)** | 10 scenes and 45 hotspot rectangles validated. Every scene background resolves through a manifest asset ID; rectangles are in the 1920×1080 canvas, and each hotspot center maps inside the view at zoom 1.0, 1.25, and 1.8. |
| Quest completion | **PASS (reference runtime)** | Runtime QA completed all seven quests through game-model/dialogue events: five resource bottlenecks, the faction delivery, and the rescue. |
| Reference save/load round trips | **PASS** | Colony snapshots restore byte-for-data-equivalent state; dialogue flags and unlocked bond-scene state round-trip; all three save slots round-trip and invalid slot 4 is rejected. |
| Hardcoded asset paths | **PASS** | Runtime engine and game-data scan found no direct image-file paths outside `MANIFEST.json`; hotspot backgrounds and dialogue portraits use manifest IDs. |

## Commands run

```sh
./run.sh . lint --error-code
python3 tools/validate.py
node tools/qa_runtime.mjs
python3 tools/tickalign.py --input assets/characters/source --output assets/characters/aligned --style docs/STYLE.md
python3 tools/alphakey.py --input assets/characters/aligned --output assets/characters/keyed --tolerance 40
python3 tools/validate.py --whole-project
./run.sh .
source /home/user/renpy-deps/env.sh   # exports SDL_VIDEODRIVER/AUDIODRIVER=dummy,
                                       # RENPY_RENDERER=sw, SDL_NO_SIGNAL_HANDLERS=1,
                                       # SDL_QUIT_ON_LAST_WINDOW_CLOSE=0, RENPY_PERFORMANCE_TEST=0,
                                       # PKG_CONFIG_PATH + PATH with prefix/bin (pkg-config = pkgconf)
env "renpy.pygame_AVOID_GL=1" ./run.sh . test ashfall
```

Note: `PKG_CONFIG` no longer needs (or accepts) the former `pkg-config-keep` shim; the from-source `prefix/bin` is on `PATH` and its `pkg-config` is the pkgconf binary.

The first validator invocation failed because Pillow was absent. After installing Pillow and generating the ignored aligned/keyed intermediates, `python3 tools/validate.py` and `python3 tools/validate.py --whole-project` both returned `validation passed`. Runtime QA returned `passed: true` with 5 resource quests, the faction quest, the rescue quest, colony and dialogue round trips, and 3 save slots confirmed.

## Addendum — 2026-11-09 (stops 11–20 and itinerary navigation)

- Ten new background plates `assets/env/11_mess_hall.png` … `assets/env/20_river_crossing.png` (1920×1080, hand-painted cel-shaded style) were generated and registered in `MANIFEST.json` (assets `env.11_mess_hall` … `env.20_river_crossing`, plus twenty `scenes` entries in route order) and in `data/hotspots.json` (five inspectable hotspots per new scene; canvas 1920×1080 unchanged). `python3 tools/validate.py --whole-project` re-run after regenerating the ignored `assets/characters/aligned` and `assets/characters/keyed` intermediates: **validation passed** (manifest resolution, hotspot bounds and reachability, quest/dialogue runtime round-trips, hardcoded-path policy).
- Field engine navigation switched from click-to-move walking (canvas pathfinding) to itinerary buttons: a numbered "Itinerary" sidebar (`#itineraryList`) travels to all twenty stops; the location dropdown and the on-canvas walker were removed. Click-to-inspect hotspots, wheel zoom, right-drag pan, the F1 debug overlay, the inventory strip, and three-slot save/load are unchanged. Legacy saves containing an `actor` position still load; the field is ignored and new saves omit it.

## Validation limits

The engine playthrough now runs end to end headlessly (see addendum). It has not been exercised on real audio/video hardware or in a windowed session, and the suite intentionally covers only Act 1. Structural checks separately confirmed the exact fifteen canonical bond labels, the five-row roster, all sixty raw frame paths, valid manifest JSON, and generator output byte-identical to `game/definitions.rpy`.

## Addendum — 2026-11-09 (engine evidence: headless playthrough)

Item: run the Ren'Py engine end to end and attach the evidence to this report (previously BLOCKED).

Environment (built this session, outside the repo):

- `uv sync` provides Python 3.12.16; compiled Ren'Py extension modules were built against a from-source prefix at `/home/user/renpy-deps/prefix` (SDL 3.4.20 with dummy/offscreen video, FFmpeg, HarfBuzz, Freetype rebuilt with Brotli so `.woff2` fonts — the engine's DejaVu substitutes — load, zlib, OpenSSL).
- Freetype without Brotli raised `renpy.text.hbfont.FreetypeError: 2: b'unknown file format'` on every Say; after the Brotli rebuild the suite boots and renders.
- SDL 3 was initially linked **statically** into every Ren'Py extension module. Each module then carried its own copy of the file-scope `SDL_surface_magic`, and with `sys.getdlopenflags() == 2` (RTLD_NOW, no RTLD_GLOBAL) the copies never interpose, so `SDL_SurfaceValid` failed across modules and `SDL_BlitSurfaceScaled` returned false — a hard crash at `renpy/pygame/transform.pyx` during the main menu. Fix (outside the repo): SDL 3.4.20 and SDL3_image 3.4.8 were rebuilt with `BUILD_SHARED_LIBS=ON` into the prefix, all Ren'Py extension `.so` files were rebuilt, and every module now resolves one shared `libSDL3.so.0` via `DT_RUNPATH=/home/user/renpy-deps/prefix/lib`. The static `.a` files remain in the prefix but are no longer used.
- The `before testcase` hook was changed from a `renpy.session` flag to a screen-state check (`if not screen "main_menu"`), because `full_restart` re-enters the hook at the main menu where the `MainMenu` action is insensitive and previously deadlocked the suite with a 5 s timeout after every reboot.

Headless invocation (all one shell):

```sh
source /home/user/renpy-deps/env.sh   # brings in the SDL3 dummy/sw stack and the prefix on PATH
env "renpy.pygame_AVOID_GL=1" ./run.sh . test ashfall
```

Result: **exit 0 — test suites 2/2 passed, 3/3 testcases (`playthrough_to_act2`, `save_load_rollback_day2`, `hud_overlay`), 5/5 hooks, 73/73 assertions, ~15 s.** `./run.sh . lint --error-code` exits 0 (above). Save directory is isolated via `config.save_directory = "ashfall-1"`; the engine save/load assertions use save slot 7.

What the engine verified (not just modeled):

- `playthrough_to_act2`: cold open (labour branch) to `act2_stub` — water/food/scrap/meds arithmetic across the colony phase engine (dawn/evening food, night water upkeep), the Day 2 water-crisis trade, the Day 3 levy menu (outer menu + submenu), and the act break at `act2_stub` after "Open talks". `probation` observed `True`; `act1_commit == "talks"`; `line_standing == -2`; engine-confirmed `act = 2` is set inside `act1_close.rpy` after the branch dialogue.
- `save_load_rollback_day2`: `FileSave(7)` at the Day 2 crisis menu, trade branch checked through Day 3, engine `FileLoad(7)` back into the crisis menu (scrap/water/cut_trade restore), "Cut rations" branch, engine `Rollback()` to the pre-choice state, "Draw the cistern" reserve branch, refusal raid path (`raid_triggered`, `wounded_companion == "alice"`, `food_loss == 1`), act break.
- State defaults (`game/state.rpy`) and the phase engine (`game/colony.rpy`) behave as coded under engine rollback (including the Day 2 -> Day 3 night-upkeep boundary).

Engine-driven bug fixed this session (in the game, not the harness):

- Menu labels containing a bare `%` crashed the menu system with `TypeError: %c requires int or char` because menu text is `%`-substituted by the engine. `game/act1.rpy` "25% chance" -> `25%%`, `game/act1_close.rpy` "35% injury risk" -> `35%%`.

Harness findings worth recording (Ren'Py behavior, not bugs in this project):

- The engine test runner only advances on drawn frames; once text finishes revealing a static scene performs no redraws, so the suite starves without a `config.needs_redraw_callbacks` hook (present in `game/tests/playthrough.rpy`; no-op outside tests).
- Custom screens now exist in `game/screens.rpy` (say/choice/HUD/quick menu/main menu/game menu/save/load/preferences/history/confirm) with `game/gui.rpy` (palette, plate-bordered frames, baked exact-size UI plates). Menu choices are still matched by text in tests; `screen "choice"` remains unused. `hud_overlay` in `game/tests/playthrough.rpy` asserts the HUD renders, shows day/phase/resource readouts, and flags low Water/Meds.
- Reaching the end of `label start` silently reboots into a fresh game (normal Ren'Py end-of-start behavior); assertions on stores therefore cannot observe post-`act = 2` state. The suite uses `advance until label act2_stub` to prove the act break instead.

Remaining items not verified by this engine pass: real audio/video drivers, windowed/interactive UI, Android/iOS, long-term save compatibility, and any path past `act2_stub` (act 2 content is out of scope).

## Addendum — 2026-11-12 (areas 21–30)

- Ten new background plates `assets/env/21_orchard_ruin.png` … `assets/env/30_seed_bank.png` (1920×1080, hand-painted cel-shaded style, no characters or legible text). Each was generated at 1376×768, center-cropped to 16:9, and upscaled to 1920×1080 with a light sharpen, so they are softer than the original 1920×1080 plates and may be worth regenerating at native resolution.
- Registered in `MANIFEST.json` (assets `env.21_orchard_ruin` … `env.30_seed_bank`, plus ten `scenes` entries appended in route order) and in `data/hotspots.json` (five hotspots per scene).
- Game integration: copies in `game/images/env/`; `game/areas.rpy` declares `bg <area>` images, a per-area table with titles and narration, the `visit_area` label, and a repeatable `area_survey` menu. The areas are not yet part of the day loop, because that would change the menu flow that `game/tests/playthrough.rpy` depends on.
- `python3 tools/validate.py --whole-project` reports the same 27 pre-existing errors as before this change (missing git-ignored `aligned`/`keyed` intermediates and stale `ui/` frames under `game/images`). It adds no new errors. The new hotspot rectangles pass bounds and zoom reachability checks.
- Not verified: Ren'Py lint and the headless playthrough were not run in this session, because the engine build dependencies (`renpy-deps`) are not present. `game/areas.rpy` should be linted with `./run.sh . lint --error-code` before merging.
- Note: `tools/imagesrpy.py` treats every subfolder of `game/images/` as a character. `game/images/env/` (like the existing `ui/`) will break that generator, so `game/definitions.rpy` must not be regenerated from the images root without fixing the tool.

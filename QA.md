# Whole-project QA report

**Status: PASS for derived assets and reference runtime; BLOCKED for the Ren'Py engine playthrough.** The former 72/80 sprite-count blocker is retracted because the derived raw-source count passes: 6 characters × 10 frames = 60 frames. The twelve derived blush overlays remain declared assets but are not counted as raw source frames. See `docs/CANON.md`.

## Results

| Check | Result | Evidence / notes |
| --- | --- | --- |
| Character frame anchors | **PASS** | `tools/validate.py` compares foot-midline anchors across base frames; measured maximum drift is below the 6 px limit for all six characters. Alice 0.5 px; Denice 0 px; MC 0.5 px; Sable 0.5 px; Sophia 1.118 px; Tory 0 px. |
| Manifest assets | **PASS** | All 92 declared assets resolve to project-contained files and their image data verifies. No duplicate asset paths or unresolved manifest IDs were reported. |
| Sprite-frame requirement | **PASS** | Raw source count is 60: Alice 10, Denice 10, MC 10, Sable 10, Sophia 10, and Tory 10. `spriteFrames.expectedCount` is 60, `assetIds` contains 60 IDs, and all 60 unique files exist. The additional twelve blush overlays remain available through `assets` and are excluded from this raw-source contract. |
| Act 1 playthrough to act break | **BLOCKED (Ren'Py); PASS (state model only)** | `./run.sh .` could not launch because the required Python 3.12 environment is unavailable. A non-engine state model saved before the Day 2 water choice, loaded the Cut-trade state (9 scrap, 14 water), rolled back to the pre-choice state (12 scrap, 8 water), chose below-reserve, stalled the Line, fortified, and reached `act = 2` with `probation = True`. This is not represented as an engine playthrough or engine save/load/rollback. |
| Act break canon state | **PASS (static and state model)** | `probation` has one assignment, `$ probation = True`, and remained true at the modeled act break. A dialogue-string scan of `game/*.rpy` found zero references to Mara, Vesper, Ren, Iona, Brick, Tamsin, or Juno. |
| Ren'Py lint | **BLOCKED** | `./run.sh . lint --error-code` prints `Please use 'uv sync' to creat the virtual environment.` `uv sync` could not obtain the required Python 3.12 runtime; the sandbox provides Python 3.11 and no compiled Ren'Py extension modules. |
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
```

The first validator invocation failed because Pillow was absent. After installing Pillow and generating the ignored aligned/keyed intermediates, `python3 tools/validate.py` and `python3 tools/validate.py --whole-project` both returned `validation passed`. Runtime QA returned `passed: true` with 5 resource quests, the faction quest, the rescue quest, colony and dialogue round trips, and 3 save slots confirmed.

## Validation limits

An actual Ren'Py playthrough from `label start` to `act2_stub`, including engine save, load, and rollback across the Day 2 water choice, remains unverified. The state-model check is supplemental only and does not replace those engine checks. Structural checks separately confirmed the exact fifteen canonical bond labels, the five-row roster, all sixty raw frame paths, valid manifest JSON, and generator output byte-identical to `game/definitions.rpy`.

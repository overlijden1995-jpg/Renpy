# Whole-project QA report

**Status: PASS.** The whole-project validator and reference-runtime QA complete successfully. The canonical raw-source contract is 6 characters × 10 frames = 60 frames; the twelve derived blush overlays remain declared assets but are not counted as raw source frames. See `docs/CANON.md`.

## Results

| Check | Result | Evidence / notes |
| --- | --- | --- |
| Character frame anchors | **PASS** | `tools/validate.py` compares foot-midline anchors across base frames; measured maximum drift is below the 6 px limit for all six characters. Alice 0.5 px; Denice 0 px; MC 0.5 px; Sable 0.5 px; Sophia 1.118 px; Tory 0 px. |
| Manifest assets | **PASS** | All 92 declared assets resolve to project-contained files and their image data verifies. No duplicate asset paths or unresolved manifest IDs were reported. |
| Sprite-frame requirement | **PASS** | All 60 raw-source counterparts listed in `spriteFrames.assetIds` resolve to unique files against `expectedCount: 60`. The additional twelve blush overlays remain available through `assets` and are excluded from this raw-source contract. |
| Hotspots | **PASS (static reachability)** | 10 scenes and 45 hotspot rectangles validated. Every scene background resolves through a manifest asset ID; rectangles are in the 1920×1080 canvas, and each hotspot center maps inside the view at zoom 1.0, 1.25, and 1.8. |
| Quest completion | **PASS** | Runtime QA completed all seven quests through game-model/dialogue events: five resource bottlenecks, the faction delivery, and the rescue. |
| Save/load round trips | **PASS** | Colony snapshots restore byte-for-data-equivalent state; dialogue flags and unlocked bond-scene state round-trip; all three save slots round-trip and invalid slot 4 is rejected. |
| Hardcoded asset paths | **PASS** | Runtime engine and game-data scan found no direct image-file paths outside `MANIFEST.json`; hotspot backgrounds and dialogue portraits use manifest IDs. |

## Commands run

```sh
PYTHONPATH=/tmp/ashfall-pillow python tools/tickalign.py --input assets/characters/source --output assets/characters/aligned --style docs/STYLE.md
PYTHONPATH=/tmp/ashfall-pillow python tools/alphakey.py --input assets/characters/aligned --output assets/characters/keyed --tolerance 40
PYTHONPATH=/tmp/ashfall-pillow python tools/validate.py --whole-project
node tools/qa_runtime.mjs
```

The whole-project validator returned `validation passed`. The runtime QA command returned `passed: true` with 5 resource quests, the faction quest, the rescue quest, colony and dialogue round trips, and 3 save slots confirmed.

## Validation limits

Ren'Py lint was not run because this checkout has no configured virtual environment or compiled Ren'Py extension modules. Structural checks confirmed the exact fifteen canonical bond labels, the five-row roster, all sixty raw frame paths, valid manifest JSON, and generator output byte-identical to `game/definitions.rpy`.

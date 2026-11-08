# Whole-project QA report

**Status: BLOCKED by missing source art.** The validator exercises the full manifest and runtime checks. It reports one remaining failure: only 72 of the expected 80 sprite frames exist in the repository. No duplicate or blank frames were created to mask the shortfall.

## Results

| Check | Result | Evidence / notes |
|---|---|---|
| Character frame anchors | **PASS** | `tools/validate.py` compares foot-midline anchors across base frames; measured maximum drift is below the 6 px limit for all six characters. Alice 0.5 px; Denice 0 px; MC 0.5 px; Sable 0.5 px; Sophia 1.118 px; Tory 0 px. |
| Manifest assets | **PASS** | All 92 declared assets resolve to project-contained files and their image data verifies. No duplicate asset paths or unresolved manifest IDs were reported. |
| Sprite-frame requirement | **FAIL / unresolved** | 72 unique frame files are present against `expectedCount: 80`; **8 frames are missing**. The repository does not identify source art for those eight, so they were not fabricated. |
| Hotspots | **PASS (static reachability)** | 10 scenes and 45 hotspot rectangles validated. Every scene background resolves through a manifest asset ID; rectangles are in the 1920×1080 canvas, and each hotspot center maps inside the view at zoom 1.0, 1.25, and 1.8. |
| Quest completion | **PASS** | Runtime QA completed all seven quests through game-model/dialogue events: five resource bottlenecks, the faction delivery, and the rescue. |
| Save/load round trips | **PASS** | Colony snapshots restore byte-for-data-equivalent state; dialogue flags and unlocked bond-scene state round-trip; all three save slots round-trip and invalid slot 4 is rejected. |
| Hardcoded asset paths | **PASS** | Runtime engine and game-data scan found no direct image-file paths outside `MANIFEST.json`; hotspot backgrounds and dialogue portraits use manifest IDs. |

## Commands run

```sh
PYTHONPATH=/tmp/ashfall-pillow python tools/validate.py --whole-project
node tools/qa_runtime.mjs
```

The runtime QA command returned `passed: true` with 5 resource quests, the faction quest, the rescue quest, colony and dialogue round trips, and 3 save slots confirmed. The whole-project validator exits nonzero only for the 72/80 sprite-frame count.

## Unresolved items

1. Provide the source art or an authoritative list of the eight intended sprite frames. Until then, the 80-frame requirement remains unmet; no placeholders or duplicates were added.

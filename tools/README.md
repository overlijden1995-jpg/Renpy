# Character image tools

These are ordinary Python 3 command-line tools; they run outside the Ren'Py interpreter and require Pillow (`python3 -m pip install Pillow`). Run `tools/build.sh` from any working directory. Set `PROJECT_DIR`, `ASSET_ROOT`, `PYTHON`, and/or `RENPY_EXE` to override defaults. `RENPY_EXE` defaults to `renpy.exe` on `PATH`.

## Input naming and output layout

Put full-canvas, fully clothed sprite renders in `assets/characters/source/<character>/<frame>.png`. Each source PNG must match the `STYLE_LOCK` canvas in `docs/STYLE.md` and contain four black L registration marks centered at the 24px inset. The character folder name and frame stem must be lowercase Ren'Py identifiers.

Use these frame stems so the generated layers can be assembled:

- `base_idle`, `base_walk`, `base_work`, `base_hurt`
- `face_neutral`, `face_smile`, `face_soft`, `face_surprise`, `face_angry`, `face_pain`
- `blush_off`, `blush_on`
- Optional, currently ungrouped overlays: `sweat_off`, `sweat_on`

The generator also accepts unprefixed base names (`idle`, `walk`, `work`, `hurt`), unprefixed face names (`neutral`, `smile`, `soft`, `surprise`, `angry`, `pain`), and blush names (`off`, `on`). Do not provide both forms for the same group member.

The pipeline writes aligned images to `assets/characters/aligned/`, keyed images to `assets/characters/keyed/`, trimmed base frames and full-canvas overlays to `game/images/<character>/`, anchors to `game/images/anchors.json`, and generated declarations to `game/definitions.rpy`. Base anchors store the foot-midline in the untrimmed canvas coordinate system and the offset of the trimmed PNG. This lets a later placement system restore the frame's original canvas alignment.

## Individual commands

Each script accepts `--help`; all directory arguments can be overridden:

```sh
python3 tools/tickalign.py --input assets/characters/source --output assets/characters/aligned
python3 tools/alphakey.py --input assets/characters/aligned --output assets/characters/keyed --tolerance 40
python3 tools/layerize.py --input assets/characters/keyed --output game/images --anchors game/images/anchors.json
python3 tools/validate.py
python3 tools/imagesrpy.py --images game/images --output game/definitions.rpy
```

`build.sh` runs those stages in order, validates again with the fresh lint report, invokes `renpy.exe <project-dir> lint`, and writes the report to `lint.txt`. The build exits non-zero on missing frames, failed image checks, lint errors, or a failed Ren'Py command.

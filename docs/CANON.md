# Canon

## Cast and bond tracking

The protagonist is `mc`. The canonical companions are Alice, Denice, Sophia, Tory, and Sable. [ROSTER.md](ROSTER.md) fixes their roles, disposition axes, voices, and fifteen bond-scene IDs; `game/bonds.rpy` contains their empty scene placeholders.

Mara, Vesper, Ren, Iona, Brick, Tamsin, and Juno are retired from bond tracking. Denice's scanner-based gate triage replaces the cut medic role, and Alice's cistern ownership replaces the cut water-engineer role.

## Implementation boundary

`game/*.rpy` is the only game implementation. `project/src/*.js` and `index.html` are reference-only material, not a parallel implementation or a source of canon. Do not implement new gameplay in those reference files.

## Sprite source count

The raw source sets in `docs/raw/` cover six characters: the five companions plus `mc`. Each character has ten raw frames: four body frames (idle, walk, one role-specific action, and hurt) and six face frames (neutral, smile, soft, surprise, angry, and pain).

The canonical raw-frame arithmetic is **6 characters × (4 body + 6 face) frames = 60 frames**. Accordingly, `MANIFEST.json` sets `spriteFrames.expectedCount` to `60`, and `spriteFrames.assetIds` lists the sixty processed counterparts of those raw frames.

The additional twelve `blush_off` and `blush_on` images under `game/images/` are derived overlays, not raw source frames. They remain declared in `assets` but are excluded from the raw-source sprite count.

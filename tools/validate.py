#!/usr/bin/env python3
"""Validate character assets, expected layer members, anchors, and Ren'Py lint output."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from PIL import Image

DEFAULT_ROOT = Path(__file__).resolve().parent.parent
REQUIRED = {
    "base": ("idle", "walk", "work", "hurt"),
    "face": ("neutral", "smile", "soft", "surprise", "angry", "pain"),
    "blush": ("off", "on"),
}
OVERLAYS = ("face_", "blush_", "sweat_")
BASE_ATTRIBUTES = set(REQUIRED["base"])
FACE_ATTRIBUTES = set(REQUIRED["face"])
BLUSH_ATTRIBUTES = set(REQUIRED["blush"])


def is_base_frame(frame: str) -> bool:
    return frame in BASE_ATTRIBUTES or (frame.startswith("base_") and frame[5:] in BASE_ATTRIBUTES)


def is_overlay_frame(frame: str) -> bool:
    return (
        frame.startswith(OVERLAYS)
        or frame in FACE_ATTRIBUTES
        or frame in BLUSH_ATTRIBUTES
    )


def has_member(frames: set[str], group: str, attribute: str) -> bool:
    return f"{group}_{attribute}" in frames or attribute in frames


def style_geometry(path: Path) -> tuple[int, int, int]:
    text = path.read_text(encoding="utf-8")
    canvas = re.search(r"Canvas:\s*`(\d+)\s*x\s*(\d+)`", text, re.IGNORECASE)
    inset = re.search(r"(?:tick inset|mark inset|inset):?\s*`?(\d+)\s*px", text, re.IGNORECASE)
    if not canvas or not inset:
        raise ValueError(f"Unable to read canvas and tick inset from {path}")
    return int(canvas.group(1)), int(canvas.group(2)), int(inset.group(1))


def png_map(root: Path) -> dict[str, Path]:
    if not root.is_dir():
        return {}
    return {
        p.relative_to(root).as_posix(): p
        for p in sorted(root.rglob("*.png"))
        if p.is_file()
    }


def alpha_coverage(image: Image.Image) -> tuple[int, float]:
    hist = image.convert("RGBA").getchannel("A").histogram()
    visible = sum(hist[128:])
    total = image.width * image.height
    return visible, visible / total if total else 0.0


def figure_blob_count(image: Image.Image) -> int:
    """Count substantial 8-connected figure blobs, ignoring tiny keying specks."""
    alpha = image.convert("RGBA").getchannel("A")
    mask = bytearray(1 if value >= 128 else 0 for value in alpha.tobytes())
    width, height = image.size
    visited = bytearray(width * height)
    min_figure_area = max(64, int(width * height * 0.0025))
    blobs = 0
    for start, value in enumerate(mask):
        if not value or visited[start]:
            continue
        visited[start] = 1
        stack = [start]
        area = 0
        while stack:
            index = stack.pop()
            area += 1
            y, x = divmod(index, width)
            y0, y1 = max(0, y - 1), min(height - 1, y + 1)
            x0, x1 = max(0, x - 1), min(width - 1, x + 1)
            for ny in range(y0, y1 + 1):
                row = ny * width
                for nx in range(x0, x1 + 1):
                    neighbor = row + nx
                    if mask[neighbor] and not visited[neighbor]:
                        visited[neighbor] = 1
                        stack.append(neighbor)
        if area >= min_figure_area:
            blobs += 1
            if blobs > 1:
                return blobs
    return blobs


def validate(args: argparse.Namespace) -> list[str]:
    errors: list[str] = []
    try:
        canvas_w, canvas_h, inset = style_geometry(args.style)
    except (OSError, ValueError) as exc:
        return [str(exc)]
    crop_size = (canvas_w - 2 * inset, canvas_h - 2 * inset)
    if crop_size[0] <= 0 or crop_size[1] <= 0:
        return [f"STYLE_LOCK crop is invalid: {canvas_w}x{canvas_h} with inset {inset}"]

    lock_image = args.style.parent / "_stylelock.png"
    if not lock_image.is_file():
        errors.append(f"STYLE_LOCK reference image is missing: {lock_image}")
    else:
        try:
            with Image.open(lock_image) as image:
                if image.size != (canvas_w, canvas_h):
                    errors.append(
                        f"STYLE_LOCK image canvas is {image.width}x{image.height}; expected {canvas_w}x{canvas_h}"
                    )
        except OSError as exc:
            errors.append(f"Cannot read STYLE_LOCK image {lock_image}: {exc}")

    source = png_map(args.source)
    aligned = png_map(args.aligned)
    keyed = png_map(args.keyed)
    layered = png_map(args.layerized)
    if not source:
        errors.append(f"No source PNGs found in {args.source}")
    for stage, mapping, expected_keys in (
        ("aligned", aligned, set(source)),
        ("keyed", keyed, set(source)),
        ("layerized", layered, set(source)),
    ):
        missing = sorted(expected_keys - set(mapping))
        extra = sorted(set(mapping) - expected_keys)
        if missing:
            errors.append(f"{stage}: missing frame(s): {', '.join(missing)}")
        if extra:
            errors.append(f"{stage}: unexpected stale frame(s): {', '.join(extra)}")

    for rel, path in source.items():
        try:
            with Image.open(path) as image:
                if image.size != (canvas_w, canvas_h):
                    errors.append(f"source {rel}: canvas {image.width}x{image.height}, expected STYLE_LOCK {canvas_w}x{canvas_h}")
        except OSError as exc:
            errors.append(f"source {rel}: cannot read image ({exc})")

    for stage, mapping in (("aligned", aligned), ("keyed", keyed)):
        for rel, path in mapping.items():
            try:
                with Image.open(path) as image:
                    if image.size != crop_size:
                        errors.append(f"{stage} {rel}: canvas {image.width}x{image.height}, expected cropped canvas {crop_size[0]}x{crop_size[1]}")
            except OSError as exc:
                errors.append(f"{stage} {rel}: cannot read image ({exc})")

    characters: dict[str, set[str]] = {}
    for rel, path in keyed.items():
        relative = Path(rel)
        if len(relative.parts) != 2:
            errors.append(f"keyed frame must be under a character directory: {rel}")
            continue
        character, filename = relative.parts
        frame = Path(filename).stem
        characters.setdefault(character, set()).add(frame)
        if not is_base_frame(frame) and not is_overlay_frame(frame):
            errors.append(f"keyed {rel}: unrecognized base or overlay frame name")

    for character, frames in sorted(characters.items()):
        for group, members in REQUIRED.items():
            missing = [attribute for attribute in members if not has_member(frames, group, attribute)]
            if missing:
                errors.append(f"{character}: missing {group} group member(s): {', '.join(missing)}")

    try:
        anchors = json.loads(args.anchors.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        anchors = {}
        errors.append(f"Cannot read anchor metadata {args.anchors}: {exc}")

    for rel, path in keyed.items():
        relative = Path(rel)
        if len(relative.parts) != 2:
            continue
        character, filename = relative.parts
        frame = Path(filename).stem
        key_path = args.layerized / relative
        if not key_path.is_file():
            continue
        try:
            with Image.open(path) as keyed_image, Image.open(key_path) as result:
                if is_base_frame(frame):
                    visible, coverage = alpha_coverage(keyed_image)
                    if coverage < 0.04:
                        errors.append(f"{rel}: foreground alpha {coverage:.2%} is below 4%")
                    elif coverage > 0.85:
                        errors.append(f"{rel}: foreground alpha {coverage:.2%} exceeds 85%")
                    if figure_blob_count(keyed_image) != 1:
                        errors.append(f"{rel}: expected exactly one connected figure blob")
                    bbox = keyed_image.convert("RGBA").getchannel("A").getbbox()
                    metadata = anchors.get(character, {}).get(frame)
                    if metadata is None:
                        errors.append(f"{rel}: missing foot-midline anchor metadata")
                    else:
                        expected_bbox = list(bbox) if bbox else None
                        if metadata.get("bbox") != expected_bbox:
                            errors.append(f"{rel}: recorded trim bbox {metadata.get('bbox')} does not match alpha bbox {expected_bbox}")
                        expected_size = (bbox[2] - bbox[0], bbox[3] - bbox[1]) if bbox else None
                        if expected_size and result.size != expected_size:
                            errors.append(f"layerized {rel}: trimmed canvas {result.width}x{result.height}, expected {expected_size[0]}x{expected_size[1]}")
                elif is_overlay_frame(frame):
                    if keyed_image.size != crop_size or result.size != crop_size:
                        errors.append(f"overlay {rel}: must retain full cropped canvas {crop_size[0]}x{crop_size[1]}")
        except OSError as exc:
            errors.append(f"{rel}: cannot read keyed/layerized image ({exc})")

    # Extra anchor records usually indicate stale output from a previous build.
    expected_bases = {
        (Path(rel).parts[0], Path(rel).stem)
        for rel in keyed
        if len(Path(rel).parts) == 2 and is_base_frame(Path(rel).stem)
    }
    for character, character_anchors in anchors.items():
        if not isinstance(character_anchors, dict):
            errors.append(f"Invalid anchor record for {character}")
            continue
        for frame in character_anchors:
            if (character, frame) not in expected_bases:
                errors.append(f"Stale anchor metadata: {character}/{frame}")

    if args.lint:
        try:
            lint_text = args.lint.read_text(encoding="utf-8", errors="replace")
            matching = []
            for line in lint_text.splitlines():
                if not re.search(r"\berrors?\b|\berror\s*:", line, re.IGNORECASE):
                    continue
                if re.search(r"\bno errors?\b|\b0 errors?\b", line, re.IGNORECASE):
                    continue
                matching.append(line.strip())
            if matching:
                errors.append("Ren'Py lint reported an error: " + " | ".join(matching[:5]))
        except OSError as exc:
            errors.append(f"Cannot read lint output {args.lint}: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_ROOT / "assets/characters/source")
    parser.add_argument("--aligned", type=Path, default=DEFAULT_ROOT / "assets/characters/aligned")
    parser.add_argument("--keyed", type=Path, default=DEFAULT_ROOT / "assets/characters/keyed")
    parser.add_argument("--layerized", type=Path, default=DEFAULT_ROOT / "game/images")
    parser.add_argument("--anchors", type=Path, default=DEFAULT_ROOT / "game/images/anchors.json")
    parser.add_argument("--style", type=Path, default=DEFAULT_ROOT / "docs/STYLE.md")
    parser.add_argument("--lint", type=Path, help="optional Ren'Py lint output; any error is fatal")
    args = parser.parse_args()
    try:
        errors = validate(args)
    except (OSError, ValueError) as exc:
        print(f"validate: ERROR: {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"validate: ERROR: {error}", file=sys.stderr)
        print(f"validation failed with {len(errors)} error(s)", file=sys.stderr)
        return 1
    print("validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

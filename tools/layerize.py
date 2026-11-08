#!/usr/bin/env python3
"""Keep overlay canvases intact; trim base frames and save their foot anchors."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Iterable

from PIL import Image

DEFAULT_ROOT = Path(__file__).resolve().parent.parent
OVERLAY_PREFIXES = ("face_", "blush_", "sweat_")
BASE_ATTRIBUTES = {"idle", "walk", "work", "hurt"}
FACE_ATTRIBUTES = {"neutral", "smile", "soft", "surprise", "angry", "pain"}
BLUSH_ATTRIBUTES = {"off", "on"}
BASE_PREFIX = "base_"


def png_files(path: Path) -> Iterable[Path]:
    if not path.is_dir():
        raise ValueError(f"Input directory does not exist: {path}")
    yield from sorted(p for p in path.rglob("*") if p.is_file() and p.suffix.lower() == ".png")


def is_base_frame(frame: str) -> bool:
    return frame in BASE_ATTRIBUTES or (frame.startswith(BASE_PREFIX) and frame[len(BASE_PREFIX):] in BASE_ATTRIBUTES)


def anchor_offsets(sources: list[Path]) -> dict[Path, tuple[int, int]]:
    """Translate base frames on their full transparent canvases to a shared foot anchor."""
    anchors: dict[str, dict[Path, tuple[tuple[float, float], tuple[int, int, int, int], tuple[int, int]]]] = {}
    for source in sources:
        if not is_base_frame(source.stem):
            continue
        with Image.open(source) as opened:
            image = opened.convert("RGBA")
        bbox = image.getchannel("A").getbbox()
        if bbox is None:
            raise ValueError(f"{source}: base frame has no visible pixels")
        left, top, right, bottom = bbox
        anchors.setdefault(source.parent.name, {})[source] = (
            ((left + right - 1) / 2, bottom - 1), bbox, image.size
        )

    offsets: dict[Path, tuple[int, int]] = {}
    for character, frames in anchors.items():
        target_x = statistics.median(item[0][0] for item in frames.values())
        target_y = statistics.median(item[0][1] for item in frames.values())
        # Keep every translated figure inside its full canvas. A frame which already
        # touches an edge constrains the shared foot-anchor target.
        min_x = max(point[0] - bbox[0] for point, bbox, _ in frames.values())
        max_x = min(point[0] + size[0] - bbox[2] for point, bbox, size in frames.values())
        min_y = max(point[1] - bbox[1] for point, bbox, _ in frames.values())
        max_y = min(point[1] + size[1] - bbox[3] for point, bbox, size in frames.values())
        target_x = min(max(target_x, min_x), max_x)
        target_y = min(max(target_y, min_y), max_y)
        for source, (point, _, _) in frames.items():
            # Integer translation preserves the original render; half-pixel residuals
            # are below the 6px registration tolerance.
            offsets[source] = (round(target_x - point[0]), round(target_y - point[1]))
    return offsets


def translate(image: Image.Image, offset: tuple[int, int]) -> Image.Image:
    dx, dy = offset
    if dx == 0 and dy == 0:
        return image
    shifted = Image.new("RGBA", image.size, (0, 0, 0, 0))
    source_x = max(0, -dx)
    source_y = max(0, -dy)
    target_x = max(0, dx)
    target_y = max(0, dy)
    width = image.width - abs(dx)
    height = image.height - abs(dy)
    if width > 0 and height > 0:
        shifted.paste(image.crop((source_x, source_y, source_x + width, source_y + height)), (target_x, target_y))
    return shifted


def process(source: Path, destination: Path, anchors: dict, offset: tuple[int, int] = (0, 0)) -> None:
    frame = source.stem
    if frame.startswith(OVERLAY_PREFIXES) or frame in FACE_ATTRIBUTES or frame in BLUSH_ATTRIBUTES:
        with Image.open(source) as opened:
            image = opened.convert("RGBA")
        destination.parent.mkdir(parents=True, exist_ok=True)
        image.save(destination, format="PNG", optimize=True)
        print(f"kept overlay canvas {source} -> {destination} ({image.width}x{image.height})")
        return

    if not (frame.startswith(BASE_PREFIX) or frame in BASE_ATTRIBUTES):
        if frame in FACE_ATTRIBUTES or frame in BLUSH_ATTRIBUTES:
            raise ValueError(f"{source}: overlay frames must use face_ or blush_ prefixes")
        raise ValueError(
            f"{source}: frame must be a base attribute or start with base_, face_, blush_, or sweat_"
        )
    with Image.open(source) as opened:
        image = translate(opened.convert("RGBA"), offset)
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        raise ValueError(f"{source}: base frame has no visible pixels")
    left, top, right, bottom = bbox
    trimmed = image.crop(bbox)
    destination.parent.mkdir(parents=True, exist_ok=True)
    trimmed.save(destination, format="PNG", optimize=True)
    char = source.parent.name
    anchors.setdefault(char, {})[frame] = {
        "source_canvas": [image.width, image.height],
        "bbox": [left, top, right, bottom],
        "display_offset": [left, top],
        "alignment_offset": list(offset),
        "foot_midline": [round((left + right - 1) / 2.0, 2), bottom - 1],
        "trimmed_size": [trimmed.width, trimmed.height],
    }
    print(f"trimmed base {source} -> {destination}; bbox={bbox}; anchor shift={offset}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_ROOT / "assets/characters/keyed")
    parser.add_argument("--output", type=Path, default=DEFAULT_ROOT / "game/images")
    parser.add_argument("--anchors", type=Path, default=DEFAULT_ROOT / "game/images/anchors.json")
    parser.add_argument("--clean", action="store_true", help="remove prior PNG outputs and anchor JSON")
    args = parser.parse_args()
    try:
        sources = list(png_files(args.input))
        if not sources:
            raise ValueError(f"No PNG files found under {args.input}")
        if args.clean and args.output.exists():
            for stale in args.output.rglob("*.png"):
                stale.unlink()
            # Remove empty generated character folders too, so deleted characters
            # cannot leak into the next definitions.rpy generation.
            for directory in sorted((p for p in args.output.rglob("*") if p.is_dir()), reverse=True):
                try:
                    directory.rmdir()
                except OSError:
                    pass
            if args.anchors.exists():
                args.anchors.unlink()
        anchors: dict = {}
        offsets = anchor_offsets(sources)
        for source in sources:
            relative = source.relative_to(args.input)
            process(source, args.output / relative, anchors, offsets.get(source, (0, 0)))
        args.anchors.parent.mkdir(parents=True, exist_ok=True)
        args.anchors.write_text(json.dumps(anchors, indent=2) + "\n", encoding="utf-8")
        print(f"wrote anchor metadata: {args.anchors}")
    except (OSError, ValueError) as exc:
        print(f"layerize: ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

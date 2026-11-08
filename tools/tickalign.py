#!/usr/bin/env python3
"""Verify STYLE_LOCK corner registration marks and crop the 24px tick band."""

from __future__ import annotations

import argparse
from collections import Counter
import re
import sys
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw

DEFAULT_ROOT = Path(__file__).resolve().parent.parent


def style_geometry(style_path: Path) -> tuple[int, int, int]:
    text = style_path.read_text(encoding="utf-8")
    canvas = re.search(r"Canvas:\s*`(\d+)\s*x\s*(\d+)`", text, re.IGNORECASE)
    inset = re.search(r"(?:tick inset|tick inset:|mark inset|inset):?\s*`?(\d+)\s*px", text, re.IGNORECASE)
    if not canvas:
        raise ValueError(f"Could not read STYLE_LOCK canvas from {style_path}")
    if not inset:
        raise ValueError(f"Could not read registration-mark inset from {style_path}")
    return int(canvas.group(1)), int(canvas.group(2)), int(inset.group(1))


def dark(pixel: tuple[int, ...]) -> bool:
    r, g, b = pixel[:3]
    return max(r, g, b) < 100


def arm_score(pixels, width: int, height: int, x: int, y: int, dx: int, dy: int, length: int = 14) -> int:
    """Count dark samples along an arm, allowing a 2px antialias/stroke width."""
    score = 0
    for distance in range(1, length + 1):
        xx, yy = x + dx * distance, y + dy * distance
        found = False
        for thickness in range(-2, 3):
            sx = xx if dx else xx + thickness
            sy = yy + thickness if dx else yy
            if 0 <= sx < width and 0 <= sy < height and dark(pixels[sx, sy]):
                found = True
                break
        score += int(found)
    return score


def find_tick(image: Image.Image, corner: str, inset: int, tolerance: int) -> tuple[int, int]:
    width, height = image.size
    expected = {
        "top-left": (inset, inset, 1, 1),
        "top-right": (width - 1 - inset, inset, -1, 1),
        "bottom-left": (inset, height - 1 - inset, 1, -1),
        "bottom-right": (width - 1 - inset, height - 1 - inset, -1, -1),
    }
    ex, ey, hdir, vdir = expected[corner]
    pixels = image.convert("RGB").load()
    matches = []
    for y in range(max(0, ey - tolerance), min(height, ey + tolerance + 1)):
        for x in range(max(0, ex - tolerance), min(width, ex + tolerance + 1)):
            horizontal = arm_score(pixels, width, height, x, y, hdir, 0)
            vertical = arm_score(pixels, width, height, x, y, 0, vdir)
            if horizontal >= 11 and vertical >= 11:
                # Prefer a strong, accurately placed turn where the two arms meet.
                distance = abs(x - ex) + abs(y - ey)
                matches.append((horizontal + vertical, -distance, x, y))
    if not matches:
        raise ValueError(
            f"{corner} registration mark missing or misaligned: expected an L-turn at "
            f"({ex}, {ey}) within ±{tolerance}px"
        )
    _, _, x, y = max(matches)
    return x, y


def png_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        if path.suffix.lower() != ".png":
            raise ValueError(f"Input is not a PNG: {path}")
        yield path
        return
    if not path.is_dir():
        raise ValueError(f"Input path does not exist: {path}")
    yield from sorted(p for p in path.rglob("*") if p.is_file() and p.suffix.lower() == ".png")


def process(source: Path, destination: Path, width: int, height: int, inset: int, tolerance: int) -> None:
    with Image.open(source) as opened:
        image = opened.convert("RGB")
    if image.size != (width, height):
        raise ValueError(f"{source}: canvas is {image.width}x{image.height}, expected {width}x{height}")
    for corner in ("top-left", "top-right", "bottom-left", "bottom-right"):
        x, y = find_tick(image, corner, inset, tolerance)
        ex = inset if "left" in corner else width - 1 - inset
        ey = inset if "top" in corner else height - 1 - inset
        if abs(x - ex) > tolerance or abs(y - ey) > tolerance:
            raise ValueError(f"{source}: {corner} mark at ({x},{y}) is outside ±{tolerance}px")
    # A 24px crop on each edge strips the registration band: 768x1280 -> 720x1232.
    result = image.crop((inset, inset, width - inset, height - inset))
    # Some renderers draw the L arms inward from the inset point. Clear only the
    # small, figure-free corner registration zones left at the crop boundary.
    patch = min(inset + 16, result.width // 2, result.height // 2)
    draw = ImageDraw.Draw(result)
    for corner in ("top-left", "top-right", "bottom-left", "bottom-right"):
        if corner.endswith("left"):
            x0, x1 = 0, patch - 1
        else:
            x0, x1 = result.width - patch, result.width - 1
        if corner.startswith("top"):
            y0, y1 = 0, patch - 1
        else:
            y0, y1 = result.height - patch, result.height - 1
        region = result.crop((x0, y0, x1 + 1, y1 + 1))
        raw = region.tobytes()
        samples = [tuple(raw[i : i + 3]) for i in range(0, len(raw), 3)]
        bins = Counter(tuple((c // 8) * 8 for c in pixel) for pixel in samples)
        key_bin = bins.most_common(1)[0][0]
        samples = [pixel for pixel in samples if tuple((c // 8) * 8 for c in pixel) == key_bin]
        background = tuple(round(sum(pixel[channel] for pixel in samples) / len(samples)) for channel in range(3))
        draw.rectangle((x0, y0, x1, y1), fill=background)
    destination.parent.mkdir(parents=True, exist_ok=True)
    result.save(destination, format="PNG", optimize=True)
    print(f"aligned {source} -> {destination} ({result.width}x{result.height})")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_ROOT / "assets/characters/source")
    parser.add_argument("--output", type=Path, default=DEFAULT_ROOT / "assets/characters/aligned")
    parser.add_argument("--style", type=Path, default=DEFAULT_ROOT / "docs/STYLE.md")
    parser.add_argument("--tolerance", type=int, default=3, help="allowed L-turn displacement in pixels")
    args = parser.parse_args()
    try:
        width, height, inset = style_geometry(args.style)
        if inset <= 0 or width <= 2 * inset or height <= 2 * inset:
            raise ValueError(f"Invalid STYLE_LOCK geometry: {width}x{height}, inset {inset}")
        sources = list(png_files(args.input))
        if not sources:
            raise ValueError(f"No PNG files found under {args.input}")
        input_root = args.input if args.input.is_dir() else args.input.parent
        for source in sources:
            rel = source.relative_to(input_root) if args.input.is_dir() else Path(source.name)
            process(source, args.output / rel, width, height, inset, args.tolerance)
    except (OSError, ValueError) as exc:
        print(f"tickalign: ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Flood-fill a flat magenta background to transparency and despill its edge."""

from __future__ import annotations

import argparse
from collections import Counter
import sys
from pathlib import Path
from typing import Iterable

from PIL import Image

DEFAULT_ROOT = Path(__file__).resolve().parent.parent


def png_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        if path.suffix.lower() != ".png":
            raise ValueError(f"Input is not a PNG: {path}")
        yield path
        return
    if not path.is_dir():
        raise ValueError(f"Input path does not exist: {path}")
    yield from sorted(p for p in path.rglob("*") if p.is_file() and p.suffix.lower() == ".png")


def estimate_key(rgb: Image.Image) -> tuple[int, int, int]:
    """Use the most common quantized perimeter color as the flat magenta key."""
    width, height = rgb.size
    px = rgb.load()
    samples = []
    for x in range(width):
        samples.append(px[x, 0])
        if height > 1:
            samples.append(px[x, height - 1])
    for y in range(1, height - 1):
        samples.append(px[0, y])
        if width > 1:
            samples.append(px[width - 1, y])
    bins = Counter(tuple((c // 8) * 8 for c in color) for color in samples)
    winning = bins.most_common(1)[0][0]
    selected = [color for color in samples if tuple((c // 8) * 8 for c in color) == winning]
    return tuple(round(sum(color[channel] for color in selected) / len(selected)) for channel in range(3))


def flood_background(rgb: Image.Image, key: tuple[int, int, int], tolerance: int) -> bytearray:
    width, height = rgb.size
    pixels = rgb.load()
    target = bytearray(width * height)
    for y in range(height):
        row = y * width
        for x in range(width):
            r, g, b = pixels[x, y]
            if (r - key[0]) ** 2 + (g - key[1]) ** 2 + (b - key[2]) ** 2 <= tolerance * tolerance:
                target[row + x] = 1

    visited = bytearray(width * height)
    stack = []
    for x in range(width):
        if target[x]:
            stack.append(x)
        bottom = (height - 1) * width + x
        if target[bottom]:
            stack.append(bottom)
    for y in range(height):
        left, right = y * width, y * width + width - 1
        if target[left]:
            stack.append(left)
        if target[right]:
            stack.append(right)

    # Scanline flood-fill uses spans instead of storing every background pixel
    # as a Python tuple, keeping memory modest for full-resolution sprite sheets.
    while stack:
        index = stack.pop()
        if visited[index] or not target[index]:
            continue
        y, x = divmod(index, width)
        left = x
        while left > 0 and target[y * width + left - 1] and not visited[y * width + left - 1]:
            left -= 1
        right = x
        while right + 1 < width and target[y * width + right + 1] and not visited[y * width + right + 1]:
            right += 1
        start = y * width + left
        visited[start : y * width + right + 1] = b"\x01" * (right - left + 1)
        for adjacent_y in (y - 1, y + 1):
            if not 0 <= adjacent_y < height:
                continue
            column = left
            adjacent_row = adjacent_y * width
            while column <= right:
                neighbor = adjacent_row + column
                if target[neighbor] and not visited[neighbor]:
                    stack.append(neighbor)
                    # Avoid pushing every pixel in the same adjacent run.
                    while column <= right and target[adjacent_row + column] and not visited[adjacent_row + column]:
                        column += 1
                else:
                    column += 1
    return visited


def despill(rgb: Image.Image, transparent: bytearray, visible: bytearray, key: tuple[int, int, int]) -> Image.Image:
    width, height = rgb.size
    raw = bytearray(rgb.tobytes())
    kr, kg, kb = key
    dr, db = kr - kg, kb - kg
    if dr <= 0 or db <= 0:
        return rgb
    for y in range(height):
        row = y * width
        for x in range(width):
            index = row + x
            if not visible[index]:
                continue
            near_key = (
                (x > 0 and transparent[index - 1])
                or (x + 1 < width and transparent[index + 1])
                or (y > 0 and transparent[index - width])
                or (y + 1 < height and transparent[index + width])
            )
            if not near_key:
                continue
            offset = index * 3
            r, g, b = raw[offset], raw[offset + 1], raw[offset + 2]
            red_fraction = (r - g) / dr
            blue_fraction = (b - g) / db
            fraction = min(0.65, max(0.0, min(red_fraction, blue_fraction)))
            raw[offset] = max(0, min(255, round(r - fraction * dr)))
            raw[offset + 2] = max(0, min(255, round(b - fraction * db)))
    return Image.frombytes("RGB", (width, height), bytes(raw))


def process(source: Path, destination: Path, tolerance: int) -> None:
    with Image.open(source) as opened:
        original = opened.convert("RGBA")
    rgb = original.convert("RGB")
    key = estimate_key(rgb)
    transparent = flood_background(rgb, key, tolerance)
    alpha = bytearray(original.getchannel("A").tobytes())
    for i, background in enumerate(transparent):
        # Hard edge: pixels below 128 become fully clear; the rest fully opaque.
        alpha[i] = 0 if background or alpha[i] < 128 else 255
    visible = bytearray(1 if value else 0 for value in alpha)
    rgb = despill(rgb, transparent, visible, key)
    keyed = rgb.convert("RGBA")
    keyed.putalpha(Image.frombytes("L", original.size, bytes(alpha)))
    destination.parent.mkdir(parents=True, exist_ok=True)
    keyed.save(destination, format="PNG", optimize=True)
    print(f"keyed {source} -> {destination}; background RGB={key}, tolerance={tolerance}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_ROOT / "assets/characters/aligned")
    parser.add_argument("--output", type=Path, default=DEFAULT_ROOT / "assets/characters/keyed")
    parser.add_argument("--tolerance", type=int, default=40, help="RGB Euclidean-distance key tolerance")
    args = parser.parse_args()
    try:
        if args.tolerance < 0:
            raise ValueError("tolerance must be non-negative")
        sources = list(png_files(args.input))
        if not sources:
            raise ValueError(f"No PNG files found under {args.input}")
        input_root = args.input if args.input.is_dir() else args.input.parent
        for source in sources:
            relative = source.relative_to(input_root) if args.input.is_dir() else Path(source.name)
            process(source, args.output / relative, args.tolerance)
    except (OSError, ValueError) as exc:
        print(f"alphakey: ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

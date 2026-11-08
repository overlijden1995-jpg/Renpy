#!/usr/bin/env python3
"""Validate character assets and, optionally, the complete manifest-driven game project."""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
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

    for character, frames in sorted(characters.items()):
        points = []
        for frame in sorted(frames):
            if not is_base_frame(frame):
                continue
            metadata = anchors.get(character, {}).get(frame)
            point = metadata.get("foot_midline") if metadata else None
            if isinstance(point, list) and len(point) == 2:
                points.append((frame, point))
        for index, (frame_a, point_a) in enumerate(points):
            for frame_b, point_b in points[index + 1:]:
                drift = math.dist(point_a, point_b)
                if drift > 6.0:
                    errors.append(f"{character}: anchor drift {drift:.2f}px between {frame_a} and {frame_b} exceeds 6px")

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
                        dx, dy = metadata.get("alignment_offset", [0, 0])
                        expected_bbox = None
                        if bbox:
                            expected_bbox = [
                                max(0, bbox[0] + dx), max(0, bbox[1] + dy),
                                min(keyed_image.width, bbox[2] + dx), min(keyed_image.height, bbox[3] + dy),
                            ]
                        if metadata.get("bbox") != expected_bbox:
                            errors.append(f"{rel}: recorded trim bbox {metadata.get('bbox')} does not match translated alpha bbox {expected_bbox}")
                        expected_size = (expected_bbox[2] - expected_bbox[0], expected_bbox[3] - expected_bbox[1]) if expected_bbox else None
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


def read_project_json(path: Path, label: str, errors: list[str]):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{label}: cannot read {path}: {exc}")
        return None


def objective_leaves(objective):
    if isinstance(objective, dict) and isinstance(objective.get("all"), list):
        return [leaf for child in objective["all"] for leaf in objective_leaves(child)]
    return [objective] if isinstance(objective, dict) else []


def collect_dialogue_flags(graph):
    flags = set()
    for node in graph.get("nodes", {}).values():
        flags.update((node.get("flags") or {}).get("set", {}).keys())
        for choice in node.get("choices", []):
            flags.update((choice.get("flags") or {}).get("set", {}).keys())
            for action in choice.get("actions", []):
                if action.get("result_flag"):
                    flags.add(action["result_flag"])
    return flags


def validate_project(args: argparse.Namespace) -> list[str]:
    errors: list[str] = []
    root = DEFAULT_ROOT.resolve()
    manifest = read_project_json(args.manifest, "MANIFEST", errors)
    hotspots = read_project_json(args.hotspots, "hotspots", errors)
    quests = read_project_json(args.quests, "quests", errors)
    dialogue = read_project_json(args.dialogue, "dialogue graph", errors)
    if not all((manifest, hotspots, quests, dialogue)):
        return errors

    # Every runtime image is declared once through the manifest, and all paths are contained by the project.
    assets = manifest.get("assets", {})
    seen_asset_paths: dict[str, str] = {}
    for asset_id, entry in assets.items():
        src = entry.get("src") if isinstance(entry, dict) else None
        if not isinstance(src, str) or not src:
            errors.append(f"MANIFEST asset {asset_id}: missing src")
            continue
        relative = Path(src)
        if relative.is_absolute() or ".." in relative.parts or "://" in src:
            errors.append(f"MANIFEST asset {asset_id}: path must be project-relative: {src}")
            continue
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            errors.append(f"MANIFEST asset {asset_id}: path escapes project root")
            continue
        if src in seen_asset_paths:
            errors.append(f"MANIFEST assets {seen_asset_paths[src]} and {asset_id} duplicate path {src}")
        else:
            seen_asset_paths[src] = asset_id
        if not path.is_file():
            errors.append(f"MANIFEST asset {asset_id}: missing file {src}")
            continue
        if entry.get("type") != "image":
            errors.append(f"MANIFEST asset {asset_id}: unsupported type {entry.get('type')!r}")
        try:
            with Image.open(path) as image:
                image.verify()
        except (OSError, ValueError) as exc:
            errors.append(f"MANIFEST asset {asset_id}: unreadable image {src}: {exc}")

    sprite_contract = manifest.get("spriteFrames", {})
    sprite_ids = sprite_contract.get("assetIds", [])
    expected_sprites = int(sprite_contract.get("expectedCount", 80))
    if len(sprite_ids) != len(set(sprite_ids)):
        errors.append("MANIFEST spriteFrames: duplicate asset ID")
    missing_sprite_ids = [asset_id for asset_id in sprite_ids if asset_id not in assets]
    if missing_sprite_ids:
        errors.append("MANIFEST spriteFrames: unresolved IDs: " + ", ".join(missing_sprite_ids))
    sprite_paths = {assets[asset_id]["src"] for asset_id in sprite_ids if asset_id in assets and "src" in assets[asset_id]}
    sprite_file_count = sum(1 for src in sprite_paths if (root / src).is_file())
    if sprite_file_count != expected_sprites:
        errors.append(f"sprite frame contract: {sprite_file_count}/{expected_sprites} unique frames are present")

    # Scene art and all hotspot rectangles must be manifest-resolved and reachable by canvas clicks.
    canvas = hotspots.get("canvas", [])
    if canvas != [manifest.get("canvas", {}).get("width"), manifest.get("canvas", {}).get("height")]:
        errors.append("hotspots: canvas dimensions do not match MANIFEST.json")
    scene_configs = manifest.get("scenes", {})
    hotspot_scenes = hotspots.get("scenes", {})
    if set(scene_configs) != set(hotspot_scenes):
        errors.append("hotspots: scene IDs differ from MANIFEST.json")
    hotspot_count = 0
    for scene_id, scene in hotspot_scenes.items():
        config = scene_configs.get(scene_id, {})
        background_id = scene.get("backgroundAsset")
        if background_id != config.get("backgroundAsset") or background_id not in assets:
            errors.append(f"hotspots {scene_id}: background must reference a MANIFEST asset ID")
        ids = set()
        for hotspot in scene.get("hotspots", []):
            hotspot_count += 1
            hotspot_id = hotspot.get("id")
            rect = hotspot.get("rect", [])
            if not hotspot_id or hotspot_id in ids:
                errors.append(f"hotspots {scene_id}: duplicate or missing hotspot ID {hotspot_id!r}")
            ids.add(hotspot_id)
            if len(rect) != 4 or not all(isinstance(value, (int, float)) for value in rect):
                errors.append(f"hotspots {scene_id}/{hotspot_id}: invalid rectangle")
                continue
            x, y, width, height = rect
            if x < 0 or y < 0 or width <= 0 or height <= 0 or x + width > canvas[0] or y + height > canvas[1]:
                errors.append(f"hotspots {scene_id}/{hotspot_id}: rectangle falls outside the internal canvas")
                continue
            # A camera can center a click anywhere in the world; test the letterboxed canvas transform at legal zooms.
            world_x, world_y = x + width / 2, y + height / 2
            for zoom in (1.0, 1.25, 1.8):
                cam_x = min(max(world_x, canvas[0] / (2 * zoom)), canvas[0] - canvas[0] / (2 * zoom))
                cam_y = min(max(world_y, canvas[1] / (2 * zoom)), canvas[1] - canvas[1] / (2 * zoom))
                screen_x = canvas[0] / 2 + (world_x - cam_x) * zoom
                screen_y = canvas[1] / 2 + (world_y - cam_y) * zoom
                if not (0 <= screen_x <= canvas[0] and 0 <= screen_y <= canvas[1]):
                    errors.append(f"hotspot {scene_id}/{hotspot_id}: center is unreachable at zoom {zoom}")
                    break
        if not scene.get("hotspots"):
            errors.append(f"hotspots {scene_id}: no clickable hotspots")
    if hotspot_count == 0:
        errors.append("hotspots: no hotspots were validated")

    # Validate that each quest has an executable chain in the colony/dialogue APIs.
    quest_list = quests.get("side_quests", [])
    if len(quest_list) != 7:
        errors.append(f"quests: expected seven side quests, found {len(quest_list)}")
    resource_quests = {quest.get("resource") for quest in quest_list if quest.get("category") == "resource_bottleneck"}
    if resource_quests != {"scrap", "water", "food", "power", "meds"}:
        errors.append("quests: resource bottlenecks must cover scrap, water, food, power, and meds")
    node_flags = collect_dialogue_flags(dialogue)
    if quests.get("unlocked_by_flag") not in node_flags:
        errors.append("quests: opening sequence never sets the quest-board unlock flag")
    building_data = read_project_json(root / "data/buildings.json", "buildings", errors) or {}
    building_types = building_data.get("buildingTypes", {})
    grids = {grid.get("id"): grid for grid in building_data.get("placementGrids", [])}
    companions = {companion.get("id"): companion for companion in building_data.get("companions", [])}
    factions = {faction.get("id") for faction in building_data.get("factions", [])}
    supported = {"resource_gathered", "resource_produced", "building_placed", "assigned_building", "companion_assigned", "resource_available", "faction_standing_change", "flag"}
    for quest in quest_list:
        quest_id = quest.get("id", "(unnamed)")
        entry_node = quest.get("dialogue_entry_node")
        if entry_node and entry_node not in dialogue.get("nodes", {}):
            errors.append(f"quest {quest_id}: missing dialogue entry node {entry_node}")
        for stage in quest.get("stages", []):
            for objective in objective_leaves(stage.get("objective")):
                if objective.get("all"):
                    continue
                kind = objective.get("type")
                if kind not in supported:
                    errors.append(f"quest {quest_id}/{stage.get('id')}: unsupported objective {kind}")
                    continue
                if kind in {"resource_gathered", "resource_produced", "resource_available"} and objective.get("resource") not in building_data.get("resources", {}).get("initial", {}):
                    errors.append(f"quest {quest_id}: unknown resource {objective.get('resource')}")
                if kind == "building_placed":
                    type_id = objective.get("building_type")
                    grid_ids = objective.get("grid_ids") or ([objective["grid_id"]] if objective.get("grid_id") else [])
                    if type_id not in building_types or not any(type_id in grids.get(grid_id, {}).get("allows", []) for grid_id in grid_ids):
                        errors.append(f"quest {quest_id}: no compatible placement grid for {type_id}")
                if kind in {"assigned_building", "companion_assigned"}:
                    companion = companions.get(objective.get("companion_id"))
                    type_id = objective.get("building_type")
                    if not companion or type_id not in building_types:
                        errors.append(f"quest {quest_id}: invalid companion/building assignment objective")
                    else:
                        building = building_types[type_id]
                        skills = {companion.get("specialty"), *companion.get("secondarySpecialties", [])}
                        if building.get("jobRole") not in skills:
                            errors.append(f"quest {quest_id}: {companion['id']} cannot specialize in {type_id}")
                if kind == "resource_produced":
                    producing = [type_id for type_id, definition in building_types.items() if definition.get("productionPerWorker", {}).get(objective.get("resource"), 0) > 0 and definition.get("jobRole")]
                    if not producing:
                        errors.append(f"quest {quest_id}: no staffed building can produce {objective.get('resource')}")
                if kind == "faction_standing_change" and objective.get("faction_id") not in factions:
                    errors.append(f"quest {quest_id}: unknown faction {objective.get('faction_id')}")
                if kind == "flag" and objective.get("name") not in node_flags:
                    errors.append(f"quest {quest_id}: no dialogue node sets objective flag {objective.get('name')}")

    # Runtime image references outside MANIFEST.json are forbidden; content stores asset IDs instead of file paths.
    runtime_files = [root / "index.html", *sorted((root / "project/src").glob("*.js")), args.hotspots, args.dialogue, args.quests]
    hardcoded_asset = re.compile(r"(?:assets/|game/images/|images/[a-z0-9_]+/)")
    for path in runtime_files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"path policy: cannot inspect {path}: {exc}")
            continue
        match = hardcoded_asset.search(text)
        if match:
            errors.append(f"path policy: hardcoded asset path in {path.relative_to(root)}")

    # Exercise real quest completion and all supported save/load serializers.
    try:
        result = subprocess.run(["node", "tools/qa_runtime.mjs"], cwd=root, text=True, capture_output=True, check=False)
        if result.returncode != 0:
            errors.append("runtime round-trip/quest test failed: " + (result.stderr.strip() or result.stdout.strip()))
    except OSError as exc:
        errors.append(f"runtime QA could not start Node.js: {exc}")
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
    parser.add_argument("--whole-project", action="store_true", help="validate MANIFEST.json, scenes, quests, runtime save/load, and path policy")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_ROOT / "MANIFEST.json")
    parser.add_argument("--hotspots", type=Path, default=DEFAULT_ROOT / "data/hotspots.json")
    parser.add_argument("--quests", type=Path, default=DEFAULT_ROOT / "data/quests.json")
    parser.add_argument("--dialogue", type=Path, default=DEFAULT_ROOT / "data/dialogue/graph.json")
    args = parser.parse_args()
    try:
        errors = validate(args)
        if args.whole_project:
            errors.extend(validate_project(args))
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

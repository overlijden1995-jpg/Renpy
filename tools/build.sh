#!/usr/bin/env bash
# Build the character pipeline and lint the Ren'Py project.
set -euo pipefail

TOOLS_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd -- "$TOOLS_DIR/.." && pwd)}"
PYTHON="${PYTHON:-python3}"
RENPY_EXE="${RENPY_EXE:-renpy.exe}"
ASSET_ROOT="${ASSET_ROOT:-$PROJECT_DIR/assets/characters}"
SOURCE_DIR="$ASSET_ROOT/source"
ALIGNED_DIR="$ASSET_ROOT/aligned"
KEYED_DIR="$ASSET_ROOT/keyed"
IMAGE_DIR="$PROJECT_DIR/game/images"
STYLE_FILE="$PROJECT_DIR/docs/STYLE.md"
ANCHORS_FILE="$IMAGE_DIR/anchors.json"
LINT_FILE="$PROJECT_DIR/lint.txt"

if ! "$PYTHON" -c 'from PIL import Image' >/dev/null 2>&1; then
    echo "build: ERROR: Python Imaging Library is required (install Pillow for $PYTHON)." >&2
    exit 1
fi

# These are generated stages; discard stale frames before starting a fresh run.
mkdir -p "$ALIGNED_DIR" "$KEYED_DIR"
find "$ALIGNED_DIR" "$KEYED_DIR" -type f -name '*.png' -delete

"$PYTHON" "$TOOLS_DIR/tickalign.py" --input "$SOURCE_DIR" --output "$ALIGNED_DIR" --style "$STYLE_FILE"
"$PYTHON" "$TOOLS_DIR/alphakey.py" --input "$ALIGNED_DIR" --output "$KEYED_DIR" --tolerance 40
"$PYTHON" "$TOOLS_DIR/layerize.py" --input "$KEYED_DIR" --output "$IMAGE_DIR" --anchors "$ANCHORS_FILE" --clean

VALIDATE_ARGS=(
    --source "$SOURCE_DIR"
    --aligned "$ALIGNED_DIR"
    --keyed "$KEYED_DIR"
    --layerized "$IMAGE_DIR"
    --anchors "$ANCHORS_FILE"
    --style "$STYLE_FILE"
)
"$PYTHON" "$TOOLS_DIR/validate.py" "${VALIDATE_ARGS[@]}"
"$PYTHON" "$TOOLS_DIR/imagesrpy.py" --images "$IMAGE_DIR" --output "$PROJECT_DIR/game/definitions.rpy"

LINT_TMP="$(mktemp)"
trap 'rm -f "$LINT_TMP"' EXIT
lint_status=0
"$RENPY_EXE" "$PROJECT_DIR" lint >"$LINT_TMP" 2>&1 || lint_status=$?
cat "$LINT_TMP"
cp "$LINT_TMP" "$LINT_FILE"

# Run validation again with the freshly written lint report. Ren'Py's own
# non-zero exit status is preserved even if the report text is incomplete.
validate_status=0
"$PYTHON" "$TOOLS_DIR/validate.py" "${VALIDATE_ARGS[@]}" --lint "$LINT_FILE" || validate_status=$?
if (( lint_status != 0 )); then
    echo "build: ERROR: Ren'Py lint exited with status $lint_status; see $LINT_FILE." >&2
    exit "$lint_status"
fi
if (( validate_status != 0 )); then
    echo "build: ERROR: asset or lint validation failed; see $LINT_FILE for lint output." >&2
    exit "$validate_status"
fi

echo "build: complete; lint output saved to $LINT_FILE"

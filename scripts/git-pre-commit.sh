#!/bin/bash
# Pre-commit: optional venv check + consistency kit + theme/export sync.
#
# The gates run before the sync block so a drifted SKILL.md / config fails fast,
# rather than after a pass that rewrites templates. Mirrors .github/workflows/ci.yml.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "Checking python dependencies compatibility..."
if [ -x "$ROOT/.venv/bin/pip" ]; then
    if ! "$ROOT/.venv/bin/pip" check; then
        echo "ERROR: Broken requirements found in virtual environment. Commit aborted."
        exit 1
    fi
else
    echo "No .venv/bin/pip — skipping pip check."
fi

# One kit, five checks: version / byte budget / routing surface / count claims
# / CJK encoding. Config lives in archviz-checks.json.
echo "Checking consistency kit..."
python3 "$ROOT/scripts/check_archviz.py"

echo "Checking consistency kit's own checker..."
python3 "$ROOT/scripts/check_archviz.py" --self-test >/dev/null

# Order is load-bearing and must match .github/workflows/ci.yml:
#   sync modules -> stage
# Both sync scripts exit non-zero if a template is missing its anchor, which
# aborts the commit on purpose.
echo "Syncing theme and export templates..."
python3 "$ROOT/scripts/sync_theme.py"
python3 "$ROOT/scripts/sync_export.py"

# Stage HTML templates only if still inside a git commit
if git rev-parse --git-dir >/dev/null 2>&1; then
    git add templates/html/*.html 2>/dev/null || true
fi

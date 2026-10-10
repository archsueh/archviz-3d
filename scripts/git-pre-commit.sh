#!/bin/bash
# Pre-commit: optional venv check + theme/export sync + prettier on HTML templates
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "Checking python dependencies compatibility..."
if [ -x "$ROOT/.venv/bin/pip" ]; then
    # `pip check` reads distribution metadata off `sys.path`, so an ambient
    # PYTHONPATH leaks foreign packages into the verdict. Measured 2026-10-09:
    # Hermes injects a Python 3.14 site-packages into PYTHONPATH, the 3.12 venv
    # then "sees" a `ruamel-yaml` that was never installed here, and `pip check`
    # aborts the commit over a dependency that does not belong to this repo at
    # all. A venv is self-contained by design — its internal consistency must be
    # judged on its own contents, not on whatever the calling shell exported.
    # `-u PYTHONPATH` restores that isolation.
    if ! env -u PYTHONPATH "$ROOT/.venv/bin/pip" check; then
        echo "ERROR: Broken requirements found in virtual environment. Commit aborted."
        exit 1
    fi
else
    echo "No .venv/bin/pip — skipping pip check."
fi

# Independent of the sync/prettier block below (whose order is load-bearing),
# so it runs first: fail fast on a drifted palette registry rather than after
# a formatting pass. Mirrors the same-named CI step.
#
# The palette registry is a **archviz-diagram-only** concept: the other four
# repos have no `_archviz-theme.html` and no palette gate, so the script is
# absent there. Guard on existence rather than calling unconditionally — the
# unconditional call made every commit in the other four repos abort with
# `can't open file .../check_palette_registry.py` (measured 2026-10-09). A
# missing script is "not applicable here", not "the check failed"; only a
# present-and-failing script may abort.
if [ -f "$ROOT/scripts/check_palette_registry.py" ]; then
    echo "Checking palette registry consistency..."
    python3 "$ROOT/scripts/check_palette_registry.py"
else
    echo "No check_palette_registry.py — palette gate not applicable to this repo."
fi

# Same class of problem, same placement: fail fast before the sync/prettier
# block. The kit owns version / byte budget / routing surface / count claims /
# reference reachability / declared imports / compilation / CJK encoding.
# Do not write the count here — run `python3 scripts/check_archviz.py --list`.
# This comment has drifted twice already. SKILL.md metadata.version is the
# truth for the version check. Mirrors the same-named CI steps.
echo "Checking consistency kit..."
python3 "$ROOT/scripts/check_archviz.py"

echo "Checking consistency kit's own checker..."
python3 "$ROOT/scripts/check_archviz.py" --self-test >/dev/null

# Order is load-bearing and must match .github/workflows/ci.yml:
#   sync modules -> prettier --write -> stage
# Prettier re-indents the embedded <style>/<script> blocks that the sync
# scripts paste in, so a sync-only commit can never satisfy CI's
# `git diff --exit-code` check. Both sync scripts exit non-zero if a template
# is missing its anchor, which aborts the commit on purpose.
#
# Same existence-guard as the palette block above: only archviz-diagram and
# archviz-3d carry the sync scripts and `templates/html`; the other three repos
# have neither, and an unconditional call aborts their commits (measured
# 2026-10-09). Guard each piece on its own presence so a repo without HTML
# templates still gets the kit gates above.
if [ -f "$ROOT/scripts/sync_theme.py" ] && [ -f "$ROOT/scripts/sync_export.py" ]; then
    echo "Syncing theme and export templates..."
    python3 "$ROOT/scripts/sync_theme.py"
    python3 "$ROOT/scripts/sync_export.py"

    if compgen -G "$ROOT/templates/html/*.html" >/dev/null; then
        echo "Formatting synced templates with Prettier..."
        npx --yes prettier@3.9.9 --write "templates/html/*.html"

        # Stage HTML templates only if still inside a git commit
        if git rev-parse --git-dir >/dev/null 2>&1; then
            git add templates/html/*.html 2>/dev/null || true
        fi
    fi
else
    echo "No sync scripts — theme/export sync not applicable to this repo."
fi

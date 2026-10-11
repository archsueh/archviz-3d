"""Sync the shared theme block (_archviz-theme.html) into every HTML template.

Why this script fails loudly
----------------------------
It used the same implicit-silence pattern as `sync_export.py`: a template that
lacked the `<style id="archviz-theme-vars">` anchor was skipped without a word.
`network-topology.html` was the victim — it referenced 11 distinct `--av-*`
variables across 40 call sites while defining none of them, so every colour and
the page background fell back to nothing, and nothing ever reported it.

A template is now skipped only if it is in EXCLUDED, or in THEME_EXEMPT with a
stated reason. A missing anchor anywhere else is an error and exits non-zero.
"""

import re
import sys
from pathlib import Path

# Partial templates that are not meant to carry the theme block.
# The shared skip set lives in one place — see sync_common.py for why.
from sync_common import EXCLUDED

# Templates that deliberately do not carry the shared theme block, with the
# reason. Currently empty — every full-page template reads --av-* tokens, so
# every one of them needs the theme. Add entries here only with a real reason.
THEME_EXEMPT = {}

ANCHOR = '<style id="archviz-theme-vars">'
THEME_BLOCK_RE = re.compile(r'<style id="archviz-theme-vars">.*?</script>', re.DOTALL)


def load_theme_block(templates_dir):
    theme_file = templates_dir / "_archviz-theme.html"
    if not theme_file.exists():
        raise SystemExit(f"ERROR: {theme_file} does not exist")

    theme_content = theme_file.read_text(encoding="utf-8")
    match = THEME_BLOCK_RE.search(theme_content)
    if not match:
        raise SystemExit("ERROR: could not find theme block in _archviz-theme.html")
    return match.group(0)


def sync():
    templates_dir = Path(__file__).resolve().parent.parent / "templates" / "html"
    block = load_theme_block(templates_dir)

    synced, drifted = [], []

    for f in sorted(templates_dir.glob("*.html")):
        if f.name in EXCLUDED or f.name in THEME_EXEMPT:
            continue

        content = f.read_text(encoding="utf-8")
        if ANCHOR not in content:
            drifted.append(f.name)
            continue

        # lambda replacement: the block contains backslash escapes that
        # re.sub would otherwise interpret as group references.
        f.write_text(THEME_BLOCK_RE.sub(lambda _: block, content), encoding="utf-8")
        synced.append(f.name)

    for name in synced:
        print(f"Syncing theme block to {name}...")

    if drifted:
        print()
        print("ERROR: theme anchor not found in:")
        for name in drifted:
            print(f"  - {name}")
        print()
        print("These templates never received the shared theme block. Any")
        print("var(--av-*) in them resolves to nothing, so colours and the page")
        print("background silently fall back to the browser default. To fix,")
        print("insert this line in <head>:")
        print()
        print(f"  {ANCHOR}")
        print()
        print("followed by the style + script blocks from _archviz-theme.html.")
        print("If a template genuinely does not need the theme, add it to")
        print("THEME_EXEMPT with a reason.")
        return 1

    print(f"OK: theme block in sync across {len(synced)} templates.")
    return 0


if __name__ == "__main__":
    sys.exit(sync())

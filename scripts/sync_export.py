"""Sync the shared export module (_archviz-export.html) into every HTML template.

Why this script fails loudly
----------------------------
It used to skip a template silently whenever none of the anchor patterns
matched. `academic-table.html`, `network-topology.html` and
`webgl-info-viz.html` sat in that blind spot: they kept their own stub
`exportPNG()` / `exportWebP()` (which only fired an `alert`) or had no export
at all, and because the skip produced no diff, CI's `git diff --exit-code`
guard passed green the whole time. The drift was invisible by construction.

Every skip is now either (a) an anchor match, or (b) a named entry in
EXCLUDED. Anything else is an error and exits non-zero.
"""

import re
import sys
from pathlib import Path

# Partial templates that are not meant to carry the export module.
EXCLUDED = {
    "_archviz-export.html",
    "_archviz-theme.html",
    "_archviz-animated.html",
    "_flow-attach.html",
    # archviz-3d 自有的 paste-in 模块：它们是片段，不该带导出锚点
    "_archviz-3d-contract.html",
    "_archviz-deps.html",
    "_archviz-svg-overlay.html",
}

# Anchors left behind by earlier versions of this script. Whichever matches,
# the span from the anchor through the final </body> is replaced.
ANCHOR_PATTERNS = (
    r"<!-- === Export System Script === -->.*?</body>",
    r"<!-- archviz-skills Export Utility Script -->.*?</body>",
    r"<!-- Export Utility Module — paste BEFORE </body> of any archviz HTML template -->.*?</body>",
    r"<!-- archviz-skills Export Utility Module -->.*?</body>",
    r'<style id="archviz-export-styles">.*?</body>',
    r"<script>\s*/\* archviz-skills Export System.*?</body>",
)

ANCHOR_COMMENT = "<!-- archviz-skills Export Utility Module -->"


def load_export_block(templates_dir):
    export_file = templates_dir / "_archviz-export.html"
    if not export_file.exists():
        raise SystemExit(f"ERROR: {export_file} does not exist")

    content = export_file.read_text(encoding="utf-8")
    style = re.search(
        r'(<style id="archviz-export-styles">.*?</style>)', content, re.DOTALL
    )
    script = re.search(r"(<script>.*?</script>)", content, re.DOTALL)
    if not style or not script:
        raise SystemExit(
            "ERROR: could not find style or script blocks in _archviz-export.html"
        )
    return f"{style.group(1)}\n\n{script.group(1)}\n"


def sync():
    templates_dir = Path(__file__).resolve().parent.parent / "templates" / "html"
    block = load_export_block(templates_dir)

    synced, drifted = [], []

    for f in sorted(templates_dir.glob("*.html")):
        if f.name in EXCLUDED:
            continue

        content = f.read_text(encoding="utf-8")

        start = None
        for pattern in ANCHOR_PATTERNS:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                start = match.start()
                break

        end = content.rfind("</body>") if start is not None else -1
        if start is None or end == -1 or end <= start:
            drifted.append(f.name)
            continue

        new_content = content[:start] + ANCHOR_COMMENT + "\n" + block + content[end:]
        f.write_text(new_content, encoding="utf-8")
        synced.append(f.name)

    for name in synced:
        print(f"Syncing export module to {name}...")

    if drifted:
        print()
        print("ERROR: export module anchor not found in:")
        for name in drifted:
            print(f"  - {name}")
        print()
        print("These templates never received the shared export module. Any local")
        print("exportPNG()/exportWebP() in them is a stub, so PNG / WebP /")
        print("clipboard export does not actually work. To fix, insert this line")
        print("immediately before </body>:")
        print()
        print(f"  {ANCHOR_COMMENT}")
        print()
        print("followed by the style + script blocks from _archviz-export.html.")
        print("If a template genuinely must not have export, add it to EXCLUDED.")
        return 1

    print(f"OK: export module in sync across {len(synced)} templates.")
    return 0


if __name__ == "__main__":
    sys.exit(sync())

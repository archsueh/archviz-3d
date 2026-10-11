"""Shared constants for the sync scripts.

Why this module exists
----------------------
`sync_theme.py` and `sync_export.py` both skip the same set of partial
templates — the paste-in fragments that are not meant to carry a full theme
block or export module. That set used to be written out **twice**, once in each
script. Two copies of one fact is exactly the disease this family keeps
catching (a version number in four places, a palette in four, a check count in
prose): the day someone adds a fragment to one list and not the other, the two
scripts disagree about which files to skip, and nothing notices because each
list is internally consistent.

So the list lives here, once, and both scripts import it. Adding a new
paste-in fragment means editing one set.
"""

# Partial templates that are not meant to carry the theme block or the export
# module. Both sync scripts skip exactly these (plus each script's own
# reason-bearing exemption table, which is deliberately per-script because the
# reasons differ).
#
# The first three are archviz-3d's own paste-in fragments — snippets, not full
# pages, so they must not carry the shared theme block or export module.
EXCLUDED = {
    "_archviz-3d-contract.html",
    "_archviz-deps.html",
    "_archviz-svg-overlay.html",
    "_archviz-theme.html",
    "_archviz-export.html",
    "_archviz-animated.html",
    "_flow-attach.html",
}

---
name: archviz-3d
description: |
  3D spatial visualization skill for AI agents. Self-contained HTML with Three.js + animejs v4.
  Use when the user asks for 3D building, floorplan, structure, spatial walkthrough, exploded view,
  mechanical visualization, 3D archviz, 建筑3D, 结构可视化, 爆炸图, 空间漫游, 楼层导航,
  or any brief mentioning "3D", "Three.js", "walkthrough", "exploded".
  Default: do NOT enter 3D unless the brief explicitly mentions spatial/3D/building/mechanical.
  For 2D diagrams (flowchart, architecture, data viz) → use archviz (2D infoviz).
  For article illustrations / sketches → use archviz-sketch.
license: MIT
metadata:
  version: 0.1.0
  source: https://github.com/archsueh/archviz-3d
  risk: safe
  author: archsueh
  triggers: 3d, three.js, building, floorplan, structure, walkthrough, exploded, archviz, 建筑, 结构, 爆炸图, 空间, 漫游, 楼层, mechanical, kinematics
---

# archviz-3d

> 3D spatial visualization — self-contained HTML, zero build step, CDN importmap.

## When to Use

- Building structure visualization (envelope, column grid, floor slabs)
- Floor plan navigation (multi-floor, section cut)
- Product exploded views (assembly/disassembly)
- Mechanical system visualization (kinematics, gears, engines)
- Spatial walkthrough (camera orbit, preset views)

## When NOT to Use

- 2D flowcharts, architecture diagrams, data charts → **archviz** (2D)
- Article illustrations, concept sketches → **archviz-sketch**
- Full React/WebGL app with build step → use Vite + R3F directly

## Skill Boundaries

| Need | Use |
|---|---|
| 2D diagram/chart/card | archviz (2D infoviz) |
| 3D building/structure | **this skill** |
| Sketch/illustration | archviz-sketch |
| Full interactive 3D app | Vite + R3F (not self-contained) |

## Tech Stack

- Three.js (CDN importmap, v0.170+)
- animejs v4 (CDN, `dist/bundles/anime.esm.js`)
- OrbitControls (Three.js addons)
- Self-contained HTML (no build step, no npm)

## Key Gotchas

| Issue | Fix |
|---|---|
| animejs v4 path | `dist/bundles/anime.esm.js`, not v3's `lib/anime.es.js` |
| animejs v4 API | `animate(target, props)`, not `anime({targets})` |
| Function naming | NEVER name a function `animate` — shadows the import |
| Ground burial | Objects at y=0 bury into ground; offset to y=2+ |
| Camera transitions | Use tween, never direct `.set()` |
| Max lights | 3 lights enforced for performance |
| OrbitControls + keyboard | Canvas needs `data-orbit` attribute to prevent export keyboard conflicts |

## Architecture

```
archviz-3d/
├── SKILL.md              # This file — routing + gotchas
├── README.md             # GitHub overview
├── templates/html/
│   ├── _archviz-theme.html    # Shared theme system (from archviz)
│   ├── _archviz-export.html   # Shared export system (from archviz)
│   ├── _archviz-deps.html     # CDN importmap reference
│   ├── threejs-archviz.html   # Building structure visualization
│   └── threejs-floorplan.html # Floor plan navigation
├── examples/
│   ├── teaching-building-3d.html
│   └── hair-dryer-exploded.html
└── references/
    └── (Phase 3: kinematics-formulas.md, performance-hygiene.md, mechlab-contract.md)
```

## Theme & Export

Shared with archviz (2D): `_archviz-theme.html` + `_archviz-export.html`.
- T = cycle theme, E = export menu
- 3D canvas has `data-orbit` to prevent keyboard conflicts

## Dials (inherited from archviz)

| Dial | Default | Note |
|---|---|---|
| COMPLEXITY | 5 | 3D inherently higher |
| DENSITY | 4 | Spatial = less dense |
| RESTRAINT | 7 | Minimal chrome, focus on structure |

## Future (Phase 3)

- Physics-correct kinematics (slider-crank, planetary gears)
- ArchVizBuild contract interface
- Baked vector lerp explode
- Offscreen canvas thumbnails
- Engineering hygiene (single renderer, dpr cap, dispose)

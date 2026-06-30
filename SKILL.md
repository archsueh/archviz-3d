---
name: archviz-3d
description: |
  当用户需要建筑结构、楼层功能、机械爆炸图、空间剖面或交互式 3D 教学可视化（明确提到 3D/building/floorplan/structure/exploded/spatial/walkthrough/mechanical）时加载。
  自包含 HTML（Three.js + animejs v4 CDN），零构建。
  2D 流程图/信息可视化 → archviz。
  手绘/草图配图 → archviz-sketch。
  超出自包含复杂度时引导切 Vite + R3F。
license: MIT
metadata:
  version: 0.6.0
  source: https://github.com/archsueh/archviz-3d
  risk: safe
  author: archsueh
  triggers: 3d, three.js, building, floorplan, structure, walkthrough, exploded, 建筑3D, 结构可视化, 爆炸图, 空间漫游, 楼层导航, mechanical, kinematics, spatial
---

# archviz-3d

> 3D spatial visualization — self-contained HTML, zero build step, CDN importmap.

## When to Use

**Tier A — Three.js procedural (self-contained HTML, default)**
- Building structure visualization (envelope, column grid, floor slabs)
- Floor plan navigation (multi-floor, section cut)
- Product exploded views (assembly/disassembly)
- Mechanical system visualization (kinematics, gears, engines)
- Spatial walkthrough (camera orbit, preset views)

**Tier B — Blender Python → glTF (project-directory mode)**
- Complex parametric geometry: real walls with thickness, stairs, curved/irregular structures
- Triggers: "真实墙体" / "楼梯" / "异形结构" / "参数化建筑" / "precise geometry"

**Tier C — Hyper3D AI model → glTF (project-directory mode)**
- Realistic organic/product models: furniture, vegetation, mechanical parts, detailed facades
- Triggers: "家具" / "植被" / "写实" / "realistic" / "furniture" / "detailed model"

## When NOT to Use

- 2D flowcharts, architecture diagrams, data charts → **archviz** (2D)
- Article illustrations, concept sketches → **archviz-sketch**
- Full React/WebGL app with build step → use Vite + R3F directly

## Skill Boundaries

| Need | Use | Output mode |
|---|---|---|
| 2D diagram/chart/card | archviz (2D infoviz) | — |
| 3D structural / exploded / walkthrough | **this skill — Tier A** | self-contained HTML |
| Complex parametric geometry (walls/stairs) | **this skill — Tier B** | project-directory |
| Realistic models (furniture/vegetation) | **this skill — Tier C** | project-directory |
| Sketch/illustration | archviz-sketch | — |
| Full interactive 3D app with build step | Vite + R3F | — |

**Output mode decision:**
```
need realistic/complex models?
  YES → project-directory: index.html + assets/*.glb
  NO  → self-contained: single .html file (default)
```

## Tech Stack

| Path | Version | Tier |
|---|---|---|
| three.js | v0.170.0+ | A / B / C |
| animejs | **v4.5.0** (built-in Three.js adapter + 3D stagger) | A / B / C |
| GLTFLoader | three/addons/loaders/GLTFLoader.js | B / C |
| SVG overlay | inline (no library) — use `_archviz-svg-overlay.html` | A |
| Blender MCP | `mcp__blender__execute_blender_code` / `generate_hyper3d_model_via_text` | B / C |

- OrbitControls (Three.js addons)
- Tier A: Self-contained HTML (no build step, no npm)
- Tier B/C: Project-directory mode (`index.html` + `assets/*.glb`)

## Blender MCP Workflow (Tier B / C)

> Requires Blender running with MCP addon. Tool prefix: `mcp__blender__`.

### Tier B — Parametric geometry via Blender Python

```python
# 1. Build geometry in Blender
mcp__blender__execute_blender_code(code="""
import bpy, bmesh
bpy.ops.mesh.primitive_cube_add(size=1)
obj = bpy.context.active_object
obj.name = "Wall_A"
obj.scale = (8, 0.3, 3)   # 8m wide, 30cm thick, 3m tall
bpy.ops.object.transform_apply(scale=True)
""")

# 2. Preview
mcp__blender__get_viewport_screenshot()

# 3. Export glTF
mcp__blender__execute_blender_code(code="""
import bpy
bpy.ops.export_scene.gltf(
    filepath="/path/to/project/assets/scene.glb",
    export_format='GLB',
    export_apply=True,
)
""")
```

### Tier C — AI model via Hyper3D

```python
# 1. Generate model from text
mcp__blender__generate_hyper3d_model_via_text(
    text_prompt="modern minimalist sofa, white fabric, wooden legs",
    bbox_condition=[2.0, 0.9, 0.8]   # L×W×H ratio
)

# 2. Import into scene (use task_uuid from step 1)
mcp__blender__import_generated_asset(name="sofa", task_uuid="<uuid>")

# 3. Position + export
mcp__blender__execute_blender_code(code="""
import bpy
obj = bpy.data.objects["sofa"]
obj.location = (0, 0, 0)
bpy.ops.export_scene.gltf(
    filepath="/path/to/project/assets/sofa.glb",
    export_format='GLB', export_apply=True,
)
""")
```

### Three.js side — GLTFLoader template

```html
<script type="importmap">
{
  "imports": {
    "three": "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"
  }
}
</script>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const loader = new GLTFLoader();
loader.load('./assets/scene.glb', (gltf) => {
  scene.add(gltf.scene);
  // Blender materials, hierarchy, and animations are preserved
}, undefined, (err) => console.error('GLTFLoader error:', err));
</script>
```

### Constraints

| Rule | Reason |
|---|---|
| Export path must be absolute in Blender Python | Blender resolves relative paths from its own CWD |
| `export_apply=True` | Applies modifiers + transforms before export |
| ≤ 2MB .glb for base64 embed | Larger files must stay as external references |
| Run `get_viewport_screenshot` before export | Catch geometry errors visually |

---

## SVG Annotation Overlay

Use `_archviz-svg-overlay.html` when the 3D scene needs 2D text labels anchored to world positions.

```
Keyword triggers → add SVG overlay:
  "标注楼层" / "标注零件" / "显示数据" / "标注面积"
  "label" / "annotate" / "data overlay" / "floor label"
  "点击显示信息" / "click to show info"

Pure Three.js (no overlay needed):
  pure walkthrough / structural visualization / animation-only
```

```js
// detectAnnotationNeed — call before choosing template
function detectAnnotationNeed(request) {
  const annotationKw = ['标注', '标签', 'label', 'annotate', '面积', '楼层名', 'data overlay', '信息面板'];
  return annotationKw.some(k => request.includes(k));
}

// Template selection
const useOverlay = detectAnnotationNeed(userRequest);
// useOverlay=true  → threejs-archviz.html + _archviz-svg-overlay.html
// useOverlay=false → threejs-archviz.html alone
```

**Gotcha:** SVG layer must be `pointer-events: none` — otherwise it blocks OrbitControls mouse events. The `AnnotationLayer` class in the template handles this automatically.

## CDN Importmap (verified)

```html
<script type="importmap">
{
  "imports": {
    "three": "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/",
    "animejs": "https://cdn.jsdelivr.net/npm/animejs@4.5.0/dist/bundles/anime.esm.js",
    "animejs/adapters/three": "https://cdn.jsdelivr.net/npm/animejs@4.5.0/dist/modules/adapters/three/index.js"
  }
}
</script>
```

## Three.js Adapter (v4.5.0+)

Import as a side-effect **after** `animejs` — registers itself globally so `animate()` can target Three.js objects directly.

```js
import { animate, stagger } from 'animejs';
import 'animejs/adapters/three'; // side-effect: registers adapter

// Animate any Object3D property:
animate(mesh.position, { x: 5, y: 2, duration: 800, easing: 'easeOutCubic' });
animate(mesh.rotation, { y: Math.PI, duration: 600 });
animate(material, { opacity: 0, roughness: 0.2, duration: 500 });
animate(light, { intensity: 3, duration: 1000 });
animate(camera.position, { x: 10, y: 5, z: 15, duration: 1200 });

// 3D stagger — floor-by-floor building reveal:
animate(floorMeshes, {
  position: { y: stagger(3, { grid: [1, floorMeshes.length, 1], from: 'first' }) },
  opacity: stagger([0, 1], { grid: [1, floorMeshes.length, 1] }),
  delay: stagger(120),
  duration: 600,
  easing: 'easeOutExpo',
});
```

**What the adapter can target:** `Object3D` (position/rotation/scale), `Material` (opacity/roughness/metalness/color), `Light` (intensity/color), `Camera` (fov/position), `InstancedMesh`, `UniformNode` (TSL shaders).

**Instance safety:** The adapter imports from `animejs` (same importmap entry as the bundle), so both share the same module instance — no duplicate registration.

## Key Gotchas

| Issue | Fix |
|---|---|
| animejs v4 path | `dist/bundles/anime.esm.js`, not v3's `lib/anime.es.js` |
| animejs v4 API | `animate(target, props)`, not `anime({targets})` |
| Function naming | NEVER name a function `animate` — shadows the import; use `renderLoop` or `tick` |
| Three.js adapter | v4.5.0+ can animate Three.js targets natively: `animate(mesh.position, {x: 1})`; use `tween` wrapper only for non-Three targets |
| Ground burial | Objects at y=0 bury into ground; offset to y=2+ or lower ground plane |
| Camera transitions | Use tween, never direct `.set()` (causes instant jump) |
| Max lights | 3 lights enforced for performance |
| OrbitControls + keyboard | Canvas needs `data-orbit` attribute to prevent export keyboard conflicts |

## Detailed Pitfalls & Patterns

### 1. Module Scope — THREE Not Available in Non-Module Scripts

**Symptom:** `THREE is not defined` in non-module script that runs before module imports.

**Cause:** Non-module `<script>` runs synchronously before `<script type="module">` (which is deferred). A non-module `<script>` defining a contract class runs FIRST, when THREE hasn't been imported yet.

**Fix:** Put all code inside one `<script type="module">` block, after imports:

```html
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// Contract/utility code here — THREE is available
class ArchVizBuild {
  constructor() { this.root = new THREE.Group(); }
}

// Scene code follows
const renderer = createArchVizRenderer(canvas);
```

**Alternative (fallback):** Expose globally from the module:
```html
<script type="module">
import * as THREE from 'three';
window.THREE = THREE;
</script>
<script>
// Contract code here — THREE is available via window.THREE
</script>
```

**Symptom of wrong approach:** Canvas goes completely black — the module silently fails, nothing renders.

### 2. HTML Comment Nesting — Metadata Leaks as Visible Text

**Symptom:** File metadata (author, date, description) appears as visible text on the page.

**Cause:** Nested HTML comments — the `-->` on an inner comment closes the outer one:
```html
<!--                           ← opens comment A
<!-- archviz Phase 3 | 2026-06-13 -->   ← closes comment A (the --> on this line)
  Three.js Building...          ← NOW OUTSIDE COMMENT — rendered as text!
-->
```

**Fix:** Don't nest comments. Either:
```html
<!-- archviz Phase 3 | 2026-06-13 -->
<!-- Three.js Building Structure Visualization -->
```
Or a single block:
```html
<!--
  archviz Phase 3 | 2026-06-13
  Three.js Building Structure Visualization
-->
```

### 3. Batch Template Injection — drawChart Not Wrapping

**Symptom:** After batch-injecting theme/export modules, canvas charts don't redraw on theme change.

**Cause:** The injection script adds `window.addEventListener('archviz-theme-changed', ...)` but the drawing code isn't wrapped in a `drawChart()` function.

**Fix:** After injection, find the main drawing script (contains `getContext`) and wrap:
```js
// Before (inline drawing code):
const ctx = document.getElementById('c').getContext('2d');
// ... drawing code ...

// After (wrapped):
function drawChart() {
  const ctx = document.getElementById('c').getContext('2d');
  // ... drawing code ...
}
drawChart();
```

**Note:** Theme toggle changes CSS vars but canvas stays same color — because canvas reads colors once at load, not reactively. Wrapping in `drawChart()` enables re-invocation on theme change.

### 4. WebGL Not Rendering in Headless Browser

**Symptom:** Canvas is blank in automated browser tests, but works in real browser.

**Cause:** Headless browser may not have GPU/WebGL 2.0 support. Even original working templates show black canvas + empty exceptions.

**Mitigation:** This is a testing limitation, not a code bug. Verify code structure (braces balanced, references correct) via script. Ask user to test in real browser.

### 5. MCP Server `--args` Pitfall

**Wrong:** `--args "-m archviz3d.mcp_server"` (single string)
**Right:** `--args "-m" "archviz3d.mcp_server"` (space-separated)

## Engineering Hygiene Constants

```js
const ARCHVIZ_HYGIENE = {
  DPR_CAP: 2,                    // Math.min(devicePixelRatio, 2)
  MAX_LIGHTS: 3,
  SHADOW_MAP_SIZE: 1024,         // Not 2048 — perf balance
  FRUSTUM_CULLING: true,
};
```

## Architecture

```
archviz-3d/
├── SKILL.md              # This file — routing + gotchas
├── README.md             # GitHub overview
├── templates/html/
│   ├── _archviz-theme.html       # Shared theme system (from archviz)
│   ├── _archviz-export.html      # Shared export system (from archviz)
│   ├── _archviz-deps.html        # CDN importmap reference
│   ├── _archviz-3d-contract.html # ArchVizBuild contract
│   ├── _archviz-svg-overlay.html # SVG annotation layer (AnnotationLayer class)
│   ├── _archviz-gltf.html        # GLTFLoader template (Tier B/C)  ← NEW
│   ├── threejs-archviz.html      # Building structure visualization (Tier A)
│   └── threejs-floorplan.html    # Floor plan navigation (Tier A)
├── examples/
│   ├── teaching-building-3d.html
│   └── hair-dryer-exploded.html
│   └── living-room-gltf/         # Tier C example: Hyper3D sofa + GLTFLoader ← NEW
│       ├── index.html
│       └── assets/sofa.glb
└── references/
    └── (Phase 3: kinematics-formulas.md, performance-hygiene.md, mechlab-contract.md)
```

**Tier A output:** single `.html` file (self-contained)
**Tier B/C output:** project directory with `index.html` + `assets/*.glb`

## ArchVizBuild Contract

**File:** `_archviz-3d-contract.html` — reusable contract for all 3D templates.

**Provides:**
- `ArchVizBuild` base class (root, parts[], addPart, update, dispose, setWireframe, thumbnail)
- `createArchVizRenderer(canvas)` — enforces dpr cap 2, shadow map, tone mapping
- `createArchVizScene(bgColor)` — enforces frustum culling
- `addLight(scene, light)` — enforces max 3 lights, standardizes shadow map size
- `ARCHVIZ_HYGIENE` constants (DPR_CAP, MAX_LIGHTS, SHADOW_MAP_SIZE)
- `window.beforeunload` dispose guard

**Integration:** Include full content inside `<script type="module">` (after THREE import), NOT as a separate non-module script.

**Explode pattern:** Two approaches — baked vector lerp (scrub-friendly, slider-driven) or animejs adapter (fire-and-forget, v4.5.0+):

**Option A — baked lerp** (use when you need scrubbing / a range slider to control explode %):
```js
// Driven by a 0–1 value (e.g. slider), NOT time-based
_updateExplode(t) { ... } // see lerp pattern below
```

**Option B — animejs adapter** (use when you want a one-shot "explode" animation on click):
```js
import 'animejs/adapters/three';
parts.forEach((part, i) => {
  animate(part.position, {
    x: targetPositions[i].x, y: targetPositions[i].y, z: targetPositions[i].z,
    duration: 800, delay: i * 60, easing: 'easeOutExpo',
  });
});
```

**Option A detail — baked vector lerp** (`lerpVectors` + smoothstep):

```js
_updateExplode(t) {
  const eased = t * t * (3 - 2 * t); // smoothstep
  this.parts.forEach(part => {
    const data = this._exploders.get(part.name);
    part.group.position.lerpVectors(data.originalPos, data.originalPos.clone().add(data.vec), eased);
  });
}
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

## MCP Server Setup

```bash
cd ~/Developer/archviz-3d
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[mcp]"

hermes mcp add archviz-3d \
  --command "/Users/mac/Developer/archviz-3d/.venv/bin/python" \
  --args "-m" "archviz3d.mcp_server"
```

**Tools:** `archviz3d_generate(type, data, options)`, `archviz3d_list_types()`

Full MCP architecture: see `sankey-rendering` skill → `references/mcp-architecture.md`.

## Future (Phase 3)

- Physics-correct kinematics (slider-crank, planetary gears)
- Baked vector lerp explode
- Offscreen canvas thumbnails
- Engineering hygiene (single renderer, dpr cap, dispose)
- WebGPU + TSL GPGPU strand simulation (ref: [Collective Trajectories](https://github.com/jeonghopark/Collective-Trajectories) — `~/Developer/collective-trajectories/`)

---

## 技术参考：WebGPU + TSL GPGPU

来源：[Collective Trajectories](https://github.com/jeonghopark/Collective-Trajectories) (jeonghopark · CC BY-NC 4.0)

**本地路径：** `~/Developer/collective-trajectories/`  
**构建：** `pnpm install && pnpm build` → `dist/`  
**运行：** `cd dist && python3 -m http.server 8768`

**核心技术栈：**
- Three.js `^0.184.0` — `three/webgpu` + `three/tsl`
- GPGPU compute: `Fn(...).compute()` → `StorageBufferAttribute`
- 每帧在 GPU 上计算粒子位置/亮度，CPU 零负担

**适用场景：**
- 大规模粒子/strand 模拟（100–5000 条）
- 实时 curl noise 变形
- U-shaped 亮度包络 + 脉冲流
- 球面波纹 + 音频响应
- 深度线索（雾/DoF/遮挡）

---

## 交叉优化：3D × Animate (Explosion Animation)

**功能：** 将 3D 爆炸图数据转换为动画 GIF

**脚本：** `scripts/render_3d_explosion.py`

**数据格式：**
```json
{
  "title": "Product Exploded View",
  "subtitle": "Assembly breakdown",
  "width": 800,
  "height": 600,
  "parts": [
    {
      "name": "Top Cover",
      "x": 0,
      "y": -80,
      "z": 0,
      "width": 120,
      "height": 40,
      "depth": 15,
      "explode_x": 0,
      "explode_y": -100,
      "explode_z": 50
    }
  ]
}
```

**渲染命令：**
```bash
python3 scripts/render_3d_explosion.py \
  --spec explosion-spec.json \
  --outdir ./output \
  --basename explosion-name \
  --frames 30 \
  --fps 15
```

**参数：**
- `--frames`: 帧数（默认 30）
- `--fps`: 帧率（默认 15）

**输出：**
- `explosion-name.gif` — 爆炸动画
- `explosion-name.png` — 静态爆炸图

**动画效果：**
- 零件从中心向外爆炸
- ease-in-out 缓动函数
- 连接线淡入
- 3D 深度模拟

---

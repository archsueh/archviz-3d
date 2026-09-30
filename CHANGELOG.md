# Changelog

## v0.6.2 (2026-09-30)

Re-synced the shared partials to archviz-diagram and gave this repo the same
maintenance scripts, so the inline copies stop being hand-maintained.

### Changed
- **`_archviz-theme.html` and `_archviz-export.html` re-synced** to
  archviz-diagram's modules. They had been stale forks since 2026-06-13. The
  theme registry goes **7 → 11** palettes (`still-paper`, `signal-proof`,
  `bridge-canvas`, `blueprint`); the export module picks up the `tagName`
  case fix and the 10 s `svgToBlob` guard diagram received.
- **This repo now carries `scripts/sync_theme.py` + `scripts/sync_export.py`**
  (copied from archviz-diagram; this repo's three extra paste-in partials —
  `_archviz-3d-contract.html`, `_archviz-deps.html`, `_archviz-svg-overlay.html`
  — added to `EXCLUDED` with a reason). The templates' inline copies are now
  generated, not hand-written. That removes the failure mode behind v0.6.1's
  P0: a hand-minified copy that lost a `}`.
- **The theme block was relocated in both templates.** It used to be split —
  palette CSS inside the head's shared `<style>`, theme JS in a separate
  `<script>` near the end. `sync_theme.py` requires the block to be contiguous
  between `<style id="archviz-theme-vars">` and the first `</script>`, so the
  whole block (CSS + JS) now sits as one unit in `<head>`.

### Docs
- `README.md` / `SKILL.md` no longer advertise a palette count (both said "4",
  and had been wrong since long before). They point at `ARCHVIZ_PALETTES`.

### Verified
- `node --check` on every inline `<script>` (classic and module), both templates.
- Headless Chromium: no `pageerror`; `ARCHVIZ_PALETTES` = **11** keys and
  cycles; PNG / WebP export at 5760×3600, **100 % opaque** — 1407 and 9920
  distinct colours respectively, i.e. the same numbers as before the splice, so
  the export path was not disturbed.
- Both sync scripts are idempotent: a second run leaves `git diff --stat`
  unchanged.

### Known, not fixed here
- **Still no CI.** Nothing enforces the sync; run both scripts before committing.

## v0.6.1 (2026-09-30)

Export chain was non-functional in both templates. Reproduced in headless
Chromium before and after each fix.

### Fixed
- **`threejs-floorplan.html` export was completely dead.** A hand-minified
  inline copy of the export module had lost the `}` that closes
  `blob=>{…}` in `svgToBlob`, so `)`, `;`, `}` landed one token out of
  place. The whole `<script>` failed to parse (`SyntaxError: Unexpected
  token ')'`), `window.archvizExport` was never defined, and the Export
  button never appeared. One character: `reject(…)),format` →
  `reject(…));},format`.
- **PNG and WebP export were 100% transparent.** `WebGLRenderer` was
  created without `preserveDrawingBuffer`, so once a frame had been
  composited the drawing buffer was discarded and the export module's
  `ctx.drawImage(renderer.domElement, …)` path read back an empty buffer.
  A 5760×3600 PNG containing exactly one colour and 0% opaque pixels is
  what "export" produced. Both templates now pass
  `preserveDrawingBuffer: true`.
- **SVG-namespace `tagName` comparison never matched.** SVG elements report
  a lowercase `tagName` (`"svg"`), HTML elements an uppercase one
  (`"CANVAS"`). Comparing against `'SVG'` sent every SVG target down the
  HTML branch. Both inline copies and the shared `_archviz-export.html`
  partial now lowercase the tag first.
- **Removed the `<foreignObject>` HTML fallback.** Wrapping `outerHTML` in a
  `<foreignObject>` and loading it as an `<img>` blocks Chromium's image
  decoder on any non-trivial subtree — it hangs the main thread so
  completely that even a timeout guard cannot fire. HTML targets now fail
  fast with an explanatory error instead of hanging forever.
- **`ReferenceError: scene is not defined` on every `threejs-archviz.html`
  load.** The "ArchVizBuild Contract" block sat in a classic `<script>` but
  referenced `scene` / `renderer`, which are `const` at module scope in the
  preceding `type="module"` script. The block threw on the first statement,
  so the GPU dispose guard and the light cap never installed. It now lives
  inside the module, immediately after `scene` is initialised and before the
  `addLight()` calls — the light cap only works if `scene.add` is wrapped
  before the scene is populated.
- Added a 10s timeout guard to the partial's `svgToBlob` so a stalled
  rasterization rejects instead of leaving a promise pending forever.

### Changed
- Metadata version bumped to 0.6.1.

### Known, not fixed here
- `canvasToBlob` checks for a `canvas.renderAtScale(ctx, scale)` hook that no
  template in this repo — or in archviz-diagram — implements. The branch is
  dead code in the whole family; canvas export always takes the upscale
  fallback. Left as-is for consistency.
- The two inline copies of the export module remain hand-minified, which is
  what corrupted `threejs-floorplan.html` in the first place. There is no
  sync script and no CI in this repo, so the partials have drifted from
  archviz-diagram since 2026-06-13. See the note in `SKILL.md`.

## v0.5.0 (2026-06-23)

### Added
- Three.js adapter support (animejs v4.5.0): `import 'animejs/adapters/three'` as side-effect
- `animejs/adapters/three` importmap entry in both SKILL.md and `_archviz-deps.html`
- New "Three.js Adapter" section in SKILL.md with usage patterns for Object3D, Material, Light, Camera
- 3D stagger pattern for floor-by-floor building reveals (`grid: [cols, rows, depth]`)
- Implemented a staggered floor-by-floor entry reveal animation utilizing 3D stagger in `threejs-floorplan.html` and `threejs-archviz.html`
- Added support for `isExploded` and `isWireframe` startup parameters injected by the server in `threejs-archviz.html`

### Changed
- animejs CDN bumped from v4.4.1 → v4.5.0 in importmap + `_archviz-deps.html`
- Explode pattern section updated: Option A (baked lerp, scrub-friendly) vs Option B (animejs adapter, fire-and-forget)
- Refactored `threejs-floorplan.html` and `threejs-archviz.html` templates, as well as `teaching-building-3d.html` and `hair-dryer-exploded.html` examples, to use `animejs@4.5.0` and register the Three.js adapter
- Unified `threejs-archviz.html` with the `ArchVizBuild` contract (supporting explode views, wireframe toggles, renderer/scene/light factories)
- Fixed a renderLoop crash in `threejs-archviz.html` caused by the local `animate` loop shadowing the animejs `animate` import
- Metadata version bumped to 0.5.0
- `_archviz-deps.html` verified date updated to 2026-06-23

## v0.2.0 (2026-06-13)

### Added
- _archviz-3d-contract.html: ArchVizBuild contract (addPart, update, dispose, setWireframe, thumbnail)
- Engineering hygiene: createArchVizRenderer (dpr cap 2), createArchVizScene, addLight (cap 3, shadow map 1024)
- references/3d/boundary-declaration.md: self-contained HTML vs full app thresholds
- threejs-archviz.html refactored to use contract

### Changed
- Explode uses baked vector lerp (smoothstep) instead of per-frame animejs
- Render loop renamed from `animate` to `renderLoop` (avoids animejs import conflict)
- Renderer uses `createArchVizRenderer()` factory (enforces dpr cap, shadow settings)
- Lights use `addLight()` (enforces cap, standardizes shadow map size)
- dispose() on window.beforeunload for GPU resource cleanup

## v0.1.0 (2026-06-13)

### Added
- Initial split from archviz (formerly archviz-skills)
- Three.js building structure template
- Three.js floor plan template
- Shared theme/export modules from archviz
- Examples: teaching building, hair dryer exploded

# Changelog

## v0.5.0 (2026-06-23)

### Added
- Three.js adapter support (animejs v4.5.0): `import 'animejs/adapters/three'` as side-effect
- `animejs/adapters/three` importmap entry in both SKILL.md and `_archviz-deps.html`
- New "Three.js Adapter" section in SKILL.md with usage patterns for Object3D, Material, Light, Camera
- 3D stagger pattern for floor-by-floor building reveals (`grid: [cols, rows, depth]`)

### Changed
- animejs CDN bumped from v4.4.1 → v4.5.0 in importmap + `_archviz-deps.html`
- Explode pattern section updated: Option A (baked lerp, scrub-friendly) vs Option B (animejs adapter, fire-and-forget)
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

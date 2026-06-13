# Changelog

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

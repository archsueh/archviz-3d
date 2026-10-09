# Changelog

## v0.7.1 (2026-10-09)

### Fixed

- **`references/` 索引是错的，而且两个方向都错。** SKILL.md 的 `## Architecture`
  目录树里写着 `└── (Phase 3: kinematics-formulas.md, performance-hygiene.md,
  mechlab-contract.md)` —— **这三个文件一个都不存在**；而目录里实际有的四个文件
  （`3d-models-sources.md` / `gotchas.md` / `mechlab-analysis.md` /
  `threejs-gotchas.md`）**一个都没列**。现在树里列全四个，并标出哪两个是维护者
  文件（非 agent 面）。这是套件新增的 `coverage` 检查第一次派上用场的现场。
- **`scripts/` 有未声明的第三方依赖。** `render_3d_explosion.py` 顶层 `import PIL`，
  而仓库既无 `requirements.txt`，pyproject 的 `dependencies = []` 又是刻意的
  （包本身零依赖）。现由 `requirements.txt` 声明 Pillow，并由套件的 `deps`
  检查守住不再复发。同一缺陷在**家族五个仓库里全部存在**。

### Added

- **`requirements.txt`** —— `Pillow`。此前干净检出直接 `ImportError`。
- **`coverage` 检查** —— 套件新增：`references/*.md` 必须从 SKILL.md **可达**。
  索引里漏一个文件，任何计数都还是对的 —— 这个失效模式 `counts` 结构上看不见。
- **`deps` 检查** —— 套件新增：把仓库里每个第三方 import 与清单对账。

### Changed

- **`design-judgment` 集成块移出 SKILL.md 正文。** 2026-10-09 20:32:55 有并行会话
  在五个 archviz 仓库的 SKILL.md 末尾各追加了一段 956 字节的
  `<!-- design-judgment-integration -->` 块（交付前跑五段判断链自检）。
  **内容逐字保留，未删改一字**，但 956 字节会把本仓顶到 23,205 / 23,000 —— 超限。
  现移入 `references/design-judgment.md`，正文只留一行指针，SKILL.md 回到
  22,615 字节。`references/` 目录树里同步列出该文件。

## v0.7.0 (2026-10-09)

This repo had **no CI at all** before this release, and the version was written
down in two places that disagreed. Both are now gated.

### Fixed

- **`pyproject.toml` was 0.2.0 while SKILL.md and CHANGELOG said 0.6.2 — four
  minor releases of drift, with nothing able to notice.** `pip install -e .`
  would have installed a package whose metadata reported 0.2.0 while the skill
  shipped as 0.6.2. SKILL.md `metadata.version` is the release truth; everything
  else is now checked against it.
- **`description` now states the type count explicitly** (`2 类型：building…、
  floorplan…`). Both names were already routed, but the count was written
  nowhere, so there was nothing for a count gate to hold. The description is the
  one text an agent reads *before* deciding to load the skill, which makes it the
  right place for both the routing surface and the count.

### Added

- **`scripts/check_archviz.py`** — the family's portable consistency kit
  (archviz-diagram ADR-003). One file, per-repo `archviz-checks.json`, stdlib
  only, no venv and no package import required. Five checks: `version` /
  `budget` / `routing` / `counts` / `cjk`. `--self-test` carries 23 adversarial
  fixtures, four of which must **not** fire.
- **`.github/workflows/ci.yml`** — first CI for this repo. Runs the sync scripts,
  requires zero diff (a committed template that no longer matches its source is
  silent drift), then runs the kit and the kit's own checker.
- **`scripts/git-pre-commit.sh`** — same gates locally, before the sync block.
- **`.gitattributes`** — pins SKILL.md to LF. The byte cap counts LF-normalised
  bytes so a checkout with `core.autocrlf=true` measures the committed size.
- **`archviz-checks.json`** — registry: 2 types from `archviz3d/engine.py`.

### Verified

- `scripts/check_archviz.py` → PASS (5/5)
- `scripts/check_archviz.py --self-test` → 23/23
- Sync scripts produce zero diff on a clean tree, so the CI sync-drift step is
  satisfiable rather than permanently red.
- `cjk` flagged 4 templates without a charset declaration; all four are
  `_`-prefixed paste-in fragments with no `<head>` of their own. Registered as
  exemptions **with a stated reason each** — the kit fails an exemption that
  carries no reason, and `_archviz-export.html` (also a fragment, but it does
  declare a charset) was deliberately left out.

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

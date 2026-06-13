# Gotchas (Highest Value — 3D Spatial)

## Kinematics & Contract (Phase 3 Priority)
- 动画 keyframe 容易不物理：必须用公式驱动 (slider-crank, epicyclic ratios, Wankel epitrochoid)。
- 切换机器不 dispose：GPU 内存泄漏。强制 ArchVizBuild { root, parts, update(t,mode), dispose }。

## Performance & Hygiene
- dpr 不 cap：移动端卡。永远 Math.min(window.devicePixelRatio, 2)。
- 多光源 + 实时 shadow：性能杀手。最多 3 光 + hero-only shadow 或 ContactShadows。
- 模型加载后 y=0 埋地：所有 root 物体必须 offset y=2+ 或地面下沉。

## Self-Contained CDN
- animejs v4 路径错：必须 dist/bundles/anime.esm.js + named import { animate }。
- render loop 命名 animate：shadow import。永远用 renderLoop。
- 键盘 T/E 与 OrbitControls 冲突：canvas 必须 data-orbit 属性 + event 守卫。

**追加**：真实 3D 教学任务后立即记录。

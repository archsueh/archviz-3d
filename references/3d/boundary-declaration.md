# archviz-3d 边界声明

## 自包含HTML vs 完整App的边界

archviz-3d 的核心交付形态是**自包含HTML**（CDN importmap，零构建步骤）。当场景复杂度超过以下阈值时，应指引用户切到 Vite + R3F 完整应用。

### 适用自包含HTML的场景

| 条件 | 满足则用自包含HTML |
|---|---|
| 部件数 | ≤8 个独立可交互部件 |
| 物理交互 | 无或简单（explode/rotate/keyframe） |
| 教学UI | 基础（按钮切换视图、explode滑块） |
| 部署方式 | 直接打开HTML文件或嵌入iframe |
| 分享需求 | 零依赖，邮件/微信/网页直接发 |

### 超出阈值 → 切 Vite + R3F

| 信号 | 建议 |
|---|---|
| >8 部件 + 物理仿真 | 用 Vite + R3F + cannon-es/rapier |
| 需要复杂状态管理 | 用 Zustand + R3F |
| 需要LOD/instancing | 用 Three.js BufferGeometry + InstancedMesh |
| 需要多人协作/实时 | 用完整Web应用架构 |
| 需要离屏缩略图+sidebar | 用 React + 离屏canvas |

### 参考实现

- mechlab (thebuggeddev/mechlab)：React + R3F + GSAP + Zustand，物理正确kinematics
- 如果需要从自包含HTML迁移到完整App，mechlab的 `MachineBuild` contract 是好的参考

## ArchVizBuild Contract

所有自包含3D模板必须实现：

```js
class ArchVizBuild {
  constructor() { this.root = new THREE.Group(); this.parts = []; }
  addPart(name, group, explodeVec) { /* register explodable part */ }
  update(t, mode) { /* 'normal'|'explode'|'wireframe' */ }
  dispose() { /* GPU cleanup: geometry + material + texture + shadow map */ }
}
```

### dispose() 要求

- 遍历 scene graph，dispose 所有 geometry、material、texture
- 移除 shadow map render targets
- 从 parent group 移除 root
- window.beforeunload 自动调用

### 工程卫生常量

```js
const ARCHVIZ_HYGIENE = {
  DPR_CAP: 2,
  MAX_LIGHTS: 3,
  SHADOW_MAP_SIZE: 1024,
  FRUSTUM_CULLING: true,
  CONTACT_SHADOW_SIZE: 512,
};
```

## 动画规范

- 相机过渡：必须用 animejs tween，不用 `.set()`（会导致跳变）
- Explode：用 baked vector lerp（`lerpVectors` + smoothstep），不用逐帧 animejs
- 渲染循环函数：不能叫 `animate`（和 animejs import 冲突），用 `renderLoop` 或 `tick`

## CDN 路径（已验证 2026-06-13）

```
three: https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js
three/addons/: https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/
animejs: https://cdn.jsdelivr.net/npm/animejs@4.4.1/dist/bundles/anime.esm.js
```

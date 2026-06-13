# mechlab — 3D Mechanical Systems Explorer 参考分析

来源: https://github.com/thebuggeddev/mechlab
用途: archviz-3d 升级参考

## 核心架构

### MachineBuild Contract (借鉴目标)
```ts
interface MachineBuild {
  root: THREE.Group           // 场景根节点
  parts: MachinePart[]        // 部件组 + 预烘焙爆炸向量
  update(t: number, mode: string): void  // 运动学驱动
  dispose(): void             // GPU资源清理
}
```
archviz-3d 的 ArchVizBuild 已有类似设计，可升级为更完整的 contract。

### 注册表模式
所有机器在 `modules/machines/registry.ts` 注册（名称、统计、动画触发器、相机位置）。
侧边栏、查看器、控件都从注册表读取，添加新机器不需要修改核心代码。

→ archviz-3d 应采用同样模式：`archviz3d/engine.py` 中 TYPE_REGISTRY 已是雏形，扩展为完整注册表。

### 物理正确动画（非关键帧）
- 活塞: slider-crank 公式（曲柄角度→活塞位置）
- V8: 十字平面相位 + 点火顺序闪烁
- 凸轮轴: 曲轴转速的一半（四冲程正时）
- 转子引擎: 偏心轨道 + 1/3 转速旋转
- 差速器: 环齿轮比 + 转弯时±35%轴速差
- 行星齿轮: 精确周转轮比

→ archviz-3d Phase 3 目标。

### 性能优化
- 单 WebGLRenderer（dpr cap 2, ACES tone mapping）
- 程序化几何（无外部模型加载，<50ms生成）
- 离屏缩略图预渲染（启动时一次性生成）
- 零内存分配渲染循环
- 机器切换时完整 GPU dispose
- 视锥剔除（V8 引擎仅~60k 三角面）

### 无障碍
- 键盘可达控件
- ARIA 标签/角色
- 可见焦点环
- prefers-reduced-motion 支持
- 高对比度单色模式

## archviz-3d 升级路线

1. 升级 ArchVizBuild → MachineBuild 风格 contract（parts + update + dispose）
2. 添加注册表模式（TYPE_REGISTRY 扩展为完整注册表）
3. 添加物理 kinematics 模块（slider-crank, planetary gear）
4. 添加缩略图预渲染
5. 添加无障碍支持
6. 参照 mechlab 的性能优化（dpr cap, frustum culling, dispose）

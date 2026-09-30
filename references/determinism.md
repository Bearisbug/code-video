# DET · 画面确定性

HyperFrames 逐帧 seek 渲染，可能乱序、可能多进程并行。任何一帧都必须只由它的时间 t 算出来。这里只写 HyperFrames lint 查不到、或本机实测会出错的规则；lint 能查到的禁用项以 `check` 为准（`HF-006`）。

### DET-001 · 画面只由时间 t 决定
- 触发: 写任何会随时间变化的视觉状态
- 规则: 禁止用 `Date.now()`、`performance.now()`、未设种子的 `Math.random()`、`setTimeout`/`setInterval`、`requestAnimationFrame` 循环、无限循环（GSAP `repeat: -1`、CSS `infinite`）、hover/scroll/pointer 状态来决定画面。需要随机感时用带种子的伪随机；需要「每帧都变」的随机（故障切片、乱码、数据流）时，种子取帧号 `Math.floor(t * fps)`，保证同一帧每次渲染结果相同
- 为什么: 渲染器按帧号 seek，墙钟时间与真实渲染耗时无关；随机数不设种子时，多进程渲染的各段画面对不上
- 验证: `npx hyperframes check .` 无 `non_deterministic_code`、`requestanimationframe_in_composition`

```js
// ✓ 带种子的伪随机（mulberry32）
function rng(seed) {
  return () => {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const layout = rng(42);                           // 固定布局：整片共用一个种子
const perFrame = (t) => rng(Math.floor(t * 30));  // 每帧变化：种子取帧号
```

### DET-002 · 禁止用 CSS transition 做动画
- 触发: 想用「加 class → CSS transition」做进出场
- 规则: 所有进出场与状态切换写成 GSAP 时间线上的 tween（`tl.to(el, vars, 时间点)`）。禁止用 `transition` 属性配合 class 切换或 `setTimeout` 触发
- 为什么: 0.8.96 的 lint 查不出这种写法；本机实测「`setTimeout` 1 秒后加 class 触发 2 秒 transition」两次渲染的起步帧分别是第 21 帧和第 24 帧，与设计的第 30 帧都不符
- 验证: `grep -n "transition" index.html` 无结果，或只出现在不随时间变化的静态样式里

### DET-003 · 避开两个已知偏帧缺陷
- 触发: 用 CSS `@keyframes` 或 `el.animate()`（WAAPI）
- 规则: 禁止在 `::before`/`::after` 伪元素或 shadow DOM 里的元素上写 CSS 动画，改成真实元素；`el.animate()` 必须在组合文件的主脚本里同步创建，不能放进异步回调。能用 GSAP 表达的动画默认用 GSAP
- 为什么: HyperFrames issue #4555（伪元素、shadow DOM 动画每次加载偏差不同）与 #4559（运行时加载前创建的 WAAPI 动画偏移）截至 2026-09-30 未修复；本机实测伪元素动画两次渲染分别偏 0px 与 2.5px（半帧）
- 来源: https://github.com/heygen-com/hyperframes/issues/4555 ，https://github.com/heygen-com/hyperframes/issues/4559

### DET-004 · 禁止逐帧累积状态
- 触发: 写弹簧、惯性、粒子、数值读数收敛、打字机等「上一帧决定下一帧」的效果
- 规则: 一律写成 t 的闭式函数。弹簧用阻尼振动闭式解；读数收敛用指数逼近 `v(t) = end + (start − end)·e^(−k·t)`；打字机用 `chars = floor((t − t0) × 速率)`；粒子位置用初速度加时间的解析式，初始参数取自带种子的伪随机
- 为什么: 帧可能乱序或分段并行渲染，累积状态在第 n 帧拿不到前 n−1 帧的结果
- 验证: 用 `snapshot --at` 单独抽中段某一帧，与整片渲染中同一帧对比，画面一致

```js
// ✓ 欠阻尼弹簧闭式解：从 0 到 1，zeta 为阻尼比，w 为角频率（rad/s）
const spring = (t, zeta = 0.5, w = 14) => {
  if (t <= 0) return 0;
  const wd = w * Math.sqrt(1 - zeta * zeta);
  return 1 - Math.exp(-zeta * w * t) * (Math.cos(wd * t) + (zeta * w / wd) * Math.sin(wd * t));
};
```

### DET-005 · 固定尺寸与像素比
- 触发: 设定画布、WebGL 渲染器、canvas
- 规则: 根元素用固定像素尺寸（默认 1920×1080 或 1080×1920）；禁止用 `vw`、`vh`、媒体查询做布局。Three.js 必须 `renderer.setPixelRatio(1)` 与 `renderer.setSize(宽, 高, false)`；2D canvas 的 `width`/`height` 属性写成组合的像素尺寸
- 为什么: 渲染分辨率由 HyperFrames 控制（如 `--resolution 4k` 通过提高 deviceScaleFactor 实现）；依赖视口或 devicePixelRatio 的效果（辉光半径、线宽）会随输出分辨率变化
- 来源: HyperFrames v0.8.96 `skills/hyperframes-animation/adapters/three.md`「Avoid」一节

### DET-006 · 初始状态在时间线外设定
- 触发: 用 GSAP 给元素设初始状态（隐藏、缩小、移到画面外、起始颜色）
- 规则: 初始状态在创建时间线之前用 `gsap.set(el, { … })` 设一次；时间线里只用 `tl.to(el, vars, 时间点)` 从当前状态补间。禁止在时间线里用 `fromTo`/`from` 表达「晚些时候才开始」的动画，确需使用时加 `immediateRender: false`。禁止在时间线第 0 秒用 `tl.set` 设初始状态
- 为什么: 时间线里的 `fromTo`/`from` 默认在创建时立即把起始值写到元素上，排在后面的动画会在第 0 帧就生效；`check` 查不出来，只能靠抽帧发现。blind-04 首轮抽帧里，句点圆环从第 0 帧就可见、角色在下落前就被缩成 0.34 倍，都是这个原因。第 0 秒的 `tl.set` 会触发 lint `gsap_timeline_set_initial_hide`（reg-001-r2 实测）
- 验证: 抽第 0 帧与每个元素出场前 1 帧，元素处于分镜写的初始状态

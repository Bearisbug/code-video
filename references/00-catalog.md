# 00 Catalog · 规则卡索引

遇到具体处境时先扫本表，按「触发」匹配，再 grep `<ID>` 到对应文件读卡。流程清单（`flow-*.md`）与风格包（`styles/`）不在本表。前缀与文件的对应见 [CONVENTIONS.md](CONVENTIONS.md)。

| ID | 触发 | 约束 |
|---|---|---|
| HF-001 | 新建项目或执行 hyperframes 命令 | 项目内 `--save-exact hyperframes@0.8.96`，禁止 `@latest` 与全局安装 |
| HF-002 | 执行 hyperframes 命令 | 带 `HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_SKIP_SKILLS=1`，禁止 `init` 与 `skills` 子命令 |
| HF-003 | 执行 snapshot | `env -u GEMINI_API_KEY`，禁止 `--describe` |
| HF-004 | 写组合文件 | 根元素、clip、GSAP 注册、`data-no-timeline` + `hf-seek`、`<audio id>` 的最小契约 |
| HF-005 | 需要未写到的 HyperFrames 细节 | 按 docs 命令 → 包内 skill → v0.8.96 tag 的顺序查，禁止读 main |
| HF-006 | 准备渲染 | `check` 通过后 `render --strict` |
| HF-007 | 组合用到库或素材 | npm 装进项目、从 `./node_modules` 加载，渲染时不联网 |
| HF-008 | 首次使用、每轮结束 | 浏览器全局复用一份，每轮 `clean`，禁止 `browser clear` |
| HF-009 | 浏览器预览或测试 | 渲染用 HyperFrames 自带浏览器，预览与测试用 Edge |
| DET-001 | 写随时间变化的视觉状态 | 画面只由 t 决定；随机用种子，逐帧随机以帧号为种子 |
| DET-002 | 想用 class 切换加 CSS transition | 改用 GSAP tween |
| DET-003 | 用 CSS @keyframes 或 WAAPI | 禁止伪元素与 shadow DOM 动画；WAAPI 在主脚本同步创建 |
| DET-004 | 写弹簧、惯性、粒子、读数收敛、打字机 | 写成 t 的闭式函数，禁止逐帧累积 |
| DET-005 | 设定画布与渲染器尺寸 | 固定像素尺寸，Three.js `setPixelRatio(1)` |
| DET-006 | 给元素设初始状态 | 初始状态在时间线外用 `gsap.set`，时间线里只用 `to`；禁止时间线里的 `fromTo`/`from` 与第 0 秒 `tl.set` |
| CRAFT-001 | 开始一支新视频 | 分镜表经用户确认后才写代码 |
| CRAFT-002 | 选配色、字体、缓动、镜头 | 只从选定风格包取值；品牌色替换相对亮度最接近的一格、保持明暗结构；题材固有色可单独加入 |
| CRAFT-003 | 按风格包写分镜 | 参考节拍只借节奏手法，禁止命中题材禁用清单 |
| CRAFT-004 | 排版文字 | 1080 宽主标题 ≥84px、辅助 ≥44px，安全区 80/100px，可读文字停留 ≥1 秒 |
| CRAFT-005 | 安排事件与音效时间 | 卡在 BPM 节拍网格上，非整帧拍点取 `floor(t×fps)`，画面与音效用同一帧号 |
| CRAFT-006 | 两个及以上场景 | 配色、字号、时长集中成 token |
| AUD-001 | 需要配乐或音效 | 分镜 → cues.json → synth.py → 归一 → `<audio id>`；外部音乐须有使用权 |
| AUD-002 | 写音效时间 | 起音型与画面同帧；whoosh 提前 dur/2，riser 提前 dur |
| AUD-003 | 全片最重要的揭晓 | 揭晓前 50–200ms 近静音，揭晓帧落 impact |
| AUD-004 | 交付前 | 在成片上测：−14 LUFS ±1、真峰值 ≤ −1 dBTP，超出则抽轨归一再合回 |
| FONT-001 | 组合显示文字 | 只用登记表字体，`@font-face` 内联进组合，中文按用字子集化；字体栈只写已声明家族与通用族，不写系统字体名 |
| FONT-002 | Manim 显示中文 | 下载 TTF，`register_font` 注册 |
| MANIM-001 | 选渲染层 | 公式、几何、函数、算法演示用 Manim，其余用 HyperFrames |
| MANIM-002 | 首次用 Manim | Python 3.12 venv 装 `manim[typst]==0.21.0`，公式默认 MathTypst |
| MANIM-003 | 预览或出片 | `-ql` 草稿、`-s` 末帧、`-qh --frame_rate 30` 成片 |
| MANIM-004 | 写 Manim 场景 | 用 `Paced` 的 `seg`/`hold_until` 按整帧排时间；起步类事件提前 1 帧，到位类事件以拍点为 t1；固定随机种子 |
| MANIM-005 | Manim 需要声音 | 合成归一后用 ffmpeg 合入，再测成片响度 |

# HF · HyperFrames 使用护栏

本 Skill 的 HTML 视频一律由 HyperFrames 渲染。本文件规定锁定版本、调用方式和本机实测过的契约要点；写法细节以锁定版本的官方文档为准（`HF-005`）。

### HF-001 · 锁定版本，项目内安装
- 触发: 新建视频项目；或准备执行任何 `hyperframes` 命令
- 规则: 在视频项目目录执行 `npm install --save-exact hyperframes@0.8.96`，之后一律在项目目录用 `npx hyperframes …` 调用本地版本。禁止 `npx hyperframes@latest`，禁止全局安装。升级版本属于 Skill 维护：先在 `skill-tests/code-video/` 重跑渲染器对照与盲测，通过后再改本卡的版本号
- 为什么: 0.x 版本几乎每天发布，渲染结果与 lint 规则随版本变化；锁定版本才能让「check 通过」和「成片帧精确」可复现
- 验证: `package.json` 的 `dependencies.hyperframes` 为 `0.8.96`（无 `^`、`~`）；`npx hyperframes doctor` 首行显示 `Version 0.8.96`

### HF-002 · 固定环境变量，禁止自动装官方 skills
- 触发: 执行任何 `hyperframes` 命令
- 规则: 每条命令前带 `HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_SKIP_SKILLS=1`（可在当前 shell `export` 一次）。禁止执行 `hyperframes init`、`hyperframes skills`、`hyperframes skills update`；项目骨架按 [flow-setup.md](flow-setup.md) 手工建
- 为什么: 0.8.96 的 `init` 会把整套官方 skills 装进本机 AI 工具目录，`--skip-skills` 参数在该版本被忽略，只有环境变量能关；遥测默认开启
- 验证: `ls ~/.claude/skills` 没有新增 `hyperframes*` 目录；`npx hyperframes telemetry status` 显示 `disabled`

### HF-003 · 抽帧时禁止外发画面
- 触发: 执行 `hyperframes snapshot`
- 规则: 必须写成 `env -u GEMINI_API_KEY npx hyperframes snapshot …`；禁止传 `--describe`。执行后在输出里确认出现 `GEMINI_API_KEY not set, skipping`
- 为什么: 环境里有 `GEMINI_API_KEY` 时，`snapshot` 默认把抽出的帧发给 Gemini 做描述，并自动安装 `@google/genai`；本机环境设有该变量
- 验证: 命令输出含 `GEMINI_API_KEY not set, skipping`

### HF-004 · 组合文件的最小契约
- 触发: 写或改 `index.html`（组合文件）
- 规则:
  - 根元素：`data-composition-id`、`data-start="0"`、`data-duration`、`data-fps`、`data-width`、`data-height`，并用 CSS 固定同样的像素宽高。
  - 有时间的子元素：`class="clip"` 加 `data-start`、`data-duration`、`data-track-index`。
  - GSAP：`gsap.timeline({ paused: true })`，所有 tween 加完后再执行 `window.__timelines["<composition-id>"] = tl`；禁止 `tl.play()`。
  - 只用 Three.js 或 canvas、没有 GSAP 时间线：根元素加 `data-no-timeline`，画面在 `hf-seek` 事件里按 `event.detail.time` 重绘，首帧用 `window.__hfThreeTime || 0`。
  - 音频：`<audio id="…" src="…" data-start data-duration data-track-index data-volume>`，必须有 `id`。
- 为什么: 以上每条都在本机 0.8.96 上验证过；缺 `data-no-timeline` 时 `check` 报 `missing_timeline_registry`，渲染会先空等 45 秒；`<audio>` 没有 `id` 不会进混音，成片无声
- 验证: `npx hyperframes check .` 通过
- 来源: HyperFrames v0.8.96 `skills/hyperframes-core/references/determinism-rules.md`、`variables-and-media.md`，`skills/hyperframes-animation/adapters/three.md`

### HF-005 · 按锁定版本查官方文档
- 触发: 需要本 Skill 没写到的 HyperFrames 细节（子组合、变量、转场、字幕、Lottie、关键帧诊断等）
- 规则: 按这个顺序查，禁止读 `main` 分支或凭记忆写：
  1. `npx hyperframes docs <topic>`，topic 为 `data-attributes`、`compositions`、`gsap`、`rendering`、`troubleshooting`、`examples`。
  2. 包内 skill：`node_modules/hyperframes/dist/skills/hyperframes-cli/`（命令与检查）、`node_modules/hyperframes/dist/skills/media-use/`（素材）。
  3. 锁定 tag 下的其余官方 skill：`https://raw.githubusercontent.com/heygen-com/hyperframes/v0.8.96/skills/<skill>/<path>`。常用路径：`hyperframes-core/SKILL.md`、`hyperframes-core/references/determinism-rules.md`、`hyperframes-animation/adapters/<gsap|css-animations|waapi|three|lottie>.md`、`hyperframes-keyframes/SKILL.md`。
- 为什么: 用户决定不全局安装官方 skills；包里只带 3 个 skill，写法核心契约 `hyperframes-core` 只在仓库 tag 下
- 验证: 引用的每条官方规则都能指出来自哪个文件

### HF-006 · 先 check，后 render
- 触发: 准备渲染整片
- 规则: 先执行 `npx hyperframes check .`，退出码为 0 才渲染；渲染命令必须带 `--strict`（lint 错误直接阻断）。`check` 的 warning 允许保留 `nested_structure_needs_subcomposition` 与 `composition_file_too_large` 两条，它们只影响 Studio 时间线显示与文件维护；其余 warning 要修掉，或在交付说明里写明原因。禁止为了避开 `composition_file_too_large` 把脚本拆到外部 `.js`：`check.sh` 只检查 `index.html`，拆出去的代码就不受确定性检查
- 为什么: 本机实测 `check` 能拦下随机数、墙钟时间、`requestAnimationFrame`、文字溢出画面、对比度不足，并给出修法。单文件组合超过 300 行就触发 `composition_file_too_large`，四个 HyperFrames 测试的组合为 301–728 行，按风格包配方写必然触发
- 验证: 交付说明里贴出 `check` 结果行（`Check passed`）

### HF-007 · 依赖全部本地化
- 触发: 组合文件需要 GSAP、Three.js 或其他库
- 规则: 用 `npm install --save-exact gsap@3.15.0 three@0.186.1` 装进项目，GSAP 用 `<script src="./node_modules/gsap/dist/gsap.min.js">`，Three.js 用 importmap 指向 `./node_modules/three/build/three.module.js` 与 `./node_modules/three/examples/jsm/`。禁止渲染时从 CDN 加载；图片、数据、音频放 `assets/`。字体见 `FONT-001`
- 为什么: 渲染时联网会让成片依赖网络状态；本机实测 HyperFrames 渲染能正常读取项目内 `node_modules`
- 验证: `grep -E "https?://" index.html` 除注释外无结果

### HF-008 · 浏览器复用与环境回收
- 触发: 首次使用、每轮渲染结束、交付前
- 规则: 首次执行 `npx hyperframes browser ensure`，下载的 chrome-headless-shell（约 207MB）留在 `~/.cache/hyperframes/` 供所有项目共用；`~/.hyperframes/config.json` 存着遥测关闭设置，不得删除。每轮结束在项目目录执行 `npx hyperframes clean`；禁止执行 `browser clear`，禁止按项目重复下载浏览器
- 为什么: 全局磁盘规则要求复用同一套环境；渲染的确定性建立在这个固定版本的浏览器上
- 验证: `du -sh ~/.cache/hyperframes` 只有一份浏览器目录

### HF-009 · 渲染浏览器与预览浏览器分开
- 触发: 需要在浏览器里预览组合或做浏览器测试
- 规则: 渲染、`check`、`snapshot` 用 HyperFrames 自带的 chrome-headless-shell；人工预览与 Playwright 测试按全局约定用 Microsoft Edge。禁止为了统一而把渲染改成 Edge
- 为什么: HyperFrames 的逐帧捕获与确定性依赖它固定的浏览器版本；本机对照实测中，同一样片在 Edge 154 与 Chrome 152 下的栅格化有细微差异（PSNR 约 26dB，位置精度相同）

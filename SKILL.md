---
name: code-video
description: 适用于用代码制作视频并渲染成 MP4：品牌片头与字标演绎、产品与功能发布片、AI 工具宣传片、无旁白的科技科普与原理讲解短片、数据与概念动画、数学与算法讲解动画，并用代码合成配乐与音效；也用于照参考片做同款节奏，或修「像 PPT」「没节奏」「转场生硬」的视频。Use when the user asks to make, animate, or render a video / motion graphic / launch video / animated intro / explainer clip with code, or to apply a named video style. NOT for AI 生成画面（Seedance、Kling、Runway 等文生视频）、实拍素材与录屏剪辑、TTS 旁白配音、网页或 App 里的 UI 动效（那是 ui-constraints / mobile-ui-constraints）。中文触发：用代码做视频 / 做个动画视频 / 产品发布视频 / 宣传短片 / 科普短片 / 原理讲解动画 / 讲清楚某个技术是怎么工作的 / 照这个参考片做 / 像这个视频的感觉 / MG 动画 / 片头 / 字标动画 / 动效视频 / 数据动画 / 数学讲解动画 / Manim / HyperFrames / 渲染 MP4 / 形变动画 / 赛博 HUD / 科幻界面 / 吉祥物宣传片 / 可爱角色讲故事 / 打字机字幕 / 给视频配音效配乐。其余能力：HTML 视频由 HyperFrames（锁定 0.8.96）逐帧渲染，数学讲解用 Manim CE；内置风格包 shape-morph（一形贯穿形变）、fui-hud（电影科幻界面）、mascot-story（吉祥物小剧场）、light-launch（浅底发布片）；分镜前出三个构思，节奏与段落衔接检查，参考片拆解，用 HTML 复刻产品界面做功能演示，画面事实核对。
---

# code-video

## 适用范围

- **适用**：用代码生成画面并渲染成视频文件，包括 10–60 秒的动态图形、片头、宣传短片、产品发布片、科普讲解、概念动画、数学讲解，以及与之配套的代码合成配乐和音效。
- **不适用**：
  - AI 文生视频、实拍剪辑、TTS 旁白。
  - 录屏素材剪辑；要展示软件界面时用 HTML 复刻（`CRAFT-016`）。
  - 网页或 App 界面里的交互动效，交给 ui-constraints 或 mobile-ui-constraints。
  - 用户点名用 Remotion 或项目已经是 Remotion 时，写法按 Remotion 官方文档；本 Skill 仍提供风格包、音频与验收规则。

## 优先级

用户在当前对话里的明确要求 > 本 Skill > HyperFrames 官方文档（锁定版本）。视频组合文件不是交付给用户操作的界面，ui-constraints 里的交互、响应式、无障碍规则不适用于它。

## 红线

1. HyperFrames 固定用 0.8.96，装在视频项目内。每条命令都带 `HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_SKIP_SKILLS=1`；禁止 `hyperframes init`、`hyperframes skills`（`HF-001`、`HF-002`）。渲染一律走 HyperFrames，禁止为运动模糊等效果另写逐帧截图渲染器（`CRAFT-013`）。
2. `snapshot` 一律写成 `env -u GEMINI_API_KEY npx hyperframes snapshot …`，禁止把画面发给外部模型（`HF-003`）。
3. 画面只由时间 t 决定：禁止墙钟时间、未设种子的随机、定时器、`requestAnimationFrame` 循环、CSS transition、逐帧累积状态（`DET-001`–`DET-004`）。
4. 宣传片、发布片、科普片在用户没给构思时，先给三个构思（`CRAFT-009`）；分镜表经用户明确确认后才写代码（`CRAFT-001`）。画面上的数字与断言都要有出处，没有出处的改写或标「示意」（`CRAFT-018`）。
5. 视觉取值只来自选定风格包；项目有品牌目录时，强调色、字体与标志取自品牌目录，字标与 Logo 用母版路径（`CRAFT-002`、`CRAFT-007`、`CRAFT-008`）。风格包的参考节拍只借节奏，禁止照搬原作题材（`CRAFT-003`）。
6. 字体、库、音频全部放进项目本地，渲染时不联网（`HF-007`、`FONT-001`）。
7. `check` 通过才渲染，渲染带 `--strict`（`HF-006`）；交付前按 `flow-verify.md` 核对帧数、节奏、分界衔接、响度与联系表。
8. 每轮结束回收临时文件；HyperFrames 浏览器缓存全局复用一份，不得删除（`HF-008`）。

## 流程

1. 读 [references/flow-make.md](references/flow-make.md)，按步骤执行：问清需求（有参考片先量）→ 选渲染层，出三个构思与风格包 → 分镜并确认 → 搭项目 → 实现 → 中途检查（含节奏） → 音频 → 渲染 → 验收。
2. 搭项目时读 [references/flow-setup.md](references/flow-setup.md)。
3. 验收交付时读 [references/flow-verify.md](references/flow-verify.md)。
4. 遇到具体问题时先查 [references/00-catalog.md](references/00-catalog.md)，再 grep 卡 ID 读卡。

## 按需读取

| 处境 | 读 |
|---|---|
| 选风格、写分镜 | [references/styles/00-index.md](references/styles/00-index.md) 与选定的风格包 |
| HyperFrames 版本、命令、组合契约、查官方文档 | [references/hyperframes.md](references/hyperframes.md) |
| 动画写法是否会逐帧出错 | [references/determinism.md](references/determinism.md) |
| 分镜、文字大小、节拍、多场景一致、品牌参数、字标与 Logo | [references/craft.md](references/craft.md) |
| 三个构思、节奏、段落衔接、镜头运动、快速移动、强调手法 | [references/craft.md](references/craft.md) 的 `CRAFT-009`–`CRAFT-014` |
| 参考片、产品界面复刻、科普讲解、画面事实核对 | [references/craft.md](references/craft.md) 的 `CRAFT-015`–`CRAFT-018` |
| 配乐、音效、响度、起始增益与「轻」、音效密度与混响 | [references/audio.md](references/audio.md) |
| 字体选择与下载 | [references/fonts.md](references/fonts.md) |
| 公式、几何、函数、算法讲解 | [references/manim.md](references/manim.md) |
| 维护本 Skill、新增风格包 | [references/CONVENTIONS.md](references/CONVENTIONS.md) |

## 工具

| 脚本 | 用途 |
|---|---|
| `scripts/fetch-font.mjs` | 从 Google Fonts 下载登记表字体的 woff2，中文按用字子集化，把 `@font-face` 写进 `index.html` 的 `<style>` |
| `scripts/synth.py` | 按 `cues.json` 合成配乐与音效（音床可做增益自动化，可选共用混响 `space`），输出 48kHz 立体声 WAV，同一清单输出逐字节一致；相隔 1–40ms 的音效会告警 |
| `scripts/normalize-audio.sh` | 两遍 loudnorm 归一到 −14 LUFS、真峰值上限 −2 dBTP，输出 `input_plr` 与 linear/dynamic 模式，dynamic 时按 `AUD-005` 提示怎么改 |
| `scripts/analyze.py` | 分析成片：画面变化区间、音频起音、近黑像素占比、音画同步偏差、事件响度排序；节奏（静止占比、最长静止段、瞬变与快切段、分界与段落时长分布，`--chart` 打印能量图）、分镜节拍的变异系数、浅底留白 |

脚本路径相对本 Skill 根目录。环境要求：Node ≥22、ffmpeg 8.x（带 `drawtext` 与 `libass`）、`uv`；Python 一律在视频项目的 `uv venv --python 3.12` 里运行。

## 自检

`bash check.sh` 检查本 Skill 的结构；`bash check.sh <视频项目目录>` 检查一个视频项目是否遵守护栏，并复核 `renders/` 里成片的帧数与响度。

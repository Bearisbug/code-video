<h1 align="center">code-video</h1>

<p align="center">用代码做视频的 Agent Skill：动态图形、品牌开场、产品宣传片、数学讲解，渲染成带合成配乐与音效的 MP4。</p>

<p align="center"><a href="README.md">English</a> · <b>简体中文</b></p>

---

`code-video` 带着 AI 编程 Agent 从一句需求走到一支验收过的 MP4。Agent 先写分镜并等你确认，再选风格包，写 HTML 合成（由 [HyperFrames](https://github.com/heygen-com/hyperframes) 逐帧渲染）或 [Manim](https://www.manim.community/) 场景，合成配乐，渲染，最后逐项核对帧数、响度、音画同步和风格清单。

Skill 正文用中文写成，和 Agent 对话用什么语言都可以。

## 覆盖范围

| 任务 | Agent 从哪里读起 |
| --- | --- |
| 任何新视频：需求 → 分镜 → 实现 → 渲染 → 验收 | [flow-make](references/flow-make.md) |
| 选风格 | [风格索引](references/styles/00-index.md) |
| 建项目、锁版本、字体 | [flow-setup](references/flow-setup.md)、[HF-001](references/hyperframes.md)、[FONT-001](references/fonts.md) |
| 逐帧精确、不漂移的动画 | [确定性规则](references/determinism.md) |
| 分镜、字号、节拍网格、品牌色、品牌目录与字标 | [工艺规则](references/craft.md) |
| 配乐、音效、响度 | [音频规则](references/audio.md) |
| 公式、几何、算法 | [Manim 档](references/manim.md) |
| 验收与交付 | [flow-verify](references/flow-verify.md) |

不做：AI 生成画面（文生视频模型）、实拍剪辑、TTS 配音、App 内 UI 动效。

## 工作方式

- **每一帧都是时间的纯函数。** 禁用系统时钟、无种子随机数、定时器、`requestAnimationFrame` 循环和 CSS transition；HyperFrames 逐帧 seek，同一份源码每次渲染结果相同。
- **工具链锁版本并加护栏。** HyperFrames 锁定 0.8.96，按项目安装；关闭遥测和自动安装官方 Skill，快照不把画面发给外部模型。
- **渲染时不联网。** 字体按用字子集化后以内联 `@font-face` 嵌入，库从 `node_modules` 加载。渲染过程下载了任何东西，验收即不通过。
- **风格包给实测参数。** 每个包写明色值、1080p 下的字号、缓动参数、时长和音效点位，并列出原作题材的禁用清单，防止照搬。
- **先做机械验收。** `check.sh` 既查 Skill 自身，也查视频项目；`analyze.py` 在成片上测运动区间、音频起音点、音画偏差、暗像素占比和事件响度。

## 目录

```text
SKILL.md                 入口：适用范围、红线、路由
check.sh                 不带参数自检；bash check.sh <项目目录> 查项目
references/              34 张规则卡（HF、DET、CRAFT、AUD、FONT、MANIM）、3 个流程、目录、编写约定
references/styles/       风格包与索引
scripts/fetch-font.mjs   从 Google Fonts 下载登记过的字体，中文按用字子集化，内联 @font-face
scripts/synth.py         按音效表合成配乐底和 9 种音效（结果确定）
scripts/normalize-audio.sh  两遍 loudnorm 到 −14 LUFS、真峰值上限 −2 dBTP，用 ebur128 复核
scripts/analyze.py       运动区间、起音点、音画偏差、暗像素占比、最响事件
```

| 风格包 | 画面 | 渲染层 |
| --- | --- | --- |
| `shape-morph` | 一个扁平形状一路变形讲完故事，纸张颗粒，圆形扩散换色 | SVG/DOM + GSAP MorphSVG |
| `fui-hud` | 电影感科幻 HUD：单色青线框、辉光、锁定时切琥珀色 | Three.js + DOM |
| `mascot-story` | 吉祥物讲「问题 → 解决」的故事，颗粒与线条抖动，打字机字幕 | SVG/DOM + canvas 颗粒 |

三个包的数值都来自逐帧拆解或原作源码，配方在 HyperFrames 0.8.96 上实测过。`mascot-story` 已标为「已盲测」：执行者只拿到 Skill 和一个无关题材，成片按包内验收清单全部通过。`shape-morph` 与 `fui-hud` 仍是「草稿」。

## 安装

Claude Code，全部项目可用：

```sh
git clone --depth 1 https://github.com/Bearisbug/code-video.git ~/.claude/skills/code-video
```

Claude Code，只给一个项目用：克隆到 `<项目>/.claude/skills/code-video`。其他读取 `SKILL.md` 的 Agent，把目录放进该 Agent 的 skills 目录。

## 环境要求

| 工具 | 用途 |
| --- | --- |
| Node.js 22+ 与 npm | HyperFrames（每个视频项目单独安装）、`fetch-font.mjs` |
| ffmpeg 8.x（带 `drawtext` 与 `libass`） | 编码、联系表、响度检查 |
| uv、Python 3.12 | `synth.py` 与 `analyze.py`（只依赖 numpy）、Manim 档 |
| Manim CE 0.21（可选） | 数学讲解；需要 `cairo`、`pango`、`pkgconf`；LaTeX 可选（`MathTypst` 不依赖 LaTeX） |

HyperFrames 第一次渲染会下载锁定版本的 chrome-headless-shell（约 207 MB），之后所有项目共用这一份。

## 用法

直接用自然语言提需求，例如：

- 「给我们的记账 App 做一支 10 秒品牌开场，一个形状接一个形状地变，最后落到 App 名字上，配乐和音效都要。」
- 「做一支 10 秒科幻 HUD 预告：我们的代码审查工具扫过一个巨大的代码库，锁定一处隐藏的竞态条件。」
- 「给我们的健身 App 做一支 20 秒宣传片，让一个可爱的吉祥物讲故事，要纸张颗粒质感和打字机字幕。」
- 「做一支 20 秒讲解视频，用方块拼图证明 1 + 2 + … + n = n(n+1)/2，中文标题，配轻音乐。」

## 验证

```sh
bash check.sh                      # Skill：链接、规则卡与目录一致、卡号引用、风格包章节、脚本语法、品牌区块夹具
bash check.sh /path/to/project     # 项目：锁定版本、不联网、确定性模式、字体、品牌参数区块、帧数、响度
```

这个 Skill 用盲测循环打磨：Agent 手里只有 Skill 和任务描述，三轮共做了 13 支视频，每次改规则都回到之前的任务复测。机械检查通过不等于画面合格，画面质量靠风格包验收清单和联系表目检。

## 许可证

Skill 正文与脚本以 [MIT 许可证](LICENSE) 发布。仓库不打包任何第三方内容：HyperFrames（Apache-2.0）、GSAP（GreenSock Standard License）、Three.js（MIT）、Manim（MIT）和字体（SIL OFL 1.1）都由使用者按各自条款安装或下载。`shape-morph` 与 `fui-hud` 两个包描述的风格实测自一支第三方风格合集视频（作者未确认），包里只有参数，没有画面。

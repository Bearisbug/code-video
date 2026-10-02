# FONT · 字体

### FONT-001 · 字体下载到项目本地
- 触发: 组合文件要显示文字
- 规则: 只用下方登记表里的字体，或品牌目录字体配置里的家族（`CRAFT-007`）。在视频项目根目录运行 `node <skill>/scripts/fetch-font.mjs --family "<家族名>" --weights <字重> [--text-file fonts/chars.txt]`：它把 woff2 下载到 `fonts/`，并把 `@font-face` 直接写进 `index.html` 第一个 `<style>` 里的 `/* fonts:<slug> */` 区块。中文字体必须加 `--text-file`，文件内容是组合里出现的全部中文，改了文案要重跑（会替换同一区块）。品牌字体能从 Google Fonts 取得时同样用 `fetch-font.mjs`；取不到时把品牌目录里的字体文件复制到 `fonts/`，在同一个 `<style>` 里手写 `@font-face`（`src: url("fonts/<文件>")`），许可以品牌 `DESIGN.md` 的字体记录为准，不进登记表。`font-family` 字体栈里只写已内联声明的家族和通用族名（`sans-serif`、`serif`、`monospace`），例如 `"Courier Prime", monospace`。禁止在字体栈里写系统字体名当后备（`"Courier New"`、Arial、PingFang、微软雅黑等）；禁止用 `<link>` 或 `@import` 引入字体样式表。品牌 tokens 里的字体栈带系统字体名时不照搬，按本条重写
- 为什么: 0.8.96 的编译器只识别 HTML 里直接写的 `@font-face`。本机实测：`font-family` 声明配 `<link>` 引入的本地字体，渲染时仍会去 Google Fonts 下载（9 个文件），并覆盖本地子集，而 `check` 照样通过；blind-02 里这一项让首次渲染多花了 6 分钟。改成内联后下载数为 0。字体栈里的系统字体名也会触发下载：移植实测 `'CP','Courier New',monospace` 在首选字体已内联的情况下，渲染时仍下载了替代字体，去掉 `'Courier New'` 后下载数为 0。系统字体换一台机器就缺字，lint 会报 `font_family_without_font_face`
- 验证: 渲染前 `export HYPERFRAMES_FONT_CACHE_DIR="$PWD/.hf-font-cache"`，渲染后该目录不存在或为空（有文件说明渲染时联网下载了字体）；抽帧里各字重粗细分明

### FONT-002 · Manim 用 TTF 注册字体
- 触发: Manim 场景里用 `Text` 显示中文或指定字体
- 规则: 从登记表的 google/fonts 路径下载 TTF 到项目 `fonts/`，用 `with register_font("fonts/<文件>.ttf"):` 包住构造文字的代码，`Text(..., font="<家族名>", weight=...)`。可变字体用 `weight=NORMAL`/`BOLD`/`HEAVY` 选字重
- 为什么: Manim 通过 Pango 排字，只认 TTF/OTF，不认 woff2；本机实测 `NotoSansSC[wght].ttf` 注册后 `NORMAL` 与 `HEAVY` 均正确
- 验证: 用 `manim -s` 渲染末帧，确认中文不是方框、字重正确

## 登记表

许可证均于 2026-09-30 在 google/fonts 仓库核对（目录内有 `OFL.txt`）。OFL 允许商用和嵌入视频，禁止单独售卖字体文件。

| 家族名 | 用途 | 字重 | google/fonts 路径 | 许可证 |
|---|---|---|---|---|
| Noto Sans SC | 中文黑体：标题、字幕、标签 | 100–900 可变 | `ofl/notosanssc` | OFL-1.1 |
| Noto Serif SC | 中文宋体：人文、报刊、纪录风 | 200–900 可变 | `ofl/notoserifsc` | OFL-1.1 |
| Outfit | 小写几何无衬线字标 | 100–900 可变 | `ofl/outfit` | OFL-1.1 |
| Space Grotesk | 几何无衬线正文与标题 | 300–700 可变 | `ofl/spacegrotesk` | OFL-1.1 |
| Rajdhani | 宽体科技读数、HUD 大数字 | 300/400/500/600/700 | `ofl/rajdhani` | OFL-1.1 |
| Oxanium | 方角科技标题 | 200–800 可变 | `ofl/oxanium` | OFL-1.1 |
| JetBrains Mono | 等宽：编号、代码、数据流 | 100–800 可变 | `ofl/jetbrainsmono` | OFL-1.1 |
| Share Tech Mono | 等宽科技标签 | 400 | `ofl/sharetechmono` | OFL-1.1 |
| Courier Prime | 打字机等宽：字幕、贴纸、手写感标题（2026-10-01 核对） | 400、700，各带斜体 | `ofl/courierprime` | OFL-1.1 |

新增家族：在 google/fonts 仓库确认目录下有 `OFL.txt` 或 `LICENSE.txt`（Apache-2.0），在本表加一行写明核对日期；非 google/fonts 来源的字体须另附许可证原文链接。

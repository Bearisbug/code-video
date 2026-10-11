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
| CRAFT-001 | 开始一支新视频 | 分镜表经用户确认后才写代码；列含收尾、衔接、文字字数与可见秒、要点，表头含选定构思与节奏数，表后附事实清单 |
| CRAFT-002 | 选配色、字体、缓动、镜头 | 只从选定风格包取值，有品牌目录时强调色、字体、标志按 CRAFT-007；品牌色替换相对亮度最接近的一格、保持明暗结构；题材固有色可单独加入；品牌限制彩色或禁用渐变时直接用 `light-launch` |
| CRAFT-003 | 写分镜里的物件、剧情与文案 | 文案按用户原话 → 仓库 README/CHANGELOG/品牌文档 → 提炼的功能性文字取，禁止自造数字与评价；参考节拍只借节奏手法，禁止命中题材禁用清单 |
| CRAFT-004 | 排版文字 | 1080 宽主标题 ≥84px、辅助 ≥44px，安全区 80/100px；可读文字停留 ≥ max(1 秒, 汉字数÷7 + 拉丁字符数÷17)，每行 ≤16 汉字或 42 字符、≤2 行 |
| CRAFT-005 | 安排事件与音效时间 | 卡在 BPM 节拍网格上，非整帧拍点取 `floor(t×fps)`，画面与音效用同一帧号 |
| CRAFT-006 | 两个及以上场景 | 配色、字号、时长集中成 token |
| CRAFT-007 | 仓库根有 `brand/DESIGN.md`，或用户给了品牌目录 | 强调色、字体、Logo 取自品牌目录；颜色用命令从 tokens 生成 CSS 变量，禁止手抄 hex |
| CRAFT-008 | 画面里要出现产品的字标或 Logo | 母版 SVG 路径原样拆分做动画，不重排字形、不改大小写与字距；品牌最小尺寸与安全区优先于风格包；没有母版标「临时字标」，正式标志转 visual-system |
| CRAFT-009 | 宣传片、发布片、科普片，用户没给构思 | 分镜前给三个核心想法不同的构思，与风格包推荐一次确认；结论由已出现的物件排出；无人可问时自选并写明 |
| CRAFT-010 | 写分镜、中途检查、验收成片 | 节拍变异系数 ≥0.25 且长短比 ≥4；至少一拍 ≥1 秒真停顿；相邻收尾方式不同；成片 `longest_low_energy` ≥1 秒、`still_ratio` ≥0.25（≤20 秒）或 ≥0.08 |
| CRAFT-011 | 段落之间的转换、验收 | 每个分界写出跨过去的元素，（承接 + 锚定÷2）÷ 分界数 ≥0.5；硬切只在快切段内与切到落版 |
| CRAFT-012 | 推拉、跟拍、甩镜头、抖动 | 镜头是舞台容器 transform 的闭式函数；跟拍提前 0.1–0.2 秒；落地抖动 3–16px 固定种子；停顿段镜头完全不动；主体不出画 |
| CRAFT-013 | 元素或镜头一两帧内移动很远 | 0.8.96 不加运动模糊（官方组件实测不确定），禁止自写渲染器；峰值 >80px/帧时分镜写明处理：压到 2 帧、残影、降速、到位后再读，或按包的挤压拉伸 |
| CRAFT-014 | 给落地、完成、揭晓加强调 | 不用粒子、彩纸、闪点；强调靠主体挤压、缩放、抖动、翻转；包内装饰按包 |
| CRAFT-015 | 用户给了参考片 | 先用 `analyze.py rhythm --chart` 与 `ground` 量，读数写进表头；取规则不取画面，参考片物件与文案按禁用清单处理 |
| CRAFT-016 | 宣传片要展示软件界面或操作 | 用 HTML 按截图复刻，数据取真实输出或标「示意」；被点名的界面文字屏幕字号 ≥44px；一个操作一个特写；不做整页缩略卡 |
| CRAFT-017 | 给非技术观众讲技术机制 | HyperFrames + `light-launch` 图解；问题→比喻→机制 3–5 拍→答案→结论定格 ≥2 秒；一拍一个概念，标签贴图形，比喻 ≤2 个 |
| CRAFT-018 | 画面上有断言、数字、机制描述或比喻 | `storyboard.md` 末尾列事实清单，每条有出处，没有出处改写或标「示意」；比喻写对应关系与不成立之处 |
| AUD-001 | 需要配乐或音效 | 分镜 → cues.json → synth.py → 归一 → `<audio id>`；外部音乐须有使用权 |
| AUD-002 | 写音效时间 | 起音型与画面同帧；whoosh 提前 dur/2，riser 提前 dur |
| AUD-003 | 全片最重要的揭晓 | 揭晓前 50–200ms 近静音，揭晓帧落 impact；开 `space` 时 `bed.send` 写 0 |
| AUD-004 | 交付前 | 在成片上测：−14 LUFS ±1、真峰值 ≤ −1 dBTP，超出则抽轨归一再合回；归一须为 linear |
| AUD-005 | 写 gain、归一报 dynamic、用户要「轻」配乐 | 按实测增益表起配，`input_plr` ≤12 才是 linear；先抬音床再降最响事件，禁止换 seed；「轻」= 无鼓 + pluck + Δ 3–4.5 dB |
| AUD-006 | 写音效事件 | 事件数少于拍数；1–40ms 内两声只留一个；打字三字一声、点击两声；可开 `space` 共用混响 |
| FONT-001 | 组合显示文字 | 只用登记表字体或品牌目录的字体，`@font-face` 内联进组合，中文按用字子集化；字体栈只写已声明家族与通用族，不写系统字体名 |
| FONT-002 | Manim 显示中文 | 下载 TTF，`register_font` 注册 |
| MANIM-001 | 选渲染层 | 公式推导、几何证明、函数图像、坐标系用 Manim；方块箭头式的算法与机制图解和其余内容用 HyperFrames |
| MANIM-002 | 首次用 Manim | Python 3.12 venv 装 `manim[typst]==0.21.0`，公式默认 MathTypst |
| MANIM-003 | 预览或出片 | `-ql --frame_rate 30` 草稿、`-s` 末帧、`-qh --frame_rate 30` 成片 |
| MANIM-004 | 写 Manim 场景 | 用 `Paced` 的 `seg`/`hold_until` 按整帧排时间；起步类事件提前 1 帧，到位类事件以拍点为 t1；固定随机种子 |
| MANIM-005 | Manim 需要声音 | 合成归一后用 ffmpeg 合入，再测成片响度 |

# flow-make · 从需求到成片

按顺序执行，不跳步。用户只要求改现有视频的某一处时，从第 5 步开始。

1. **问清需求**：用途、总时长、画幅（16:9 / 9:16 / 1:1）、必须出现的文字、有没有指定风格、有没有参考片。声音分开问：要配乐、要音效，还是都要；科普讲解片不问，默认「轻」配乐加少量起音型音效（`AUD-005`）。画面上要出现的数字与功能说明从哪里取（README、文档、截图），一并问（`CRAFT-018`）；要展示软件界面时，按 `CRAFT-016` 只提一个截图请求。品牌先查不问：仓库根有 `brand/DESIGN.md` 或用户给了品牌目录时，品牌参数按 `CRAFT-007` 取；都没有才问有没有品牌色或 logo。缺哪项问哪项，一次问完。
   - 用户给了参考片：先按 `CRAFT-015` 量，读数留给第 3 步写进分镜表头。

2. **选渲染层，出构思与风格包**：
   - 渲染层按 `MANIM-001` 判定：公式推导、几何证明、函数图像、坐标系用 Manim，其余用 HyperFrames；给非技术观众讲机制的科普片按 `CRAFT-017`。
   - 风格包按 `CRAFT-002` 从 [styles/00-index.md](styles/00-index.md) 选。用户没指定时推荐 1–2 个并说明理由。
   - 宣传片、发布片、科普片在用户没给构思时，按 `CRAFT-009` 写三个构思，与风格包推荐放在同一条消息里，让用户一次选定构思与风格包。
   - 没有人可以确认时，自己选定一个构思与风格包，把选择与理由写进第 3 步的分镜表头，另外两个构思写进交付说明，然后继续。

3. **写分镜，交用户确认**（`CRAFT-001`、`CRAFT-003`、`CRAFT-005`）：
   - 写进项目的 `storyboard.md`，表头与列按 `CRAFT-001`；表头另写 BPM，有参考片时写它的读数（`CRAFT-015`）。
   - 节奏数：用 `python <skill>/scripts/analyze.py beats <CRAFT-010 所说节拍行的起点,…,最后一行的终点>` 算变异系数与长短比，连同计划静止秒数写进表头，按 `CRAFT-010` 核对；风格包声明了节奏例外的按包。
   - 「衔接」列按 `CRAFT-011` 填，算出衔接得分；「收尾」列相邻两行不同（`CRAFT-010`）；「文字」列写字数与可见秒数（`CRAFT-004`）。
   - 有镜头运动时按 `CRAFT-012` 写明哪些元素在哪个时间窗必须完整在画内；峰值超过 80px/帧的动作按 `CRAFT-013` 在「动作」列写明处理。
   - 表后附事实清单（`CRAFT-018`）；展示软件界面时按 `CRAFT-016` 写明数据来源。
   - 节奏与手法照风格包的「风格语法」；题材、物件、文案按 `CRAFT-003` 取。
   - 对照风格包的「题材禁用清单」自查一遍；分镜里只写结论「已对照题材禁用清单，无命中」，不要把清单里的词抄进分镜。
   - 要出现字标或 Logo 时按 `CRAFT-008`：表头写明标志用哪个母版文件；没有母版就标「临时字标」。
   - 在对话里给出分镜，等用户明确确认。用户改了就改分镜，再确认。

4. **搭项目**：按 [flow-setup.md](flow-setup.md) 执行。

5. **实现画面**：
   - HyperFrames 档：按风格包的「技术配方」写 `index.html`，遵守 `HF-004`、`DET-001`–`DET-005`、`CRAFT-004`、`CRAFT-006`；有品牌目录时加 `CRAFT-007`，有标志时加 `CRAFT-008`。
   - Manim 档：按 `MANIM-003`、`MANIM-004` 写 `scene.py`。
   - 镜头运动按 `CRAFT-012`，快速移动按 `CRAFT-013`，强调手法按 `CRAFT-014`，软件界面按 `CRAFT-016`。
   - 风格包没写到的 HyperFrames 细节按 `HF-005` 查锁定版本文档。
   - 实现中发现已确认的分镜做不到、必须改时间或改画面时，同步改 `storyboard.md`，并在交付说明里逐条列出改了什么、为什么改；改动涉及文字或画面内容时，先问用户再改。

6. **中途检查**（HyperFrames 档）：
   ```bash
   npx hyperframes check .
   env -u GEMINI_API_KEY npx hyperframes snapshot . --at <分镜里 4–6 个关键时刻，逗号分隔>
   ```
   `--at` 按帧向下取整，时刻写成帧号 ÷ fps（如 30fps 的第 211 帧写 7.0334）。输出在 `snapshots/`：帧多时联系表分成 `contact-sheet-1.jpg`…，并自动追加一张时间线末尾帧。看联系表与关键帧大图，对照风格包「验收清单」逐项修。Manim 档用 `-s` 出末帧、用草稿画质出整片抽看。
   - 节奏（HyperFrames 档）：出一版草稿画质，按 `CRAFT-010` 核对读数，停顿段与落版定格段在能量图上应为 100% 静止；不达标先改分镜里的节拍时长，再改实现。风格包写明 `analyze.py` 画面侧失效的（`mascot-story` 的全屏颗粒）跳过这一项，改逐帧拼图目检。草稿放 `snapshots/`，看完删除：
     ```bash
     npx hyperframes render . -o snapshots/draft.mp4 --quality draft
     python <skill>/scripts/analyze.py rhythm snapshots/draft.mp4 --beats <同第 3 步> --chart
     ```
     草稿画质的读数与正式渲染一致（10 秒探针实测）。
   - 衔接：`snapshot --at` 加上每个分界前 0.2 秒、分界帧、后 0.2 秒，确认「衔接」列写的元素在三帧里都在（`CRAFT-011`）。
   - 抽帧图集中在这一步和第 9 步看，其余步骤不要逐张看图：会话中途插入图片会让 prompt cache 失效。

7. **音频**（`AUD-001`–`AUD-006`）：按分镜写 `audio/cues.json`（揭晓前的空拍写进 `bed.automation`，起始增益按 `AUD-005`，事件密度按 `AUD-006`），合成、归一，`loudnorm_mode` 为 linear 才挂进组合（`<audio id>`）；Manim 档留到出片后合并（`MANIM-005`）。

8. **渲染成片**（`HF-006`）：
   ```bash
   npx hyperframes check .
   npx hyperframes render . -o renders/<name>.mp4 --strict
   ```
   竖屏 1080×1920 与方形 1080×1080 在组合根上直接写对应宽高；需要 4K 时加 `--resolution 4k`。

9. **验收与交付**：按 [flow-verify.md](flow-verify.md) 执行。

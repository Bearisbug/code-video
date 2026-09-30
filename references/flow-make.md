# flow-make · 从需求到成片

按顺序执行，不跳步。用户只要求改现有视频的某一处时，从第 5 步开始。

1. **问清需求**：用途、总时长、画幅（16:9 / 9:16 / 1:1）、必须出现的文字、要不要声音、有没有指定风格、有没有品牌色或 logo。缺哪项问哪项，一次问完。

2. **选渲染层与风格包**：
   - 渲染层按 `MANIM-001` 判定：公式、几何、函数、算法演示用 Manim，其余用 HyperFrames。
   - 风格包按 `CRAFT-002` 从 [styles/00-index.md](styles/00-index.md) 选。用户没指定时推荐 1–2 个并说明理由，由用户选。

3. **写分镜，交用户确认**（`CRAFT-001`、`CRAFT-003`、`CRAFT-005`）：
   - 写进项目的 `storyboard.md`：表头是用途、时长、画幅、fps、风格包 id、渲染层、BPM；正文每行一个节拍（片内秒 / 画面 / 动作 / 文字 / 音效）。
   - 节奏与手法照风格包的「风格语法」；题材、物件、文案全部来自用户。
   - 对照风格包的「题材禁用清单」自查一遍；分镜里只写结论「已对照题材禁用清单，无命中」，不要把清单里的词抄进分镜。
   - 在对话里给出分镜，等用户明确确认。用户改了就改分镜，再确认。

4. **搭项目**：按 [flow-setup.md](flow-setup.md) 执行。

5. **实现画面**：
   - HyperFrames 档：按风格包的「技术配方」写 `index.html`，遵守 `HF-004`、`DET-001`–`DET-005`、`CRAFT-004`、`CRAFT-006`。
   - Manim 档：按 `MANIM-003`、`MANIM-004` 写 `scene.py`。
   - 风格包没写到的 HyperFrames 细节按 `HF-005` 查锁定版本文档。
   - 实现中发现已确认的分镜做不到、必须改时间或改画面时，同步改 `storyboard.md`，并在交付说明里逐条列出改了什么、为什么改；改动涉及文字或画面内容时，先问用户再改。

6. **中途检查**（HyperFrames 档）：
   ```bash
   npx hyperframes check .
   env -u GEMINI_API_KEY npx hyperframes snapshot . --at <分镜里 4–6 个关键时刻，逗号分隔>
   ```
   `--at` 按帧向下取整，时刻写成帧号 ÷ fps（如 30fps 的第 211 帧写 7.0334）。输出在 `snapshots/`：帧多时联系表分成 `contact-sheet-1.jpg`…，并自动追加一张时间线末尾帧。看联系表与关键帧大图，对照风格包「验收清单」逐项修。Manim 档用 `-s` 出末帧、用草稿画质出整片抽看。
   - 抽帧图集中在这一步和第 9 步看，其余步骤不要逐张看图：会话中途插入图片会让 prompt cache 失效。

7. **音频**（`AUD-001`–`AUD-003`）：按分镜写 `audio/cues.json`（揭晓前的空拍写进 `bed.automation`），合成、归一，把 `<audio id>` 挂进组合；Manim 档留到出片后合并（`MANIM-005`）。

8. **渲染成片**（`HF-006`）：
   ```bash
   npx hyperframes check .
   npx hyperframes render . -o renders/<name>.mp4 --strict
   ```
   竖屏 1080×1920 与方形 1080×1080 在组合根上直接写对应宽高；需要 4K 时加 `--resolution 4k`。

9. **验收与交付**：按 [flow-verify.md](flow-verify.md) 执行。

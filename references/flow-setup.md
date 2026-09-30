# flow-setup · 建视频项目

按顺序执行，每步后面是验证方法。`<skill>` 指本 Skill 的根目录。纯 Manim 项目只做第 1、4 步和末尾「Manim 档」一节。

1. **建目录**：在用户指定位置建 `<项目名>/`，默认结构：
   ```
   <项目名>/
     index.html        组合文件（HyperFrames 档）或 scene.py（Manim 档）
     storyboard.md     分镜表（CRAFT-001）
     audio/cues.json   音效清单（AUD-001）
     assets/           音频、图片、数据
     fonts/            字体（FONT-001、FONT-002）
     renders/          只放交付物：一个成片 mp4 与它的联系表
   ```
   验证：目录存在，且不在任何 Skill 目录内。

2. **装 HyperFrames 与依赖**（`HF-001`、`HF-007`）：
   ```bash
   export HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_SKIP_SKILLS=1    # HF-002
   export HYPERFRAMES_FONT_CACHE_DIR="$PWD/.hf-font-cache"         # FONT-001 的验证手段
   npm init -y
   npm install --save-exact hyperframes@0.8.96 gsap@3.15.0
   npm install --save-exact three@0.186.1        # 只有 Three.js 层需要
   ```
   npm 11 会提示 `allow-scripts`，不影响使用，不要执行 `npm approve-scripts`。验证：`package.json` 里版本号不带 `^`。

3. **确认浏览器与系统依赖**（`HF-008`）：
   ```bash
   npx hyperframes browser ensure
   npx hyperframes doctor
   ```
   验证：`doctor` 里 `FFmpeg`、`FFprobe`、`Chrome` 三项为 ✓。whisper-cpp、Kokoro、MusicGen 三项的 ✗ 可以忽略，第一版不用它们。

4. **Python 环境**（合成音频、分析成片、Manim 时需要）：
   ```bash
   uv venv --python 3.12
   source .venv/bin/activate
   uv pip install numpy                          # 合成音频与 analyze.py
   uv pip install "manim[typst]==0.21.0"         # 只有 Manim 档需要（MANIM-002）
   ```
   验证：`python -V` 为 3.12.x。

5. **组合文件骨架**（`HF-004`）：GSAP 档从下面的骨架开始；Three.js 档改用对应风格包的「技术配方」。`<audio>` 等第 7 步音频生成后再加，否则 `check` 会报 `audio_src_not_found`。时间线直接赋值给 `window.__timelines[...]` 即可，运行时会先建好这个对象（本机 0.8.96 实测）。
   ```html
   <!doctype html>
   <html>
   <head>
   <meta charset="utf-8">
   <style>
     :root { /* CRAFT-006 token：配色、字号、时长只在这里定义 */ }
     html, body { margin: 0; }
     #root { position: relative; width: 1920px; height: 1080px; overflow: hidden; }
     .clip { position: absolute; inset: 0; }
   </style>
   </head>
   <body>
   <div id="root" data-composition-id="main" data-start="0" data-duration="10" data-fps="30" data-width="1920" data-height="1080">
     <div id="scene" class="clip" data-start="0" data-duration="10" data-track-index="0">
       <!-- 画面 -->
     </div>
     <!-- 第 7 步音频生成后加：<audio id="audio" src="assets/audio.wav" data-start="0" data-duration="10" data-track-index="9"></audio> -->
   </div>
   <script src="./node_modules/gsap/dist/gsap.min.js"></script>
   <script>
     const tl = gsap.timeline({ paused: true });
     // tl.to(...) 按分镜时间写
     window.__timelines["main"] = tl;
   </script>
   </body>
   </html>
   ```
   验证：`npx hyperframes check .` 通过。

6. **字体**（`FONT-001`）：把组合里出现的全部中文写进 `fonts/chars.txt`，再按风格包列出的家族逐个执行（在项目根目录）：
   ```bash
   node <skill>/scripts/fetch-font.mjs --family "Noto Sans SC" --weights 400,900 --text-file fonts/chars.txt
   node <skill>/scripts/fetch-font.mjs --family "JetBrains Mono" --weights 400,700
   ```
   脚本把 `@font-face` 写进 `index.html` 第一个 `<style>` 的 `/* fonts:<slug> */` 区块。改了文案后重跑同一条命令。验证：`index.html` 里有这些区块，`fonts/` 下有 `.woff2`，`check` 无字体报错。

## Manim 档

纯 Manim 项目在第 1、4 步之后执行：

1. 按 `FONT-002` 下载 TTF（在项目根目录）：
   ```bash
   curl -sSfL "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf" -o "fonts/NotoSansSC[wght].ttf"
   ```
   其他家族把路径换成 `fonts.md` 登记表里的 `google/fonts` 路径与文件名。
2. `scene.py` 的场景类继承 `MANIM-004` 的 `Paced`。
3. 验证：`python -c "import manim; print(manim.__version__)"` 输出 `0.21.0`；用 `manim -ql -s` 出一张末帧，中文不是方框。

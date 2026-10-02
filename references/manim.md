# MANIM · 数学讲解档

### MANIM-001 · 什么时候用 Manim
- 触发: 选渲染层
- 规则: 内容以公式推导、几何证明、函数图像、算法步骤演示为主时用 Manim CE；其余一律用 HyperFrames。同一支视频需要两者时，分别渲染，再用 ffmpeg 拼接（`flow-verify.md` 附拼接命令）
- 为什么: Manim 的 `MathTex`/`MathTypst`、`Transform` 与坐标系原生支持公式与图形变换；网页栈写公式动画要额外引 KaTeX 并手写逐项动画

### MANIM-002 · 环境
- 触发: 首次在项目里用 Manim
- 规则: 在视频项目目录执行 `uv venv --python 3.12`、`source .venv/bin/activate`、`uv pip install "manim[typst]==0.21.0" numpy`。系统依赖 `cairo`、`pango`、`pkgconf` 用 Homebrew 装。公式默认用 `MathTypst`（不需要 LaTeX）；需要 LaTeX 语法时用 `MathTex`，先确认 `which latex` 有输出
- 为什么: Manim 0.21 要求 Python ≥3.11；本机实测 3.12 环境安装约 18 秒、占 271MB，`Text`（中文）、`MathTex`、`MathTypst` 三者都能渲染
- 验证: `python -c "import manim; print(manim.__version__)"` 输出 `0.21.0`

### MANIM-003 · 渲染命令
- 触发: 预览、抽帧、出成片
- 规则:
  - 草稿：`manim -ql --disable_caching --frame_rate 30 scene.py <Scene>`（854×480、30fps）
  - 末帧静图：加 `-s`，产物在 `media/images/<文件名>/`
  - 成片：`manim -qh --disable_caching --frame_rate 30 scene.py <Scene>`（1920×1080、30fps），产物在 `media/videos/<文件名>/1080p30/<Scene>.mp4`
  - 竖屏：成片命令再加 `--resolution 1080,1920`，产物目录变为 `1920p30/`
- 为什么: `-ql` 默认 15fps，而 `MANIM-004` 的 `Paced` 按 `FPS = 30` 排整帧；草稿不加 `--frame_rate 30` 时，在草稿上核对的帧数与拍点和成片对不上
- 验证: 按 `flow-verify.md` 第 1 步用 ffprobe 核对分辨率、帧率、帧数

### MANIM-004 · 确定性与节奏
- 触发: 写 Manim 场景
- 规则: 分镜里的每个动画与停留都用整数帧排：动画用下面的 `seg(t0, t1, …)`，停留用 `hold_until(t)`，时间取片内秒，禁止直接写 `run_time=0.8`、`self.wait(0.5)` 这类秒数。场景里有更新器（`add_updater`）时，停留调用 `hold_until(t, frozen=False)`。`seg(t0, t1)` 的第一帧仍是起始状态，终态出现在 t1 那一帧：要让「开始变化」落在拍点上的事件（弹出、起步），`t0` 取拍点前 1 帧；要让「到位」落在拍点上的事件（落地、扣合），把拍点作为 `t1`；缩放弹入类动画要让满尺寸落在拍点时，按「到位」处理。用到随机数时在场景开头 `random.seed(<固定值>)` 与 `np.random.seed(<固定值>)`。中文字体按 `FONT-002` 注册
- 为什么: Manim 0.21 按秒数取整帧：`play` 的帧数是 `len(np.arange(0, run_time, 1/fps))`，浮点误差下会多 1 帧；冻结的 `wait` 按 `int(run_time × fps)` 截断，会少 1 帧。blind-03 第一版按秒数写，节拍最多提前 0.6 秒、总长少 18 帧。本机实测：`play` 与带更新器的 `wait` 取 `(n − 0.5)/fps`、冻结的 `wait` 取 `(n + 0.5)/fps` 时，帧数都精确等于 n；带更新器的 `wait` 若取 `(n + 0.5)/fps` 会多 1 帧。本机实测 `seg(1.0, 2.0)` 做匀速位移：第 30 帧仍是起始状态，画面从第 31 帧开始变，第 60 帧到达终态；reg-003-r2、reg-003-r3 的执行者分别独立报告了「起步晚 1 帧」
- 验证: 成片帧数等于分镜总时长 × fps；`python <skill>/scripts/analyze.py motion <成片>` 的运动区间与分镜逐行相差不超过 0.1 秒

```python
FPS = 30

class Paced(Scene):  # 场景类继承它
    def now(self):
        return round(self.renderer.time * FPS)          # 已渲染的整帧数

    def hold_until(self, t, frozen=True):               # 静止到片内 t 秒
        n = round(t * FPS) - self.now()
        if n > 0:
            self.wait((n + 0.5) / FPS if frozen else (n - 0.5) / FPS, frozen_frame=frozen)

    def seg(self, t0, t1, *anims, **kw):                # 动画占片内 [t0, t1) 秒
        self.hold_until(t0)
        n = round(t1 * FPS) - self.now()
        self.play(*anims, run_time=(n - 0.5) / FPS, **kw)
```

### MANIM-005 · 配乐与音效
- 触发: Manim 视频需要声音
- 规则: 按 `AUD-001` 合成并归一音频，用 ffmpeg 合进 Manim 成片：`ffmpeg -y -i media/videos/…/<Scene>.mp4 -i assets/audio.wav -map 0:v -map 1:a -c:v copy -af apad -c:a aac -b:a 192k -shortest renders/<name>.mp4`（`apad` 的作用见 `AUD-004`），再按 `AUD-004` 测成片响度
- 为什么: 音频时间统一由分镜驱动，与 HyperFrames 档共用同一套合成与验收流程

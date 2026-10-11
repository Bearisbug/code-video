# flow-verify · 验收与交付

成片渲染后按顺序执行。任何一步不通过，回到 `flow-make.md` 对应步骤修，修完从第 1 步重来。`analyze.py` 在项目的 `.venv` 里运行（`uv pip install numpy`）。

1. **帧数与时长**：
   ```bash
   ffprobe -v error -count_frames -show_entries stream=codec_type,width,height,r_frame_rate,nb_read_frames:format=duration -of compact renders/<name>.mp4
   ```
   通过条件：宽高与帧率等于分镜表头；视频帧数 = 时长 × fps；有声音时存在 audio 流。

2. **联系表与节拍**：从分镜里挑 6–12 个关键节拍，帧号 = 片内秒 × fps，拼成联系表，交付时附上：
   ```bash
   ffmpeg -y -i renders/<name>.mp4 -vf "select='eq(n,<帧号1>)+eq(n,<帧号2>)+…',scale=640:-2,tile=4x3" -fps_mode vfr -frames:v 1 renders/<name>-sheet.jpg
   ```
   逐项对照风格包「验收清单」。节拍时间用 `python <skill>/scripts/analyze.py motion renders/<name>.mp4` 输出的运动区间与分镜逐行核对，误差不超过 0.2 秒。

3. **节奏**（`CRAFT-010`）：
   ```bash
   python <skill>/scripts/analyze.py rhythm renders/<name>.mp4 --beats <CRAFT-010 所说节拍行的起点,…,最后一行的终点> --chart
   ```
   通过条件：`storyboard_beats` 的 `cv` ≥ 0.25、`max_min_ratio` ≥ 4；`longest_low_energy.s` ≥ 1.0；`still_ratio` ≥ 0.25（片长不超过 20 秒）或 ≥ 0.08；能量图上停顿段与落版定格段所在行静止为 100%。风格包声明了节奏例外的，被声明的项按包核对。有镜头运动时，停顿段再按 `CRAFT-012` 的验证方法用小区域按原分辨率核对。

4. **分界与硬切**（`CRAFT-011`）：每个分界取前 0.2 秒、分界帧、后 0.2 秒三帧，一个分界一行，拼成分界联系表（30fps 时前后各 6 帧）：
   ```bash
   ffmpeg -y -i renders/<name>.mp4 -vf "select='eq(n,<分界1帧号−6>)+eq(n,<分界1帧号>)+eq(n,<分界1帧号+6>)+…',scale=640:-2,tile=3x<分界数>" -fps_mode vfr -frames:v 1 renders/<name>-bounds.jpg
   ```
   通过条件：每一行三帧里都能看到「衔接」列写的元素，衔接得分不低于 0.5；第 3 步输出的 `hard_cuts_s` 每一个都落在 `fast_cut_segments` 内或是切到落版的那一帧，其余的抽前后各 2 帧确认是元素一帧出现，不是场景硬切。

5. **去题材化与事实复查**（`CRAFT-003`、`CRAFT-018`）：成片里的物件、文字、剧情不得命中风格包「题材禁用清单」；第 2 步联系表上的每条文字都能在 `storyboard.md` 的事实清单里找到出处，或在画面上标了「示意」。

6. **音画同步**（`AUD-002`）：
   ```bash
   python <skill>/scripts/analyze.py sync renders/<name>.mp4 --events <分镜里有音效的关键事件时间，逗号分隔>
   ```
   落地、扣合、定格这类「停下来」的事件，时间后面加 `@stop`（如 `3.5@stop`）；小面积事件（端帽闪烁、字母弹出）加 `--roi x,y,w,h` 只看那块区域。通过条件：每个事件的 `offset_frames` 在 ±1 以内。`visual_confidence` 为 low、`onset_s` 为空，或是透明度入场与交叉淡入的事件（`AUD-002`），抽事件帧前后各 2 帧目检：
   ```bash
   ffmpeg -y -i renders/<name>.mp4 -vf "select='between(n,<帧号−2>,<帧号+2>)',crop=<w>:<h>:<x>:<y>,tile=5x1" -fps_mode vfr -frames:v 1 check-<帧号>.jpg
   ```
   看完删除 `check-*.jpg`。节拍核对抓不到文字淡入这类小变化时，`analyze.py motion` 加 `--thresh 0.02`。

7. **响度**（`AUD-004`）：
   ```bash
   ffmpeg -hide_banner -nostats -i renders/<name>.mp4 -af ebur128 -f null - 2>&1 | sed -n '/Summary:/,$p'
   ffmpeg -hide_banner -nostats -i renders/<name>.mp4 -af loudnorm=print_format=json -f null - 2>&1 | grep input_tp
   ```
   通过条件：I 在 −15 到 −13 LUFS 之间，`input_tp` 不高于 −1.0 dBTP。真峰值不读 ebur128 的 Peak：它只有一位小数，并且实测会低报（`AUD-004`）。归一时 `normalize-audio.sh` 报的 `loudnorm_mode` 为 linear；要「轻」的片子 Δ 在 3.0–4.5 dB（`AUD-005`）。不通过时按 `AUD-004` 修正并替换原片。风格包要求某个事件全片最响时，再执行 `python <skill>/scripts/analyze.py loudest renders/<name>.mp4 --events <事件时间>`，该事件应排在第一。有 `AUD-003` 空拍的片子，用 `AUD-005` 的 RMS 命令测揭晓前 50ms 与揭晓帧，差不小于 30 dB。

8. **渲染没有联网下载字体**（`FONT-001`，HyperFrames 档）：`.hf-font-cache/` 不存在或为空。有文件时按 `FONT-001` 检查两处：`@font-face` 是否内联、字体栈里有没有系统字体名，改完重新渲染。

9. **机械复核**：`bash <skill>/check.sh <项目目录>`，0 个 ❌。

10. **回收环境**：
   - HyperFrames 档：在项目目录执行 `npx hyperframes clean`；保留 `~/.cache/hyperframes/` 与 `~/.hyperframes/config.json`（`HF-008`）。
   - Manim 档：交付后删除 `media/`（中间片段与 Typst 编译缓存）。
   - 两档都删除本轮新建的临时目录、`.hf-font-cache/` 与 `snapshots/draft.mp4`；项目不再迭代时删除 `.venv`（约 330MB）与 `node_modules`。

11. **交付说明**：写明以下内容，没做到的如实写：
   - 成片路径、时长、分辨率、fps；
   - 使用的风格包 id 与渲染层；
   - 选定构思与理由；没有人确认时另外两个构思（`CRAFT-009`）；
   - `check` 结果行（HyperFrames 档），第 1、3、6、7 步的读数，归一的 `loudnorm_mode` 与 `input_plr`（要「轻」时加 Δ）；
   - 联系表与分界联系表路径、衔接得分；
   - 事实清单在 `storyboard.md` 里的位置，画面上标了「示意」的条目；
   - 实现中相对已确认分镜的改动（`flow-make.md` 第 5 步）；
   - 回收了哪些文件。

## 附：拼接 Manim 与 HyperFrames 片段

两段分辨率、帧率必须一致（先按 `MANIM-003` 用 `--frame_rate 30` 出片），并且每段都要有音轨：第一段没有音轨时，拼接不报错，但成片整段无声（本机实测）。Manim 段没有配乐时先补一条静音轨：

```bash
ffmpeg -y -i manim.mp4 -f lavfi -i anullsrc=r=48000:cl=stereo -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest part1.mp4
printf "file '%s'\n" part1.mp4 part2.mp4 > list.txt
ffmpeg -y -f concat -safe 0 -i list.txt -c:v libx264 -crf 16 -pix_fmt yuv420p -c:a aac -b:a 192k renders/<name>.mp4
```

拼接后从第 1 步重新验收。

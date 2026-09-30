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

3. **去题材化复查**（`CRAFT-003`）：成片里的物件、文字、剧情不得命中风格包「题材禁用清单」。

4. **音画同步**（`AUD-002`）：
   ```bash
   python <skill>/scripts/analyze.py sync renders/<name>.mp4 --events <分镜里有音效的关键事件时间，逗号分隔>
   ```
   落地、扣合、定格这类「停下来」的事件，时间后面加 `@stop`（如 `3.5@stop`）；小面积事件（端帽闪烁、字母弹出）加 `--roi x,y,w,h` 只看那块区域。通过条件：每个事件的 `offset_frames` 在 ±1 以内。`visual_confidence` 为 low 或 `onset_s` 为空的事件，抽事件帧前后各 2 帧目检：
   ```bash
   ffmpeg -y -i renders/<name>.mp4 -vf "select='between(n,<帧号−2>,<帧号+2>)',crop=<w>:<h>:<x>:<y>,tile=5x1" -fps_mode vfr -frames:v 1 check-<帧号>.jpg
   ```
   看完删除 `check-*.jpg`。节拍核对抓不到文字淡入这类小变化时，`analyze.py motion` 加 `--thresh 0.02`。

5. **响度**（`AUD-004`）：
   ```bash
   ffmpeg -hide_banner -nostats -i renders/<name>.mp4 -af ebur128=peak=true -f null - 2>&1 | sed -n '/Summary:/,$p'
   ```
   通过条件：I 在 −15 到 −13 LUFS 之间，真峰值不高于 −1.0 dBTP。ebur128 的 Peak 只有一位小数，卡在 −1.0 附近时以 `check.sh` 报的两位小数读数为准。不通过时按 `AUD-004` 修正并替换原片。风格包要求某个事件全片最响时，再执行 `python <skill>/scripts/analyze.py loudest renders/<name>.mp4 --events <事件时间>`，该事件应排在第一。

6. **渲染没有联网下载字体**（`FONT-001`，HyperFrames 档）：`.hf-font-cache/` 不存在或为空。有文件时按 `FONT-001` 检查两处：`@font-face` 是否内联、字体栈里有没有系统字体名，改完重新渲染。

7. **机械复核**：`bash <skill>/check.sh <项目目录>`，0 个 ❌。

8. **回收环境**：
   - HyperFrames 档：在项目目录执行 `npx hyperframes clean`；保留 `~/.cache/hyperframes/` 与 `~/.hyperframes/config.json`（`HF-008`）。
   - Manim 档：交付后删除 `media/`（中间片段与 Typst 编译缓存）。
   - 两档都删除本轮新建的临时目录与 `.hf-font-cache/`；项目不再迭代时删除 `.venv`（约 330MB）与 `node_modules`。

9. **交付说明**：写明以下内容，没做到的如实写：
   - 成片路径、时长、分辨率、fps；
   - 使用的风格包 id 与渲染层；
   - `check` 结果行（HyperFrames 档），第 1、4、5 步的读数；
   - 联系表路径；
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

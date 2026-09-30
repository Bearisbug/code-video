# AUD · 配乐与音效

第一版只做两种音频来源：`scripts/synth.py` 用代码合成，或用户提供的本地音频。旁白与 TTS 不在范围内。

### AUD-001 · 音频从分镜生成，挂在组合上
- 触发: 视频需要配乐或音效
- 规则: 按分镜表的音效列写 `audio/cues.json`，用 `scripts/synth.py` 合成 WAV（参数见本文件末的「合成器参考」），经 `scripts/normalize-audio.sh` 归一后放 `assets/`，在组合里用 `<audio id>` 挂载（`HF-004`）。用户提供了音乐文件时，先确认用户有使用权，再裁剪、归一后挂载；禁止从网上下载来源不明的音乐
- 为什么: 音效时间取自分镜，改分镜只需改清单重新合成；合成器用固定 seed，同一清单每次输出逐字节一致（本机实测）
- 验证: `assets/` 里的音频都能追溯到 `audio/cues.json` 或用户提供的文件

### AUD-002 · 音效与画面事件同帧
- 触发: 写 `cues.json` 的事件时间
- 规则: 「画面事件时间」指变化在画面上看得见的那一帧：揭示是新底色铺开大半的一帧，落地是接触的一帧，闪白是白帧本身，不是补间的起点。冲击、pop、tick、blip、chime、glitch、alarm 这类「起音即重点」的音效，`t` 等于画面事件时间，误差不超过 1 帧（30fps 下 33ms）。缓入型揭示（如 0.2 秒 `power2.in` 的圆形揭示）要比拍点提前 4 帧起步，让铺开那一帧落在拍点上，音效留在拍点。whoosh 最响处在 `t + dur/2`，写 `t = 事件时间 − dur/2`；riser 在 `t + dur` 到达顶点，写 `t = 重击时间 − dur`
- 为什么: 本机实测前 7 种音效的起音落在指定时间的 5ms 以内；blind-01 把 impact 放在 0.2 秒 `power2.in` 揭示的起点，揭示圆前 3 帧被主图形挡住，声音比画面早 133ms，改为揭示提前 4 帧起步后同帧
- 验证: `python <skill>/scripts/analyze.py sync renders/<name>.mp4 --events <事件时间>`，`offset_frames` 在 ±1 以内；`visual_confidence` 为 low 的事件抽前后各 2 帧目检

### AUD-003 · 关键揭晓前留空拍
- 触发: 分镜里有全片最重要的揭晓、锁定或落版
- 规则: 揭晓前留 50–200ms 近静音，揭晓帧同时落一个 `impact`。做法：在 `cues.json` 的 `bed.automation` 加一段 `[揭晓时刻 − 0.1, 揭晓时刻, 0.03]`，这段时间内不安排音效事件；揭晓后要音床抬高一档时再加 `[揭晓时刻, 结束, 1.2]`。自动化只作用于音床，`impact` 等事件不受影响。禁止用 ffmpeg `volume` 表达式做这一步
- 为什么: 拆解的 15 段作品里，01、05、09、12、13 段都在关键揭晓前留了 50–200ms 近静音，再在同一帧落低频重击。本机实测 `automation` 做法：低谷内 −58.7dB，揭晓帧 impact −6.4dB。ffmpeg `volume` 表达式默认按约 21ms 一块求值，会把 impact 的起音一起压掉
- 验证: `analyze.py onsets` 能在揭晓时刻测到起音；揭晓前 50ms 的音量比揭晓帧低 30dB 以上

### AUD-004 · 在成片上测响度
- 触发: 交付前
- 规则: 用 `ffmpeg -hide_banner -nostats -i renders/<name>.mp4 -af ebur128=peak=true -f null -` 测成片，目标 −14 LUFS ±1，真峰值不高于 −1 dBTP。超出时抽出成片音轨归一（脚本默认真峰值上限 −2 dBTP，给 AAC 编码留余量），`-c:v copy` 合回后替换原片，`renders/` 里只留交付的那一个：
  ```bash
  <skill>/scripts/normalize-audio.sh renders/<name>.mp4 renders/<name>-audio.wav
  ffmpeg -y -i renders/<name>.mp4 -i renders/<name>-audio.wav -map 0:v -map 1:a -c:v copy -af apad -c:a aac -b:a 192k -shortest renders/<name>.tmp.mp4
  mv renders/<name>.tmp.mp4 renders/<name>.mp4 && rm renders/<name>-audio.wav
  ```
  `-af apad` 让音轨补静音到视频结束，`-shortest` 随之按视频长度截止；不加 `apad` 时，音轨只要比视频短几毫秒就会截掉最后一帧（本机实测 300 帧变 299 帧）。修正只做一次，从渲染出的原片开始；脚本输出偏离目标超过 0.5 LU 时会打印告警，按告警调合成清单的增益后重新合成、重新挂载、重新渲染
  用户要「轻」「安静」的配乐时，调低音床相对音效的比例、去掉鼓点，整片响度仍按 −14 LUFS；用户给出具体响度数值时按用户的数值
- 为什么: 混音与 AAC 编码会改变响度和真峰值。两个 HyperFrames 盲测的成片为 −15.5、−15.9 LUFS（素材已归一到 −14）。三个盲测按 −1 dBTP 上限归一再编码后，真峰值回升到 −0.4 到 −0.9 dBFS；上限降到 −1.5 或 −2 dBTP 后为 −1.1 到 −1.4。视频流用 `-c:v copy` 合回，逐帧哈希不变
- 验证: 交付说明里写出成片的 I 与 Peak 读数；`bash <skill>/check.sh <项目>` 的响度项通过

## 合成器参考（scripts/synth.py）

运行环境：视频项目的 `.venv`（`uv venv --python 3.12`，`uv pip install numpy`）。命令：`python <skill>/scripts/synth.py audio/cues.json assets/sfx-raw.wav`。

清单顶层字段：

| 字段 | 含义 | 默认 |
|---|---|---|
| `duration` | 总时长（秒），与组合 `data-duration` 相同 | 必填 |
| `bpm` | 音床速度，与 `CRAFT-005` 的节拍网格一致 | 120 |
| `seed` | 随机种子 | 1 |
| `bed` | 音床，可省略 | 无 |
| `events` | 音效事件数组 | 空 |

`bed` 字段：

| 字段 | 取值 |
|---|---|
| `style` | `pluck`（明亮拨弦，适合扁平、形变、科普）、`pad`（长铺底，适合玻璃拟态、线条）、`chip`（方波，适合像素风）、`pulse`（每拍一音的暗色音床，适合 HUD） |
| `chords` | 和弦数组，每个字符串是空格分隔的音名，如 `"A3 C4 E4"`；每 4 拍换一个，循环使用 |
| `drums` | `true` 时加底鼓（1、3 拍）、军鼓（2、4 拍）、八分踩镲 |
| `start` / `end` | 音床起止秒；起始 0.3 秒淡入，结尾 0.5 秒淡出。音符从 `start` 起按半拍排，`start` 取半拍的整数倍（120 BPM 时 0.5、1.0…），音床才在节拍网格上 |
| `gain` | 音床整体音量，默认 0.5 |
| `automation` | 可选，`[[起, 止, 增益], …]`：区间内音床乘以增益，两端各 5ms 过渡，只作用于音床（`AUD-003`） |

`events` 每项：`t`（秒）、`sfx`、`gain`（默认 1）、`pitch`（音高倍率，默认 1）、`dur`（秒，可省略）、`pan`（−1 左到 1 右，默认 0）。

| `sfx` | 声音 | 默认时长 | 典型用途 |
|---|---|---|---|
| `impact` | 约 50Hz 下潜低频加起音噪声 | 0.9 | 揭晓、锁定、落版、开机 |
| `pop` | 下滑音高的短促「啵」 | 0.25 | 落地、弹出、形变完成 |
| `tick` | 高频短点击 | 0.05 | 打字、刻度、计数跳动 |
| `blip` | 方波混正弦的短提示音 | 0.12 | UI 提示、数据刷新 |
| `chime` | 钟琴泛音 | 1.2 | 完成、点亮、正向反馈 |
| `whoosh` | 带通噪声扫频，中点最响 | 0.45 | 飞入、转场、快速位移 |
| `riser` | 上升噪声加音调，结尾最响 | 1.0 | 蓄力、倒计时 |
| `glitch` | 量化噪声碎片 | 0.15 | 故障闪帧、撕裂切片 |
| `alarm` | 1000/1750Hz 双音交替 | 0.3 | 警报、锁定确认 |

合成输出的峰值固定在 −3 dBFS，响度未归一；挂载前先执行 `<skill>/scripts/normalize-audio.sh assets/sfx-raw.wav assets/audio.wav`。

输出末端有 tanh 饱和，多个大增益事件叠在一起时会被压扁：全片最响的事件（通常是揭晓的 `impact`）`gain` 取 1.0，其余冲击类事件取 0.3–0.6。blind-02 里开机 `impact` 取 0.6 时比锁定还响，改为 0.35 后锁定成为最响。

`normalize-audio.sh` 输出的 `loudnorm_mode` 为 `dynamic` 时，说明峰值相对响度太高，loudnorm 改用动态压缩，事件之间的响度差会被压平（reg-002-r3 实测：开机与锁定冲击被压到 −7.0 与 −6.9 dB）。遇到这种情况，先降低最响事件的 `gain` 或提高音床 `gain`，重新合成后再归一。风格包要求某个事件全片最响时，用 `analyze.py loudest` 在成片上核对：HyperFrames 混音会改变各事件电平，素材里的排序不能代替成片。

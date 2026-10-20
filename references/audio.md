# AUD · 配乐与音效

音频只有两种来源：`scripts/synth.py` 用代码合成，或用户提供的本地音频。旁白与 TTS 不在范围内。

### AUD-001 · 音频从分镜生成，挂在组合上
- 触发: 视频需要配乐或音效
- 规则: 按分镜表的音效列写 `audio/cues.json`，用 `scripts/synth.py` 合成 WAV（参数见本文件末的「合成器参考」），经 `scripts/normalize-audio.sh` 归一后放 `assets/`，在组合里用 `<audio id>` 挂载（`HF-004`）。用户提供了音乐文件时，先确认用户有使用权，再裁剪、归一后挂载；禁止从网上下载来源不明的音乐
- 为什么: 音效时间取自分镜，改分镜只需改清单重新合成；合成器用固定 seed，同一清单每次输出逐字节一致（本机实测）
- 验证: `assets/` 里的音频都能追溯到 `audio/cues.json` 或用户提供的文件

### AUD-002 · 音效与画面事件同帧
- 触发: 写 `cues.json` 的事件时间
- 规则: 「画面事件时间」指变化在画面上看得见的那一帧：揭示是新底色铺开大半的一帧，落地是接触的一帧，闪白是白帧本身，不是补间的起点。冲击、pop、tick、blip、chime、glitch、alarm 这类「起音即重点」的音效，`t` 等于画面事件时间，误差不超过 1 帧（30fps 下 33ms）。缓入型揭示（如 0.2 秒 `power2.in` 的圆形揭示）要比拍点提前 4 帧起步，让铺开那一帧落在拍点上，音效留在拍点。whoosh 最响处在 `t + dur/2`，写 `t = 事件时间 − dur/2`；riser 在 `t + dur` 到达顶点，写 `t = 重击时间 − dur`。透明度从 0 起步的入场，补间提前 1 帧起步，让第一个看得见的帧落在拍点上
- 为什么: 本机实测前 7 种音效的起音落在指定时间的 5ms 以内；impact 放在 0.2 秒 `power2.in` 揭示的起点时，揭示圆前 3 帧被主图形挡住，声音比画面早 133ms，改为揭示提前 4 帧起步后同帧。开场词透明度入场提前 1 帧后，第 7 帧首次可见、与音效同帧，`sync` 仍读出 −2.1 帧并标 high；另一支片的淡入读偏 +2 到 +4 帧
- 验证: `python <skill>/scripts/analyze.py sync renders/<name>.mp4 --events <事件时间>`，`offset_frames` 在 ±1 以内；`visual_confidence` 为 low 的事件，以及透明度入场与交叉淡入的事件（`sync` 对它们会读偏 2–4 帧，仍可能标 high），抽前后各 2 帧目检

### AUD-003 · 关键揭晓前留空拍
- 触发: 分镜里有全片最重要的揭晓、锁定或落版
- 规则: 揭晓前留 50–200ms 近静音，揭晓帧同时落一个 `impact`。做法：在 `cues.json` 的 `bed.automation` 加一段 `[揭晓时刻 − 0.1, 揭晓时刻, 0.03]`，这段时间内不安排音效事件；揭晓后要音床抬高一档时再加 `[揭晓时刻, 结束, 1.2]`。自动化只作用于音床，`impact` 等事件不受影响。开了共用空间（`AUD-006`）时 `bed.send` 写 0：音床在空拍之前送进混响的尾音会穿过空拍。禁止用 ffmpeg `volume` 表达式做这一步
- 为什么: 拆解的 15 段作品里，01、05、09、12、13 段都在关键揭晓前留了 50–200ms 近静音，再在同一帧落低频重击。本机实测 `automation` 做法：低谷内 −58.7dB，揭晓帧 impact −6.4dB。ffmpeg `volume` 表达式默认按约 21ms 一块求值，会把 impact 的起音一起压掉。2026-10-07 实测，开 `space`、音床按默认送 0.15 时，揭晓前 50ms 只比揭晓帧低 22.2 dB；同一清单只把 `bed.send` 改成 0，低 44.9 dB，`input_plr` 11.29 → 11.53，仍为 linear
- 验证: `analyze.py onsets` 能在揭晓时刻测到起音；揭晓前 50ms 的音量比揭晓帧低 30dB 以上

### AUD-004 · 在成片上测响度
- 触发: 交付前
- 规则: 用 `ffmpeg -hide_banner -nostats -i renders/<name>.mp4 -af ebur128 -f null -` 读成片的 I，用 `ffmpeg -hide_banner -nostats -i renders/<name>.mp4 -af loudnorm=print_format=json -f null -` 的 `input_tp` 读真峰值（`check.sh` 同一读法），目标 −14 LUFS ±1，真峰值不高于 −1 dBTP。超出时按顺序修，`renders/` 里只留交付的那一个：
  1. 组合里只有一条 `<audio>`、没写 `data-volume`，而且 I 在目标内、只是真峰值超出时：把 `assets/` 里归一好的音轨直接合回，再复测：
     ```bash
     ffmpeg -y -i renders/<name>.mp4 -i assets/audio.wav -map 0:v -map 1:a -c:v copy -af apad -c:a aac -b:a 192k -shortest renders/<name>.tmp.mp4
     mv renders/<name>.tmp.mp4 renders/<name>.mp4
     ```
  2. 其余情况，或第 1 步后仍超出：从渲染出的原片抽出音轨归一（脚本默认真峰值上限 −2 dBTP，给 AAC 编码留余量），合回后替换原片：
     ```bash
     <skill>/scripts/normalize-audio.sh renders/<name>.mp4 renders/<name>-audio.wav
     ffmpeg -y -i renders/<name>.mp4 -i renders/<name>-audio.wav -map 0:v -map 1:a -c:v copy -af apad -c:a aac -b:a 192k -shortest renders/<name>.tmp.mp4
     mv renders/<name>.tmp.mp4 renders/<name>.mp4 && rm renders/<name>-audio.wav
     ```
  `-af apad` 让音轨补静音到视频结束，`-shortest` 随之按视频长度截止；不加 `apad` 时，音轨只要比视频短几毫秒就会截掉最后一帧（本机实测 300 帧变 299 帧）。脚本输出偏离目标超过 0.5 LU 或报 dynamic 时会打印告警，按告警调合成清单的增益后重新合成、重新挂载、重新渲染
  用户要「轻」「安静」的配乐时按 `AUD-005` 的「轻」配，整片响度仍按 −14 LUFS；用户给出具体响度数值时按用户的数值。归一必须是 linear 模式（`AUD-005`）
- 为什么: 混音与 AAC 编码会改变响度和真峰值。两个 HyperFrames 盲测的成片为 −15.5、−15.9 LUFS（素材已归一到 −14）。三个盲测按 −1 dBTP 上限归一再编码后，真峰值回升到 −0.4 到 −0.9 dBFS；上限降到 −1.5 或 −2 dBTP 后为 −1.1 到 −1.4。视频流用 `-c:v copy` 合回，逐帧哈希不变。10 秒浅底探针（2026-10-07）：归一后的音轨真峰值 −3.99 dBTP、−13.9 LUFS，HyperFrames 渲染出的成片 I 为 −14.1 LUFS，真峰值却是 −0.49 dBTP（右声道在 7.504 秒的 impact 起音处采样峰值 −1.37 dBFS），ebur128 的 Peak 只报 −2.8，低于采样峰值，不能用来判真峰值；同一音轨用上面第 1 步的命令合回后为 −14.0 LUFS、−3.78 dBTP、300 帧不变，而走第 2 步时归一进入 dynamic（`input_plr` 13.60）
- 验证: 交付说明里写出成片的 I 与 `input_tp` 读数，以及归一时的 `loudnorm_mode` 与 `input_plr`；`bash <skill>/check.sh <项目>` 的响度项通过

### AUD-005 · 归一保持 linear：起始增益与「轻」
- 触发: 写 `cues.json` 的 `gain`；`normalize-audio.sh` 报 dynamic；用户要「轻」「安静」的配乐
- 规则:
  - `normalize-audio.sh` 输出的 `loudnorm_mode` 必须是 `linear`。linear 的条件是 `input_plr`（输入真峰值减积分响度）不超过 12 dB 且 LRA 不超过 11；实用增益下 LRA 不会超，起作用的只有 `input_plr`。
  - 起始增益按下表配。实测列的种子数指 seed 从 1 起连续取，每一行在这些种子上全部进入 linear。音床 style 不同，gain 1 时电平不同（pluck −13.9、pad −15.8、pulse −18.0、chip −18.1 dBFS RMS），一行只适用于它写的 style。

    | 情形 | 音床 gain | 全片最响事件 | 其余事件 | 实测：linear 种子数，`input_plr` 最大值 |
    |---|---|---|---|---|
    | 音效密集（每秒 1.3 个以上），pluck | 1.25 | impact 1.0 | 按风格包 | `shape-morph` 片 12/12，11.33；`mascot-story` 片 8/8，11.87 |
    | 同上，最响事件降一档 | 0.95 | impact 0.8 | 其余冲击类 0.4–0.5 | `shape-morph` 片 12/12，11.68 |
    | 同上 | 1.1 | impact 0.9 | 其余冲击类 0.4–0.5 | `shape-morph` 片 12/12，11.52 |
    | pulse 音床 | 2.5 | impact 0.8 | `glitch` ≤ 0.35 | `fui-hud` 片 8/8，11.67 |
    | pulse 音床 | 3.0 | impact 1.0 | `glitch` ≤ 0.5 | `fui-hud` 片 8/8，11.70 |
    | 中等密度（每秒 0.6–1.3 个），pluck | 1.25 | impact 1.0 | 起音型 0.35–0.45 | 1/1（seed 1），11.29；Δ 3.3–3.4 |
    | 音效稀疏（每秒 0.6 个以下）且要「轻」，pluck | 0.8 | impact 0.4 | 起音型 0.3 | 8/8，11.40；Δ 3.6 |
    | 稀疏、音效要更突出，pluck | 1.2 | impact 1.0 | 起音型 0.75 | 8/8，11.74；Δ 4.3 |

  - `whoosh` 的 gain 不超过 0.3。
  - 报 dynamic 时分两步改，每步都重新合成、重新归一：先按上表提高音床 gain，最响事件保持风格包规定的值；仍超门槛，再把最响事件的 gain 降 0.1–0.2。禁止靠换 `seed` 过门槛。表里的行只是起点，换一份清单以 `normalize-audio.sh` 的输出为准；两步改完 Δ 跌到 3.0 以下时，把起音型音效的 gain 各提高 0.05–0.1，再合成核对（照「轻」一行配的另一份清单进了 dynamic，`input_plr` 12.65）。
  - 真峰值以 `normalize-audio.sh` 输出的 `input_tp` 为准，不能从合成输出的 −3 dBFS 采样峰值推算：噪声类音效的真峰值比采样峰值高，impact 高 1.8–4.3 dB，glitch 高 2.2–4.3 dB，whoosh 与 tick 不超过 1.9 dB。
  - 「轻」同时满足四条：① `drums: false`；② 音床 style 为 `pluck`；③ Δ 在 3.0–4.5 dB 之间，Δ = 起音型音效（pop、blip、chime，不含全片最响事件）起音后 0.1 秒 RMS 的中位数，减去无事件段音床 1 秒 RMS 的中位数；`tick` 不计入，它只有 50ms，0.1 秒窗口的 RMS 读不出它（同一混音里 pop 比音床高 3.3–8.7 dB 时，tick 只读出 0–0.9 dB）；④ 整片 −14 LUFS，归一为 linear。需要听清音效的稀疏片不用 `pad` 音床：pad 在 linear 组合里 Δ 最高只有 2.5 dB，pop 会被盖住。Δ 在归一后的 WAV 或成片上测：
    ```bash
    ffmpeg -hide_banner -nostats -ss <无事件段起点> -t 1 -i <文件> -af astats=measure_perchannel=none:measure_overall=RMS_level -f null - 2>&1 | grep 'RMS level'
    ffmpeg -hide_banner -nostats -ss <事件时间> -t 0.1 -i <文件> -af astats=measure_perchannel=none:measure_overall=RMS_level -f null - 2>&1 | grep 'RMS level'
    ```
- 为什么: 归一到 −14 LUFS 后，成片里音床的 1 秒 RMS 都在 −16.5 到 −15.8 dBFS，与 gain 的绝对值无关；gain 只决定音床与音效的比例，调低音床只会抬高 `input_plr`（音床 0.35、impact 1.0 时为 18.53）。Δ 低于 3 dB 时音效被音床盖住，高于约 4.5 dB 时 `input_plr` 超过 12。dynamic 不是退路：实测它把最响 impact 与 pop 的差从 11.8 dB 压到 4.7 dB，揭晓没了冲击力，音床电平也跟着起伏 1.3 dB。换 seed 不算修法：音床 0.85、impact 1.0 这一组在 seed 1–12 上 `input_plr` 跨 11.07–13.35，只有 4 个 linear，之后增减任何噪声类事件都会让结果重新跳动。一支回归成片实际按 dynamic 归一（输入 −18.13 LUFS、−1.32 dBTP，差 16.8）。以上数据是 2026-10-07 用 `synth.py` 与 `normalize-audio.sh` 在四份盲测与回归清单上扫描所得，只做了测量，没有试听
- 验证: 交付说明写出 `loudnorm_mode` 与 `input_plr`；要「轻」的片子再写 Δ

### AUD-006 · 音效密度与共用空间
- 触发: 写 `cues.json` 的 `events`
- 规则:
  - 音效事件总数少于全片拍数（120 BPM 每秒 2 拍，10 秒 20 拍）；风格包另有规定的按包（如 `shape-morph` 每次形变配一个音效）。
  - 相隔 1–40ms 的两个音效只留一个，`synth.py` 遇到会告警；同一时刻叠放两种声音（如锁定时 impact 叠 alarm）算一个复合音。
  - 不给每个画面事件都配声：打字每 3 个字一声 `tick`；点击配两声 `tick`，按下与抬起相隔 60–75ms，与画面上的按下、抬起同帧。
  - 共用空间：清单顶层写 `"space": {"t60": 1.1}` 时，全部声音按各自的送混响比例进同一个混响。默认比例：glitch 0.1，tick、blip 0.15，pop、alarm 0.2，impact 0.25，chime 0.4，riser 0.5，whoosh 0.6，音床 0.15（音床有 `AUD-003` 空拍或停顿段压低时写 0）；单个事件写 `send` 覆盖，音床写在 `bed.send`。风格包写明开不开，没写的不开。
  - 落地、碰撞这类物体接触用 `tick`、`impact` 或 `chime`；`pop`、`blip` 是纯音，听起来是界面提示音。风格包「声音」一节另有规定的按包（`shape-morph`、`mascot-story` 的落地配 `pop`）。
- 为什么: onetake motion-web 首版每个画面事件配一声（打字 40 声、字母 10 声、彩纸 26 声），声音之间没有共同空间、用的是原始正弦，审片人不到一分钟就评为「低劣」（作者自述）。`space` 的本机实测：同一清单两次合成逐字节一致；音床 0.8 的清单开启后仍为 linear，Δ 从 3.62 变为 3.41 dB；音床 1.25、seed 7 的清单开启后仍为 linear；10 秒探针 17 个事件开启后 `input_plr` 9.92、linear。混响音色没有试听
- 验证: 合成时没有 40ms 告警；事件数小于拍数
- 来源: https://github.com/feitangyuan/onetake （commit cf09bde 的案例记录；只取方法与数值）
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
| `space` | 共用混响，如 `{"t60": 1.1, "predelay": 0.012}`（`AUD-006`） | 无（不加混响） |

`bed` 字段：

| 字段 | 取值 |
|---|---|
| `style` | `pluck`（明亮拨弦，适合扁平、形变、科普）、`pad`（长铺底，适合玻璃拟态、线条；音效稀疏时会盖住音效，见 `AUD-005`）、`chip`（方波，适合像素风）、`pulse`（每拍一音的暗色音床，适合 HUD） |
| `chords` | 和弦数组，每个字符串是空格分隔的音名，如 `"A3 C4 E4"`；每 4 拍换一个，循环使用 |
| `drums` | `true` 时加底鼓（1、3 拍）、军鼓（2、4 拍）、八分踩镲 |
| `start` / `end` | 音床起止秒；起始 0.3 秒淡入，结尾 0.5 秒淡出。音符从 `start` 起按半拍排，`start` 取半拍的整数倍（120 BPM 时 0.5、1.0…），音床才在节拍网格上 |
| `gain` | 音床整体音量，默认 0.5 |
| `automation` | 可选，`[[起, 止, 增益], …]`：区间内音床乘以增益，两端各 5ms 过渡，只作用于音床（`AUD-003`） |
| `send` | 有 `space` 时音床送混响的比例，默认 0.15 |

`events` 每项：`t`（秒）、`sfx`、`gain`（默认 1）、`pitch`（音高倍率，默认 1）、`dur`（秒，可省略）、`pan`（−1 左到 1 右，默认 0）、`send`（有 `space` 时送混响的比例，默认值见 `AUD-006`）。

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

输出末端有 tanh 饱和，多个大增益事件叠在一起时会被压扁：全片最响的事件（通常是揭晓的 `impact`）按 `AUD-005` 的增益表取值，其余冲击类事件取 0.3–0.6。开机 `impact` 取 0.6 时比锁定还响，改为 0.35 后锁定成为最响。

`normalize-audio.sh` 输出的 `loudnorm_mode` 为 `dynamic` 时，loudnorm 改用动态压缩，事件之间的响度差会被压平（实测开机与锁定冲击被压到 −7.0 与 −6.9 dB），按 `AUD-005` 改增益后重新合成。风格包要求某个事件全片最响时，用 `analyze.py loudest` 在成片上核对：HyperFrames 混音会改变各事件电平，素材里的排序不能代替成片。

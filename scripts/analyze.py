"""成片分析：画面变化、音频起音、近黑占比、音画同步、节奏与留白。在装有 numpy 的 .venv 里运行，依赖 ffmpeg/ffprobe。

用法:
  python analyze.py motion <视频> [--thresh 0.5] [--roi x,y,w,h]   画面变化区间与变化最大的帧
  python analyze.py onsets <视频或音频> [--rise 6]                  音频起音时间
  python analyze.py dark <视频> --at 3.0,5.6 [--thresh 20]         指定时刻亮度低于阈值的像素占比
  python analyze.py loudest <视频> --events 0.0,6.5                每个事件起 0.1 秒的 RMS 按响度排序，并列出全片最响的 5 个窗口
  python analyze.py sync <视频> --events 0.5,5.0,8.0 [--roi x,y,w,h] [--rise 6]
      每个事件时间 ±4 帧内的「画面变化开始帧」与 ±0.2 秒内的起音，报告相差几帧。
      画面变化开始帧：窗口内第一个突增倍数达到窗口最大值一半的帧；突增倍数 = 本帧变化 ÷ 前 10 帧变化中位数。
      停止类事件（落地、扣合、定格）在时间后加 @stop，如 --events 3.5@stop,6.5，取窗口内最后一个显著变化帧。
      窗口最大突增 < 3 时标 low，需要目检。
  python analyze.py beats 0.5,2.0,2.5,4.5                          分镜节拍行的时长分布：各行起点加最后一行终点，输出最长最短比与变异系数
  python analyze.py rhythm <视频> [--beats 起点,…,终点] [--roi x,y,w,h] [--chart] [--bucket 0.5]
      按每秒 12 帧、320px 宽灰度取样：静止占比（取样差 <0.5）、低能量占比（<2）、最长静止段与最长低能量段；
      瞬变（硬切或元素一帧出现）时刻、快切段（1.5 秒内 ≥3 次大变化）、分界（约 0.4 秒内半数以上像素换内容）
      与段落时长分布；给 --beats 时另算分镜节拍。--chart 先打印能量图（参考片拆解用）。
  python analyze.py ground <视频>                                 浅底留白：每 0.5 秒一帧，主底色 hex 与底色占比的中位数、25 分位

--thresh（motion）：帧间平均灰度差大于它算「在动」，默认 0.5；文字淡入、小元素要核对时降到 0.02。
--roi：只分析画面里的一块区域（原分辨率像素），小面积事件（如 28×20 的闪烁）用它测；区域宽不超过 320px 时按原分辨率分析，能看出几像素的漂移。
--rise：起音判定门槛，比前 50ms 中位数高出的 dB 数，默认 6。
"""
import json
import subprocess
import sys

import numpy as np

W = 320  # 分析用缩小宽度，高度按比例


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=r_frame_rate,width,height", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.strip()
    w, h, rate = out.split(",")
    a, b = rate.split("/")
    return float(a) / float(b), int(w), int(h)


def gray_frames(path, roi=None, rate=None):
    """缩到 W 宽的灰度帧，形状 (帧数, 高, 宽)；rate 给定时先重采样到该帧率。"""
    _, vw, vh = probe(path)
    x, y, w, h = roi if roi else (0, 0, vw, vh)
    sw = min(W, w)
    sh = max(2, round(h * sw / w / 2) * 2)
    vf = (f"fps={rate}," if rate else "") + f"crop={w}:{h}:{x}:{y},scale={sw}:{sh}"
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", vf, "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, sh, sw)


def step_diffs(f, lag=1):
    """d[i] = 第 i 帧相对第 i-lag 帧的平均灰度差，前 lag 个为 0；逐帧计算，不建整段差分数组。"""
    d = np.zeros(len(f))
    for i in range(lag, len(f)):
        d[i] = np.abs(f[i].astype(np.int16) - f[i - lag]).mean()
    return d


def frame_diffs(path, roi=None):
    return step_diffs(gray_frames(path, roi))  # d[i] = 第 i 帧相对第 i-1 帧的变化


def envelope(path, win=0.005):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", "48000", "-f", "f32le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, np.float32)
    n = int(48000 * win)
    x = x[: x.size // n * n].reshape(-1, n)
    return 10 * np.log10((x ** 2).mean(axis=1) + 1e-12), win


def onsets(path, rise=6.0):
    db, win = envelope(path)
    look = int(0.05 / win)
    times, last = [], -1.0
    for i in range(look, db.size):
        base = np.median(db[i - look:i])
        t = i * win
        if db[i] > -45 and db[i] - base > rise and t - last > 0.08:
            times.append(round(t, 3))
            last = t
    return times


def motion(path, thresh=0.5, roi=None):
    fps = probe(path)[0]
    d = frame_diffs(path, roi)
    spans, start = [], None
    for i, m in enumerate(d > thresh):
        if m and start is None:
            start = i
        if not m and start is not None:
            spans.append([round(start / fps, 3), round((i - 1) / fps, 3)])
            start = None
    if start is not None:
        spans.append([round(start / fps, 3), round((len(d) - 1) / fps, 3)])
    peaks = [int(i) for i in np.argsort(d)[::-1][:12]]
    return {"fps": fps, "thresh": thresh, "spans_s": spans, "top_change_frames": sorted(peaks)}


def dark(path, times, thresh):
    res = {}
    for t in times:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", path, "-frames:v", "1", "-f", "rawvideo",
                              "-pix_fmt", "gray", "-"], capture_output=True).stdout
        a = np.frombuffer(raw, np.uint8)
        res[str(t)] = round(float((a < thresh).mean() * 100), 1)
    return res


def sync(path, events, roi=None, rise=6.0):
    fps = probe(path)[0]
    d = frame_diffs(path, roi)
    ons = onsets(path, rise)
    base = np.array([np.median(d[max(0, i - 10):i]) if i else 0 for i in range(len(d))])
    spike = d / (base + 0.05)
    rows = []
    for ev in events:
        t, stop = float(ev.split("@")[0]), ev.endswith("@stop")
        c = int(round(t * fps))
        lo, hi = max(1, c - 4), min(len(d), c + 5)
        if stop:  # 停止类事件（落地、扣合）：取窗口内最后一个变化量达到最大值一半的帧
            win = d[lo:hi]
            vis = lo + int(np.flatnonzero(win >= win.max() / 2)[-1])
            win = spike[lo:hi]
        else:     # 出现类事件：第一个突增达到窗口最大值一半的帧
            win = spike[lo:hi]
            vis = lo + int(np.argmax(win >= win.max() / 2))
        near = [o for o in ons if abs(o - t) <= 0.2]
        onset = min(near, key=lambda o: abs(o - t)) if near else None
        conf = "high" if win.max() >= 3 else "low：画面变化不明显或是停止类事件，抽事件帧前后各 2 帧目检"
        rows.append({"event_s": t, "visual_frame": vis, "visual_s": round(vis / fps, 3),
                     "spike": round(float(spike[vis]), 1), "visual_confidence": conf,
                     "onset_s": onset, "offset_frames": None if onset is None else round((onset - vis / fps) * fps, 1)})
    return rows


def loudest(path, events, win=0.1):
    """每个事件时刻起 win 秒的 RMS（dBFS），按响度排序；另给全片最响的 5 个窗口，核对「某事件全片最响」。"""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", "48000", "-f", "f32le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, np.float32)
    n = int(48000 * win)
    rms = lambda s: round(float(10 * np.log10((s ** 2).mean() + 1e-12)), 1)
    rows = sorted(({"event_s": t, "rms_db": rms(x[int(t * 48000): int(t * 48000) + n])} for t in events),
                  key=lambda r: -r["rms_db"])
    blocks = x[: x.size // n * n].reshape(-1, n)
    db = 10 * np.log10((blocks ** 2).mean(axis=1) + 1e-12)
    top = [{"t_s": round(i * win, 2), "rms_db": round(float(db[i]), 1)} for i in np.argsort(db)[::-1][:5]]
    return {"events_by_loudness": rows, "top_windows": sorted(top, key=lambda r: -r["rms_db"])}


RATE = 12          # rhythm 的取样帧率：30fps 与 60fps 的片子按同一口径比较
STILL, LOW, BIG = 0.5, 2.0, 8.0   # 取样间平均灰度差：静止 / 低能量 / 大变化


def runs(mask):
    """布尔序列里连续 True 段的 [起, 止) 下标。"""
    m = np.concatenate([[0], np.asarray(mask, np.int8), [0]])
    e = np.flatnonzero(np.diff(m))
    return list(zip(e[::2].tolist(), e[1::2].tolist()))


def spread(durs):
    d = np.array(durs, float)
    return {"n": int(d.size), "durations_s": [round(float(v), 2) for v in d],
            "max_min_ratio": round(float(d.max() / d.min()), 2), "cv": round(float(d.std() / d.mean()), 3)}


def hard_cuts(path, roi=None):
    """原帧率下的瞬变帧（硬切，或元素一帧内出现、消失）：本帧变化 ≥ 前后各 3 帧中位数较大者 × 4 + 0.3；相隔 ≤2 帧的合并为一次。"""
    fps = probe(path)[0]
    d = frame_diffs(path, roi)
    cuts = []
    for i in range(1, len(d)):
        base = max(np.median(d[max(1, i - 3):i]) if i > 1 else 0.0, np.median(d[i + 1:i + 4]) if i + 1 < len(d) else 0.0)
        if d[i] >= 4 * base + 0.3 and not (cuts and i - cuts[-1] <= 2):
            cuts.append(i)
    return [round(i / fps, 3) for i in cuts]


def rhythm(path, beats=None, roi=None):
    """节奏指标：静止与低能量占比、最长静止段、瞬变（硬切）、快切段、分界与段落时长分布。"""
    f = gray_frames(path, roi, RATE)
    e = step_diffs(f)[1:]                       # e[k]：第 k 到 k+1 个取样（1/12 秒）的变化
    dur = len(f) / RATE

    def longest(mask):
        r = max(runs(mask), key=lambda ab: ab[1] - ab[0], default=None)
        return {"s": round((r[1] - r[0]) / RATE, 2), "at_s": round(r[0] / RATE, 2)} if r else {"s": 0.0, "at_s": None}

    cuts = hard_cuts(path, roi)
    # 大变化事件：取样差 >BIG 的连续段算一次，与瞬变合并（相距 <0.1 秒算同一次）
    events = sorted(set(cuts) | {round((a + 1) / RATE, 3) for a, _ in runs(e > BIG)})
    events = [t for i, t in enumerate(events) if i == 0 or t - events[i - 1] >= 0.1]
    inb = [False] * len(events)              # 快切段：某次大变化起 1.5 秒内共 ≥3 次，相邻两次相距 ≤1.5 秒的连成一段
    for i, t in enumerate(events):
        j = max(k for k in range(i, len(events)) if events[k] - t <= 1.5)
        if j - i >= 2:
            inb[i:j + 1] = [True] * (j - i + 1)
    bursts = []
    for t, b in zip(events, inb):
        if b and bursts and t - bursts[-1][1] <= 1.5:
            bursts[-1][1:] = [t, bursts[-1][2] + 1]
        elif b:
            bursts.append([t, t, 1])
    # 分界：约 0.4 秒内半数以上像素变化超过 24 级，或一次瞬变
    lag = 5
    area = np.array([(np.abs(f[k + lag].astype(np.int16) - f[k]) > 24).mean() for k in range(len(f) - lag)])
    bounds = sorted(set(cuts) | {round((a + 1 + int(np.argmax(e[a:b + lag - 1]))) / RATE, 3) for a, b in runs(area >= 0.5)})
    bounds = [t for i, t in enumerate(bounds) if 0.2 < t < dur - 0.2 and (i == 0 or t - bounds[i - 1] >= 0.2)]
    edges = [0.0] + bounds + [dur]
    out = {
        "duration_s": round(dur, 2), "sample_fps": RATE,
        "still_ratio": round(float((e < STILL).mean()), 3), "low_energy_ratio": round(float((e < LOW).mean()), 3),
        "longest_still": longest(e < STILL), "longest_low_energy": longest(e < LOW),
        "hard_cuts_s": cuts, "fast_cut_segments": [{"from_s": a, "to_s": b, "changes": n} for a, b, n in bursts],
        "boundaries_s": bounds,
        "detected_segments": spread(np.diff(edges)) if len(edges) > 2 else "单一段落：没有检测到分界",
    }
    if beats:
        out["storyboard_beats"] = spread(np.diff(beats))
    return out, e


def energy_chart(e, bucket, marks):
    """每 bucket 秒一行：平均取样差的对数长度条、静止占比、该段内的瞬变与快切段标记。"""
    n = max(1, int(round(bucket * RATE)))
    lines = [f"能量图（每行 {bucket} 秒；条长 ∝ log2(1+平均取样差)；切 = 瞬变，快 = 快切段）"]
    for k in range(0, len(e), n):
        seg, t0 = e[k:k + n], k / RATE
        bar = "█" * min(48, int(round(8 * np.log2(1 + seg.mean()))))
        tag = " ".join(name for name, ts in marks if any(t0 <= t < t0 + bucket for t in ts))
        lines.append(f"{t0:6.2f}s │{bar:<48}│ {seg.mean():5.2f}  静止 {int(round((seg < STILL).mean() * 100)):3d}%  {tag}")
    return "\n".join(lines)


def ground(path, every=0.5):
    """浅底留白：每 every 秒取一帧（480 宽），每通道量化成 16 级取最多的一格为底色，底色占比 = 与底色每通道差 ≤14 的像素比例。"""
    _, vw, vh = probe(path)
    sh = round(vh * 480 / vw / 2) * 2
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"fps={1 / every},scale=480:{sh}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    frames = np.frombuffer(raw, np.uint8).reshape(-1, sh * 480, 3)
    lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    rows = []
    for px in frames:
        q = (px // 16).astype(np.int32)
        key = q[:, 0] * 256 + q[:, 1] * 16 + q[:, 2]
        top = np.bincount(key).argmax()
        base = px[key == top].mean(axis=0)
        share = float((np.abs(px.astype(np.int16) - base).max(axis=1) <= 14).mean())
        lum = float(np.dot(lin(base / 255), [0.2126, 0.7152, 0.0722]))
        rows.append((lum, share, "#%02x%02x%02x" % tuple(int(round(v)) for v in base)))
    light = [r for r in rows if r[0] > 0.75]
    out = {"samples": len(rows), "light_frame_ratio": round(len(light) / max(1, len(rows)), 2)}
    if light:
        shares = np.array([r[1] for r in light])
        hexes = [r[2] for r in light]
        out.update({"ground_hex": max(set(hexes), key=hexes.count), "ground_share_median": round(float(np.median(shares)), 2),
                    "ground_share_p25": round(float(np.percentile(shares, 25)), 2)})
    return out


def opt(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def floats(s):
    return [float(x) for x in s.split(",") if x]


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    cmd, path = sys.argv[1], sys.argv[2]
    roi = tuple(int(v) for v in opt("--roi").split(",")) if opt("--roi") else None
    rise = float(opt("--rise", 6))
    if cmd == "motion":
        out = motion(path, float(opt("--thresh", 0.5)), roi)
    elif cmd == "onsets":
        out = {"onsets_s": onsets(path, rise)}
    elif cmd == "dark":
        out = dark(path, floats(opt("--at", "")), int(opt("--thresh", 20)))
    elif cmd == "loudest":
        out = loudest(path, floats(opt("--events", "")))
    elif cmd == "sync":
        out = sync(path, [e for e in opt("--events", "").split(",") if e], roi, rise)
    elif cmd == "rhythm":
        out, energy = rhythm(path, floats(opt("--beats", "")) or None, roi)
        if "--chart" in sys.argv:
            print(energy_chart(energy, float(opt("--bucket", 0.5)),
                               [("切", out["hard_cuts_s"]), ("快", [s["from_s"] for s in out["fast_cut_segments"]])]))
    elif cmd == "ground":
        out = ground(path)
    elif cmd == "beats":
        out = spread(np.diff(floats(path)))
    else:
        sys.exit(__doc__)
    print(json.dumps(out, ensure_ascii=False, indent=1))

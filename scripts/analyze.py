"""成片分析：画面变化、音频起音、近黑占比、音画同步。在装有 numpy 的 .venv 里运行，依赖 ffmpeg/ffprobe。

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

--thresh（motion）：帧间平均灰度差大于它算「在动」，默认 0.5；文字淡入、小元素要核对时降到 0.02。
--roi：只分析画面里的一块区域（原分辨率像素），小面积事件（如 28×20 的闪烁）用它测。
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


def frame_diffs(path, roi=None):
    _, vw, vh = probe(path)
    x, y, w, h = roi if roi else (0, 0, vw, vh)
    sw = min(W, w)
    sh = max(2, round(h * sw / w / 2) * 2)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"crop={w}:{h}:{x}:{y},scale={sw}:{sh}",
                          "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
    f = np.frombuffer(raw, np.uint8).reshape(-1, sh, sw).astype(np.int16)
    d = np.abs(np.diff(f, axis=0)).mean(axis=(1, 2))
    return np.concatenate([[0.0], d])  # d[i] = 第 i 帧相对第 i-1 帧的变化


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
    else:
        sys.exit(__doc__)
    print(json.dumps(out, ensure_ascii=False, indent=1))

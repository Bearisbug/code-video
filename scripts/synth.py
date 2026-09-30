"""按音效清单（cue JSON）合成配乐与音效，输出 48kHz 立体声 16-bit WAV。同一清单、同一 seed 输出逐字节一致。

用法: python synth.py cues.json out.wav        （在 uv 建的 .venv 里运行，只依赖 numpy）

清单格式（字段含义见 references/audio.md）:
{
  "duration": 10.0, "bpm": 120, "seed": 1,
  "bed": {"style": "pluck", "chords": ["C4 E4 G4", "A3 C4 E4"], "drums": true,
          "start": 0.5, "end": 9.5, "gain": 0.5,
          "automation": [[4.9, 5.0, 0.03], [5.0, 9.5, 1.2]]},
  "events": [{"t": 0.45, "sfx": "pop", "gain": 1.0, "pitch": 1.0, "dur": 0.3, "pan": 0.0}]
}
"""
import json
import sys
import wave

import numpy as np

SR = 48000
NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def hz(name):
    base, octave = name[:-1], int(name[-1])
    semi = NOTE[base[0].upper()] + base[1:].count("#") - base[1:].count("b")
    return 440.0 * 2 ** ((semi + 12 * (octave + 1) - 69) / 12)


def tt(dur):
    return np.arange(int(dur * SR)) / SR


def decay(t, rate):
    return np.exp(-t * rate)


def lowpass(x, cutoff):
    """一阶低通；cutoff 可为标量或逐样本数组（扫频用）。"""
    cutoff = np.broadcast_to(cutoff, x.shape)
    a = 1 - np.exp(-2 * np.pi * cutoff / SR)
    y, acc = np.empty_like(x), 0.0
    for i in range(x.size):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


# ---- 音效：每个函数返回单声道数组 ----
def sfx_impact(rng, dur=0.9, pitch=1.0):
    t = tt(dur)
    f = 50 * pitch * (1 + 2.5 * decay(t, 30))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * decay(t, 4.5)
    click = rng.standard_normal(t.size) * decay(t, 90) * 0.5
    return np.tanh(1.6 * (body + click))


def sfx_pop(rng, dur=0.25, pitch=1.0):
    t = tt(dur)
    f = 900 * pitch * (0.35 + 0.65 * decay(t, 18))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * decay(t, 16) * (1 - decay(t, 400))


def sfx_tick(rng, dur=0.05, pitch=1.0):
    t = tt(dur)
    return (np.sin(2 * np.pi * 3200 * pitch * t) + 0.4 * rng.standard_normal(t.size)) * decay(t, 160)


def sfx_blip(rng, dur=0.12, pitch=1.0):
    t = tt(dur)
    wave_ = np.sign(np.sin(2 * np.pi * 1000 * pitch * t)) * 0.5 + 0.5 * np.sin(2 * np.pi * 2000 * pitch * t)
    return wave_ * (t < dur * 0.8) * (1 - decay(t, 600)) * 0.6


def sfx_chime(rng, dur=1.2, pitch=1.0):
    t = tt(dur)
    f0 = 880 * pitch
    parts = [(1.0, 1.0, 3), (2.76, 0.5, 5), (5.4, 0.25, 8), (8.93, 0.12, 12)]
    return sum(a * np.sin(2 * np.pi * f0 * r * t) * decay(t, k) for r, a, k in parts) * 0.6


def sfx_whoosh(rng, dur=0.45, pitch=1.0):
    t = tt(dur)
    shape = np.sin(np.pi * t / dur) ** 2
    cutoff = 400 + 5000 * pitch * shape
    noise = rng.standard_normal(t.size)
    band = lowpass(noise, cutoff) - lowpass(noise, cutoff * 0.25)
    return band * shape * 2.5


def sfx_riser(rng, dur=1.0, pitch=1.0):
    t = tt(dur)
    ramp = (t / dur) ** 2
    tone = np.sin(2 * np.pi * np.cumsum(200 * pitch * (1 + 3 * ramp)) / SR)
    noise = lowpass(rng.standard_normal(t.size), 300 + 6000 * ramp)
    return (0.5 * tone + noise) * ramp * (1 - decay(dur - t, 60))


def sfx_glitch(rng, dur=0.15, pitch=1.0):
    t = tt(dur)
    steps = np.repeat(rng.standard_normal(t.size // 64 + 1), 64)[: t.size]
    return np.round(steps * 3) / 3 * (rng.random(t.size) > 0.2) * 0.6


def sfx_alarm(rng, dur=0.3, pitch=1.0):
    t = tt(dur)
    f = np.where((t * 20) % 2 < 1, 1000, 1750) * pitch
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * (1 - decay(t, 500)) * decay(t, 6) * 0.7


SFX = {k[4:]: v for k, v in globals().items() if k.startswith("sfx_")}


# ---- 音床 ----
def note_pluck(f, dur):
    t = tt(dur)
    return (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) + 0.12 * np.sin(6 * np.pi * f * t)) * decay(t, 7)


def note_pad(f, dur):
    t = tt(dur)
    env = np.minimum(1, t / 0.4) * np.minimum(1, (dur - t) / 0.4)
    return sum(np.sin(2 * np.pi * f * d * t) for d in (0.997, 1.0, 1.003)) / 3 * env


def note_chip(f, dur):
    t = tt(dur)
    return np.sign(np.sin(2 * np.pi * f * t)) * 0.4 * decay(t, 5)


def note_pulse(f, dur):
    """低八度正弦加少量锯齿泛音，暗色短促低音。"""
    t = tt(dur)
    f = f / 2
    saw = 2 * ((f * t) % 1) - 1
    return (np.sin(2 * np.pi * f * t) + 0.15 * saw) * decay(t, 6) * (1 - decay(t, 300))


def bed(spec, total, bpm, rng):
    out = np.zeros(int(total * SR))
    beat = 60 / bpm
    start, end = spec.get("start", 0.0), spec.get("end", total)
    chords = [[hz(n) for n in c.split()] for c in spec.get("chords", ["C4 E4 G4"])]
    style = spec.get("style", "pluck")
    bar, i = start, 0
    while bar < end:
        notes = chords[i % len(chords)]
        if style == "pad":
            seg = sum(note_pad(f, min(4 * beat, end - bar)) for f in notes) / len(notes)
            place(out, seg, bar)
        else:
            gen = {"chip": note_chip, "pulse": note_pulse}.get(style, note_pluck)
            step = beat if style == "pulse" else beat / 2
            k = 0
            while k * step < 4 * beat and bar + k * step < end:
                place(out, gen(notes[k % len(notes)], step * 1.5) * 0.5, bar + k * step)
                k += 1
        if spec.get("drums"):
            for b in range(4):
                tb = bar + b * beat
                if tb >= end:
                    break
                if b in (0, 2):
                    place(out, sfx_impact(rng, 0.35, 1.2) * 0.8, tb)
                if b in (1, 3):
                    place(out, lowpass(rng.standard_normal(int(0.15 * SR)), 3000) * decay(tt(0.15), 25) * 0.6, tb)
                place(out, np.diff(rng.standard_normal(int(0.05 * SR) + 1)) * decay(tt(0.05), 90) * 0.25, tb + beat / 2)
        bar += 4 * beat
        i += 1
    fade = np.ones_like(out)
    a, b = int(start * SR), int(end * SR)
    fade[:a] = 0
    fade[b:] = 0
    fade[a:a + int(0.3 * SR)] *= np.linspace(0, 1, len(fade[a:a + int(0.3 * SR)]))
    tail = fade[max(a, b - int(0.5 * SR)):b]
    tail *= np.linspace(1, 0, len(tail))
    return out * fade * automation(spec.get("automation", []), out.size) * spec.get("gain", 0.5)


def automation(windows, size, ramp=0.005):
    """[[起, 止, 增益], ...]：区间内音床乘以增益，两端各 5ms 线性过渡；区间外为 1。"""
    env = np.ones(size)
    r = int(ramp * SR)
    for start, end, gain in windows:
        a, b = int(round(start * SR)), int(round(end * SR))
        w = np.ones(size)
        w[a:b] = gain
        up = w[max(0, a - r):a]
        up[:] = np.linspace(1, gain, len(up))
        down = w[b:b + r]
        down[:] = np.linspace(gain, 1, len(down))
        env *= w
    return env


def place(buf, seg, at):
    s = int(round(at * SR))
    if s >= buf.size:
        return
    seg = seg[: buf.size - s]
    buf[s:s + seg.size] += seg


def main(cue_path, out_path):
    cue = json.load(open(cue_path, encoding="utf-8"))
    total, bpm = float(cue["duration"]), float(cue.get("bpm", 120))
    rng = np.random.default_rng(cue.get("seed", 1))
    left, right = np.zeros(int(total * SR)), np.zeros(int(total * SR))
    if cue.get("bed"):
        b = bed(cue["bed"], total, bpm, rng)
        left += b
        right += b
    for ev in cue.get("events", []):
        kind = ev["sfx"]
        if kind not in SFX:
            sys.exit(f"未知音效 {kind}，可用: {', '.join(sorted(SFX))}")
        kw = {"pitch": ev.get("pitch", 1.0)}
        if "dur" in ev:
            kw["dur"] = ev["dur"]
        seg = SFX[kind](rng, **kw) * ev.get("gain", 1.0)
        pan = ev.get("pan", 0.0)
        place(left, seg * np.sqrt((1 - pan) / 2) * np.sqrt(2), ev["t"])
        place(right, seg * np.sqrt((1 + pan) / 2) * np.sqrt(2), ev["t"])
    mix = np.tanh(np.stack([left, right], axis=1))
    peak = np.abs(mix).max() or 1.0
    mix = mix / peak * 10 ** (-3 / 20)
    with wave.open(out_path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype("<i2").tobytes())
    print(json.dumps({"out": out_path, "seconds": total, "events": len(cue.get("events", []))}, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])

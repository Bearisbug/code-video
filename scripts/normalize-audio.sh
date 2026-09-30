#!/usr/bin/env bash
# 两遍 loudnorm 把音频归一到目标响度与真峰值上限，输出 48kHz WAV；最后用 ebur128 复核。
# 用法: normalize-audio.sh <输入音频或视频> <输出.wav> [目标 LUFS，默认 -14] [真峰值上限 dBTP，默认 -2]
# 真峰值上限默认 -2：成片交付要求 ≤ -1 dBTP，AAC 编码会把真峰值抬高 0.1–1.4 dB（实测），留出余量。
# 输入与输出可以是同一个文件。
set -euo pipefail
in="$1"; out="$2"; target="${3:--14}"; tp="${4:--2}"

field() { sed -n "s/.*\"$1\" : \"\([^\"]*\)\".*/\1/p" <<<"$2" | head -1; }

pass1=$(ffmpeg -hide_banner -nostats -i "$in" -af "loudnorm=I=${target}:TP=${tp}:LRA=11:print_format=json" -f null - 2>&1 | sed -n '/^{/,/^}/p')
mi=$(field input_i "$pass1"); mtp=$(field input_tp "$pass1"); mlra=$(field input_lra "$pass1"); mth=$(field input_thresh "$pass1"); off=$(field target_offset "$pass1")

tmpd="$(mktemp -d -t normalize-audio)"; tmp="$tmpd/out.wav"
trap 'rm -rf "$tmpd"' EXIT
pass2=$(ffmpeg -hide_banner -nostats -y -i "$in" -vn -af "loudnorm=I=${target}:TP=${tp}:LRA=11:measured_I=${mi}:measured_TP=${mtp}:measured_LRA=${mlra}:measured_thresh=${mth}:offset=${off}:linear=true:print_format=json" -ar 48000 "$tmp" 2>&1)
mv -f "$tmp" "$out"
mode=$(field normalization_type "$pass2")

# 复核用 ebur128（loudnorm 自身的读数与 ebur128 可差 0.5 LU）
summary=$(ffmpeg -hide_banner -nostats -i "$out" -af ebur128=peak=true -f null - 2>&1 | sed -n '/Summary:/,$p')
oi=$(awk '$1=="I:"{print $2; exit}' <<<"$summary"); op=$(awk '$1=="Peak:"{print $2; exit}' <<<"$summary")
if awk -v o="$oi" -v t="$target" 'BEGIN{d=o-t; exit !(d > 0.5 || d < -0.5)}'; then
  echo "⚠️ 输出 ${oi} LUFS，偏离目标 ${target} 超过 0.5 LU（loudnorm 模式：${mode}）。多为最响事件相对音床太响：降低最响事件的 gain 或提高音床 gain，重新合成后再归一。" >&2
fi
if [ "$mode" = "dynamic" ]; then
  lim=$(awk -v a="$tp" -v b="$target" 'BEGIN{print a-b}')
  echo "⚠️ loudnorm 进入 dynamic 模式，事件之间的电平差会被压平。linear 模式要求输入真峰值减响度不超过 ${lim} dB（本次 ${mtp} dBTP、${mi} LUFS）且 LRA 不超过 11（本次 ${mlra}）：降低真峰值最高的音效（常见是 impact、whoosh）的 gain 或提高音床 gain，重新合成后再归一。" >&2
fi
printf '{"input_lufs": %s, "output_lufs": %s, "output_true_peak_dbtp": %s, "loudnorm_mode": "%s"}\n' "$mi" "$oi" "$op" "$mode"

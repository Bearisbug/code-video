#!/usr/bin/env bash
# code-video 自检。
#   bash check.sh                 检查本 Skill 结构：链接、规则卡与 catalog、卡号引用、风格包、脚本语法、品牌区块检查夹具
#   bash check.sh <视频项目目录>   检查视频项目是否遵守护栏，并复核 renders/ 成片的帧数与响度
# 不开 pipefail：检查项大量用 `echo … | grep -q`，grep 命中即退出会让 echo 收到 SIGPIPE，
# pipefail 下整条管道随机判为失败，同一输入两次运行结论不同。
set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"
fail=0; warn=0
ok()  { echo "✅ $*"; }
bad() { echo "❌ $*"; fail=$((fail + 1)); }
wrn() { echo "⚠️  $*"; warn=$((warn + 1)); }

self_check() {
  cd "$ROOT" || exit 2
  # frontmatter
  if head -1 SKILL.md | grep -q '^---$' && grep -q '^name: code-video$' SKILL.md && grep -q '^description: .' SKILL.md; then
    ok "SKILL.md frontmatter"
  else bad "SKILL.md frontmatter 缺 name 或 description"; fi

  # 相对链接
  local broken=0 f link target
  while IFS= read -r f; do
    while IFS= read -r link; do
      case "$link" in http*|\#*|mailto:*) continue ;; esac
      target="$(dirname "$f")/${link%%#*}"
      [ -e "$target" ] || { bad "断链 ${f}: ${link}"; broken=1; }
    done < <(grep -o '](\([^)]*\))' "$f" | sed 's/^](//; s/)$//')
  done < <(find SKILL.md references -name '*.md')
  [ "$broken" = 0 ] && ok "相对链接全部可解析"

  # 规则卡：前缀与文件对应、唯一、登记进 catalog
  local map="HF:hyperframes.md DET:determinism.md CRAFT:craft.md AUD:audio.md FONT:fonts.md MANIM:manim.md"
  local cards; cards=$(grep -H -o '^### [A-Z]*-[0-9]\{3\} ·' references/*.md | sed 's/:### / /; s/ ·$//')
  local dup; dup=$(echo "$cards" | awk '{print $2}' | sort | uniq -d)
  [ -z "$dup" ] && ok "卡 ID 唯一（$(echo "$cards" | wc -l | tr -d ' ') 张）" || bad "重复卡 ID: $dup"
  local file id prefix want before=$fail
  while read -r file id; do
    prefix=${id%%-*}
    want=$(echo "$map" | tr ' ' '\n' | awk -F: -v p="$prefix" '$1==p{print $2}')
    [ "references/${want}" = "$file" ] || bad "${id} 在 ${file}，前缀 ${prefix} 应在 references/${want}"
    grep -q "^| ${id} |" references/00-catalog.md || bad "${id} 未登记进 00-catalog.md"
  done <<< "$cards"
  local cid
  for cid in $(grep -o '^| [A-Z]*-[0-9]\{3\} |' references/00-catalog.md | tr -d '| '); do
    echo "$cards" | awk '{print $2}' | grep -qx "$cid" || bad "catalog 登记了不存在的卡 ${cid}"
  done
  [ "$fail" = "$before" ] && ok "规则卡与 catalog 对账一致"

  # 反引号里的卡号引用都必须存在
  local ref missing=0
  for ref in $(grep -rho '`[A-Z]*-[0-9]\{3\}`' SKILL.md references | tr -d '`' | sort -u); do
    echo "$cards" | awk '{print $2}' | grep -qx "$ref" || { bad "引用了不存在的卡 ${ref}"; missing=1; }
  done
  [ "$missing" = 0 ] && ok "卡号引用全部存在"

  # 风格包：必备标题、元信息字段、索引登记
  local pack id2 h before2=$fail
  for pack in references/styles/*.md; do
    [ "$(basename "$pack")" = "00-index.md" ] && continue
    id2=$(basename "$pack" .md)
    head -1 "$pack" | grep -q "^# ${id2} · " || bad "${pack} 标题行应以「# ${id2} · 」开头"
    for h in "| id |" "| 渲染层 |" "| 画幅 |" "| 时长 |" "| BPM |" "| 适用用途 |" "| 状态 |" "| 证据 |"; do
      grep -qF "$h" "$pack" || bad "${pack} 元信息缺字段 ${h}"
    done
    local prev=0 n
    for h in "## 风格语法" "## 参考节拍（仅示例）" "## 题材禁用清单" "## 技术配方" "## 风格提示词" "## 翻车点" "## 验收清单"; do
      n=$(grep -n "^${h}\$" "$pack" | head -1 | cut -d: -f1)
      if [ -z "$n" ]; then bad "${pack} 缺章节 ${h}"
      elif [ "$n" -lt "$prev" ]; then bad "${pack} 章节顺序错误：${h}"
      else prev=$n; fi
    done
    grep -q "](${id2}.md)" references/styles/00-index.md || bad "${id2} 未登记进 styles/00-index.md"
  done
  [ "$fail" = "$before2" ] && ok "风格包章节、元信息、索引登记齐全"

  # 脚本
  bash -n scripts/normalize-audio.sh && ok "normalize-audio.sh 语法" || bad "normalize-audio.sh 语法错误"
  node --check scripts/fetch-font.mjs && ok "fetch-font.mjs 语法" || bad "fetch-font.mjs 语法错误"
  if [ -x "${PWD}/.venv/bin/python" ]; then
    .venv/bin/python -m py_compile scripts/synth.py && ok "synth.py 语法" || bad "synth.py 语法错误"
  else
    wrn "未找到 .venv，跳过 synth.py 语法检查（在装有 numpy 的 venv 里实跑一次即可）"
  fi
  if [ -x "${PWD}/.venv/bin/python" ]; then
    .venv/bin/python -m py_compile scripts/analyze.py && ok "analyze.py 语法" || bad "analyze.py 语法错误"
  fi

  # 品牌区块检查夹具（CRAFT-007）：正例零 ❌；反例各自报出对应问题；上级没有品牌目录时不检查
  FX=$(mktemp -d); trap 'rm -rf "$FX"' EXIT
  mkdir -p "$FX/repo/brand/promo/x" "$FX/plain"
  echo '# 品牌' > "$FX/repo/brand/DESIGN.md"
  echo '{"meta":{"modes":["light","dark"],"defaultMode":"light","roles":{"accent":"semantic.color.action.primary","text.primary":"semantic.color.text.primary"}}}' > "$FX/repo/brand/tokens.json"
  echo '{"semantic":{"color":{"action":{"primary":{"$value":"#1A1D22"}},"text":{"primary":{"$value":"#1A1D22"}}}}}' > "$FX/repo/brand/tokens.resolved.json"
  echo '{"semantic":{"color":{"action":{"primary":{"$value":"#E8EAED"}},"text":{"primary":{"$value":"#F6F7F9"}}}}}' > "$FX/repo/brand/tokens.resolved.dark.json"
  local cmt="/* node -e '…' ../.. accent text.primary@dark */" res before3=$fail
  fx_brand() {  # $1 = 视频项目目录；$2 = :root 里的区块内容；$3 = 期望输出含的片段（"无输出" = 不该有任何 CRAFT-007 行）
    printf '<style>\n:root {\n%s\n}\n</style>\n' "$2" > "$1/index.html"
    res=$(cd "$1" && fail=0 warn=0 && brand_tokens_check)
    if [ "$3" = "无输出" ]; then [ -z "$res" ] || bad "CRAFT-007 夹具误报：$res"
    else printf '%s\n' "$res" | grep -qF "$3" || bad "CRAFT-007 夹具没报出「$3」，实际：$res"; fi
  }
  local ok_block; ok_block=$(printf '/* brand:tokens */\n%s\n--brand-accent: #1A1D22;\n--brand-text-primary-dark: #F6F7F9;\n/* /brand:tokens */' "$cmt")
  fx_brand "$FX/repo/brand/promo/x" "$ok_block" "✅ brand:tokens 区块 2 个变量"
  fx_brand "$FX/repo/brand/promo/x" "--brand-accent: #1A1D22;" "缺 /* brand:tokens */"
  fx_brand "$FX/repo/brand/promo/x" "$(printf '/* brand:tokens — %s\n--brand-accent: #1A1D22;\n/* /brand:tokens */' "$cmt")" "各自单独成行"
  fx_brand "$FX/repo/brand/promo/x" "$(printf '/* brand:tokens */\n--brand-accent: #1A1D22;\n/* /brand:tokens */')" "下一行要是一条注释"
  fx_brand "$FX/repo/brand/promo/x" "${ok_block/\#F6F7F9/#FFFFFF}" "tokens 里是 #F6F7F9"
  fx_brand "$FX/repo/brand/promo/x" "${ok_block/--brand-text-primary-dark/--brand-dark-text-primary}" "对不上 meta.roles"
  fx_brand "$FX/plain" "--brand-accent: #1A1D22;" "无输出"
  [ "$fail" = "$before3" ] && ok "品牌区块检查夹具：正例通过，反例全部报出（CRAFT-007）"
}

# 品牌参数区块（CRAFT-007）：在视频项目目录内调用。上级目录有 brand/DESIGN.md 时，index.html 必须有单独成行的
# /* brand:tokens */ … /* /brand:tokens */ 区块，起始标记下一行是命令注释，其余行只放 --brand-* 变量；
# 品牌目录是 profile-2 tokens 时按「--brand-<角色>[-<模式>]」逐个核对变量值。
brand_tokens_check() {
  local line
  while IFS= read -r line; do
    case "$line" in
      OK\ *) ok "${line#OK }" ;;
      BAD\ *) bad "${line#BAD }" ;;
      WARN\ *) wrn "${line#WARN }" ;;
    esac
  done < <(node - 2>&1 <<'JS'
const fs = require("fs"), p = require("path");
const out = (k, m) => console.log(`${k} ${m}（CRAFT-007）`);
try {
  let brand = null;
  for (let d = process.cwd(); ; d = p.dirname(d)) {
    if (fs.existsSync(p.join(d, "brand", "DESIGN.md"))) { brand = p.join(d, "brand"); break; }
    if (d === p.dirname(d)) break;
  }
  if (!brand) process.exit(0);
  const rel = p.relative(process.cwd(), brand) || ".";
  const lines = fs.readFileSync("index.html", "utf8").split("\n");
  const s = lines.findIndex(l => l.trim() === "/* brand:tokens */");
  const e = s < 0 ? -1 : lines.findIndex((l, i) => i > s && l.trim() === "/* /brand:tokens */");
  if (s < 0 || e < 0) {
    out("BAD", lines.some(l => l.includes("brand:tokens"))
      ? "brand:tokens 区块的起止标记要各自单独成行，逐字写成 /* brand:tokens */ 与 /* /brand:tokens */"
      : `上级目录有品牌目录 ${rel}，index.html 缺 /* brand:tokens */ … /* /brand:tokens */ 区块`);
    process.exit(0);
  }
  if (!(e > s + 1 && /^\/\*.*\S.*\*\/$/.test(lines[s + 1].trim()) && !lines[s + 1].includes("brand:tokens")))
    out("BAD", "brand:tokens 起始标记的下一行要是一条注释，写这次运行的完整读取命令");
  const vars = [];
  for (const l of lines.slice(s + 2, e)) {
    if (!l.trim()) continue;
    const m = l.match(/^\s*(--brand-[A-Za-z0-9-]+)\s*:\s*([^;]+?)\s*;\s*$/);
    if (m) vars.push([m[1], m[2]]); else out("BAD", `brand:tokens 区块里有命令输出以外的行：${l.trim()}`);
  }
  if (!vars.length) { out("BAD", "brand:tokens 区块里没有 --brand-* 变量"); process.exit(0); }
  const tf = p.join(brand, "tokens.json");
  const t = fs.existsSync(tf) ? JSON.parse(fs.readFileSync(tf, "utf8")) : null;
  if (!t || !t.meta || !t.meta.roles) { out("WARN", `${rel} 不是 profile-2 tokens，区块值未机械核对，按 DESIGN.md 写明的来源人工核对`); process.exit(0); }
  const map = {};
  for (const [k, v] of Object.entries(t.meta.roles)) {
    if (typeof v !== "string") continue;
    const base = "--brand-" + k.replace(/\./g, "-");
    map[base] = [k, null];
    for (const md of t.meta.modes || []) map[`${base}-${md}`] = [k, md];
  }
  let good = 0;
  for (const [name, got] of vars) {
    if (!map[name]) { out("BAD", `${name} 对不上 meta.roles 里的角色，变量名应为 --brand-<角色>[-<模式>]`); continue; }
    const [k, md] = map[name];
    const f = !md || md === t.meta.defaultMode ? "tokens.resolved.json" : `tokens.resolved.${md}.json`;
    let want;
    try { want = t.meta.roles[k].split(".").reduce((o, x) => o[x], JSON.parse(fs.readFileSync(p.join(brand, f), "utf8"))).$value; } catch { want = undefined; }
    if (want === undefined) out("BAD", `${name}：读不到 ${rel}/${f} 里的 ${t.meta.roles[k]}`);
    else if (String(want).toLowerCase() !== got.toLowerCase()) out("BAD", `${name} 是 ${got}，tokens 里是 ${want}，重跑区块注释里的命令并整体替换区块`);
    else good++;
  }
  if (good === vars.length) out("OK", `brand:tokens 区块 ${good} 个变量与 ${rel} 的 tokens 一致`);
} catch (err) { out("BAD", `品牌区块检查出错：${err.message}`); }
JS
)
}

project_check() {
  local P="$1"
  [ -d "$P" ] || { echo "目录不存在: $P"; exit 2; }
  cd "$P" || exit 2
  echo "检查视频项目: $(pwd)"
  [ -f storyboard.md ] && ok "storyboard.md 存在（CRAFT-001）" || bad "缺 storyboard.md（CRAFT-001）"

  if [ -f index.html ]; then
    grep -q '"hyperframes": "0.8.96"' package.json 2>/dev/null && ok "hyperframes 锁定 0.8.96（HF-001）" || bad "package.json 未精确锁定 hyperframes 0.8.96（HF-001）"
    # 外链检查只去掉 HTML 注释；其余检查再去掉 JS/CSS 注释（/* */ 与行尾 //，不碰 URL 里的 //）
    local html_body body
    html_body=$(perl -0777 -pe 's/<!--.*?-->//gs' index.html)
    body=$(printf '%s' "$html_body" | perl -0777 -pe 's{/\*.*?\*/}{}gs; s{(?<![:"'"'"'\\])//[^\n]*}{}g')
    # w3.org 的 SVG/XLink/XHTML 命名空间只是标识字符串，不联网
    echo "$html_body" | grep -oE 'https?://[^"'"'"' )>]+' | grep -vE '^http://www\.w3\.org/(2000/svg|1999/xlink|1999/xhtml)' | grep -q . \
      && bad "index.html 含外链，渲染时会联网（HF-007）" || ok "无外链（HF-007）"
    echo "$body" | grep -qE 'Math\.random|Date\.now|performance\.now|requestAnimationFrame|setTimeout|setInterval' \
      && bad "含墙钟时间、未设种子随机或定时器（DET-001）" || ok "无墙钟与定时器（DET-001）"
    echo "$body" | grep -qE 'repeat:[[:space:]]*-1|animation[^;{}]*infinite|iteration-count[[:space:]]*:[[:space:]]*infinite' && bad "含无限循环（DET-001）" || ok "无无限循环（DET-001）"
    echo "$body" | grep -qE 'transition[[:space:]]*:' && bad "含 CSS transition（DET-002）" || ok "无 CSS transition（DET-002）"
    echo "$body" | perl -0777 -ne 'exit(/::(before|after)[^{]*\{[^}]*animation/s ? 0 : 1)' \
      && bad "伪元素上有 CSS 动画（DET-003）" || ok "无伪元素动画（DET-003）"
    echo "$body" | perl -ne '$f = 1 if /font(-family)?\s*:[^;{}]*(PingFang|Hiragino|Microsoft YaHei|SimHei|Heiti|Courier New|Arial|Helvetica|Times New Roman|Georgia|Menlo|Monaco|Consolas|Segoe UI|SF Pro)/i; END { exit($f ? 0 : 1) }' \
      && bad "字体栈里有系统字体名，渲染时会联网下载替代字体（FONT-001）" || ok "字体栈无系统字体名（FONT-001）"
    if echo "$body" | grep -qiE '<link[^>]+\.css|@import'; then
      bad "用 <link> 或 @import 引入了样式表；字体必须内联 @font-face，否则渲染时会联网下载（FONT-001）"
    fi
    if echo "$html_body" | grep -qE 'font-family[[:space:]]*:|font[[:space:]]*:[^;]*[0-9]px'; then
      echo "$html_body" | perl -0777 -ne 'exit(/\@font-face\s*\{[^}]*url\(\s*["\x27]?((\.\/)?fonts\/|data:font\/)/s ? 0 : 1)' \
        && ok "@font-face 已内联并指向 fonts/（FONT-001）" || bad "用了字体但 index.html 里没有指向 fonts/ 的内联 @font-face（FONT-001）"
    fi
    if [ -d .hf-font-cache ] && [ -n "$(find .hf-font-cache -type f 2>/dev/null | head -1)" ]; then
      bad ".hf-font-cache 里有文件：渲染时联网下载了字体（FONT-001）"
    fi
    echo "$body" | perl -ne 'exit 1 if /<audio\b(?![^>]*\bid=)/' && ok "<audio> 都有 id（HF-004）" || bad "有 <audio> 缺 id，成片会无声（HF-004）"
    brand_tokens_check
  elif ls ./*.py >/dev/null 2>&1; then
    local py; py=$(cat ./*.py | perl -pe 's/#.*$//')
    ok "Manim 项目，检查场景文件"
    if echo "$py" | grep -qE 'random\.|np\.random'; then
      echo "$py" | grep -qE 'random\.seed\(' && echo "$py" | grep -qE 'np\.random\.seed\(|numpy\.random\.seed\(' \
        && ok "随机数已设种子（MANIM-004）" || bad "用了随机数但没有同时设 random.seed 与 np.random.seed（MANIM-004）"
    fi
    echo "$py" | grep -qiE 'PingFang|Hiragino|Microsoft YaHei|SimHei|Heiti' && bad "使用了系统字体（FONT-002）" || ok "无系统字体（FONT-002）"
    if echo "$py" | perl -CSD -ne '$c = 1 if /\p{Han}/; $t = 1 if /\bText\(/; END { exit($c && $t ? 0 : 1) }'; then
      echo "$py" | grep -q 'register_font' && ok "中文文字已注册字体（FONT-002）" || bad "有中文 Text 但没有 register_font（FONT-002）"
    fi
    echo "$py" | grep -qE 'self\.play\(.*run_time[[:space:]]*=[[:space:]]*[0-9.]+[[:space:]]*[,)]|self\.wait\([[:space:]]*[0-9.]+[[:space:]]*[,)]' \
      && bad "run_time 或 wait 直接写了秒数，会按帧取整漂拍（MANIM-004）" || ok "未直接用秒数排时间（MANIM-004）"
  else
    bad "既没有 index.html 也没有 Manim 场景文件"
  fi

  # 期望帧数：HyperFrames 项目取组合根元素的 data-duration × data-fps；否则按容器时长 × 帧率取整
  local root_frames=""
  if [ -f index.html ]; then
    root_frames=$(perl -0777 -ne 'if (/<[^>]*data-composition-id[^>]*>/s) { my $t = $&; my ($d) = $t =~ /data-duration="([\d.]+)"/; my ($f) = $t =~ /data-fps="([\d.]+)"/; printf("%d", $d * $f + 0.5) if $d && $f }' index.html)
  fi
  local mp4 fr dur rate frames expect sum I peak
  for mp4 in renders/*.mp4; do
    [ -e "$mp4" ] || { wrn "renders/ 下没有成片，跳过成片复核"; break; }
    fr=$(ffprobe -v error -select_streams v:0 -count_frames -show_entries stream=nb_read_frames,r_frame_rate -of csv=p=0 "$mp4")
    rate=${fr%%,*}; frames=${fr##*,}
    dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$mp4")
    expect=${root_frames:-$(awk -v d="$dur" -v r="$rate" 'BEGIN{split(r,a,"/"); printf "%d", d*a[1]/a[2]+0.5}')}
    if [ "$frames" -eq "$expect" ]; then ok "${mp4}: ${frames} 帧，与期望一致（时长 ${dur}s × ${rate}）"
    else bad "${mp4}: 帧数 ${frames}，期望 ${expect}（组合时长 × fps）"; fi
    if ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$mp4" | grep -q .; then
      sum=$(ffmpeg -hide_banner -nostats -i "$mp4" -af ebur128 -f null - 2>&1 | sed -n '/Summary:/,$p')
      I=$(awk '$1=="I:"{print $2; exit}' <<< "$sum")
      # 真峰值取 loudnorm 的两位小数读数：ebur128 只有一位小数，−0.96 会显示成 −1.0 而误判通过
      peak=$(ffmpeg -hide_banner -nostats -i "$mp4" -af loudnorm=print_format=json -f null - 2>&1 | sed -n 's/.*"input_tp" : "\([^"]*\)".*/\1/p' | head -1)
      if awk -v i="$I" -v p="$peak" 'BEGIN{exit !(i >= -15 && i <= -13 && p <= -1.0)}'; then ok "${mp4}: ${I} LUFS，真峰值 ${peak} dBTP（AUD-004）"
      else bad "${mp4}: ${I} LUFS，真峰值 ${peak} dBTP，超出 −14±1 LUFS 或 −1 dBTP（AUD-004）"; fi
    else
      wrn "${mp4}: 无音轨"
    fi
  done
}

if [ $# -eq 0 ]; then self_check; else project_check "$1"; fi
echo "—— ${fail} 个 ❌，${warn} 个 ⚠️"
[ "$fail" -eq 0 ]

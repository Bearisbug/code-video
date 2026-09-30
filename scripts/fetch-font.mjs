#!/usr/bin/env node
// 从 Google Fonts 下载 woff2 到项目本地，并把 @font-face 直接写进组合文件的 <style>。
// 在视频项目根目录运行:
//   node fetch-font.mjs --family "Noto Sans SC" --weights 400,900 [--text-file fonts/chars.txt] [--out fonts] [--html index.html]
//   --text-file  只下载文件里出现过的字符（CJK 必用，体积从十几 MB 降到几十 KB）；省略时下载完整拉丁子集
//   --html       写入哪个组合文件，默认 index.html；在第一个 <style> 里维护 /* fonts:<slug> */ … /* /fonts:<slug> */ 区块，重复运行会替换该区块
// HyperFrames 0.8.96 只识别 HTML 里直接写的 @font-face；用 <link> 引入的字体会被当成缺失，渲染时改去 Google Fonts 下载并覆盖本地文件。
// 只允许用于 references/fonts.md 登记过许可证的家族。网络请求走 curl，以便继承 HTTPS_PROXY。
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const args = process.argv.slice(2);
const arg = (k, d) => { const i = args.indexOf(`--${k}`); return i >= 0 ? args[i + 1] : d; };
const family = arg("family");
const weights = (arg("weights", "400")).split(",").map((w) => w.trim()).filter(Boolean);
const textFile = arg("text-file");
const out = arg("out", "fonts");
const html = arg("html", "index.html");
if (!family) { console.error('缺少 --family，例如 --family "Noto Sans SC"'); process.exit(2); }
if (!existsSync(html) || !/<style[^>]*>/.test(readFileSync(html, "utf8"))) {
  console.error(`${html} 不存在或没有 <style>，先按 flow-setup 建好组合文件骨架`); process.exit(2);
}

const slug = family.toLowerCase().replace(/[^a-z0-9]+/g, "-");
const params = new URLSearchParams({ family: `${family}:wght@${weights.join(";")}`, display: "block" });
if (textFile) {
  const chars = [...new Set([...readFileSync(textFile, "utf8")].filter((c) => c.trim()))].join("");
  params.set("text", chars);
}
const UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36";
const curl = (url) => execFileSync("curl", ["-sSfL", "--retry", "3", "--retry-all-errors", "--max-time", "60", "-A", UA, url]);

const css = curl(`https://fonts.googleapis.com/css2?${params.toString().replace(/\+/g, "%20")}`).toString();
const faces = [...css.matchAll(/@font-face\s*{([^}]*)}/g)].map((m) => m[1]);
if (!faces.length) { console.error("Google Fonts 没有返回 @font-face，检查家族名与字重是否存在"); process.exit(1); }

mkdirSync(out, { recursive: true });
// 可变字体会让多个字重指向同一个 URL：同一 URL 只下载一次，字重合并成范围
const byUrl = new Map();
for (const body of faces) {
  const weight = Number((body.match(/font-weight:\s*(\d+)/) || [])[1] || 400);
  const style = (body.match(/font-style:\s*(\w+)/) || [])[1] || "normal";
  const url = (body.match(/url\((https:[^)]+)\)/) || [])[1];
  const range = (body.match(/unicode-range:\s*([^;]+);/) || [])[1];
  const face = byUrl.get(url) || { style, url, range, weights: [] };
  face.weights.push(weight);
  byUrl.set(url, face);
}
let n = 0;
const blocks = [...byUrl.values()].map((f) => {
  const lo = Math.min(...f.weights), hi = Math.max(...f.weights);
  const file = `${slug}-${lo}${hi > lo ? `-${hi}` : ""}-${++n}.woff2`;
  writeFileSync(join(out, file), curl(f.url));
  return `  @font-face { font-family: "${family}"; font-style: ${f.style}; font-weight: ${hi > lo ? `${lo} ${hi}` : lo}; font-display: block; src: url("${join(out, file)}") format("woff2");${f.range ? ` unicode-range: ${f.range};` : ""} }`;
});

const begin = `/* fonts:${slug} */`, end = `/* /fonts:${slug} */`;
const block = `  ${begin}\n${blocks.join("\n")}\n  ${end}`;
let doc = readFileSync(html, "utf8");
const i = doc.indexOf(begin), j = doc.indexOf(end);
doc = i >= 0 && j > i
  ? doc.slice(0, i).replace(/[ \t]*$/, "") + block + doc.slice(j + end.length)
  : doc.replace(/<style[^>]*>/, (m) => `${m}\n${block}`);
writeFileSync(html, doc);
console.log(JSON.stringify({ family, html, files: blocks.length }));

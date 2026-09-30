<h1 align="center">code-video</h1>

<p align="center">An Agent Skill for making videos with code: motion graphics, brand intros, product promos and math explainers, rendered to MP4 with synthesized music and sound effects.</p>

<p align="center"><b>English</b> · <a href="README.zh-CN.md">简体中文</a></p>

---

`code-video` guides an AI coding agent from a one-line request to a verified MP4. The agent writes a storyboard and waits for your confirmation, picks a style pack, builds an HTML composition (rendered frame by frame by [HyperFrames](https://github.com/heygen-com/hyperframes)) or a [Manim](https://www.manim.community/) scene, synthesizes the soundtrack, renders, and then checks frame count, loudness, audio-visual sync and style against a checklist.

The skill text is written in Chinese. You can talk to the agent in any language.

## What it covers

| Task | Where the agent starts |
| --- | --- |
| Any new video: brief → storyboard → build → render → verify | [flow-make](references/flow-make.md) |
| Choosing a look | [Style index](references/styles/00-index.md) |
| Project setup, pinned versions, fonts | [flow-setup](references/flow-setup.md), [HF-001](references/hyperframes.md), [FONT-001](references/fonts.md) |
| Frame-accurate animation that never drifts | [Determinism rules](references/determinism.md) |
| Storyboard, text size, beat grid, brand colors | [Craft rules](references/craft.md) |
| Music, sound effects, loudness | [Audio rules](references/audio.md) |
| Formulas, geometry, algorithms | [Manim tier](references/manim.md) |
| Acceptance and delivery | [flow-verify](references/flow-verify.md) |

Out of scope: AI-generated footage (text-to-video models), live-action editing, TTS narration, and in-app UI animation.

## How it works

- **Every frame is a pure function of time.** Wall-clock time, unseeded randomness, timers, `requestAnimationFrame` loops and CSS transitions are banned; HyperFrames seeks each frame and the result is reproducible.
- **Pinned toolchain with guardrails.** HyperFrames is pinned to 0.8.96 and installed per project. Telemetry and automatic skill installation are switched off, and snapshots never send frames to external models.
- **Nothing is fetched at render time.** Fonts are subset and embedded as inline `@font-face`, and libraries load from `node_modules`. A render that downloads anything fails verification.
- **Style packs are measured, not described.** Each pack gives hex values, font sizes at 1080p, easing parameters, timing and sound cues, plus a list of the source work's subjects that must not be copied.
- **Verification is mechanical first.** `check.sh` checks the skill itself and any video project; `analyze.py` measures motion, audio onsets, sync offsets, dark-pixel ratio and event loudness on the final MP4.

## What's inside

```text
SKILL.md                 entry: scope, red lines, routing
check.sh                 self-check (no args) or project check (bash check.sh <project>)
references/              32 rule cards (HF, DET, CRAFT, AUD, FONT, MANIM), 3 flows, catalog, conventions
references/styles/       style packs and index
scripts/fetch-font.mjs   download registered fonts from Google Fonts, subset CJK, inline @font-face
scripts/synth.py         synthesize a music bed and 9 sound effects from a cue sheet (deterministic)
scripts/normalize-audio.sh  two-pass loudnorm to −14 LUFS / −2 dBTP ceiling, verified with ebur128
scripts/analyze.py       motion spans, onsets, sync offsets, dark ratio, loudest events
```

| Style pack | Look | Renderer |
| --- | --- | --- |
| `shape-morph` | one flat shape morphing through a story, paper grain, circular color reveals | SVG/DOM + GSAP MorphSVG |
| `fui-hud` | cinematic sci-fi HUD: monochrome cyan wireframe, bloom, lock-on switch to amber | Three.js + DOM |
| `mascot-story` | a mascot tells a problem → solution story, grain and line boil, typewriter captions | SVG/DOM + canvas grain |

Every pack gives numbers from a frame-by-frame teardown or source code, with recipes tested on HyperFrames 0.8.96. `mascot-story` is marked `blind-tested`: an agent given only the skill and an unrelated subject passed its checklist. `shape-morph` and `fui-hud` are still `draft`.

## Install

Claude Code, available in every project:

```sh
git clone --depth 1 https://github.com/Bearisbug/code-video.git ~/.claude/skills/code-video
```

Claude Code, one project only: clone into `<project>/.claude/skills/code-video`. For other agents that read `SKILL.md` skills, put the folder in that agent's skills directory.

## Requirements

| Tool | Needed for |
| --- | --- |
| Node.js 22+ and npm | HyperFrames (installed per video project), `fetch-font.mjs` |
| ffmpeg 8.x with `drawtext` and `libass` | encoding, contact sheets, loudness checks |
| uv, Python 3.12 | `synth.py` and `analyze.py` (numpy only), Manim tier |
| Manim CE 0.21 (optional) | math explainers; needs `cairo`, `pango`, `pkgconf`; LaTeX optional (`MathTypst` works without it) |

The first HyperFrames render downloads its pinned chrome-headless-shell (about 207 MB) once; the skill reuses it across projects.

## Usage

Ask the agent in plain language, for example:

- "Make a 10-second brand intro for our budgeting app, one shape morphing into the next, ending on the app name. Add music and sound."
- "A 10-second sci-fi HUD teaser: our code-review tool scans a huge codebase and locks onto a hidden race condition."
- "A 20-second promo for our fitness app where a cute mascot tells the story, with grainy paper texture and typewriter captions."
- "A 20-second explainer proving 1 + 2 + … + n = n(n+1)/2 with block puzzles, with a Chinese title and light background music."

## Validation

```sh
bash check.sh                      # skill: links, rule cards vs catalog, card references, style pack sections, script syntax
bash check.sh /path/to/project     # project: pinned version, no network, determinism patterns, fonts, frame count, loudness
```

The skill was developed with a blind-test loop: agents that had only the skill and a task produced 13 videos across three rounds, and every rule change was re-checked against earlier tasks. A mechanical pass does not prove visual quality; the style pack checklists and a contact sheet review cover that.

## License

Skill text and scripts are released under the [MIT License](LICENSE). Nothing third-party is bundled: HyperFrames (Apache-2.0), GSAP (GreenSock Standard License), Three.js (MIT), Manim (MIT) and fonts (SIL OFL 1.1) are installed or downloaded by the user under their own terms. The `shape-morph` and `fui-hud` packs describe styles measured from a third-party showcase video (author unconfirmed); they contain parameters, not footage.

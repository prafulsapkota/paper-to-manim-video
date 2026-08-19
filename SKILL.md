---
name: paper-to-manim-video
description: >
  Use when a user wants to create an animated explainer video from a research
  paper. Triggers on: "make a video from this paper", "animate this research",
  "explain this paper as a video", "create a manim video for this paper",
  "turn this PDF into an explainer video", "visualise this paper", or any
  request combining a research paper with video, animation, or visual explanation.
  Also triggers when the user provides an arXiv URL, OpenReview link, ACL
  Anthology link, Semantic Scholar link, or any URL to a paper and wants a video.

  Uses 3b1b's manimgl (https://github.com/3b1b/manim) as the animation engine.
  The LLM (coding agent) writes the manim Python code. Output is a rendered MP4.

  Always use this skill when the user provides a paper (file OR URL) AND wants
  a video — even if they say "short clip", "animation", "slides-style video", or similar.
---

# Research Paper → Manim Explainer Video

## Overview

You are the coding agent that writes the animation. This skill pipelines:

```
Paper input: file path OR URL
      │
      ├─ URL? → [0] download_paper.py  (zero tokens, pure Python)
      │              Resolves arXiv / OpenReview / ACL / direct PDF links
      │              Downloads PDF, validates it's a real PDF
      │
      ▼
Paper (local PDF/TXT)
      │
      ▼
[1] paper_extractor.py   — pure Python, zero tokens
    Detects sections, classifies each as math_heavy / has_results / key_section
      │
      ▼
[2] YOU (Claude, coding agent)
    Read the JSON, plan scenes, write explainer_video.py in manimgl
      │
      ▼
[3] preflight.py         — validates deps, detects render mode
      │
      ▼
[4] render.py            — invokes manimgl in the right mode (local/headless/server)
      │
      ▼
[5] Present the MP4 to the user
```

The skill directory is at:
`~/.claude/skills/paper-to-manim-video/`

Scripts are in `scripts/`.

---

## Step 1 — Get the paper (file or URL)

The user may provide either a **local file path** or a **URL**. Handle both.

### If the user gave a file path or uploaded a file

```bash
ls /mnt/user-data/uploads/   # Claude.ai uploads
# or use the path the user gave directly
```

Note the full path and skip to Step 2.

### If the user gave a URL

`download_paper.py` handles URL normalisation and download automatically.
It supports: arXiv abstract pages, arXiv PDF links, OpenReview forum/PDF pages,
ACL Anthology paper pages, Semantic Scholar paper pages, direct `.pdf` links,
and generic HTML pages that link to a PDF.

```bash
# Copy the download script
cp ~/.claude/skills/paper-to-manim-video/scripts/download_paper.py /tmp/

# Download — the last line of output is the local PDF path
python /tmp/download_paper.py "https://arxiv.org/abs/1706.03762"

# You can also specify a destination:
python /tmp/download_paper.py "https://arxiv.org/abs/1706.03762" \
    --output /tmp/attention_paper.pdf

# The script prints the final PDF path on the last stdout line.
# Capture it:
PAPER_PATH=$(python /tmp/download_paper.py "https://arxiv.org/abs/1706.03762" | tail -1)
echo "Paper saved to: $PAPER_PATH"
```

**Supported URL formats:**

| URL type | Example | How it's resolved |
|----------|---------|-------------------|
| arXiv abstract | `arxiv.org/abs/2303.08774` | → `arxiv.org/pdf/2303.08774.pdf` |
| arXiv PDF | `arxiv.org/pdf/2303.08774.pdf` | Used directly |
| OpenReview forum | `openreview.net/forum?id=XYZ` | → `openreview.net/pdf?id=XYZ` |
| OpenReview PDF | `openreview.net/pdf?id=XYZ` | Used directly |
| ACL Anthology | `aclanthology.org/2023.acl-long.1` | → `aclanthology.org/2023.acl-long.1.pdf` |
| Semantic Scholar | `semanticscholar.org/paper/Name/abcdef...` | → open-access PDF via SS API |
| Direct PDF link | `example.com/paper.pdf` | Used directly |
| HTML page with PDF link | any page with `href="*.pdf"` | PDF link extracted from HTML |

**If download fails** (paywall, 403, login required): tell the user to download the PDF manually and pass the file path instead.

---

## Step 2 — Set up the Python environment and run paper_extractor.py

### Python/venv setup (do this once per project directory)

**Always use `uv` with a venv. Never use the system Python directly.**

```bash
# Check which Python has the C dev headers (needed to compile manimpango)
# Python 3.12 needs python3.12-dev; Python 3.14 has headers by default on Ubuntu
python3 --version          # see what's available
find /usr/include -name "Python.h" 2>/dev/null   # find header location

# Create a venv with the Python version that has dev headers.
# Use 3.14 if python3.12-dev is not installed (no sudo needed for 3.14 on Ubuntu 24+):
uv venv -p 3.14   # or -p 3.12 if python3.12-dev is installed
source .venv/bin/activate

# Install all deps in one shot
uv pip install pypdf pdfplumber "setuptools<71" manimgl
```

**Python 3.13+ compatibility note:** `manimgl` depends on `pydub` which imports
`audioop`, a module removed in Python 3.13. `preflight.py` detects this and
automatically installs an `audioop.py` stub into site-packages — no manual action
needed. Just run preflight first (Step 5) before rendering.

```bash
# After activating the venv, use $VIRTUAL_ENV/bin/python (not bare 'python')
# The venv's python is available as 'python' when the venv is active:
which python    # should point to .venv/bin/python
```

### Run extraction

```bash
cp ~/.claude/skills/paper-to-manim-video/scripts/paper_extractor.py /tmp/

python /tmp/paper_extractor.py \
    "/path/to/paper.pdf" \
    --output /tmp/paper_scenes.json \
    --dump-text
```

Read the output:
```python
import json
with open("/tmp/paper_scenes.json") as f:
    data = json.load(f)

meta = data["meta"]
sections = data["sections"]
```

Key fields per section:
- `heading` — section title
- `content` — section text
- `math_heavy` — True if LaTeX math patterns detected
- `has_results` — True if figures/tables/numbers referenced
- `key_section` — True for Abstract, Introduction, Conclusion, etc.
- `word_count` — approximate word count

---

## Step 3 — Plan the scene list

Before writing any code, build a scene plan as a mental table:

| Scene # | Section | Type | Duration |
|---------|---------|------|----------|
| 0 | Title card | text | 8s |
| 1 | Abstract | concept or math | 45-60s |
| 2 | Introduction | concept | 60-90s |
| … | … | … | … |
| N | Takeaway | text | 15s |

**Scene type selection:**
- `math_heavy == True` → **math scene** (use Tex/OldTex, equation animation)
- `has_results == True` → **results scene** (use Axes + graphs or animated data)
- `key_section == True` and not math → **concept scene** (text + geometric diagrams)
- Everything else → **concept scene**

**Total video budget: under 8 minutes.** Allocate time proportionally to word count
of sections. Skip very short sections (< 80 words) or fold them into adjacent scenes.

If `meta["latex_in_paper"]` is False, never use `Tex()` — use `Text()` everywhere.

---

## Step 4 — Write explainer_video.py

Write the complete file to `/tmp/explainer_video.py`.

### File skeleton

```python
from manimlib import *

class ExplainerVideo(Scene):
    """
    Auto-generated explainer for: <paper title>
    Sections: <N> scenes
    """

    def construct(self):
        self.scene_title_card()
        self.scene_abstract()
        # ... one method per section
        self.scene_takeaway()

    # ── Scene methods ─────────────────────────────────────────

    def scene_title_card(self):
        """Title card: paper title and authors."""
        ...

    def scene_abstract(self):
        """Abstract overview."""
        ...
```

Keep each scene in its own method. The single `construct` method calls them
in order. This makes the file readable and debuggable.

---

### Scene templates

Use these templates as starting points. Adapt them — do not copy verbatim.
The goal is a video that feels alive, not a slideshow.

#### Title card scene

```python
def scene_title_card(self):
    title = Text(
        "Title of the Paper",
        font_size=48,
        color=WHITE,
    )
    title.to_edge(UP, buff=1.5)

    subtitle = Text(
        "Author Names · Conference/Journal · Year",
        font_size=24,
        color=GREY_A,
    )
    subtitle.next_to(title, DOWN, buff=0.5)

    underline = Line(LEFT * 5, RIGHT * 5, color=BLUE_C, stroke_width=2)
    underline.next_to(subtitle, DOWN, buff=0.4)

    self.play(Write(title), run_time=2)
    self.play(FadeIn(subtitle, shift=UP * 0.3))
    self.play(ShowCreation(underline))
    self.wait(3)
    self.play(FadeOut(VGroup(title, subtitle, underline)))
```

#### Concept scene (text + bullets)

```python
def scene_introduction(self):
    heading = Text("Introduction", font_size=40, color=BLUE_C)
    heading.to_edge(UP, buff=0.8)
    separator = Line(LEFT * 6, RIGHT * 6, color=GREY_D, stroke_width=1)
    separator.next_to(heading, DOWN, buff=0.2)

    bullets = VGroup(
        Text("• First key point from this section", font_size=28),
        Text("• Second key point", font_size=28),
        Text("• Third key point", font_size=28),
    )
    bullets.arrange(DOWN, aligned_edge=LEFT, buff=0.4)
    bullets.next_to(separator, DOWN, buff=0.6)
    bullets.to_edge(LEFT, buff=1.0)

    self.play(FadeIn(heading), ShowCreation(separator))
    for bullet in bullets:
        self.play(FadeIn(bullet, shift=RIGHT * 0.3), run_time=0.6)
        self.wait(1.5)
    self.wait(2)
    self.play(FadeOut(VGroup(heading, separator, bullets)))
```

#### Math scene (equations, LaTeX)

Only use when `latex_in_paper == True` AND the section is `math_heavy`.

```python
def scene_method(self):
    heading = Text("Methodology", font_size=40, color=TEAL_C)
    heading.to_edge(UP, buff=0.8)

    # Use OldTex for multi-part expressions, Tex for single ones
    eq1 = OldTex(r"\mathcal{L}(\theta) = -\sum_{t} \log p_\theta(x_t | x_{<t})")
    eq1.scale(0.9)
    eq1.move_to(ORIGIN + UP * 0.5)

    label1 = Text("Training objective", font_size=24, color=GREY_A)
    label1.next_to(eq1, DOWN, buff=0.4)

    eq2 = OldTex(r"\text{Attention}(Q, K, V) = \text{softmax}\!\left(\frac{QK^T}{\sqrt{d_k}}\right)V")
    eq2.scale(0.85)
    eq2.next_to(label1, DOWN, buff=0.8)

    self.play(Write(heading))
    self.play(Write(eq1), run_time=2)
    self.play(FadeIn(label1, shift=UP * 0.2))
    self.wait(2)
    self.play(Write(eq2), run_time=2)
    self.wait(3)
    self.play(FadeOut(VGroup(heading, eq1, label1, eq2)))
```

#### Results scene (with axes/graph)

Use when `has_results == True` and the section contains numerical comparisons.

```python
def scene_results(self):
    heading = Text("Results", font_size=40, color=GREEN_C)
    heading.to_edge(UP, buff=0.8)

    axes = Axes(
        x_range=(0, 5),
        y_range=(0, 100, 20),
        height=4,
        width=8,
        axis_config={"stroke_color": GREY_A, "stroke_width": 2},
    )
    axes.add_coordinate_labels(font_size=18)
    axes.shift(DOWN * 0.5)

    # Replace with actual data points from the paper
    baseline_graph = axes.get_graph(lambda x: 40 + 5 * x, color=RED_C)
    proposed_graph = axes.get_graph(lambda x: 55 + 10 * x, color=BLUE_C)

    legend = VGroup(
        VGroup(Line(LEFT * 0.3, RIGHT * 0.3, color=RED_C), Text(" Baseline", font_size=22)).arrange(RIGHT),
        VGroup(Line(LEFT * 0.3, RIGHT * 0.3, color=BLUE_C), Text(" Proposed", font_size=22)).arrange(RIGHT),
    ).arrange(DOWN, aligned_edge=LEFT).to_corner(DR)

    self.play(Write(heading))
    self.play(Write(axes, lag_ratio=0.01), run_time=1.5)
    self.play(ShowCreation(baseline_graph), FadeIn(legend[0]))
    self.play(ShowCreation(proposed_graph), FadeIn(legend[1]))
    self.wait(3)
    self.play(FadeOut(VGroup(heading, axes, baseline_graph, proposed_graph, legend)))
```

#### Results scene (text-based, no numeric data)

Use when `has_results == True` but the paper is qualitative (no clean numeric data for graphs).

```python
def scene_results(self):
    heading = Text("Results", font_size=40, color=GREEN_C)
    heading.to_edge(UP, buff=0.8)

    rows = [
        ("Method", "Score", "Notes"),
        ("Baseline", "72.3%", "Standard approach"),
        ("Ours", "89.1%", "+16.8pp improvement"),
    ]
    cols = [Text(cell, font_size=26) for row in rows for cell in row]
    table = VGroup(*cols)
    table.arrange_in_grid(rows=len(rows), cols=3, buff=(1.5, 0.5))
    table.next_to(heading, DOWN, buff=0.8)

    self.play(Write(heading))
    self.play(FadeIn(table, lag_ratio=0.05), run_time=1.5)
    self.wait(4)
    self.play(FadeOut(VGroup(heading, table)))
```

#### Takeaway scene

```python
def scene_takeaway(self):
    heading = Text("Key Takeaways", font_size=40, color=GOLD_C)
    heading.to_edge(UP, buff=0.8)

    points = VGroup(
        Text("1. First main contribution of the paper", font_size=30),
        Text("2. Second main contribution", font_size=30),
        Text("3. Third main contribution or future direction", font_size=30),
    )
    points.arrange(DOWN, aligned_edge=LEFT, buff=0.6)
    points.center().shift(DOWN * 0.3)

    self.play(Write(heading))
    for p in points:
        self.play(Write(p), run_time=1)
        self.wait(1)
    self.wait(3)
    self.play(FadeOut(VGroup(heading, points)))
```

---

### Critical code rules — read these before writing a single line

1. **No `self.embed()`** — breaks headless rendering unconditionally.
2. **No `self.open()`** — opens a viewer window; breaks server/headless.
3. **Exactly one Scene class** named `ExplainerVideo` — render.py targets it by name.
4. **No `wait()` with interactive intent** — `self.wait(N)` is fine; `self.embed()` is not.
5. **Text must fit the frame** — max font size: headings 48, body 32, captions 22.
   If text is long, break it across two Text objects or reduce font_size.
6. **VGroup for multi-element layouts** — always group related elements.
7. **Every element must animate in** — never use `self.add()` for main content; use
   `self.play(FadeIn(...))`, `self.play(Write(...))`, or `self.play(ShowCreation(...))`.
   `self.add()` is only acceptable for background elements set up before the scene starts.
8. **FadeOut everything** at the end of each scene method before returning.
   The screen must be clear when the next scene starts.
9. **Timing budget per scene:**
   - Title card: 8-12s
   - Key sections (Abstract, Introduction, Conclusion): 50-90s
   - Other sections: 30-60s
   - Takeaway: 15-20s
   - Total: < 8 minutes
10. **LaTeX fallback**: If you determined `latex_available = False` from the preflight
    report, replace ALL `Tex(...)` and `OldTex(...)` calls with `Text(...)`.
    Render the math as its plain-English equivalent or Unicode approximation.

---

### Geometric diagrams for concepts

When a concept section describes a relationship, architecture, or process,
draw a simple geometric diagram instead of (or alongside) bullets.

```python
# Example: visualising a pipeline A → B → C
box_a = RoundedRectangle(width=2, height=1, color=BLUE_C)
label_a = Text("Encoder", font_size=24).move_to(box_a)
group_a = VGroup(box_a, label_a)

box_b = RoundedRectangle(width=2, height=1, color=TEAL_C)
label_b = Text("Attention", font_size=24).move_to(box_b)
group_b = VGroup(box_b, label_b)

box_c = RoundedRectangle(width=2, height=1, color=GREEN_C)
label_c = Text("Decoder", font_size=24).move_to(box_c)
group_c = VGroup(box_c, label_c)

pipeline = VGroup(group_a, group_b, group_c).arrange(RIGHT, buff=1)
arrows = VGroup(
    Arrow(group_a.get_right(), group_b.get_left(), buff=0.1),
    Arrow(group_b.get_right(), group_c.get_left(), buff=0.1),
)

self.play(FadeIn(group_a))
self.play(ShowCreation(arrows[0]), FadeIn(group_b))
self.play(ShowCreation(arrows[1]), FadeIn(group_c))
```

Use color deliberately: BLUE for inputs, TEAL for processing, GREEN for outputs,
RED for errors/baselines, GOLD for highlights/key points.

---

### Handling long sections

If a section has more than ~600 words, split it across 2 scenes:

```python
def scene_related_work_1(self):
    """Related work — part 1: prior approaches."""
    ...

def scene_related_work_2(self):
    """Related work — part 2: comparison to this work."""
    ...
```

Call both from `construct()` in sequence.

---

## Step 5 — Run preflight.py

```bash
cp ~/.claude/skills/paper-to-manim-video/scripts/preflight.py /tmp/
python /tmp/preflight.py
```

This will:
- Detect Python version — on 3.13+, automatically install the `audioop` stub
  so pydub/manimgl imports work (Python 3.13 removed the `audioop` C module)
- Pin `setuptools<71` if `pkg_resources` is missing (manimgl needs it)
- Check all required system deps (ffmpeg, manimgl, libpango, etc.)
- Detect render mode: `local`, `headless`, or `server`
- Warn if LaTeX is absent (non-fatal — math falls back to Text())
- Write `/tmp/manim_preflight_report.json`
- Exit 1 with exact fix instructions if any required dep is missing

**Read the preflight report** to know whether LaTeX is available:

```python
import json
with open("/tmp/manim_preflight_report.json") as f:
    report = json.load(f)
latex_available = report["latex_available"]
render_mode = report["render_mode"]
```

If preflight exits 1, fix the reported issues before proceeding. Do not try to
render with broken deps — it will fail in confusing ways.

**Common setup issues and fixes:**

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: No module named 'audioop'` | Python 3.13+ | Run preflight.py — it auto-installs the stub |
| `ModuleNotFoundError: No module named 'pkg_resources'` | setuptools >= 71 | Run preflight.py — it pins `setuptools<71` automatically |
| `manimpango build fails` | Missing Python dev headers | Use Python 3.14 (`uv venv -p 3.14`) — its headers are pre-installed on Ubuntu 24+ |
| `python: command not found` | No `python` alias | Use `python3` or activate venv (`source .venv/bin/activate`) first |
| `error: externally-managed-environment` | System Python blocked | Always use a uv venv, never system pip |

---

## Step 6 — Render the video

```bash
cp ~/.claude/skills/paper-to-manim-video/scripts/render.py /tmp/

# Auto-detect mode (recommended):
python /tmp/render.py /tmp/explainer_video.py

# Force a specific mode:
python /tmp/render.py /tmp/explainer_video.py --mode headless
python /tmp/render.py /tmp/explainer_video.py --mode local
python /tmp/render.py /tmp/explainer_video.py --mode server --server user@host

# Quality options:
python /tmp/render.py /tmp/explainer_video.py --quality low     # fast preview
python /tmp/render.py /tmp/explainer_video.py --quality hd      # default
python /tmp/render.py /tmp/explainer_video.py --quality uhd     # 4K

# Specify output directory:
python /tmp/render.py /tmp/explainer_video.py --output-dir /tmp/video_out/
```

The script prints the MP4 path on the last line of stdout.

---

## Step 7 — Present the video

Use `present_files` if available, passing the MP4 path:

```
present_files(["/tmp/video_out/ExplainerVideo.mp4"])
```

If `present_files` is not available, tell the user the absolute path of the MP4 file.

---

## Server mode setup

The `server` render mode is for delegating the GPU-intensive manimgl rendering
to a remote machine, while keeping all AI work local.

### Requirements on the remote server

```bash
# The server must have:
manimgl          # pip install manimgl
ffmpeg           # sudo apt install ffmpeg
xvfb-run         # sudo apt install xvfb
libpango         # sudo apt install libpango1.0-dev
# Optional:
texlive          # sudo apt install texlive-science texlive-fonts-extra texlive-latex-extra
```

SSH key authentication must be configured (no password prompts):
```bash
ssh-copy-id user@your-render-host
```

### Activating server mode

```bash
export MANIM_SERVER=user@your-render-host

# Then run render.py as usual — it auto-detects server mode:
python /tmp/render.py /tmp/explainer_video.py
```

Or pass it explicitly:
```bash
python /tmp/render.py /tmp/explainer_video.py --server user@your-render-host
```

What happens under the hood:
1. `render.py` SSHs to the server and creates a temp directory
2. Uploads `explainer_video.py` and `custom_config.yml` via SCP
3. Runs `xvfb-run manimgl` on the server
4. SCPs the resulting MP4 back to your local `output_dir`
5. Cleans up the remote temp directory

The remote render can take 2-30 minutes depending on video length and server speed.

---

## Render mode reference

| Mode | Trigger | Command |
|------|---------|---------|
| `local` | `$DISPLAY` is set | `manimgl -w ...` directly |
| `headless` | No `$DISPLAY`, `xvfb-run` present | `xvfb-run -a manimgl -w ...` |
| `server` | `MANIM_SERVER` env var set | SSH + remote render + SCP back |

`render.py` auto-detects in priority order: server → local → headless.

---

## Troubleshooting

### Download issues

| Problem | Likely cause | Fix |
|---------|-------------|-----|
| `HTTP 403 Forbidden` | Paywall or bot-blocking | Ask the user to download the PDF manually and pass the file path |
| `HTTP 401 Unauthorized` | Login required | Same as above |
| `Downloaded file does not appear to be a PDF` | URL served an HTML login page | The paper is behind a paywall; ask for manual download |
| arXiv URL gives wrong paper | Old-style arXiv ID (`hep-ph/0601001`) | Script handles these — if it fails, use direct PDF URL |
| OpenReview PDF 403 | Some OpenReview papers restrict PDF access | Try the forum URL; if still 403, download manually |
| Semantic Scholar API timeout | SS API unavailable | Script falls back to HTML scraping; if that fails too, pass PDF directly |
| Slow download | Large PDF or slow server | Increase `--timeout 120` |

### Render issues

| Problem | Likely cause | Fix |
|---------|-------------|-----|
| `pyglet.canvas.xlib.NoSuchDisplayException` | Running locally without display | Use headless mode: `--mode headless` |
| `xvfb-run: command not found` | Xvfb not installed | `sudo apt install xvfb` |
| `manimgl: command not found` | manimgl not on PATH | `uv pip install manimgl` |
| `latex not found` or `TexFileNotFoundError` | LaTeX not installed | `sudo apt install texlive-science texlive-fonts-extra`; or remove all `Tex()` calls |
| `libGL error` | OpenGL driver missing | On headless: ensure `xvfb-run` is wrapping the call; add `--server-args='-screen 0 1920x1080x24'` |
| `Connection refused` (server mode) | SSH not reachable | Check `ssh user@host echo ok`; run `ssh-copy-id user@host` |
| MP4 not found after render | manimgl wrote to unexpected dir | Check `videos/` subdirectory next to scene file; or pass `--output-dir` explicitly |
| Blank/black video | `self.add()` instead of `self.play()` | Replace all `self.add(X)` for main content with `self.play(FadeIn(X))` |
| Text clipped off frame | Font size too large | Reduce to max 48 for headings, 30 for body |
| Render hangs | Missing `FadeOut` at scene end | Every scene method must clear the screen before returning |

---

## manimgl quick reference

### Mobject types

| Type | Use for |
|------|---------|
| `Text(str, font_size=N)` | Plain text (always works, no LaTeX needed) |
| `Tex(r"...")` | LaTeX math (requires LaTeX installed) |
| `OldTex(r"...")` | Multi-part LaTeX expressions |
| `Circle()`, `Square()`, `Rectangle()` | Geometric shapes |
| `RoundedRectangle(width, height)` | Boxes for diagrams |
| `Arrow(start, end)` | Directed arrows |
| `Line(start, end)` | Undirected lines |
| `Axes(x_range, y_range, ...)` | Coordinate systems |
| `Dot()` | Points |
| `VGroup(*mobjects)` | Group of objects, layoutable |

### Layout methods

| Method | Effect |
|--------|--------|
| `.to_edge(UP/DOWN/LEFT/RIGHT, buff=N)` | Push to edge with buffer |
| `.to_corner(UL/UR/DL/DR)` | Push to corner |
| `.center()` | Center on screen |
| `.next_to(mob, direction, buff=N)` | Position relative to another |
| `.shift(direction * N)` | Move by a vector |
| `.scale(factor)` | Resize |
| `VGroup(...).arrange(DOWN/RIGHT, buff=N)` | Auto-arrange group |

### Animation types

| Animation | Use for |
|-----------|---------|
| `Write(mob)` | Text writing effect |
| `FadeIn(mob, shift=direction)` | Fade in, optionally with motion |
| `FadeOut(mob)` | Fade out |
| `ShowCreation(mob)` | Reveal stroke-based objects |
| `Transform(a, b)` | Morph one object to another |
| `TransformMatchingTex(a, b)` | Match LaTeX symbols during transform |
| `ReplacementTransform(a, b)` | Transform and replace |

### Direction constants

`UP`, `DOWN`, `LEFT`, `RIGHT`, `UL`, `UR`, `DL`, `DR`, `IN`, `OUT`, `ORIGIN`

### Color constants (3b1b palette)

```
BLUE_E  BLUE_D  BLUE_C  BLUE_B  BLUE_A
TEAL_E  TEAL_C
GREEN_E GREEN_C
YELLOW_C GOLD_C
RED_C   RED_E
GREY_A  GREY_C  GREY_E
WHITE   BLACK
```

Use `_C` variants (medium) for main elements, `_A` for light/secondary, `_E` for dark/shadow.

---

## Installation (first-time setup)

```bash
# 1. Create a uv venv — use the Python version with C dev headers
#    On Ubuntu 24+, Python 3.14 has headers by default.
#    Python 3.12 requires: sudo apt install python3.12-dev
uv venv -p 3.14        # or: uv venv -p 3.12 (if python3.12-dev is installed)
source .venv/bin/activate

# 2. Python packages (setuptools<71 needed for pkg_resources with manimgl)
uv pip install pypdf pdfplumber "setuptools<71" manimgl

# 3. Linux system deps
sudo apt update
sudo apt install ffmpeg libpango1.0-dev

# 4. Headless rendering support
sudo apt install xvfb

# 5. LaTeX (optional — enables Tex() math rendering)
sudo apt install texlive-science texlive-fonts-extra texlive-latex-extra
```

**Python 3.13+ extra step** (handled automatically by preflight.py, but shown for reference):
```bash
# Install audioop stub so pydub doesn't crash manimgl import
python -c "
import site, os
stub = '''
def __getattr__(name):
    def _stub(*a, **k): raise NotImplementedError(f\"audioop.{name} unavailable\")
    return _stub
'''
path = os.path.join(site.getsitepackages()[0], 'audioop.py')
open(path, 'w').write(stub)
print('audioop stub installed at', path)
"
```

Verify:
```bash
python -c "import manimlib; print('manimgl OK')"
python -c "import pypdf; print('pypdf OK')"
ffmpeg -version | head -1
```

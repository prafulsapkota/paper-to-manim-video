# Research Paper → Manim Explainer Video

An AI Agent Skill and automated pipeline that transforms academic research papers (PDF or URL) into high-quality, 3b1b-style animated explainer videos using [`manimgl`](https://github.com/3b1b/manim).

Designed for AI coding agents (**Claude Code**, **opencode**, **Cursor**, **Windsurf**, **Cline**, **Roo Code**) as well as standalone CLI usage.

---

## 🎬 How It Works

```
Paper Input (PDF file or arXiv / OpenReview / ACL URL)
      │
      ├─ URL? ──► [0] download_paper.py  (Pure Python, zero tokens)
      │               Resolves and downloads open-access PDF
      ▼
Paper (Local PDF / Text)
      │
      ▼
[1] paper_extractor.py (Pure Python, zero tokens)
    Parses sections, detects math/LaTeX, empirical results, and key chapters
      │
      ▼
[2] AI Coding Agent (Claude / GPT-4 / Gemini)
    Reads extracted metadata, plans visual scenes, writes Manim animation script
      │
      ▼
[3] preflight.py
    Verifies system dependencies, detects render mode, applies Python 3.13+ shims
      │
      ▼
[4] render.py
    Executes manimgl in local, headless (Xvfb), or remote GPU server mode
      │
      ▼
Rendered MP4 Explainer Video (1080p HD, 30/60 FPS)
```

---

## 🚀 Installation & Agent Setup

### Method 1: Install as a Claude Code / opencode Skill

Clone or symlink the repository into your skills directory:

```bash
# For Claude Code
mkdir -p ~/.claude/skills
git clone https://github.com/prafulsapkota/paper-to-manim-video.git ~/.claude/skills/paper-to-manim-video

# For opencode
mkdir -p ~/.config/opencode/skills
git clone https://github.com/prafulsapkota/paper-to-manim-video.git ~/.config/opencode/skills/paper-to-manim-video
```

Once installed, your agent will automatically recognize trigger phrases such as:
- *"Make a video from this paper"*
- *"Explain this arXiv URL with an animated Manim video: https://arxiv.org/abs/2412.20138"*
- *"Turn this PDF into a visual explainer video"*

---

### Method 2: Standalone CLI Setup

#### 1. System Dependencies (Linux/Ubuntu)

```bash
sudo apt update
sudo apt install -y ffmpeg libpango1.0-dev xvfb

# Optional: For LaTeX math rendering via Tex()
sudo apt install -y texlive-science texlive-fonts-extra texlive-latex-extra
```

#### 2. Python Environment (Recommended via `uv`)

```bash
uv venv -p 3.11 .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

---

## 🛠️ CLI Pipeline Usage

You can also run every step of the pipeline manually via the CLI:

### 1. Download Paper from URL
```bash
python scripts/download_paper.py "https://arxiv.org/abs/2412.20138" --output /tmp/paper.pdf
```
Supports:
- arXiv abstracts (`arxiv.org/abs/...`) and PDFs (`arxiv.org/pdf/...`)
- OpenReview forum pages (`openreview.net/forum?id=...`)
- ACL Anthology (`aclanthology.org/...`)
- Semantic Scholar papers (`semanticscholar.org/paper/...`)
- Direct `.pdf` links

### 2. Extract & Classify Sections
```bash
python scripts/paper_extractor.py /tmp/paper.pdf --output /tmp/paper_scenes.json --dump-text
```
Generates structured JSON classifying sections by:
- `math_heavy`: LaTeX patterns and equations detected
- `has_results`: Numerical tables, metrics, and figures referenced
- `key_section`: Abstract, Introduction, Methodology, Conclusion

### 3. Preflight Check
```bash
python scripts/preflight.py
```
Validates required dependencies (`ffmpeg`, `libpango`, `manimgl`, `xvfb`) and writes `/tmp/manim_preflight_report.json`.

### 4. Render Video
```bash
# Auto-detects local vs headless mode (Xvfb)
python scripts/render.py examples/sample_explainer_video.py --quality hd --output-dir ./output/
```

Options:
- `--quality`: `low` (480p), `medium` (720p), `hd` (1080p), `uhd` (4K)
- `--mode`: `auto`, `local`, `headless` (via `xvfb-run`), `server`
- `--server`: Remote SSH host (`user@host`) for delegated GPU rendering

---

## 📁 Repository Structure

```
paper-to-manim-video/
├── SKILL.md                          # Main Skill instruction file for AI agents
├── README.md                         # Project documentation
├── requirements.txt                  # Python dependencies
├── pyproject.toml                    # Package metadata
├── LICENSE                           # MIT License
├── scripts/
│   ├── download_paper.py             # Paper URL resolution & downloader
│   ├── paper_extractor.py            # PDF/Text parser & section classifier
│   ├── preflight.py                  # Dependency & render mode validator
│   └── render.py                     # Headless/local manimgl render orchestrator
└── examples/
    └── sample_explainer_video.py     # Complete working explainer scene script
```

---

## 🎨 Best Practices for Manim Scenes

When writing or generating `ExplainerVideo` scripts:
1. **Scene Modularization**: Implement each section in its own `scene_*()` method and execute them sequentially in `construct()`.
2. **Clean Transitions**: Always `FadeOut` all elements before returning from a scene method to ensure a clean canvas for subsequent sections.
3. **No Interactive Traps**: Never use `self.embed()` or `self.open()` — this ensures headless and automated rendering never hangs.
4. **Adaptive Text**: Use `Text()` with balanced font sizes (`font_size=36-42` for headings, `18-24` for content) and auto-group layouts with `VGroup`.

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.

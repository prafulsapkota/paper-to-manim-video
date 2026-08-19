"""
paper_extractor.py

Extracts structured, classified sections from a research paper (PDF or TXT).
Zero LLM tokens — pure Python preprocessing step for the paper-to-manim-video skill.

Usage:
    python paper_extractor.py <paper_path> --output <output.json> [options]

Output JSON schema:
    {
        "meta": {
            "source_file": str,
            "paper_title": str,
            "extraction_method": str,   # "pypdf" | "pdfplumber" | "text"
            "total_sections": int,
            "total_words": int,
            "latex_in_paper": bool      # any LaTeX math detected anywhere
        },
        "sections": [
            {
                "index": int,
                "heading": str,
                "depth": int,           # 0=top-level, 1=sub, 2=sub-sub
                "word_count": int,
                "content": str,
                "math_heavy": bool,     # LaTeX math patterns detected
                "has_results": bool,    # figures/tables/numeric data referenced
                "key_section": bool     # Abstract, Intro, Conclusion, etc.
            }
        ]
    }
"""

import argparse
import json
import os
import re
import sys


# ---------------------------------------------------------------------------
# Regex patterns for section detection
# ---------------------------------------------------------------------------

KNOWN_SECTIONS = re.compile(
    r"^(?:abstract|introduction|background|related\s+work|motivation|"
    r"methodology|methods?|approach|model|architecture|framework|"
    r"experiments?|evaluation|results?|discussion|analysis|"
    r"conclusion|conclusions?\s+and\s+future\s+work|"
    r"future\s+work|limitations?|acknowledgements?|references?|appendix)",
    re.IGNORECASE,
)

NUMBERED_HEADING = re.compile(
    r"^(\d+(?:\.\d+){0,2})\s+([A-Z][^\n]{2,80})$"
)

ROMAN_HEADING = re.compile(
    r"^(I{1,3}|IV|V?I{0,3}|IX|X{0,3}(?:IX|IV|V?I{0,3}))\.\s+([A-Z][^\n]{2,80})$"
)

ALLCAPS_HEADING = re.compile(
    r"^([A-Z][A-Z\s\-]{3,50})$"
)

# ---------------------------------------------------------------------------
# Math/LaTeX detection patterns
# ---------------------------------------------------------------------------

MATH_PATTERNS = [
    re.compile(r"\$[^$\n]{1,200}\$"),               # $inline math$
    re.compile(r"\$\$[^$]{1,1000}\$\$"),             # $$block math$$
    re.compile(r"\\(?:frac|sum|prod|int|lim|inf|"
               r"mathbb|mathcal|mathbf|mathrm|"
               r"alpha|beta|gamma|delta|epsilon|"
               r"theta|lambda|sigma|mu|phi|psi|omega|"
               r"nabla|partial|forall|exists|"
               r"rightarrow|leftarrow|Rightarrow|"
               r"leq|geq|neq|approx|sim|propto|"
               r"begin|end|text|hat|bar|tilde|"
               r"sqrt|vec|norm)\b"),
    re.compile(r"\\begin\{(?:equation|align|array|matrix|bmatrix|pmatrix)\*?\}"),
]

GREEK_TECHNICAL = re.compile(
    r"\b(?:alpha|beta|gamma|delta|epsilon|zeta|eta|theta|"
    r"iota|kappa|lambda|mu|nu|xi|pi|rho|sigma|tau|"
    r"upsilon|phi|chi|psi|omega)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Results/data detection patterns
# ---------------------------------------------------------------------------

RESULTS_PATTERNS = [
    re.compile(r"\b(?:figure|fig\.|table|tbl\.|equation|eq\.)\s*\d+", re.IGNORECASE),
    re.compile(r"\b\d+(?:\.\d+)?%"),                              # percentages
    re.compile(r"\b(?:accuracy|precision|recall|f1|bleu|rouge|"
               r"perplexity|loss|error rate|throughput|latency|"
               r"speedup|improvement|baseline|outperform|"
               r"state.of.the.art|SOTA|benchmark)\b", re.IGNORECASE),
    re.compile(r"\b\d+\s*(?:ms|fps|gb|mb|params|parameters|tokens)\b", re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# Key section names
# ---------------------------------------------------------------------------

KEY_SECTION_NAMES = {
    "abstract", "introduction", "conclusion", "conclusions",
    "conclusions and future work", "summary", "overview",
    "key contributions", "contributions",
}


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def extract_text_pypdf(path):
    """Extract text from PDF using pypdf."""
    import pypdf
    text_parts = []
    with open(path, "rb") as f:
        reader = pypdf.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts), "pypdf"


def extract_text_pdfplumber(path):
    """Extract text from PDF using pdfplumber (fallback)."""
    import pdfplumber
    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts), "pdfplumber"


def extract_text(path):
    """
    Extract raw text from a PDF or TXT file.

    Returns:
        Tuple of (text: str, method: str).
    """
    ext = os.path.splitext(path)[1].lower()

    if ext == ".txt":
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(), "text"

    if ext != ".pdf":
        raise ValueError(f"Unsupported file type: {ext!r}. Expected .pdf or .txt")

    # Try pypdf first, fall back to pdfplumber
    try:
        text, method = extract_text_pypdf(path)
        if len(text.strip()) > 200:
            return text, method
    except Exception:
        pass

    try:
        text, method = extract_text_pdfplumber(path)
        if len(text.strip()) > 200:
            return text, method
    except Exception:
        pass

    raise RuntimeError(
        "Could not extract text from PDF.\n"
        "If the file is a scanned image PDF, run:\n"
        "  ocrmypdf input.pdf output.pdf\n"
        "then pass output.pdf to this script."
    )


# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------

def clean_text(text):
    """
    Remove common PDF artifacts: headers, footers, hyphenation, ligatures.

    Args:
        text: Raw extracted text string.

    Returns:
        Cleaned text string.
    """
    # Normalise line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove lines that look like page numbers (standalone digits)
    text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

    # Fix hyphenated line breaks (word-\ncontinuation → wordcontinuation)
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    # Collapse ligature artifacts
    for lig, rep in [("ﬁ", "fi"), ("ﬂ", "fl"), ("ﬀ", "ff"), ("ﬃ", "ffi"), ("ﬄ", "ffl")]:
        text = text.replace(lig, rep)

    # Collapse multiple blank lines to max two
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ---------------------------------------------------------------------------
# Title extraction
# ---------------------------------------------------------------------------

def extract_title(text, fallback_filename):
    """
    Heuristically extract a paper title from the first ~20 lines.

    Args:
        text: Full cleaned paper text.
        fallback_filename: Used if no title can be detected.

    Returns:
        Title string.
    """
    lines = [l.strip() for l in text.split("\n")[:30] if l.strip()]

    # Title is usually one of the first 5 non-empty lines, longer than 10 chars,
    # not all caps (that's a heading), no trailing period
    candidates = []
    for line in lines[:8]:
        if (10 < len(line) < 200
                and not line.endswith(".")
                and not KNOWN_SECTIONS.match(line)
                and not NUMBERED_HEADING.match(line)):
            candidates.append(line)

    if candidates:
        return candidates[0]

    return os.path.splitext(os.path.basename(fallback_filename))[0].replace("_", " ").title()


# ---------------------------------------------------------------------------
# Section detection
# ---------------------------------------------------------------------------

def is_heading(line):
    """
    Determine if a line looks like a section heading.

    Returns:
        Tuple of (is_heading: bool, depth: int, clean_title: str).
    """
    stripped = line.strip()
    if not stripped or len(stripped) > 120:
        return False, 0, ""

    # Known section names (depth 0)
    if KNOWN_SECTIONS.match(stripped) and len(stripped.split()) <= 6:
        return True, 0, stripped

    # Numbered heading (1. Title → depth 0, 1.1 → depth 1, 1.1.1 → depth 2)
    m = NUMBERED_HEADING.match(stripped)
    if m:
        number, title = m.group(1), m.group(2)
        depth = number.count(".")
        return True, depth, f"{number} {title}"

    # Roman numeral heading (depth 0)
    m = ROMAN_HEADING.match(stripped)
    if m:
        return True, 0, stripped

    # ALL CAPS short heading (depth 0) — only if 2–6 words
    m = ALLCAPS_HEADING.match(stripped)
    if m and 2 <= len(stripped.split()) <= 6:
        return True, 0, stripped.title()

    return False, 0, ""


def detect_sections(text, min_words=60):
    """
    Split text into labelled sections.

    Args:
        text: Cleaned paper text.
        min_words: Minimum word count per section to include.

    Returns:
        List of dicts with heading, depth, content.
    """
    lines = text.split("\n")
    sections = []
    current_heading = "Preamble"
    current_depth = 0
    current_lines = []

    def flush(heading, depth, lines_buf):
        """Append accumulated lines as a section if meeting word count threshold."""
        content = "\n".join(lines_buf).strip()
        if content and len(content.split()) >= min_words:
            sections.append({
                "heading": heading,
                "depth": depth,
                "content": content,
            })

    for line in lines:
        detected, depth, title = is_heading(line)
        if detected:
            flush(current_heading, current_depth, current_lines)
            current_heading = title
            current_depth = depth
            current_lines = []
        else:
            current_lines.append(line)

    flush(current_heading, current_depth, current_lines)

    # If no sections found at all, fall back to overlapping windows
    if not sections:
        words = text.split()
        window = 300
        overlap = 50
        for i, start in enumerate(range(0, len(words), window - overlap)):
            chunk = " ".join(words[start:start + window])
            if len(chunk.split()) >= min_words:
                sections.append({
                    "heading": f"Segment {i + 1}",
                    "depth": 0,
                    "content": chunk,
                })

    return sections


# ---------------------------------------------------------------------------
# Section classification
# ---------------------------------------------------------------------------

def is_math_heavy(content):
    """
    Detect if a section contains significant mathematical notation.

    Args:
        content: Section text.

    Returns:
        True if math-heavy.
    """
    hits = 0
    for pattern in MATH_PATTERNS:
        matches = pattern.findall(content)
        hits += len(matches)
        if hits >= 3:
            return True

    # Greek letters in technical context (equations) — needs multiple hits
    greek_hits = len(GREEK_TECHNICAL.findall(content))
    if greek_hits >= 4:
        hits += 2

    return hits >= 3


def has_results_data(content):
    """
    Detect if a section references figures, tables, or quantitative results.

    Args:
        content: Section text.

    Returns:
        True if results/data detected.
    """
    hits = 0
    for pattern in RESULTS_PATTERNS:
        hits += len(pattern.findall(content))
        if hits >= 2:
            return True
    return hits >= 2


def is_key_section(heading):
    """
    Detect if a section is structurally important (always included prominently).

    Args:
        heading: Section heading string.

    Returns:
        True if key section.
    """
    normalized = re.sub(r"^\d+[\.\d]*\s*", "", heading).strip().lower()
    # Remove roman numerals prefix
    normalized = re.sub(r"^[ivxlcdm]+\.\s*", "", normalized)
    return normalized in KEY_SECTION_NAMES


# ---------------------------------------------------------------------------
# Main extraction pipeline
# ---------------------------------------------------------------------------

def extract_paper(path, output_path, title_override=None, min_words=60, dump_text=False):
    """
    Full pipeline: extract, clean, section-detect, classify, and write JSON.

    Args:
        path: Path to input PDF or TXT file.
        output_path: Path for output JSON file.
        title_override: Optional manual title override.
        min_words: Minimum words per section.
        dump_text: If True, also writes cleaned text to .txt alongside JSON.
    """
    print(f"[paper_extractor] Reading: {path}")
    raw_text, method = extract_text(path)
    print(f"[paper_extractor] Extracted {len(raw_text):,} chars via {method}")

    text = clean_text(raw_text)

    if dump_text:
        txt_path = os.path.splitext(output_path)[0] + "_cleaned.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"[paper_extractor] Cleaned text written to: {txt_path}")

    title = title_override or extract_title(text, path)
    print(f"[paper_extractor] Detected title: {title!r}")

    raw_sections = detect_sections(text, min_words=min_words)
    print(f"[paper_extractor] Detected {len(raw_sections)} sections")

    # Detect if this paper has any LaTeX math at all
    latex_in_paper = any(is_math_heavy(s["content"]) for s in raw_sections)

    classified = []
    for i, sec in enumerate(raw_sections):
        content = sec["content"]
        math = is_math_heavy(content)
        results = has_results_data(content)
        key = is_key_section(sec["heading"])

        classified.append({
            "index": i + 1,
            "heading": sec["heading"],
            "depth": sec["depth"],
            "word_count": len(content.split()),
            "content": content,
            "math_heavy": math,
            "has_results": results,
            "key_section": key,
        })

    total_words = sum(s["word_count"] for s in classified)

    output = {
        "meta": {
            "source_file": os.path.basename(path),
            "paper_title": title,
            "extraction_method": method,
            "total_sections": len(classified),
            "total_words": total_words,
            "latex_in_paper": latex_in_paper,
        },
        "sections": classified,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"[paper_extractor] Output written to: {output_path}")
    print(f"[paper_extractor] Summary:")
    print(f"  Total sections : {len(classified)}")
    print(f"  Total words    : {total_words:,}")
    print(f"  Math-heavy     : {sum(1 for s in classified if s['math_heavy'])}")
    print(f"  Has results    : {sum(1 for s in classified if s['has_results'])}")
    print(f"  Key sections   : {sum(1 for s in classified if s['key_section'])}")
    print(f"  LaTeX in paper : {latex_in_paper}")

    return output


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    """Entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Extract and classify sections from a research paper for manim video generation."
    )
    parser.add_argument("paper", help="Path to input PDF or TXT file")
    parser.add_argument("--output", "-o", required=True, help="Path for output JSON file")
    parser.add_argument("--title", help="Override detected paper title")
    parser.add_argument("--min-words", type=int, default=60, help="Min words per section (default: 60)")
    parser.add_argument("--dump-text", action="store_true", help="Also save cleaned text as .txt")
    args = parser.parse_args()

    if not os.path.isfile(args.paper):
        print(f"ERROR: File not found: {args.paper}", file=sys.stderr)
        sys.exit(1)

    try:
        extract_paper(
            path=args.paper,
            output_path=args.output,
            title_override=args.title,
            min_words=args.min_words,
            dump_text=args.dump_text,
        )
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except ImportError as e:
        missing = str(e).split("'")[1] if "'" in str(e) else str(e)
        print(f"ERROR: Missing dependency: {missing}", file=sys.stderr)
        print("Install with:", file=sys.stderr)
        print("  uv pip install pypdf pdfplumber", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

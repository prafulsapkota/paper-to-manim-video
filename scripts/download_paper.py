"""
download_paper.py

Download a research paper from a URL to a local PDF file.
Handles direct PDF links, arXiv abstract pages, arXiv PDF links,
Semantic Scholar, ACL Anthology, OpenReview, and generic HTML pages
with an embedded PDF link.

Zero LLM tokens — pure Python, part of the paper-to-manim-video skill.

Usage:
    python download_paper.py <url> [--output /path/to/paper.pdf] [--timeout 60]

Output:
    Prints the absolute path of the downloaded PDF to stdout on success.

Exit codes:
    0  - Downloaded successfully
    1  - Download failed (reason printed to stderr)
"""

import argparse
import os
import re
import sys
import tempfile
import urllib.parse
import urllib.request
import urllib.error


# ---------------------------------------------------------------------------
# URL normalisation / resolution
# ---------------------------------------------------------------------------

ARXIV_ABS_RE = re.compile(
    r"arxiv\.org/abs/(\d{4}\.\d{4,5}(?:v\d+)?|[a-z\-]+/\d{7}(?:v\d+)?)",
    re.IGNORECASE,
)
ARXIV_PDF_RE = re.compile(
    r"arxiv\.org/pdf/(\d{4}\.\d{4,5}(?:v\d+)?|[a-z\-]+/\d{7}(?:v\d+)?)",
    re.IGNORECASE,
)
OPENREVIEW_RE = re.compile(
    r"openreview\.net/forum\?id=([^&]+)",
    re.IGNORECASE,
)
OPENREVIEW_PDF_RE = re.compile(
    r"openreview\.net/pdf\?id=([^&]+)",
    re.IGNORECASE,
)
ACL_ANTHOLOGY_RE = re.compile(
    r"aclanthology\.org/([A-Z0-9\-\.]+?)(?:\.pdf)?/?$",
    re.IGNORECASE,
)
SEMANTIC_SCHOLAR_RE = re.compile(
    r"semanticscholar\.org/paper/[^/]+/([a-f0-9]{40})",
    re.IGNORECASE,
)


def resolve_url(url):
    """
    Normalise a paper URL to a direct PDF download URL.

    Handles:
    - Direct .pdf links (returned as-is)
    - arXiv abstract pages   → arXiv PDF URL
    - arXiv PDF pages        → ensure correct PDF URL format
    - OpenReview forum pages → OpenReview PDF URL
    - ACL Anthology pages    → ACL Anthology PDF URL
    - Semantic Scholar pages → attempts to extract PDF via SS API

    Args:
        url: Raw URL string from the user.

    Returns:
        Tuple of (pdf_url: str, source: str) where source describes what was resolved.
    """
    url = url.strip()

    # Direct PDF link
    parsed = urllib.parse.urlparse(url)
    if parsed.path.lower().endswith(".pdf"):
        return url, "direct"

    # arXiv abstract page: arxiv.org/abs/XXXX.XXXXX
    m = ARXIV_ABS_RE.search(url)
    if m:
        paper_id = m.group(1)
        pdf_url = f"https://arxiv.org/pdf/{paper_id}.pdf"
        return pdf_url, f"arxiv:{paper_id}"

    # arXiv PDF page (may be missing .pdf extension)
    m = ARXIV_PDF_RE.search(url)
    if m:
        paper_id = m.group(1)
        pdf_url = f"https://arxiv.org/pdf/{paper_id}.pdf"
        return pdf_url, f"arxiv:{paper_id}"

    # OpenReview forum → PDF
    m = OPENREVIEW_RE.search(url)
    if m:
        paper_id = m.group(1)
        pdf_url = f"https://openreview.net/pdf?id={paper_id}"
        return pdf_url, f"openreview:{paper_id}"

    # OpenReview PDF (already a PDF link, normalise)
    m = OPENREVIEW_PDF_RE.search(url)
    if m:
        return url, f"openreview-pdf"

    # ACL Anthology
    m = ACL_ANTHOLOGY_RE.search(url)
    if m:
        paper_id = m.group(1).upper()
        pdf_url = f"https://aclanthology.org/{paper_id}.pdf"
        return pdf_url, f"acl:{paper_id}"

    # Semantic Scholar — use their public API to get the PDF URL
    m = SEMANTIC_SCHOLAR_RE.search(url)
    if m:
        corpus_id = m.group(1)
        pdf_url = _resolve_semantic_scholar(corpus_id)
        if pdf_url:
            return pdf_url, f"semanticscholar:{corpus_id[:8]}..."
        # If API fails, fall through to generic HTML scrape

    # Generic: try to find a PDF link by fetching the page HTML
    generic = _scrape_pdf_link_from_html(url)
    if generic:
        return generic, "scraped-html"

    # Last resort: try the URL directly and hope the server returns a PDF
    return url, "unknown"


def _resolve_semantic_scholar(corpus_id):
    """
    Use the Semantic Scholar public API to find the open-access PDF URL.

    Args:
        corpus_id: 40-character hex corpus ID from the SS URL.

    Returns:
        PDF URL string or None.
    """
    api_url = (
        f"https://api.semanticscholar.org/graph/v1/paper/{corpus_id}"
        f"?fields=openAccessPdf"
    )
    try:
        req = urllib.request.Request(api_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            import json
            data = json.loads(resp.read().decode())
            oa = data.get("openAccessPdf")
            if oa and oa.get("url"):
                return oa["url"]
    except Exception:
        pass
    return None


def _scrape_pdf_link_from_html(url):
    """
    Fetch the HTML at a URL and look for a .pdf href.

    Args:
        url: Page URL to scrape.

    Returns:
        Absolute PDF URL or None.
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=20) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if "pdf" in content_type.lower():
                # The URL itself serves a PDF
                return url
            html = resp.read().decode("utf-8", errors="replace")

        # Look for href="*.pdf" or href containing /pdf/
        pdf_links = re.findall(
            r'href=["\']([^"\']*\.pdf[^"\']*)["\']',
            html,
            re.IGNORECASE,
        )
        pdf_links += re.findall(
            r'href=["\']([^"\']*(?:/pdf/|/download/)[^"\']*)["\']',
            html,
            re.IGNORECASE,
        )

        if pdf_links:
            # Make absolute
            link = pdf_links[0]
            if link.startswith("http"):
                return link
            return urllib.parse.urljoin(url, link)
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

USER_AGENT = (
    "Mozilla/5.0 (compatible; paper-to-manim-video/1.0; "
    "+https://github.com/3b1b/manim)"
)

# Servers that require a browser-like Referer
REFERER_MAP = {
    "arxiv.org": "https://arxiv.org/",
    "openreview.net": "https://openreview.net/",
    "aclanthology.org": "https://aclanthology.org/",
}


def _referer_for(url):
    """Return an appropriate Referer header for the given URL, if any."""
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lstrip("www.")
    for domain, referer in REFERER_MAP.items():
        if host.endswith(domain):
            return referer
    return None


def download_pdf(url, dest_path, timeout=60, show_progress=True):
    """
    Download a PDF from a URL to a local file with progress reporting.

    Args:
        url: Direct PDF URL.
        dest_path: Local file path to write.
        timeout: HTTP timeout in seconds.
        show_progress: Print download progress.

    Returns:
        dest_path on success.
    Raises:
        RuntimeError on HTTP or IO error.
    """
    headers = {"User-Agent": USER_AGENT, "Accept": "application/pdf,*/*"}
    ref = _referer_for(url)
    if ref:
        headers["Referer"] = ref

    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get("Content-Type", "")
            total = resp.headers.get("Content-Length")
            total = int(total) if total else None

            # Validate we're actually getting a PDF
            # (Some servers redirect to login pages on bad requests)
            if total and total < 1000:
                raise RuntimeError(
                    f"Response is only {total} bytes — likely not a PDF. "
                    "The paper may require authentication or be behind a paywall."
                )

            downloaded = 0
            chunk_size = 65536  # 64 KB
            with open(dest_path, "wb") as f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if show_progress and total:
                        pct = downloaded / total * 100
                        bar_len = 30
                        filled = int(bar_len * downloaded / total)
                        bar = "█" * filled + "░" * (bar_len - filled)
                        mb = downloaded / 1_048_576
                        print(
                            f"\r  [{bar}] {pct:5.1f}%  {mb:.1f} MB",
                            end="",
                            flush=True,
                        )
                    elif show_progress:
                        mb = downloaded / 1_048_576
                        print(f"\r  Downloaded {mb:.1f} MB...", end="", flush=True)

            if show_progress:
                print()  # newline after progress bar

    except urllib.error.HTTPError as e:
        raise RuntimeError(
            f"HTTP {e.code} {e.reason} when downloading:\n  {url}\n"
            + _http_error_hint(e.code)
        )
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Network error downloading {url}:\n  {e.reason}\n"
            "Check your internet connection."
        )

    # Validate downloaded file is actually a PDF
    with open(dest_path, "rb") as f:
        header = f.read(5)
    if header != b"%PDF-":
        os.remove(dest_path)
        raise RuntimeError(
            f"Downloaded file does not appear to be a PDF (header: {header!r}).\n"
            "The URL may require login, or may not directly serve a PDF.\n"
            "Try downloading the PDF manually and passing the file path instead."
        )

    size_kb = os.path.getsize(dest_path) / 1024
    print(f"[download] Saved: {dest_path} ({size_kb:.0f} KB)")
    return dest_path


def _http_error_hint(code):
    """Return a human-readable hint for common HTTP error codes."""
    hints = {
        401: "The paper requires authentication. Download it manually.",
        403: "Access forbidden. The paper may be paywalled. Try the arXiv version.",
        404: "URL not found. Check the URL or try the DOI/arXiv link.",
        429: "Rate limited. Wait a moment and try again.",
        503: "Server unavailable. Try again later.",
    }
    return hints.get(code, "")


# ---------------------------------------------------------------------------
# Output path builder
# ---------------------------------------------------------------------------

def build_output_path(url, source, output_dir=None):
    """
    Derive a sensible local filename from the resolved URL and source.

    Args:
        url: Resolved PDF URL.
        source: Source description string from resolve_url().
        output_dir: Directory to put the file in (defaults to /tmp).

    Returns:
        Absolute path string.
    """
    out_dir = output_dir or tempfile.gettempdir()
    os.makedirs(out_dir, exist_ok=True)

    # Use arXiv ID as filename if we have it
    if source.startswith("arxiv:"):
        paper_id = source.split(":", 1)[1].replace("/", "_")
        return os.path.join(out_dir, f"{paper_id}.pdf")

    if source.startswith("openreview:"):
        paper_id = source.split(":", 1)[1][:20]  # truncate long IDs
        return os.path.join(out_dir, f"openreview_{paper_id}.pdf")

    if source.startswith("acl:"):
        paper_id = source.split(":", 1)[1]
        return os.path.join(out_dir, f"acl_{paper_id}.pdf")

    # Try to get filename from URL path
    path = urllib.parse.urlparse(url).path
    basename = os.path.basename(path)
    if basename.lower().endswith(".pdf") and len(basename) > 5:
        # Sanitise filename
        safe = re.sub(r"[^\w\-.]", "_", basename)
        return os.path.join(out_dir, safe)

    # Fallback: generic name with timestamp
    import time
    ts = int(time.time())
    return os.path.join(out_dir, f"paper_{ts}.pdf")


# ---------------------------------------------------------------------------
# High-level fetch function (used by SKILL.md pipeline)
# ---------------------------------------------------------------------------

def fetch_paper(url, output_dir=None, timeout=60):
    """
    Resolve a paper URL and download the PDF.

    This is the main entry point for the skill pipeline. Handles URL
    normalisation, platform-specific resolution (arXiv, OpenReview, etc.),
    download with progress, and PDF validation.

    Args:
        url: Any URL pointing to or describing a research paper.
        output_dir: Local directory to save the PDF (default: /tmp).
        timeout: HTTP timeout in seconds.

    Returns:
        Absolute path to the downloaded PDF file.
    Raises:
        RuntimeError with a human-readable message on failure.
    """
    print(f"[download] Input URL  : {url}")

    pdf_url, source = resolve_url(url)
    print(f"[download] Resolved to: {pdf_url}  (via: {source})")

    dest = build_output_path(pdf_url, source, output_dir)
    print(f"[download] Destination: {dest}")

    download_pdf(pdf_url, dest, timeout=timeout)
    return os.path.abspath(dest)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    """Entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description=(
            "Download a research paper PDF from a URL.\n"
            "Supports: direct PDF links, arXiv, OpenReview, ACL Anthology,\n"
            "Semantic Scholar, and generic HTML pages with embedded PDF links."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python download_paper.py https://arxiv.org/abs/1706.03762\n"
            "  python download_paper.py https://arxiv.org/pdf/1706.03762.pdf\n"
            "  python download_paper.py https://openreview.net/forum?id=abc123\n"
            "  python download_paper.py https://example.com/paper.pdf --output /tmp/my_paper.pdf\n"
        ),
    )
    parser.add_argument("url", help="URL of the research paper")
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output file path (default: auto-named in /tmp/)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (default: /tmp). Ignored if --output is set.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="HTTP timeout in seconds (default: 60)",
    )
    args = parser.parse_args()

    try:
        if args.output:
            # Full explicit path given — derive output_dir from it
            out_dir = os.path.dirname(os.path.abspath(args.output)) or "/tmp"
            pdf_url, source = resolve_url(args.url)
            print(f"[download] Input URL  : {args.url}")
            print(f"[download] Resolved to: {pdf_url}  (via: {source})")
            dest = os.path.abspath(args.output)
            print(f"[download] Destination: {dest}")
            download_pdf(pdf_url, dest, timeout=args.timeout)
            path = dest
        else:
            path = fetch_paper(args.url, output_dir=args.output_dir, timeout=args.timeout)

        # Machine-readable: final line is the path
        print(path)

    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

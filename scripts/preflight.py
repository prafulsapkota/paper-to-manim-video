"""
preflight.py

Dependency checker for the paper-to-manim-video skill.
Detects the correct render mode, validates all required tools are present,
and auto-applies known compatibility shims (audioop stub for Python 3.13+,
setuptools pin for pkg_resources).

Usage:
    python3 preflight.py [--mode auto|local|headless|server]

Exit codes:
    0  - All required deps present, prints RENDER_MODE to stdout
    1  - Missing required dependency (with exact fix instructions)
    2  - Configuration error (e.g. MANIM_SERVER set but unreachable)

Render modes:
    local     - $DISPLAY is set, render directly with manimgl
    headless  - No $DISPLAY, use xvfb-run (Linux virtual framebuffer)
    server    - MANIM_SERVER env var is set, SSH to remote host to render
"""

import json
import os
import shutil
import subprocess
import sys


# ---------------------------------------------------------------------------
# ANSI colour helpers (degrade gracefully on non-TTY)
# ---------------------------------------------------------------------------

USE_COLOR = sys.stdout.isatty()


def _c(code, text):
    """Wrap text in an ANSI color code if the terminal supports it."""
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def red(t):
    """Return red-coloured text."""
    return _c("31", t)


def green(t):
    """Return green-coloured text."""
    return _c("32", t)


def yellow(t):
    """Return yellow-coloured text."""
    return _c("33", t)


def bold(t):
    """Return bold text."""
    return _c("1", t)


# ---------------------------------------------------------------------------
# Python version helpers
# ---------------------------------------------------------------------------

PY_VERSION = sys.version_info
IS_PY313_PLUS = PY_VERSION >= (3, 13)


def get_site_packages():
    """
    Return the site-packages directory of the current interpreter.

    Returns:
        Path string, or None if not determinable.
    """
    try:
        import site
        pkgs = site.getsitepackages()
        return pkgs[0] if pkgs else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Compatibility shims
# ---------------------------------------------------------------------------

AUDIOOP_STUB = '''\
"""
Stub shim for the removed 'audioop' module (Python 3.13+).
pydub imports audioop, but manimgl never invokes audio ops during
non-interactive rendering, so an empty stub is sufficient.
Auto-installed by preflight.py.
"""


def __getattr__(name):
    """Return a stub callable for any attribute access."""
    def _stub(*args, **kwargs):
        raise NotImplementedError(
            f"audioop.{name} is not available (removed in Python 3.13+). "
            "If you need audio support, use Python 3.12 or earlier."
        )
    return _stub
'''


def ensure_audioop_shim():
    """
    Install a stub audioop.py into site-packages if running Python 3.13+
    and audioop is not importable.

    Python 3.13 removed the built-in audioop C extension. pydub (a manimgl
    dependency) imports audioop at module level, causing ImportError before
    manimlib can even load. The shim satisfies the import without providing
    real audio functionality, which is fine for rendering-only usage.

    Returns:
        Tuple of (installed: bool, message: str).
    """
    if not IS_PY313_PLUS:
        return False, "not needed (Python < 3.13)"

    # Check if audioop already importable (shim already installed, or some other provider)
    try:
        import audioop  # noqa: F401
        return False, "already present"
    except ImportError:
        pass

    site_pkgs = get_site_packages()
    if not site_pkgs:
        return False, "could not determine site-packages path"

    shim_path = os.path.join(site_pkgs, "audioop.py")
    try:
        with open(shim_path, "w") as f:
            f.write(AUDIOOP_STUB)
        return True, shim_path
    except OSError as e:
        return False, f"could not write shim: {e}"


def ensure_setuptools_compatible():
    """
    Ensure pkg_resources is available for manimgl.

    manimgl uses pkg_resources (from setuptools) to read its own package
    metadata. setuptools >= 71 removed pkg_resources from the default install;
    downgrading to < 71 restores it. This runs the pin via uv pip if needed.

    Returns:
        Tuple of (ok: bool, message: str).
    """
    try:
        import pkg_resources  # noqa: F401
        return True, "ok"
    except ImportError:
        pass

    # Try to install compatible setuptools
    print(f"    → pkg_resources missing — pinning setuptools<71 ...", flush=True)
    result = subprocess.run(
        [sys.executable, "-m", "uv", "pip", "install", "setuptools<71", "--quiet"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        # Fall back to plain pip
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "setuptools<71", "--quiet"],
            capture_output=True,
            text=True,
        )

    if result.returncode == 0:
        try:
            import pkg_resources  # noqa: F401
            return True, "pinned setuptools<71"
        except ImportError:
            return False, "still missing after pin"

    return False, f"pin failed: {result.stderr.strip()[:200]}"


# ---------------------------------------------------------------------------
# Individual dependency checks
# ---------------------------------------------------------------------------

def check_python_package(package, import_name=None):
    """
    Check if a Python package can be imported.

    Args:
        package: pip install name.
        import_name: Module import name if different from package name.

    Returns:
        True if importable.
    """
    name = import_name or package
    try:
        __import__(name)
        return True
    except ImportError:
        return False


def check_manimgl():
    """
    Check if manimgl/manimlib is importable, applying shims first.

    Separated from the generic check_python_package because manimlib
    has known Python 3.13+ compatibility issues that can be auto-fixed.

    Returns:
        Tuple of (importable: bool, notes: list[str]).
    """
    notes = []

    # Step 1: audioop shim
    if IS_PY313_PLUS:
        installed, msg = ensure_audioop_shim()
        if installed:
            notes.append(f"audioop shim installed → {msg}")
        elif msg not in ("already present", "not needed (Python < 3.13)"):
            notes.append(f"audioop shim: {msg}")

    # Step 2: pkg_resources / setuptools pin
    pkg_ok, pkg_msg = ensure_setuptools_compatible()
    if pkg_msg not in ("ok",):
        notes.append(f"setuptools: {pkg_msg}")

    # Step 3: actual import
    try:
        import manimlib  # noqa: F401
        return True, notes
    except ImportError as e:
        notes.append(f"import error: {e}")
        return False, notes


def check_binary(name):
    """
    Check if a system binary exists on PATH.

    Args:
        name: Binary name.

    Returns:
        True if found.
    """
    return shutil.which(name) is not None


def check_pkg_config(lib):
    """
    Check if a system library is detectable via pkg-config.

    Args:
        lib: Library name (e.g. 'pango').

    Returns:
        True if found, False if not, None if pkg-config itself is absent.
    """
    try:
        result = subprocess.run(
            ["pkg-config", "--exists", lib],
            capture_output=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return None  # unknown — pkg-config not installed


def check_ssh_reachable(server):
    """
    Test SSH connectivity to a remote server with a 5-second timeout.

    Args:
        server: user@host or host string.

    Returns:
        True if connection succeeds.
    """
    try:
        result = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes",
             server, "echo ok"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0 and "ok" in result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def find_python3():
    """
    Find the correct python3 binary to use for running scripts.

    Returns:
        Path string (e.g. 'python3' or absolute path).
    """
    # Prefer the same interpreter running this script
    return sys.executable


# ---------------------------------------------------------------------------
# Render mode detection
# ---------------------------------------------------------------------------

def detect_render_mode():
    """
    Auto-detect the appropriate render mode based on environment.

    Priority:
        1. MANIM_SERVER env var set → server
        2. $DISPLAY set → local
        3. xvfb-run available → headless
        4. Neither → error

    Returns:
        One of: 'local', 'headless', 'server'
    Raises:
        SystemExit if no viable mode found.
    """
    if os.environ.get("MANIM_SERVER"):
        return "server"

    if os.environ.get("DISPLAY"):
        return "local"

    if check_binary("xvfb-run"):
        return "headless"

    print(red(bold("\nERROR: Cannot determine render mode.\n")))
    print("No display ($DISPLAY) and no xvfb-run found.\n")
    print("Options:")
    print("  1. For headless rendering, install Xvfb:")
    print("     " + bold("sudo apt install xvfb"))
    print()
    print("  2. For remote server rendering, set MANIM_SERVER:")
    print("     " + bold("export MANIM_SERVER=user@your-render-host"))
    print()
    print("  3. For local rendering, ensure $DISPLAY is set (run from a desktop session).")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Full preflight check
# ---------------------------------------------------------------------------

def run_preflight(mode="auto"):
    """
    Run all dependency checks and return a preflight report dict.

    Automatically applies compatibility shims for known issues:
    - audioop stub for Python 3.13+ (pydub/manimgl compatibility)
    - setuptools<71 pin for pkg_resources availability

    Args:
        mode: 'auto', 'local', 'headless', or 'server'.

    Returns:
        Dict with 'render_mode', 'latex_available', 'python_bin', 'issues' list.
        Side effect: prints status to stdout, exits 1 on fatal missing dep.
    """
    print(bold("\n=== paper-to-manim-video preflight check ===\n"))

    python_bin = find_python3()
    py_ver = f"{PY_VERSION.major}.{PY_VERSION.minor}.{PY_VERSION.micro}"
    print(f"  Python        : {python_bin} ({py_ver})")
    if IS_PY313_PLUS:
        print(f"  Python 3.13+  : {yellow('audioop shim will be applied automatically')}")

    resolved_mode = mode if mode != "auto" else detect_render_mode()
    print(f"  Render mode   : {bold(resolved_mode)}")

    issues = []
    warnings = []
    ok = green("✓")
    fail = red("✗")
    warn = yellow("!")

    # --- Python packages (required) ---
    print("\n  Python packages (required):")

    for pkg, imp in [("pypdf", "pypdf"), ("pdfplumber", "pdfplumber")]:
        found = check_python_package(pkg, imp)
        status = ok if found else fail
        print(f"    {status} {pkg}")
        if not found:
            issues.append((pkg, f"uv pip install {pkg}"))

    # manimgl needs special handling — apply shims before import check
    print(f"    checking manimgl (applying any needed shims)...", flush=True)
    manimgl_ok, manimgl_notes = check_manimgl()
    status = ok if manimgl_ok else fail
    print(f"    {status} manimgl")
    for note in manimgl_notes:
        print(f"      → {note}")
    if not manimgl_ok:
        issues.append(("manimgl", "uv pip install manimgl  +  uv pip install 'setuptools<71'"))

    # --- System binaries (required) ---
    print("\n  System binaries (required):")

    if not check_binary("ffmpeg"):
        print(f"    {fail} ffmpeg")
        issues.append(("ffmpeg", "sudo apt install ffmpeg"))
    else:
        print(f"    {ok} ffmpeg")

    # manimgl binary — may be in venv or on PATH
    manimgl_bin = check_binary("manimgl") or manimgl_ok
    print(f"    {ok if manimgl_bin else fail} manimgl (binary or module)")
    if not manimgl_bin:
        issues.append(("manimgl binary", "uv pip install manimgl"))

    # --- Pango (required for text rendering) ---
    pango_result = check_pkg_config("pango")
    if pango_result is True:
        print(f"    {ok} libpango")
    elif pango_result is False:
        print(f"    {fail} libpango")
        issues.append(("libpango1.0-dev", "sudo apt install libpango1.0-dev"))
    else:
        print(f"    {warn} libpango (pkg-config not found — assuming installed)")

    # --- Mode-specific checks ---
    if resolved_mode == "headless":
        found = check_binary("xvfb-run")
        status = ok if found else fail
        print(f"\n  Headless rendering:")
        print(f"    {status} xvfb-run")
        if not found:
            issues.append(("xvfb", "sudo apt install xvfb"))

    elif resolved_mode == "server":
        server = os.environ.get("MANIM_SERVER", "")
        print(f"\n  Server rendering:")
        print(f"    Target: {server}")
        if not server:
            print(f"    {fail} MANIM_SERVER env var is empty")
            issues.append(("MANIM_SERVER", "export MANIM_SERVER=user@your-host"))
        else:
            reachable = check_ssh_reachable(server)
            status = ok if reachable else fail
            print(f"    {status} SSH connectivity to {server}")
            if not reachable:
                issues.append(
                    ("ssh", f"Ensure SSH key auth is set up: ssh-copy-id {server}")
                )

    # --- LaTeX (optional but recommended) ---
    latex_found = check_binary("latex") or check_binary("pdflatex")
    print(f"\n  LaTeX (optional — needed for Tex() math rendering):")
    print(f"    {ok if latex_found else warn} latex")
    if not latex_found:
        warnings.append(
            "LaTeX not found. Math equations will use Text() instead of Tex(). "
            "Install: sudo apt install texlive-science texlive-fonts-extra texlive-latex-extra"
        )

    # --- Print warnings ---
    if warnings:
        print(f"\n  {warn} Warnings:")
        for w in warnings:
            print(f"    - {w}")

    # --- Print errors and exit if fatal issues ---
    if issues:
        print(red(bold(f"\n  {fail} Missing required dependencies:\n")))
        for dep, fix in issues:
            print(f"    Dependency : {bold(dep)}")
            print(f"    Fix        : {bold(fix)}")
            print()
        print(red("Preflight failed. Fix the above issues and re-run.\n"))
        sys.exit(1)

    print(green(bold("\n  All required dependencies satisfied.\n")))

    report = {
        "render_mode": resolved_mode,
        "latex_available": latex_found,
        "python_bin": python_bin,
        "manim_server": os.environ.get("MANIM_SERVER", ""),
        "issues": [],
    }

    # Write report to temp file so render.py can read it
    report_path = "/tmp/manim_preflight_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"  Report saved to: {report_path}")
    print(f"  render_mode    : {resolved_mode}")
    print(f"  latex_available: {latex_found}")
    print(f"  python_bin     : {python_bin}")

    return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    """Entry point for CLI usage."""
    import argparse
    parser = argparse.ArgumentParser(
        description="Preflight check for paper-to-manim-video skill.\n"
                    "Validates deps and auto-applies Python 3.13+ compatibility shims."
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "local", "headless", "server"],
        default="auto",
        help="Force a render mode (default: auto-detect)",
    )
    args = parser.parse_args()
    run_preflight(mode=args.mode)


if __name__ == "__main__":
    main()

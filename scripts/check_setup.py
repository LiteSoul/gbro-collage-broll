#!/usr/bin/env python3
"""
gbro-collage-broll environment self-check.
Cross-platform (Windows, macOS, Linux).
Supports both Manual Mode (Default, No-API) and API Mode.
Exit 0 = all good; exit 1 = at least one required item missing.
"""

import argparse
import os
import shutil
import subprocess
import sys

def check_command(cmd):
    """Checks if a command-line tool exists in PATH."""
    return shutil.which(cmd) is not None

def run_self_check(mode="manual"):
    fail = False
    print(f"=== gbro-collage-broll Environment Check [Mode: {mode.upper()}] ===")

    # 1. Python version (>= 3.10)
    py_major, py_minor = sys.version_info[:2]
    if (py_major, py_minor) >= (3, 10):
        print(f"PASS: Python {py_major}.{py_minor} (>= 3.10 required)")
    else:
        print(f"FAIL: Python {py_major}.{py_minor} is too old. Requires Python >= 3.10.")
        fail = True

    # 2. ffmpeg & ffprobe
    has_ffmpeg = check_command("ffmpeg")
    has_ffprobe = check_command("ffprobe")
    if has_ffmpeg and has_ffprobe:
        print("PASS: ffmpeg / ffprobe available (used for frame scaling, background generation, audio stripping, QA sheets)")
    else:
        missing = []
        if not has_ffmpeg:
            missing.append("ffmpeg")
        if not has_ffprobe:
            missing.append("ffprobe")
        print(f"FAIL: Missing tool(s): {', '.join(missing)}")
        print("      Installation guide:")
        print("      - Windows: winget install Gyan.FFmpeg or choco install ffmpeg")
        print("      - macOS: brew install ffmpeg")
        print("      - Linux: sudo apt update && sudo apt install ffmpeg")
        fail = True

    # 3. Mode-specific checks
    if mode == "api":
        # Check GEMINI_API_KEY
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            print("PASS: GEMINI_API_KEY is configured")
        else:
            print("FAIL: GEMINI_API_KEY is not set.")
            print("      Create a key at https://aistudio.google.com/apikey and set GEMINI_API_KEY.")
            fail = True

        # Check google-genai
        try:
            from google import genai
            print(f"PASS: google-genai SDK available (v{getattr(genai, '__version__', 'unknown')})")
        except ImportError:
            print("FAIL: google-genai package not found.")
            print("      Install via: pip install 'google-genai>=2.10.0'")
            fail = True
    else:
        # Manual Mode (No API key needed)
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            print("INFO: GEMINI_API_KEY is detected (optional in Manual Mode).")
        else:
            print("PASS: Manual Mode active (No API key needed! Complete prompts will be written to file).")

    # Check Pillow (Optional but recommended for image scripts)
    try:
        import PIL
        print("PASS: Pillow library available")
    except ImportError:
        print("INFO: Pillow library not installed (optional, pip install Pillow).")

    print("==================================================================")
    if fail:
        print("STATUS: FAILED - Please install the missing dependencies above.")
        return 1
    else:
        print(f"STATUS: READY for {mode.upper()} workflow!")
        return 0

def main():
    parser = argparse.ArgumentParser(description="Environment check for gbro-collage-broll")
    parser.add_argument(
        "--mode",
        choices=["manual", "api"],
        default="manual",
        help="Workflow mode to check: 'manual' (default, no API key needed) or 'api' (requires GEMINI_API_KEY and google-genai)"
    )
    args = parser.parse_args()
    sys.exit(run_self_check(mode=args.mode))

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
scripts/inspect_voiceover.py
Analyzes voiceover input for gbro-collage-broll.

Supports:
1. Audio file input (.mp3, .wav, .m4a, .aac, .ogg):
   - Measures exact spoken duration using ffprobe.
   - Recommends optimal video duration (3 to 10 seconds).
2. Text script input:
   - Analyzes word count and pacing.
   - Estimates natural spoken duration (130-160 WPM for English, ~3.5-4.5 chars/sec for Chinese).
   - Recommends video duration (3 to 10 seconds).
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

def get_audio_duration(audio_path):
    """Uses ffprobe to extract exact duration of an audio file in seconds."""
    if not shutil.which("ffprobe"):
        raise RuntimeError("ffprobe is required to inspect audio files.")

    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration:stream=codec_name,sample_rate,channels",
        "-of", "json",
        str(audio_path)
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed on {audio_path}:\n{result.stderr}")

    data = json.loads(result.stdout)
    duration = float(data.get("format", {}).get("duration", 0.0))
    streams = data.get("streams", [])
    codec = streams[0].get("codec_name", "unknown") if streams else "unknown"
    sample_rate = streams[0].get("sample_rate", "unknown") if streams else "unknown"
    channels = streams[0].get("channels", 1) if streams else 1

    return {
        "duration": round(duration, 2),
        "codec": codec,
        "sample_rate": sample_rate,
        "channels": channels
    }

def estimate_text_duration(text, wpm=140):
    """
    Estimates spoken duration from text.
    Standard voiceover speed is approx. 130-160 words per minute (WPM).
    For CJK characters, average reading speed is ~3.5 - 4.5 characters per second.
    """
    clean_text = text.strip()
    words = clean_text.split()
    word_count = len(words)

    # Check for CJK characters
    cjk_count = sum(1 for c in clean_text if '\u4e00' <= c <= '\u9fff' or '\u3040' <= c <= '\u30ff')

    if cjk_count > len(clean_text) * 0.3:
        # CJK dominant
        est_seconds = cjk_count / 3.8
    else:
        # Latin / English dominant: words / (WPM / 60)
        est_seconds = word_count / (wpm / 60.0)

    return round(max(est_seconds, 2.0), 1), word_count, cjk_count

def recommend_video_duration(seconds):
    """Recommends an integer video duration between 3 and 10 seconds."""
    # Round to nearest integer clamped between 3 and 10
    clamped = max(3, min(10, round(seconds)))
    return clamped

def main():
    parser = argparse.ArgumentParser(description="Analyze voiceover audio or text script for gbro-collage-broll")
    parser.add_argument("input", nargs="?", help="Voiceover text line OR path to an audio file (.mp3, .wav, etc.)")
    parser.add_argument("--wpm", type=int, default=140, help="Estimated speaking rate in words per minute (default: 140)")
    parser.add_argument("--json", action="store_true", help="Output analysis in machine-readable JSON format")
    args = parser.parse_args()

    if not args.input:
        parser.print_help()
        sys.exit(1)

    input_str = args.input.strip()

    # Check if input is a local file
    if os.path.isfile(input_str):
        ext = os.path.splitext(input_str)[1].lower()
        audio_extensions = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".wma"}
        if ext in audio_extensions:
            info = get_audio_duration(input_str)
            dur = info["duration"]
            rec = recommend_video_duration(dur)
            exceeds_10s = dur > 10.0
            
            if args.json:
                res = {
                    "type": "audio",
                    "file": input_str,
                    "codec": info["codec"],
                    "sample_rate": info["sample_rate"],
                    "channels": info["channels"],
                    "exact_duration_seconds": dur,
                    "recommended_duration_seconds": rec,
                    "exceeds_10s": exceeds_10s,
                    "options": [
                        {"type": "single_clip", "duration": rec},
                        {"type": "split_clips", "suggested_count": 2, "duration_per_clip": 5} if dur > 7.0 else None
                    ]
                }
                res["options"] = [o for o in res["options"] if o]
                print(json.dumps(res, indent=2))
                return

            print(f"=== Voiceover Audio Analysis ===")
            print(f"File:                 {input_str}")
            print(f"Format:               {info['codec'].upper()} ({info['sample_rate']} Hz, {info['channels']} ch)")
            print(f"Exact Audio Duration: {dur}s")
            print(f"Recommended Duration: {rec} seconds")
            if exceeds_10s:
                print(f"Note: Audio exceeds 10s. Consider generating two 5s B-roll clips or one 10s maximum clip.")
            return

    # Treat as text script
    est_dur, word_count, cjk_count = estimate_text_duration(input_str, wpm=args.wpm)
    rec = recommend_video_duration(est_dur)
    exceeds_5s = est_dur > 6.0 or word_count > 18

    if args.json:
        options = []
        if exceeds_5s:
            options.append({
                "option": "extended_clip",
                "recommended_duration": rec,
                "description": f"Extended {rec}s single clip with layered assembly (0-{rec-3}s) and hold ({rec-3}-{rec}s)"
            })
            options.append({
                "option": "split_sequence",
                "suggested_count": 2,
                "duration_per_clip": 5,
                "description": "Two 5s complementary B-roll clips cutting on the conceptual turn (highest viewer retention)"
            })
            options.append({
                "option": "tighten_script",
                "target_words": 13,
                "duration": 5,
                "description": "Condense the voiceover sentence to ~12-14 words to fit a single snappy 5s clip"
            })
        else:
            options.append({
                "option": "snappy_clip",
                "recommended_duration": 5,
                "description": "Quick 5s assembly: fast entrance (0-3.5s) + hold finished composition (3.5-5s)"
            })

        res = {
            "type": "text",
            "script": input_str,
            "word_count": word_count,
            "cjk_count": cjk_count,
            "wpm": args.wpm,
            "estimated_spoken_seconds": est_dur,
            "recommended_duration_seconds": rec,
            "exceeds_5s": exceeds_5s,
            "options": options
        }
        print(json.dumps(res, indent=2))
        return

    print(f"=== Voiceover Text Analysis ===")
    print(f"Script:               \"{input_str}\"")
    if cjk_count > 0:
        print(f"Character Count:      {len(input_str)} (CJK characters: {cjk_count})")
    else:
        print(f"Word Count:           {word_count} words")
    print(f"Estimated Speaking:   ~{est_dur}s (at ~{args.wpm} words/min)")
    print(f"Recommended Duration: {rec} seconds")
    
    if exceeds_5s:
        print(f"\n[!] DURATION NOTICE: This script takes ~{est_dur}s to speak at natural pace.")
        print(f"    DO NOT force it into a 5s clip (would require speaking at {int(word_count / (5.0 / 60.0))} WPM).")
        print(f"    Recommended Action Options:")
        print(f"    1. Extended Clip:   Use {rec} seconds (supported up to 10s).")
        print(f"    2. Split Sequence:  Split into two 5s clips (e.g. Cut 1 & Cut 2 on the key pivot).")
        print(f"    3. Tighten Script:  Condense copy to ~12-14 words for a single 5s clip.")
    else:
        print("Pacing Advice:        Quick 5s assembly: fast entrance (0-3.5s) + hold finished collage (3.5-5s).")

if __name__ == "__main__":
    main()

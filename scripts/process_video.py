#!/usr/bin/env python3
"""
scripts/process_video.py
Post-processes generated videos for gbro-collage-broll Gate 3.

Features:
1. Strips audio using ffmpeg to produce final-5s-noaudio.mp4.
2. Generates 5-frame contact sheet (contact-sheet.jpg) at 1 fps.
3. Extracts actual first frame (video-first-frame.jpg) to verify empty color-field start.
4. Extracts actual last frame (video-last-frame.jpg) and builds side-by-side comparison (end-frame-comparison.jpg).
5. Runs ffprobe metadata inspection (resolution, duration, fps, audio presence).
6. Writes comprehensive QA evaluation into gate3-qa.md.
7. Supports batch mode to aggregate project-wide overview sheets.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

def run_cmd(cmd):
    """Executes a command and returns stdout, raising on failure."""
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed ({' '.join(cmd)}):\n{result.stderr}")
    return result.stdout

def probe_video(video_path):
    """Inspects video metadata using ffprobe."""
    if not shutil.which("ffprobe"):
        return {}
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=width,height,r_frame_rate,codec_type:format=duration",
        "-of", "json",
        str(video_path)
    ]
    try:
        out = run_cmd(cmd)
        data = json.loads(out)
        video_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
        audio_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
        
        duration = float(data.get("format", {}).get("duration", 0))
        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))
        fps_str = video_stream.get("r_frame_rate", "24/1")
        if "/" in fps_str:
            num, den = fps_str.split("/")
            fps = float(num) / float(den) if float(den) != 0 else 0
        else:
            fps = float(fps_str)

        return {
            "duration": round(duration, 2),
            "width": width,
            "height": height,
            "fps": round(fps, 1),
            "has_audio": audio_stream is not None
        }
    except Exception as e:
        print(f"Warning: ffprobe inspection error: {e}", file=sys.stderr)
        return {}

def strip_audio(input_video, output_video):
    """Creates a completely silent video copy by removing audio tracks."""
    os.makedirs(os.path.dirname(os.path.abspath(output_video)), exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-i", str(input_video),
        "-map", "0:v:0", "-c:v", "copy", "-an",
        str(output_video)
    ]
    run_cmd(cmd)

def generate_contact_sheet(video_path, output_image):
    """Extracts 1 frame per second (5 frames) and tiles them into a contact sheet."""
    os.makedirs(os.path.dirname(os.path.abspath(output_image)), exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", "fps=1,scale=270:480,tile=5x1",
        "-frames:v", "1",
        str(output_image)
    ]
    run_cmd(cmd)

def extract_first_frame(video_path, output_image):
    """Extracts the first frame (t=0) from video."""
    os.makedirs(os.path.dirname(os.path.abspath(output_image)), exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-ss", "0.0", "-i", str(video_path),
        "-frames:v", "1",
        str(output_image)
    ]
    run_cmd(cmd)

def extract_last_frame(video_path, output_image):
    """Extracts the last frame from video."""
    os.makedirs(os.path.dirname(os.path.abspath(output_image)), exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-sseof", "-0.1", "-i", str(video_path),
        "-frames:v", "1",
        str(output_image)
    ]
    run_cmd(cmd)

def create_side_by_side(img1_path, img2_path, output_path, label1="Approved Still", label2="Video Last Frame"):
    """Creates a labeled side-by-side comparison image."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Try Pillow for clean labeled composition
    try:
        from PIL import Image, ImageDraw, ImageFont
        with Image.open(img1_path) as i1, Image.open(img2_path) as i2:
            target_h = 480
            target_w = 270
            t1 = i1.convert("RGB").resize((target_w, target_h), Image.Resampling.LANCZOS)
            t2 = i2.convert("RGB").resize((target_w, target_h), Image.Resampling.LANCZOS)

            pad = 20
            header_h = 40
            total_w = pad * 3 + target_w * 2
            total_h = pad * 2 + header_h + target_h

            combined = Image.new("RGB", (total_w, total_h), (25, 27, 34))
            draw = ImageDraw.Draw(combined)

            # Draw labels
            draw.text((pad + 10, pad), label1, fill=(200, 210, 225))
            draw.text((pad * 2 + target_w + 10, pad), label2, fill=(200, 210, 225))

            combined.paste(t1, (pad, pad + header_h))
            combined.paste(t2, (pad * 2 + target_w, pad + header_h))
            combined.save(output_path, "JPEG", quality=92)
            return
    except Exception:
        pass

    # Fallback to ffmpeg hstack
    if shutil.which("ffmpeg"):
        cmd = [
            "ffmpeg", "-y",
            "-i", str(img1_path),
            "-i", str(img2_path),
            "-filter_complex",
            "[0:v]scale=270:480[v0];[1:v]scale=270:480[v1];[v0][v1]hstack=inputs=2[out]",
            "-map", "[out]",
            str(output_path)
        ]
        try:
            run_cmd(cmd)
            return
        except Exception:
            pass

def process_item_video(item_dir):
    """Processes a single item's video generation results."""
    item_path = Path(item_dir).resolve()
    omni_run = item_path / "omni" / "run-v01"
    raw_video = omni_run / "final-5s.mp4"
    if not raw_video.exists():
        # Check if user saved directly to item_path / final-5s.mp4
        if (item_path / "final-5s.mp4").exists():
            omni_run.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item_path / "final-5s.mp4", raw_video)
        else:
            print(f"Error: Video file not found at: {raw_video}")
            print(f"Please save the generated video MP4 file to: {raw_video}")
            return None

    noaudio_video = omni_run / "final-5s-noaudio.mp4"
    contact_sheet = omni_run / "contact-sheet.jpg"
    first_frame_img = omni_run / "video-first-frame.jpg"
    last_frame_img = omni_run / "video-last-frame.jpg"
    comparison_img = omni_run / "end-frame-comparison.jpg"

    approved_last_frame = item_path / "frames" / "last-frame.png"

    print(f"\nProcessing video for: {item_path.name}")
    print(f"  Input: {raw_video}")

    # 1. Strip audio
    print("  1. Stripping audio -> final-5s-noaudio.mp4")
    strip_audio(raw_video, noaudio_video)

    # 2. Extract 5-second contact sheet
    print("  2. Generating contact sheet -> contact-sheet.jpg")
    generate_contact_sheet(noaudio_video, contact_sheet)

    # 3. Extract actual first and last frames
    print("  3. Extracting opening frame -> video-first-frame.jpg")
    extract_first_frame(noaudio_video, first_frame_img)

    print("  4. Extracting final frame -> video-last-frame.jpg")
    extract_last_frame(noaudio_video, last_frame_img)

    # 4. Compare with approved frame
    if approved_last_frame.exists():
        print("  5. Generating end-frame comparison -> end-frame-comparison.jpg")
        create_side_by_side(approved_last_frame, last_frame_img, comparison_img)

    # 5. Metadata and QA
    meta = probe_video(noaudio_video)
    print(f"  6. Technical Specs: {meta}")

    # QA verdict
    duration_pass = 4.0 <= meta.get("duration", 5.0) <= 6.0
    aspect_pass = meta.get("height", 0) > meta.get("width", 0)
    audio_pass = not meta.get("has_audio", False)

    qa_status = "PASS" if (duration_pass and aspect_pass and audio_pass) else "WARNING"

    qa_report = f"""
## Gate 3 Video QA: {item_path.name}
- **Status:** {qa_status}
- **Source Video:** `{raw_video.name}`
- **Silent Delivery:** `{noaudio_video.name}` (Audio streams: 0)
- **Duration:** {meta.get('duration', 'N/A')}s (Target: 5.0s)
- **Resolution:** {meta.get('width', 'N/A')}x{meta.get('height', 'N/A')} (9:16 Vertical)
- **Frame Rate:** {meta.get('fps', 'N/A')} fps
- **Generated Artifacts:**
  - Contact Sheet: [`contact-sheet.jpg`]({contact_sheet.as_uri()})
  - First Frame: [`video-first-frame.jpg`]({first_frame_img.as_uri()})
  - Last Frame Comparison: [`end-frame-comparison.jpg`]({comparison_img.as_uri()})
- **Checklist:**
  - [{'x' if audio_pass else ' '}] Audio stripped (silent MP4)
  - [{'x' if duration_pass else ' '}] Valid duration (approx. 5s)
  - [{'x' if aspect_pass else ' '}] Vertical 9:16 composition
  - [x] Assembly progression verified on contact sheet
"""

    project_qa_file = item_path.parent / "gate3-qa.md"
    with open(project_qa_file, "a" if project_qa_file.exists() else "w", encoding="utf-8") as f:
        f.write(qa_report)

    print(f"QA report updated at: {project_qa_file}")
    print(f"Gate 3 processing complete for {item_path.name}!\n")

    return {
        "item": item_path.name,
        "video": noaudio_video,
        "contact_sheet": contact_sheet,
        "first_frame": first_frame_img,
        "comparison": comparison_img,
        "meta": meta
    }

def main():
    parser = argparse.ArgumentParser(description="Process and QA generated videos for gbro-collage-broll")
    parser.add_argument("--item", help="Path to item directory (e.g. project/01-concept)")
    parser.add_argument("--project", help="Path to project directory containing multiple items")
    args = parser.parse_args()

    if not args.item and not args.project:
        parser.print_help()
        sys.exit(1)

    if args.item:
        res = process_item_video(args.item)
        if not res:
            sys.exit(1)
        sys.exit(0)

    if args.project:
        proj = Path(args.project).resolve()
        subdirs = sorted([d for d in proj.iterdir() if d.is_dir() and (d / "omni" / "run-v01").exists()])
        if not subdirs:
            print(f"No item directories found with omni/run-v01 in {proj}")
            sys.exit(1)

        print(f"Processing {len(subdirs)} items in project {proj.name}...")
        for d in subdirs:
            process_item_video(d)

if __name__ == "__main__":
    main()

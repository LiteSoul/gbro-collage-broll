#!/usr/bin/env python3
"""
scripts/prepare_manual_video.py
Generates comprehensive manual video generation packages and guides for Google Omni / Google Flow / Veo.
Creates:
- <item>/manual-video-prompt.md (Step-by-step human guide with full specs and copyable prompt)
- <item>/omni-prompt.txt (Raw prompt for quick copying)
- Optional project-wide MANUAL_VIDEO_GUIDE.md
"""

import argparse
import json
import os
import sys
from pathlib import Path

def generate_manual_package(item_dir, prompt_text, duration=5, aspect_ratio="9:16", color="#1E2A38"):
    item_path = Path(item_dir).resolve()
    frames_dir = item_path / "frames"
    omni_run_dir = item_path / "omni" / "run-v01"
    omni_run_dir.mkdir(parents=True, exist_ok=True)

    first_frame = frames_dir / "first-frame.png"
    last_frame = frames_dir / "last-frame.png"
    
    # Support final-{duration}s.mp4 and final-5s.mp4
    target_mp4 = omni_run_dir / f"final-{duration}s.mp4"

    # Pacing advice based on duration
    if duration <= 5:
        pacing_note = "Snappy 5s assembly: elements enter quickly from 0s to 3.5s, holding the completed collage steadily for the final 1.5s."
    elif duration <= 7:
        pacing_note = f"Balanced {duration}s assembly: structure arrives 0-2s, subjects & accents arrive 2-{duration-2}s, holding the completed collage for the final 2s."
    else:
        pacing_note = f"Extended {duration}s assembly: multi-phase assembly with structure (0-3s), main mechanics & subjects (3-{duration-3}s), accent cards ({duration-3}-{duration-2}s), holding the completed collage steadily for the final 2-3s."

    # Write raw prompt
    raw_prompt_file = item_path / "omni-prompt.txt"
    raw_prompt_file.write_text(prompt_text.strip(), encoding="utf-8")

    # Write detailed guide
    guide_file = item_path / "manual-video-prompt.md"

    guide_content = f"""# Gate 3: Manual Video Generation Guide for {item_path.name}

Use this guide to generate the {duration}-second paper-collage assembly video using **Google Omni**, **Google Flow**, or **Veo** without needing an API key.

---

## 1. Video Specifications & Settings

| Parameter | Recommended Value | Notes |
|-----------|-------------------|-------|
| **Tool / Platform** | **Google Omni Flash** / **Google Flow** | Or Veo 2 / Runway Gen-3 with first+last frame |
| **Generation Mode** | **First Frame & Last Frame** (Keyframe Interpolation) | Uses Image 1 as start, Image 2 as finish |
| **Image 1 (First Frame)** | [`{first_frame.name}`]({first_frame.as_uri()}) | Pure color paper field (`{color}`) |
| **Image 2 (Last Frame)** | [`{last_frame.name}`]({last_frame.as_uri()}) | Approved completed collage |
| **Aspect Ratio** | **9:16** (Vertical / 720×1280 or 1080×1920) | Locked vertical framing |
| **Duration** | **{duration} seconds** (Supports 3s–10s) | {pacing_note} |
| **Audio** | **None / Silent** | Audio will be stripped in post-processing |
| **Camera Movement** | **Locked-off (Static)** | No camera panning, no slow zoom |

---

## 2. Keyframe Asset Paths

Please upload these two images to your video generator:
1. **Start Frame (Image 1):**
   ```
   {first_frame}
   ```
2. **End Frame (Image 2):**
   ```
   {last_frame}
   ```

---

## 3. Video Prompt (Copy & Paste)

```text
{prompt_text.strip()}
```

*Pacing Tip:* {pacing_note}

---

## 4. Where to Save the Output Video

Once Google Omni / Flow produces the video, download the MP4 and save it to:
```
{target_mp4}
```
*(Alternative valid names: `{omni_run_dir / "final-video.mp4"}` or `{omni_run_dir / "final-5s.mp4"}`)*

---

## 5. Next Steps (Continuing the Workflow)

After saving the MP4 file, tell the agent:
> *"I have generated and saved the video for {item_path.name}."*

Or run the post-processing script directly:
```bash
python scripts/process_video.py --item "{item_path}" --duration {duration}
```

The workflow will automatically:
1. Strip any audio to create `final-{duration}s-noaudio.mp4` (or `final-video-noaudio.mp4`).
2. Extract the {duration}-frame contact sheet (`contact-sheet.jpg`).
3. Verify the opening frame is clean (`video-first-frame.jpg`).
4. Generate the side-by-side end-frame comparison (`end-frame-comparison.jpg`).
5. Run automated QA checks (validating {duration}s duration) and finalize delivery!
"""

    guide_file.write_text(guide_content, encoding="utf-8")
    print(f"Generated manual prompt package for {item_path.name}:")
    print(f"  Duration: {duration}s")
    print(f"  Guide:    {guide_file}")
    print(f"  Prompt:   {raw_prompt_file}")
    print(f"  Target:   {target_mp4}")
    return guide_file

def main():
    parser = argparse.ArgumentParser(description="Prepare manual video generation package for Google Omni / Flow")
    parser.add_argument("--item", help="Path to item directory (e.g. project/01-concept)")
    parser.add_argument("--prompt", help="Omni animation prompt text")
    parser.add_argument("--jobs", help="Path to omni-jobs.json for batch preparation")
    parser.add_argument("--duration", type=int, default=5, help="Video duration in seconds (default: 5)")
    parser.add_argument("--aspect-ratio", default="9:16", help="Aspect ratio (default: 9:16)")
    parser.add_argument("--color", default="#1E2A38", help="Background hex color")
    args = parser.parse_args()

    if args.jobs:
        jobs_path = Path(args.jobs).resolve()
        if not jobs_path.exists():
            print(f"Error: Jobs file not found: {jobs_path}", file=sys.stderr)
            sys.exit(1)
        with open(jobs_path, "r", encoding="utf-8") as f:
            jobs = json.load(f)

        project_dir = jobs_path.parent
        project_guide = project_dir / "MANUAL_VIDEO_GUIDE.md"
        guide_lines = [
            f"# Batch Manual Video Generation Guide",
            f"\nThis project contains {len(jobs)} video generation job(s).\n",
            f"| Item | First Frame | Last Frame | Target Output | Guide Link |",
            f"|------|-------------|------------|---------------|------------|"
        ]

        for idx, job in enumerate(jobs, 1):
            p = job.get("prompt", "")
            images = job.get("image", [])
            output = job.get("output", "")
            out_path = Path(output)
            # Find item directory
            item_dir = out_path.parent.parent if "omni" in out_path.parts else out_path.parent
            if not item_dir.exists():
                item_dir.mkdir(parents=True, exist_ok=True)

            color = job.get("color", args.color)
            guide = generate_manual_package(
                item_dir=item_dir,
                prompt_text=p,
                duration=job.get("duration", args.duration),
                aspect_ratio=job.get("aspect_ratio", args.aspect_ratio),
                color=color
            )
            first_frame_name = Path(images[0]).name if len(images) > 0 else "first-frame.png"
            last_frame_name = Path(images[1]).name if len(images) > 1 else "last-frame.png"
            guide_lines.append(
                f"| {item_dir.name} | `{first_frame_name}` | `{last_frame_name}` | `{out_path.name}` | [{guide.name}]({guide.as_uri()}) |"
            )

        project_guide.write_text("\n".join(guide_lines), encoding="utf-8")
        print(f"\nProject-wide batch guide created at: {project_guide}")
        return

    if not args.item or not args.prompt:
        parser.print_help()
        sys.exit(1)

    generate_manual_package(
        item_dir=args.item,
        prompt_text=args.prompt,
        duration=args.duration,
        aspect_ratio=args.aspect_ratio,
        color=args.color
    )

if __name__ == "__main__":
    main()

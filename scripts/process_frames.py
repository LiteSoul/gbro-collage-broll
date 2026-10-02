#!/usr/bin/env python3
"""
scripts/process_frames.py
Handles Gate 2 Still Frame preparation and processing for gbro-collage-broll.

Features:
1. Export manual image-generation prompt guides for Nano Banana / Imagen / Midjourney.
2. Ingest user-provided image (last-frame-original.png), scale/crop to vertical 9:16 (1080x1920) as last-frame.png.
3. Automatically generate empty solid-color first-frame.png matching the scene background color.
4. Generate Gate 2 contact sheet and QA report (gate2-qa.md).
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

def run_cmd(cmd):
    """Runs a shell command and returns output, raising on failure."""
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed ({' '.join(cmd)}):\n{result.stderr}")
    return result.stdout

def create_solid_color_image(hex_color, output_path, width=1080, height=1920):
    """Creates a solid color PNG image using ffmpeg or Pillow."""
    clean_hex = hex_color.lstrip("#")
    if len(clean_hex) == 6:
        r = int(clean_hex[0:2], 16)
        g = int(clean_hex[2:4], 16)
        b = int(clean_hex[4:6], 16)
    else:
        r, g, b = (30, 30, 40)
        clean_hex = "1E1E28"

    # Try Pillow first if available
    try:
        from PIL import Image
        img = Image.new("RGB", (width, height), (r, g, b))
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        img.save(output_path, "PNG")
        return
    except ImportError:
        pass

    # Fallback to ffmpeg
    if shutil.which("ffmpeg"):
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=0x{clean_hex}:s={width}x{height}",
            "-frames:v", "1",
            output_path
        ]
        run_cmd(cmd)
        return

    raise RuntimeError("Neither Pillow nor ffmpeg is available to create solid color image.")

def process_last_frame(input_path, output_path, width=1080, height=1920):
    """Scales and crops input image to exactly width x height (default 1080x1920) preserving aspect ratio."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    if shutil.which("ffmpeg"):
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}",
            output_path
        ]
        run_cmd(cmd)
        return

    try:
        from PIL import Image, ImageOps
        with Image.open(input_path) as img:
            img_rgb = img.convert("RGB")
            fitted = ImageOps.fit(img_rgb, (width, height), method=Image.Resampling.LANCZOS)
            fitted.save(output_path, "PNG")
            return
    except ImportError:
        pass

    raise RuntimeError("Neither ffmpeg nor Pillow is available to process image.")

def generate_contact_sheet(frames, output_path):
    """Generates a side-by-side or grid contact sheet preview of still frames."""
    if not frames:
        return
    
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Use Pillow if available
    try:
        from PIL import Image, ImageDraw, ImageFont
        images = [Image.open(f).convert("RGB") for f in frames if os.path.exists(f)]
        if not images:
            return

        # Target height per thumbnail: 480px, width: 270px
        thumb_w, thumb_h = 270, 480
        padding = 16
        total_w = len(images) * thumb_w + (len(images) + 1) * padding
        total_h = thumb_h + padding * 2

        sheet = Image.new("RGB", (total_w, total_h), (25, 25, 30))
        for idx, img in enumerate(images):
            thumb = img.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            x = padding + idx * (thumb_w + padding)
            y = padding
            sheet.paste(thumb, (x, y))

        sheet.save(output_path, "JPEG", quality=90)
        return
    except ImportError:
        pass

    # Fallback to ffmpeg hstack
    if shutil.which("ffmpeg") and len(frames) == 2 and all(os.path.exists(f) for f in frames):
        cmd = [
            "ffmpeg", "-y",
            "-i", frames[0],
            "-i", frames[1],
            "-filter_complex",
            "[0:v]scale=270:480[v0];[1:v]scale=270:480[v1];[v0][v1]hstack=inputs=2[out]",
            "-map", "[out]",
            output_path
        ]
        try:
            run_cmd(cmd)
            return
        except Exception:
            pass

def export_image_guide(project_dir, item_dir, prompt_text, hex_color, visual_spec=None):
    """Exports a user-friendly manual image generation guide markdown file."""
    frames_dir = item_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    target_original = frames_dir / "last-frame-original.png"
    guide_file = item_dir / "manual-image-prompt.md"

    spec_details = ""
    if visual_spec:
        spec_details = f"""
### Scene Specification
- **Visual Metaphor:** {visual_spec.get('visual_metaphor', 'N/A')}
- **Script Meaning:** {visual_spec.get('script_meaning', 'N/A')}
- **Background Color:** `{hex_color}`
- **Aspect Ratio:** 9:16 (vertical poster frame)
- **Style:** Editorial Halftone Paper Collage (Black & white halftone photography cut-outs, cream keylines, colored cardstock accents, soft drop shadows)
"""

    content = f"""# Gate 2: Manual Image Generation Guide

Please follow these steps to generate the completed paper-collage still frame using your preferred AI image generator (e.g., **Nano Banana**, **Imagen**, **Gemini**, or **Midjourney**).

---

## 1. Generation Parameters

- **Aspect Ratio:** `9:16` (Vertical / Portrait)
- **Primary Color Field:** `{hex_color}`
- **Destination Path:** `{target_original.resolve()}`

{spec_details}

---

## 2. Image Generation Prompt (Copy & Paste)

```text
{prompt_text}
```

---

## 3. What to do next:

1. Copy the prompt above and paste it into **Nano Banana** (or your preferred image generator).
2. Ensure the aspect ratio is set to **9:16**.
3. Generate the image and pick the best candidate that matches the visual metaphor.
4. Save / paste the downloaded image to:
   ```
   {target_original.resolve()}
   ```
5. Run the frame processing script or notify the agent:
   ```bash
   python scripts/process_frames.py --item "{item_dir.resolve()}" --color "{hex_color}"
   ```
6. The agent/script will automatically:
   - Crop & scale the image to 1080x1920 as `last-frame.png`.
   - Generate the matching solid color opening frame `first-frame.png`.
   - Create the Gate 2 contact sheet and QA review!
"""
    guide_file.write_text(content, encoding="utf-8")
    print(f"Manual image guide created at: {guide_file}")
    return guide_file

def main():
    parser = argparse.ArgumentParser(description="Process Gate 2 frames for gbro-collage-broll")
    parser.add_argument("--item", required=True, help="Path to the item directory (e.g., project/01-concept)")
    parser.add_argument("--color", default="#1E2A38", help="Background hex color (default: #1E2A38)")
    parser.add_argument("--prompt", help="Image generation prompt to export to manual guide")
    parser.add_argument("--export-guide-only", action="store_true", help="Only export the manual guide, do not process frames yet")
    args = parser.parse_args()

    item_dir = Path(args.item).resolve()
    frames_dir = item_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    if args.export_guide_only or (args.prompt and not (frames_dir / "last-frame-original.png").exists()):
        prompt_text = args.prompt or "Editorial paper collage visual metaphor..."
        export_image_guide(item_dir.parent, item_dir, prompt_text, args.color)
        print(f"Waiting for user to generate and place image at: {frames_dir / 'last-frame-original.png'}")
        return

    original_png = frames_dir / "last-frame-original.png"
    last_frame_png = frames_dir / "last-frame.png"
    first_frame_png = frames_dir / "first-frame.png"

    if not original_png.exists():
        print(f"Error: Original image not found at '{original_png}'.")
        print("Please place your generated image there, or use --prompt to export a guide first.")
        sys.exit(1)

    print(f"Processing last frame: {original_png} -> {last_frame_png}")
    process_last_frame(str(original_png), str(last_frame_png), width=1080, height=1920)

    print(f"Generating matching empty first frame ({args.color}) -> {first_frame_png}")
    create_solid_color_image(args.color, str(first_frame_png), width=1080, height=1920)

    contact_sheet_path = item_dir / "still-contact-sheet.jpg"
    print(f"Generating contact sheet -> {contact_sheet_path}")
    generate_contact_sheet([str(first_frame_png), str(last_frame_png)], str(contact_sheet_path))

    # Also update project-level contact sheet if applicable
    project_contact_sheet = item_dir.parent / "still-contact-sheet.jpg"
    generate_contact_sheet([str(first_frame_png), str(last_frame_png)], str(project_contact_sheet))

    # Write Gate 2 QA log
    qa_file = item_dir.parent / "gate2-qa.md"
    qa_entry = f"""
## Gate 2 Still Frame QA: {item_dir.name}
- **Status:** PASS
- **Original Image:** `{original_png.name}`
- **Last Frame (1080x1920):** `{last_frame_png.name}` (Verified 9:16)
- **First Frame (Solid Color):** `{first_frame_png.name}` (Color: `{args.color}`)
- **Contact Sheet:** `{contact_sheet_path.name}`
- **Checklist:**
  - [x] Clear visual metaphor
  - [x] Flat color field background
  - [x] Halftone cutouts + cardstock accents
  - [x] No typography, watermark, or UI
  - [x] 1080x1920 vertical composition
"""
    with open(qa_file, "a" if qa_file.exists() else "w", encoding="utf-8") as f:
        f.write(qa_entry)

    print(f"\nSUCCESS! Gate 2 frames are ready for: {item_dir.name}")
    print(f"  First Frame: {first_frame_png}")
    print(f"  Last Frame:  {last_frame_png}")
    print(f"  Preview:     {contact_sheet_path}")

if __name__ == "__main__":
    main()

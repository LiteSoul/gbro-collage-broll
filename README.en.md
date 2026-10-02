# gbro-collage-broll

<p align="center">
  <a href="README.md">简体中文</a> · <a href="README.en.md">English</a> · <a href="README.ja.md">日本語</a>
</p>

<p align="center">
  <img src="assets/demo-purple.gif" width="180" alt="Deep purple background: a group collaborates to press out a sci-fi filmstrip">
  <img src="assets/demo-yellow.gif" width="180" alt="Mustard yellow background: a printing press magnifies errors in bulk">
  <img src="assets/demo-red.gif" width="180" alt="Red background: a director's hand arranges positions on a board">
  <img src="assets/demo-teal.gif" width="180" alt="Teal background: scissors cut open the shot track">
</p>

Turn a 3 to 10-second voiceover line (or audio recording) into a premium editorial **halftone paper-collage assembly animation** B-roll clip.

Compatible with both **Manual / Hybrid mode** (agent direct image generation with fallback to **Nano Banana**, plus manual video generation via Google Omni Flash / Google Flow / Veo) and **Automated API mode** (direct Gemini Omni Flash first/last-frame generation).

## Results

- Bold, flat, solid-color paper fields + black-and-white halftone photo cutouts + colored cardstock accents
- Elements slide in, snap into place, and assemble piece-by-piece from an empty canvas with a tactile stop-motion feel (not a simple fade or slow zoom)
- Flexible duration: 3 to 10 seconds (default 5s for punchy cuts, up to 10s for deeper visual narratives)
- Default deliverable is a silent 9:16, 720×1280 or 1080×1920, 24 fps MP4 ready to drop directly beneath voiceover audio

## Voiceover Input: Text or Audio File

You can start the workflow in two ways:
1. **Text Script (Simplest):** Just provide the sentence or spoken quote from your video script.
2. **Audio File (`.mp3`, `.wav`, `.m4a`):** Run `python scripts/inspect_voiceover.py voiceover.mp3` to measure the exact spoken duration and automatically calculate the matching video length.

> **Pacing Rule:** Always verify spoken duration with `python scripts/inspect_voiceover.py "<text>"` before Gate 1. Never force a 20+ word sentence into 5 seconds (which requires >250 WPM). Recommend 8–10 seconds or a 2-clip split sequence.

## Workflow: Three Approval Gates

The core of this skill is a mandatory three-stage approval process, allowing you to focus on aesthetic judgment rather than wasting time or API credits:

1. **Gate 1 · Metaphor & Duration Approval** — Analyzes voiceover pacing and proposes the visual metaphor + duration pacing plan (core idea / duration & pacing / key objects / background color / assembly sequence) in text only. Halts for confirmation before creating any assets.
2. **Gate 2 · Still-Frame Approval** — Prepares the color collage ending still frame (`last-frame.png`) and the matching solid-color opening frame (`first-frame.png`).
   - *Direct Generation (Primary):* Agent generates the 9:16 image directly via built-in image tool for immediate review (time saver).
   - *Nano Banana Fallback (Manual):* If image tool is unavailable, rate-limited, or exhausted, agent exports `manual-image-prompt.md`. You generate in **Nano Banana** (or Midjourney / external AI), save to `frames/last-frame-original.png`, and the script automatically formats it.
3. **Gate 3 · Video Generation & QA** — Produces the 3–10 second assembly animation from empty first frame to approved last frame.
   - *Manual Mode (No API key needed):* Writes `manual-video-prompt.md` with complete prompts, pacing advice (5s vs 10s), generation settings, and keyframe links. You generate the video in Google Omni / Flow web generator using the first and last frame, save the MP4 into the project, and the script automatically strips audio, extracts 1-second contact sheets (adaptive Nx1 or 5x2 for 10s), and executes comprehensive QA.
   - *API Mode:* Calls `gemini-omni-flash-preview` automatically.

Batch mode supports partial approval: only approved items proceed to the next stage.

## Requirements

Run the cross-platform environment self-check:

```bash
# Check Manual Mode (No API key required)
python scripts/check_setup.py

# Check API Mode (if using GEMINI_API_KEY)
python scripts/check_setup.py --mode api
```

| Dependency | Manual Mode (Default) | API Mode | Notes |
|---|---|---|---|
| Python >= 3.10 | Required | Required | Standard Python environment |
| ffmpeg / ffprobe | Required | Required | Used for frame scaling, solid backgrounds, audio stripping & QA |
| `GEMINI_API_KEY` | **Not required** | Required | Created at [Google AI Studio](https://aistudio.google.com/apikey) |
| `google-genai` SDK | **Not required** | Required (>= 2.10.0) | For direct API calls |

## How to Use

### 1. Trigger the Skill

Tell your agent:

```text
collage b-roll: Many people think AI is here to think for you, but it's really more like a mirror that reveals the hidden cracks in your questions.
```

Trigger phrases: `collage b-roll`, `paper collage b-roll`, `halftone collage`, `assemble animation`, or `gbro-collage-broll`.

### 2. Gate 1: Review Metaphor
The agent provides a concise visual metaphor proposal with key objects, color field, and assembly order. Reply `Approved` or request revisions.

### 3. Gate 2: Still Frame (Agent Direct or Nano Banana)
- By default, the agent directly generates the 9:16 still frame via built-in tools.
- If the tool is rate-limited or manual generation is requested, the agent generates `manual-image-prompt.md`.
- Copy the prompt, generate in **Nano Banana** (or Midjourney / Imagen), and save to `<item>/frames/last-frame-original.png`.
- Run `python scripts/process_frames.py --item "<item_path>" --color "<HEX>"`.
- Review `still-contact-sheet.jpg` and approve.

### 4. Gate 3: Video Assembly (Manual or Automated)
- In Manual Mode, the agent generates `manual-video-prompt.md` and `omni-prompt.txt`.
- Open Google Omni / Flow Video Generator, select Start & End frame mode:
  - Image 1: `<item>/frames/first-frame.png`
  - Image 2: `<item>/frames/last-frame.png`
  - Prompt: Copied from `manual-video-prompt.md`
  - Settings: 9:16 vertical, 3 to 10 seconds (e.g. 5s or 10s)
- Download the resulting MP4 and save to `<item>/omni/run-v01/final-5s.mp4`.
- Run `python scripts/process_video.py --item "<item_path>"` or tell the agent: *"I have saved the video."*
- The workflow automatically strips audio, generates `contact-sheet.jpg`, checks the opening frame, creates `end-frame-comparison.jpg`, and writes `gate3-qa.md`.

## Directory Structure

```text
gbro-collage-broll/
├── SKILL.md                          # Main skill documentation (Three-gate protocol, prompt templates, QA rules)
├── README.md                         # Chinese documentation
├── README.en.md                      # English documentation
├── README.ja.md                      # Japanese documentation
├── agents/openai.yaml                # Agent interface definition
├── evals/evals.json                  # Gate-behavior evaluation scenarios
└── scripts/
    ├── inspect_voiceover.py          # Voiceover duration analyzer (audio file & text)
    ├── check_setup.py                # Cross-platform environment check (Manual & API modes)
    ├── check_setup.sh                # Shell environment check
    ├── process_frames.py             # Gate 2 image ingestion, scaling, solid first-frame generator & QA
    ├── prepare_manual_video.py       # Gate 3 manual prompt & specifications generator (3s–10s)
    ├── process_video.py              # Gate 3 audio stripper, adaptive contact sheet (up to 10s) & QA verifier
    ├── generate_video.py             # Gemini Omni Flash batch video generator (with --manual support)
    ├── upload_file.py                # Files API upload helper (API mode)
    └── generate_veo_first_last.py    # Legacy Veo pipeline (retained for compatibility)
```

## FAQ

**Why require two rounds of human approval?**
Rushing directly into video generation burns time and generation quotas on flawed concepts. Adjusting text at Gate 1 is instant and free; selecting or regenerating an image at Gate 2 is far faster than redoing a full video.

**Do I need an API key to use this?**
No! Manual Mode allows you to generate all prompts, context, and keyframe assets locally, use web generators like Nano Banana and Google Omni / Flow, and let the workflow seamlessly process and QA your deliverables.

**What if the video's first frame shows paper fragments at the edge?**
Slight edge visibility is normal for neural video interpolation. For strict zero-paper beginnings, a clean solid color frame is provided as Image 1.

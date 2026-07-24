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

Compress a roughly five-second voiceover script into one sharp visual idea, then generate a premium editorial **halftone paper-collage assembly animation** B-roll clip.

Turn a ~5s voiceover line into a premium editorial paper-collage assemble-from-empty B-roll clip, powered by Gemini Omni Flash first/last-frame video generation.

## Results

- Bold, flat, solid-color paper fields + black-and-white halftone photo cutouts + colored cardstock accents
- Elements slide in, lock into place, and assemble one by one from an empty scene (with a stop-motion feel), rather than fading in or slowly zooming
- The default output is a silent 9:16, 5-second, 720×1280, 24 fps MP4 that can be placed directly under a voiceover

## Workflow: Three Approval Gates

The core of this skill is not a prompt template but a mandatory three-stage approval process, so you can focus on aesthetic judgment instead of burning through generation costs:

1. **Gate 1 · Metaphor approval** — Outputs only the visual metaphor proposal (core idea / key objects / background color / assembly order), without generating any images or video
2. **Gate 2 · Still-frame approval** — Generates a color collage still frame and contact sheet only after approval, then waits for your confirmation again
3. **Gate 3 · Video generation** — Once the still frame is approved, automatically creates a first/last-frame assembly animation with `gemini-omni-flash-preview`, including complete QA (frame extraction at one-second intervals, empty first-frame verification, and final-frame comparison)

Batch mode supports partial approval: only approved items proceed to the next stage.

## Requirements

When first invoked, the skill automatically runs `scripts/check_setup.sh` for a self-check and provides configuration guidance for anything missing. It requires:

| Dependency | Description |
|------|------|
| Codex environment | Gate 2 still-frame generation depends on the built-in `image_gen` tool |
| `GEMINI_API_KEY` | Create one in [Google AI Studio](https://aistudio.google.com/apikey); video generation is usage-based |
| Python >= 3.10 | Used by the video-generation scripts |
| `google-genai >= 2.10.0` | The skill guides you through creating a shared venv at `~/hyperframes-projects/.omni-venv/` |
| ffmpeg / ffprobe | Used for first/last-frame processing, audio-track removal, and contact sheets |

The video-generation scripts (`scripts/generate_video.py` + `scripts/upload_file.py`) are bundled with the skill, so no additional skills need to be installed.

## Installation

Place the entire directory in your agent skills directory (for example, `~/.agents/skills/` or `~/.claude/skills/`):

```bash
git clone https://github.com/pyang5166/gbro-collage-broll.git ~/.agents/skills/gbro-collage-broll
```

## Usage

Tell your agent:

```text
collage b-roll：很多人以为 AI 是来替你思考的，其实它更像一面镜子，会把你问题里的漏洞照出来。
```

Trigger phrases: `collage b-roll`, `纸拼贴 b-roll`, `半调拼贴`, `拼贴风格配画面`, and `gbro-collage-broll`.

Then confirm each step in order from Gate 1 → Gate 2 → Gate 3. You can also provide multiple lines in a batch; each line receives one metaphor and one finished clip.

## Directory Structure

```text
gbro-collage-broll/
├── SKILL.md                        # Main skill documentation (three-gate protocol + prompt templates + QA standards)
├── agents/openai.yaml              # Codex interface configuration
├── evals/evals.json                # Four gate-behavior evaluations
└── scripts/
    ├── check_setup.sh              # First-use environment self-check
    ├── generate_video.py           # Gemini Omni Flash batch video generation
    ├── upload_file.py              # Files API upload helper
    └── generate_veo_first_last.py  # Legacy Veo path (retained only for compatibility; not used by default)
```

## FAQ

**Why require two rounds of human approval?**
Sending a poor metaphor or still frame directly into video generation wastes real API spend. Revising text at Gate 1 is free, and regenerating one image at Gate 2 is far cheaper than rerunning an entire video.

**What if a small piece of paper is visible at the edge of the first frame?**
A slight overlap is acceptable. For a strictly empty opening frame, use an editable timeline animation tool to patch the beginning.

**Can I change the video model?**
The default is fixed to `gemini-omni-flash-preview`; it switches only when another model is explicitly specified.

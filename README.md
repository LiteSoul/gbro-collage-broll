# gbro-collage-broll

<p align="center">
  <a href="README.md">简体中文</a> · <a href="README.en.md">English</a> · <a href="README.ja.md">日本語</a>
</p>

<p align="center">
  <img src="assets/demo-purple.gif" width="180" alt="深紫底：多人协作压出科幻胶片">
  <img src="assets/demo-yellow.gif" width="180" alt="芥末黄底：错误被印刷机批量放大">
  <img src="assets/demo-red.gif" width="180" alt="红底：导演之手摆放棋盘走位">
  <img src="assets/demo-teal.gif" width="180" alt="青绿底：剪刀裁开镜头轨道">
</p>

把一句约 5 秒的口播文稿，压成一个 sharp visual idea，再生成高级编辑风**半调纸拼贴（halftone paper-collage）组装动画** B-roll。

同时支持**免 API 混合模式（Manual / Hybrid Mode）**与**自动化 API 模式（API Mode）**：
- **混合模式（默认 / 无需 API）**：优先由 Agent 直接调用内置生图工具生成 9:16 静帧候选省时省力；当工具受限或配额耗尽时，自动导出完整提示词与规格说明，用户可在 **Nano Banana** 或其他 AI 手动生成并存入目录。视频部分导出规格供在 Google Omni / Google Flow / Veo 网页端生成，保存文件后脚本继续自动化处理（裁剪、生成纯色首帧、去音轨、生成 contact sheet 与 QA 对照）。
- **API 模式**：通过 `GEMINI_API_KEY` 直接调用 Gemini Omni Flash 进行首尾帧视频插值。

## 效果

- 强烈平坦的纯色纸面色场 + 黑白 halftone 照片剪贴 + 彩色卡纸点缀
- 元素从空场逐件滑入、卡位、组装（stop-motion 质感），不是淡入或慢 zoom
- 默认交付 9:16、3 至 10 秒（默认 5 秒适合快节奏短视频，最长支持 10 秒展开多阶段叙事）、720×1280 或 1080×1920、24fps、无声 MP4，可直接垫在口播下面

## 口播文稿输入方式

支持两种启动输入：
1. **文稿文字（最简方式）**：直接向 agent 提供一段台词或金句。
2. **音频文件（.mp3 / .wav）**：通过 `python scripts/inspect_voiceover.py voiceover.mp3` 自动利用 `ffprobe` 检测音频确切时长，并精确计算匹配的视频时长。

> **注意（防超时规则）：** 文本口播输入时，必须先使用 `python scripts/inspect_voiceover.py "<文稿>"` 检验语速与时长。超过 18 词（~5 秒）时切勿强行默认 5 秒（否则会导致急促失真），应推荐 8–10 秒长镜头或拆分为 2 段 5 秒节奏切片。

## 工作流：三闸门审批

这个 skill 的核心不是 prompt 模板，而是强制的三阶段审批，让你把注意力花在审美判断上，而不是烧生成费用：

1. **Gate 1 · 隐喻与时长确认** — 先检验口播语速与时长，再输出视觉隐喻方案（核心意思 / 时长与节奏规划 / 关键物件 / 底色 / 组装顺序），不生成任何图片视频。
2. **Gate 2 · 静帧确认** — 确认后准备彩色拼贴静帧（`last-frame.png`）与纯色首帧（`first-frame.png`）。优先由 Agent 直接生成以节省时间；若工具不可用则导出 `manual-image-prompt.md` 供用户在 **Nano Banana** 手动生成；通过 `scripts/process_frames.py` 自动规范化并生成预览。
3. **Gate 3 · 视频生成** — 静帧通过后生成 3–10 秒首尾帧组装动画。手动模式下导出 `manual-video-prompt.md` 与首尾帧，用户在 Google Omni / Flow 手动生成后放入目录；通过 `scripts/process_video.py` 自动去音轨、逐秒抽帧（支持 10 秒自适应 5x2 预览）、首帧空场验证、尾帧对照与 QA 校验。

批量模式下支持部分通过：只有确认过的条目进入下一阶段。

## 环境要求

首次触发时 skill 会自动运行环境自检：

```bash
# 跨平台自检（默认检查手动模式）
python scripts/check_setup.py

# 检查 API 模式
python scripts/check_setup.py --mode api
```

| 依赖 | 手动模式（默认） | API 模式 | 说明 |
|---|---|---|---|
| Python >= 3.10 | 必需 | 必需 | 用于辅助与 QA 脚本 |
| ffmpeg / ffprobe | 必需 | 必需 | 首尾帧处理、纯色首帧生成、去音轨、contact sheet |
| `GEMINI_API_KEY` | **无需** | 必需 | [Google AI Studio](https://aistudio.google.com/apikey) 创建 |
| `google-genai` | **无需** | 必需（>= 2.10.0） | 用于直接 API 调用 |

## 目录结构

```text
gbro-collage-broll/
├── SKILL.md                          # skill 主文档（三闸门协议 + 手动/API双模式 + prompt 模板 + QA 标准）
├── README.md                         # 中文说明
├── README.en.md                      # 英文说明
├── README.ja.md                      # 日文说明
├── agents/openai.yaml                # Codex / Agent interface 配置
├── evals/evals.json                  # 四条闸门行为评测
└── scripts/
    ├── inspect_voiceover.py          # 口播时长检测与分析工具（音频文件与文本估算）
    ├── check_setup.py                # 跨平台环境自检（支持 manual 与 api 模式）
    ├── check_setup.sh                # Shell 环境自检脚本
    ├── process_frames.py             # Gate 2 静帧处理、自动生成纯色首帧与预览
    ├── prepare_manual_video.py       # Gate 3 手动视频提示词与规格说明导出（支持 3-10 秒）
    ├── process_video.py              # Gate 3 视频后处理、去音轨、自适应抽帧对比与 QA
    ├── generate_video.py             # Gemini Omni Flash 视频生成（含 --manual 导出支持）
    ├── upload_file.py                # Files API 上传辅助
    └── generate_veo_first_last.py    # 旧 Veo 链路（仅兼容保留）
```

## FAQ

**需要 API Key 才能用吗？**
不需要！混合/手动模式下完全无需额外 API Key，Agent 会直接利用内置生图工具生成静帧候选；若需手动生成亦可使用 Nano Banana 等外部工具。视频部分参数与首尾帧都会写入项目文件供在 Google Omni 或 Google Flow 网页端生成，后续去音轨与 QA 全自动执行。

**为什么强制两次人工确认？**
错误的隐喻或静帧直接进视频生成，浪费的是宝贵的时间和精力。Gate 1 改文字是即时且零成本的，Gate 2 挑选或重做一张图远比重跑一条视频便宜高效。

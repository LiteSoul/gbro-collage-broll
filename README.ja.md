# gbro-collage-broll

<p align="center">
  <a href="README.md">简体中文</a> · <a href="README.en.md">English</a> · <a href="README.ja.md">日本語</a>
</p>

<p align="center">
  <img src="assets/demo-purple.gif" width="180" alt="濃い紫の背景：複数人の共同作業で SF 風フィルムを押し出す">
  <img src="assets/demo-yellow.gif" width="180" alt="マスタードイエローの背景：印刷機がエラーを大量に増幅する">
  <img src="assets/demo-red.gif" width="180" alt="赤い背景：監督の手が盤上に配置を並べる">
  <img src="assets/demo-teal.gif" width="180" alt="青緑の背景：ハサミがショットのトラックを切り開く">
</p>

約 5 秒のナレーション原稿を 1 つの鋭いビジュアルアイデアに凝縮し、上質なエディトリアル調の **ハーフトーン・ペーパーコラージュ組み立てアニメーション** B-roll を生成します。

約 5 秒のナレーションから、Gemini Omni Flash の始点・終点フレーム動画生成を利用して、空の状態から組み上がる上質なエディトリアル調ペーパーコラージュ B-roll を作成します。

## 仕上がり

- 鮮烈でフラットな単色の紙面 + 白黒ハーフトーン写真の切り抜き + 色紙のアクセント
- 要素が空の画面へ 1 つずつ滑り込み、位置に収まり、組み上がるストップモーション風の動き。フェードインや緩やかなズームではありません
- デフォルトでは 9:16、5 秒、720×1280、24 fps、無音の MP4 を出力し、そのままナレーション映像の下に配置できます

## ワークフロー：3 つの承認ゲート

この Skill の中心はプロンプトテンプレートではなく、必須の 3 段階承認です。生成費用を浪費せず、美的判断に集中できます。

1. **Gate 1 · メタファーの承認** — ビジュアルメタファー案（中心となる意味 / 主要オブジェクト / 背景色 / 組み立て順）のみを出力し、画像や動画は生成しません
2. **Gate 2 · 静止画の承認** — 承認後にのみカラーコラージュの静止画とコンタクトシートを生成し、再度確認を待ちます
3. **Gate 3 · 動画生成** — 静止画の承認後、`gemini-omni-flash-preview` で始点・終点フレームの組み立てアニメーションを自動生成し、完全な QA（1 秒ごとのフレーム抽出、始点の空画面確認、終点フレームの比較）を行います

バッチモードでは一部のみの承認にも対応し、承認された項目だけが次の段階へ進みます。

## 動作要件

初回実行時に Skill が `scripts/check_setup.sh` を自動実行してセルフチェックを行い、不足している項目の設定方法を案内します。必要なものは次のとおりです。

| 依存関係 | 説明 |
|------|------|
| Codex 環境 | Gate 2 の静止画生成は組み込みの `image_gen` ツールを使用します |
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/apikey) で作成します。動画生成は従量課金です |
| Python >= 3.10 | 動画生成スクリプトで使用します |
| `google-genai >= 2.10.0` | Skill が共有 venv `~/hyperframes-projects/.omni-venv/` の作成を案内します |
| ffmpeg / ffprobe | 始点・終点フレームの処理、音声トラックの削除、コンタクトシートの作成に使用します |

動画生成スクリプト（`scripts/generate_video.py` + `scripts/upload_file.py`）は Skill に同梱されているため、ほかの Skill を追加でインストールする必要はありません。

## インストール

ディレクトリ全体を Agent の Skills ディレクトリ（例：`~/.agents/skills/` または `~/.claude/skills/`）へ配置します。

```bash
git clone https://github.com/pyang5166/gbro-collage-broll.git ~/.agents/skills/gbro-collage-broll
```

## 使い方

Agent に次のように伝えます。

```text
collage b-roll：很多人以为 AI 是来替你思考的，其实它更像一面镜子，会把你问题里的漏洞照出来。
```

トリガーフレーズ：`collage b-roll`、`纸拼贴 b-roll`、`半调拼贴`、`拼贴风格配画面`、`gbro-collage-broll`。

その後、Gate 1 → Gate 2 → Gate 3 の順に確認します。複数の原稿をまとめて渡すこともでき、各文に対して 1 つのメタファーと 1 本の完成動画が生成されます。

## ディレクトリ構成

```text
gbro-collage-broll/
├── SKILL.md                        # Skill のメインドキュメント（3 ゲートの手順 + プロンプトテンプレート + QA 基準）
├── agents/openai.yaml              # Codex インターフェース設定
├── evals/evals.json                # 4 つのゲート動作評価
└── scripts/
    ├── check_setup.sh              # 初回使用時の環境セルフチェック
    ├── generate_video.py           # Gemini Omni Flash のバッチ動画生成
    ├── upload_file.py              # Files API アップロード補助
    └── generate_veo_first_last.py  # 旧 Veo 経路（互換性のためだけに保持。デフォルトでは未使用）
```

## FAQ

**なぜ人間による確認を 2 回必須にするのですか？**
不適切なメタファーや静止画をそのまま動画生成へ送ると、実際の API 費用が無駄になります。Gate 1 での文章修正は無料で、Gate 2 で画像を 1 枚再生成する方が動画全体をやり直すよりはるかに安価です。

**完成動画の始点フレーム端に紙片が少し見える場合は？**
わずかなはみ出しは許容できます。厳密に空の始点フレームが必要な場合は、編集可能なタイムライン式アニメーションツールで冒頭を補正してください。

**動画モデルを変更できますか？**
デフォルトは `gemini-omni-flash-preview` に固定されており、別のモデルを明示的に指定した場合にのみ切り替わります。

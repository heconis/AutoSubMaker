# AutoSubMaker

AutoSubMaker は、動画から音声を抽出し、ローカル Whisper で文字起こしを行い、字幕ファイル生成と字幕焼きこみを自動化する Windows 向けアプリです。

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e .[dev]
python -m autosubmaker
```

## Docs

- `docs/requirements.md`: 要件整理
- `docs/ui_design.md`: 画面構成案
- `docs/project_structure.md`: プロジェクト構成案

## Status

- NiceGUI のネイティブウィンドウで起動する土台を追加済み
- 設定保存、FFmpeg 検出、Whisper モデル配置確認の骨組みを追加済み
- 実際の FFmpeg ダウンロード、Whisper 文字起こし、字幕生成、焼きこみは次段階で実装予定

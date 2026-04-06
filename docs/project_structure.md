# AutoSubMaker プロジェクト構成案

## 1. 基本方針

MVP の段階から、UI と処理ロジックを分離した構成にする。

- `NiceGUI` の画面コードと動画処理コードを分離する
- FFmpeg / Whisper 呼び出しは専用ラッパーへ閉じ込める
- ジョブ管理を中心に処理フローを組み立てる
- 将来の翻訳、話者分離、字幕編集に拡張しやすくする

## 2. 推奨ディレクトリ構成

```text
AutoSubMaker/
  docs/
    requirements.md
    ui_design.md
    project_structure.md
  src/
    autosubmaker/
      __init__.py
      main.py
      bootstrap/
        startup.py
        dependency_check.py
      config/
        app_paths.py
        app_settings.py
        settings_store.py
      ui/
        app_shell.py
        pages/
          main_page.py
        components/
          header_bar.py
          input_card.py
          job_table.py
          settings_panel.py
          log_panel.py
        dialogs/
          setup_dialog.py
          error_dialog.py
      models/
        app_status.py
        job.py
        media_info.py
        transcription_options.py
        subtitle_options.py
        subtitle_style.py
        process_result.py
      services/
        environment_service.py
        ffmpeg_download_service.py
        whisper_model_service.py
        media_probe_service.py
        queue_service.py
        audio_extract_service.py
        transcription_service.py
        subtitle_service.py
        burnin_service.py
        output_service.py
      integrations/
        ffmpeg_runner.py
        whisper_runner.py
      utils/
        logger.py
        process_runner.py
        timecode.py
        text_splitter.py
  tests/
    test_text_splitter.py
    test_timecode.py
    test_subtitle_service.py
```

## 3. 主要モジュールの責務

### 3.1 `main.py`

役割:

- アプリ起動の入口
- 起動時初期化の開始
- UI シェル起動

### 3.2 `bootstrap/`

役割:

- 起動時の前処理
- 設定読込
- ディレクトリ作成
- 依存チェック

主な責務:

- アプリ管理ディレクトリの初期化
- FFmpeg パス解決
- Whisper モデル存在確認
- 起動時状態の集約

### 3.3 `config/`

役割:

- 設定値と保存先の管理

対象:

- 出力先
- FFmpeg パス
- モデルサイズ
- 字幕設定
- スタイル設定
- ウィンドウ設定

### 3.4 `ui/`

役割:

- NiceGUI コンポーネント定義
- ページ構築
- ダイアログ表示
- ユーザー操作イベント処理

注意点:

- 動画処理ロジックを直接書き込まない
- サービス層呼び出しに留める

### 3.5 `models/`

役割:

- 画面と処理間で受け渡すデータ構造の定義

例:

- ジョブ状態
- メディア情報
- 文字起こし設定
- 字幕設定
- 処理結果

### 3.6 `services/`

役割:

- アプリのユースケース実装

主な担当:

- 依存解決
- キュー制御
- 音声抽出
- 文字起こし
- 字幕整形
- 焼きこみ
- 出力整理

### 3.7 `integrations/`

役割:

- 外部ツール呼び出しの集約

対象:

- FFmpeg 実行
- Whisper 実行

注意点:

- コマンド構築と標準出力処理をまとめる
- 失敗時の例外をアプリ向けの形に変換する

### 3.8 `utils/`

役割:

- 汎用処理

対象:

- ログ整形
- 時刻変換
- 字幕分割補助
- サブプロセス実行補助

## 4. アプリ管理ディレクトリ案

Windows では以下を基本案とする。

```text
%LOCALAPPDATA%/AutoSubMaker/
  config/
  bin/
    ffmpeg/
  models/
    whisper/
  logs/
  temp/
  outputs/
```

用途:

- `config/`: 設定 JSON
- `bin/ffmpeg/`: 自動取得した FFmpeg
- `models/whisper/`: 初回取得したモデル
- `logs/`: 実行ログ
- `temp/`: 中間音声、一時 ASS
- `outputs/`: 既定出力先候補

## 5. データフロー

1. UI が動画追加を受け取る
2. `queue_service` がジョブを生成する
3. `media_probe_service` が動画情報を読む
4. `audio_extract_service` が中間音声を作る
5. `transcription_service` が文字起こしする
6. `subtitle_service` が SRT / ASS を生成する
7. `burnin_service` が必要時のみ焼きこみする
8. `output_service` が成果物整理と後始末を行う

## 6. 初期実装の入口ファイル

最初に作ると流れが作りやすいファイルは以下。

1. `src/autosubmaker/main.py`
2. `src/autosubmaker/bootstrap/startup.py`
3. `src/autosubmaker/config/app_paths.py`
4. `src/autosubmaker/config/app_settings.py`
5. `src/autosubmaker/ui/app_shell.py`
6. `src/autosubmaker/ui/pages/main_page.py`
7. `src/autosubmaker/services/environment_service.py`
8. `src/autosubmaker/services/queue_service.py`

## 7. 初期実装順

### Phase 1: 土台

- パス管理
- 設定保存
- ログ出力
- 起動時チェック

### Phase 2: 外部依存

- FFmpeg 検出
- FFmpeg 自動取得
- Whisper モデル取得
- サブプロセス実行ラッパー

### Phase 3: コア処理

- 動画情報取得
- 音声抽出
- 文字起こし
- SRT 生成
- ASS 生成
- 字幕焼きこみ

### Phase 4: UI

- メイン画面
- セットアップダイアログ
- キューテーブル
- 設定パネル
- ログ表示

### Phase 5: 仕上げ

- エラー表示改善
- テスト追加
- 配布方法整備

## 8. テスト優先対象

MVP でも以下は先にテストを書きやすい。

- 時刻変換
- 日本語字幕分割
- 出力ファイル名生成
- ジョブ状態遷移

## 9. MVP 後に追加しやすい拡張

- 字幕プレビュー
- 手動字幕編集
- 自動翻訳
- 話者分離
- プリセット管理

この構成であれば、まずはシンプルに作りつつ、動画処理アプリとしての拡張余地も十分に残せる。

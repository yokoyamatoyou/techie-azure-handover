# Phase06 Migration Note

## 変更概要
- `newalgorithm_pipeline` の監査ログ出力に互換フォールバックを追加。
- `latest_generation_output.json` に互換メタ（`log_compat_version`, `compatibility`）を追加。
- ログテキストのサニタイズを追加し、改ざん誘導文の混入影響を低減。

## 影響範囲
- 既存の主要キー参照ロジック（title/body/full_text 等）は変更不要。
- 拡張キーを利用する場合のみ、運用側で追加対応を検討。

## 主要差分
- `note/newalgorithm_pipeline/telemetry_writer.py`
  - 追加: `CORE_AUDIT_KEYS`
  - 追加: 欠損フォールバック（`status`, `article_type`, `media`, `warnings`）
  - 追加: 文字列サニタイズ（改行/制御文字除去、長文抑制）
- `note/newalgorithm_pipeline/pipeline.py`
  - 追加: `runtime_error_class`, `runtime_reason_code` をレスポンスに明示
  - 追加: エラー時監査ログに `article_type`, `media` を補完
- `note/note_writer_app.py`
  - 追加: `generation_audit_log.jsonl` 出力時の互換キー補完
  - 追加: `latest_generation_output.json` に `log_compat_version` と `compatibility` を記録

## 運用チェック項目
- 既存参照が使うキー（`title`, `body`, `full_text`, `runtime_reason_code`）が欠けていないこと
- 監査ログ1行1JSONの形式が維持されること
- `reason_code` 欠損時に `OK` が補完されること

## ロールバック方針
- 条件: 既存監視が互換拡張キーの影響で誤動作
- 手順:
  1. `telemetry_writer.py` の `_ensure_compat_record` を最小セット（主要キーのみ）へ戻す
  2. `note_writer_app.py` の `compatibility` 追加ブロックを無効化
  3. Phase06テストを再実行して主要キー読取のみを確認

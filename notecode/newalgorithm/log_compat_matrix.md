# Phase06 Log Compatibility Matrix

## 方針
- 互換モード: `quasi_strict`
- 基本方針: 既存運用が参照する主要キーは維持し、追加情報は拡張キーとして追加する。
- 対象ログ:
  - `notecode/logs/latest_generation_output.json`
  - `notecode/logs/generation_audit_log.jsonl`
  - `notecode/logs/newalgorithm_pipeline_audit.jsonl`

## 主要キー互換（維持対象）
- `timestamp`
- `attempt_id`
- `article_type`
- `title`
- `lead`
- `body`
- `references`
- `hashtags`
- `full_text`
- `runtime_reason_code`

## ログ別マッピング
- `latest_generation_output.json`
  - 維持: 主要キー + `pipeline_check` + `input_contract`
  - 追加: `log_compat_version`, `compatibility.mode`, `compatibility.core_keys`, `quality_pipeline_check`
- `generation_audit_log.jsonl`
  - 維持: `timestamp`, `attempt_id`, `article_type`, `runtime_reason_code`, `runtime_error_class`
  - 追加: `status`, `media`, `warnings`（欠損時フォールバックあり）
- `newalgorithm_pipeline_audit.jsonl`
  - 維持: `status`, `reason_code`, `article_type`, `media`, `fallback_used`, `warnings`
  - 追加: `legal_risk_level`, `legal_issue_count`

## 欠損時フォールバック（Phase06追加）
- `reason_code` 未指定: `OK`
- `runtime_reason_code` 未指定: `reason_code` を継承
- `runtime_error_class` 未指定:
  - `INP_*` -> `user_input`
  - `POL_*` -> `policy`
  - `TRN_*` -> `transient`
  - その他 -> `system`
- `article_type` 未指定: `unknown`
- `media` 未指定: `note`
- `warnings` 未指定: `[]`

## 非互換リスク（要監視）
- `pip_audit` 実行時の Windows 文字コード例外により、依存脆弱性チェックが自動化し切れていない。
- 回避策は `dependency_risk_report_phase06.md` を参照。

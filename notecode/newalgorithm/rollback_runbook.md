# Phase07 Rollback Runbook

## 目的
- 受入後に障害が発生した場合、サービス停止時間を最小化して安全状態へ戻す。

## ロールバック発動条件
- 受入基準のいずれか未達
- 連続失敗、またはリーガル誤検知多発で運用継続不可
- 主要ログキー欠損により既存監視が機能しない

## レベル0（即時運用回復）
- 対象: リーガル自動実行が原因の遅延・誤検知
- 手順:
  1. 環境変数 `LEGAL_POSTCHECK_AUTO_ENABLED=0` を設定
  2. アプリを再起動
  3. 生成後リーガルは手動再チェック運用へ切替（本文生成は継続）
- 復帰判定:
  - 生成成功率が回復し、本文保持が継続する

## レベル1（Phase06安定構成への戻し）
- 対象: Phase07受入判定でNo-Go
- 手順:
  1. `acceptance_report.md` のFail項目を特定
  2. `note/tests/test_newalgorithm_phase06_logging_compat.py` を再実行し、ログ互換を再確認
  3. `LEGAL_POSTCHECK_AUTO_ENABLED=0` を維持して運用安定化
  4. 問題修正後に `LEGAL_POSTCHECK_AUTO_ENABLED=1` へ戻して再検証
- 復帰判定:
  - Phase06/07の必須テストが再び全PASS

## レベル2（監査ログ保守モード）
- 対象: 監査ログ連携障害
- 手順:
  1. `log_compat_matrix.md` の主要キーのみ参照するよう運用側連携を一時限定
  2. `generation_audit_log.jsonl` と `newalgorithm_pipeline_audit.jsonl` の `reason_code` / `status` を監視
  3. 連携復旧後に拡張キー参照を段階再開

## 検証チェックリスト（ロールバック後）
- 生成ボタンで本文生成が成功する
- 本文が保持される（リーガル失敗時を含む）
- 手動リーガル再チェックが動作する
- `latest_generation_output.json` の主要キーが存在する
- `generation_audit_log.jsonl` に `reason_code` が記録される

## 連絡・記録
- 発動時は `WORKLOG.md` に以下を記録:
  - 発動時刻
  - 発動レベル（0/1/2）
  - 原因
  - 復旧時刻
  - 再発防止策

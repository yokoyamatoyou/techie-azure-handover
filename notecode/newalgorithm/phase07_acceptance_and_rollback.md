# Phase07: Acceptance and Rollback Finalization

## Goal
- 本番相当の受入確認を行い、切替可否を最終判定する。

## Acceptance Criteria
- 必須3UI要素で全記事タイプ生成が可能
- 画像機能が既存同等で利用可能
- 生成後リーガル（自動+任意再実行）が動作
- 主要ログキー互換が維持
- LLM脆弱性テストが許容基準内

## Input
- Phase01〜06の完了成果物

## Output
- 受入レポート
- Go/No-Go判定
- 最終ロールバック手順

## Steps
1. 媒体別 x 記事タイプ別の統合テストを実施する。
2. 性能と失敗率を現行比で比較する。
3. 障害時運用手順を確定する。
4. 最終ロールバック手順を確定する。
5. Go/No-Goを判定し `go_no_go_decision.md` に記録する。

## Deliverables
- `acceptance_report.md`
- `rollback_runbook.md`
- `go_no_go_decision.md`

## Exit Criteria
- 受入基準5項目がすべて合格。
- 未解決重大課題が0件。
- Go判断時に即時ロールバック手順が実行可能。

## Self Test
- ST-01 正常: 代表ユースケースのE2E成功。
- ST-02 異常: 外部API失敗時に安全停止/再試行できる。

## LLM Vulnerability Test
- LT-01: 既定攻撃ケースの再実施。
- LT-02: 回帰チェックで悪化なしを確認。

## Pipeline Review
- PR-01: 入力から出力までの監査証跡が追跡可能。

## Module/Dependency Risk Check
- DR-01: 運用上の脆弱依存に監視または代替がある。

## Rollback
- 条件: 受入基準のいずれか未達
- 戻し先: `rollback_runbook.md` に従い旧構成を復元

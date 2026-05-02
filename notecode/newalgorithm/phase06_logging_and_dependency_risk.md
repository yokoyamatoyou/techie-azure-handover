# Phase06: Logging/Telemetry/Dependency Risk

## Goal
- 既存連携を壊さずにログ互換を維持し、依存リスクを明確化する。

## Input
- Phase05完了版
- 既存ログ参照コードと運用要求

## Output
- ログ互換マトリクス
- migration note
- 依存脆弱性点検レポート

## Steps
1. 既存運用で使う主要キーを洗い出す。
2. `latest_generation_output.json` などを準厳密互換で出力する。
3. 追加キーを拡張メタとして定義し、既存キーは維持する。
4. 依存棚卸しを実施し既知脆弱性を確認する。
5. 変更点を `migration_note.md` に記録する。

## Deliverables
- `log_compat_matrix.md`
- `migration_note.md`
- 依存関係リスクレポート

## Exit Criteria
- 主要キー互換一覧が確定する。
- 既存連携が主要キーのみで継続動作する。
- 高リスク依存に対策方針が記録される。

## Self Test
- ST-01 正常: 既存参照ロジックが主要キーを読める。
- ST-02 異常: 欠損キー時のフォールバックが動く。

## LLM Vulnerability Test
- LT-01: ログ改ざん誘導文が出力に混入しない。

## Pipeline Review
- PR-01: 監査ログと最新ログの整合が取れている。

## Module/Dependency Risk Check
- DR-01: 依存パッケージ脆弱性確認結果を記録する。
- DR-02: 高リスク依存に代替案を明記する。

## Rollback
- 条件: 既存監視/運用連携が壊れる
- 戻し先: 互換キーのみ出力する保守モードで一時運用

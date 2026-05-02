# NEW ALGORITHM PROGRESS

- Last Updated: 2026-03-07
- Current Phase: Phase07（completed）
- Next Action: 本番運用監視（4週間）と削除候補の最終判定

## Phase Status
| Phase | Name | Status | Owner | Exit Criteria |
|---|---|---|---|---|
| Phase01 | Scope/UI Contract Fix | completed | AI+User | UI項目対応表と記事タイプ表が確定 |
| Phase02 | Archive Plan/Preparation | completed | AI | 承認後archive実行手順が確定 |
| Phase03 | Minimal Pipeline Build | completed | AI | contract→generate→dedupe→output が疎通 |
| Phase04 | UI Wiring/Cleanup | completed | AI | 必須3要素で生成完了、不要UI整理完了 |
| Phase05 | Editor/Legal/Safety | completed | AI | 編集1層・自動リーガル・再実行導線が動作 |
| Phase06 | Logging/Telemetry/Deps | completed | AI | 主要ログキー互換と依存脆弱性点検完了 |
| Phase07 | Acceptance/Rollback | completed | AI+User | 受入基準達成、ロールバック手順確定 |

## Mandatory Checks Per Phase
- Self Test: 正常系/異常系の実行ログを残す
- LLM Vulnerability Test: 注入・越権・危険誘導を検証
- Pipeline Review: 契約→生成→後処理→ログの疎通確認
- Module/Dependency Risk: 依存棚卸しと既知脆弱性確認
- Rollback Condition: 明確な戻し条件と復元先を記載

## Execution Rule
- 1つのPhaseで必須テストが1件でも失敗した場合は `in_progress` のまま修正する。
- Exit Criteria 達成後のみ次Phaseを `in_progress` に変更する。
- 進行更新時は `Last Updated`, `Current Phase`, `Next Action` を同時更新する。

## Open Questions
- なし（2026-03-07時点で解消済み）

## Open Questions Resolved
- 削除候補のログ判定期間
  - 決定: 4週間（安定化判定の観測期間を確保）
- 固定7タイプ運用に合わせたカスタムジャンル導線の停止時期
  - 決定: Phase04で非表示開始（即時削除は行わない）

## Phase01 Completion Evidence
- Deliverables
  - `ui_mapping_table.md`: 全UI項目を `残す/非表示/削除` へ分類、`未分類=0`
  - `article_type_matrix.md`: 7固定キーを凍結し、legacy -> 固定キーの互換マッピングを確定
  - `input_contract_draft.md`: required/optional/normalized/validation を v1として確定
- 実装
  - `note/input_contract_v1.py` を追加（正規化/検証、`style_compact_for_seo` system-owned化）
  - `note/note_writer_app.py` で生成前に input contract v1 正規化/検証を適用
  - `note/article_generator.py` の telemetry `pipeline_check.input_contract` に `media` / `style_compact_for_seo` / `question_mode` / `contract_version` を追加
- Mandatory Checks
  - ST-01: PASS（7記事タイプ正規化）
  - ST-02: PASS（未定義記事タイプで `validation_error`）
  - LT-01: PASS（注入文字列混入でもsystem-owned正規化を維持）
  - LT-02: PASS（`style_compact_for_seo` 越権上書きを拒否）
  - PR-01: PASS（UI相当payloadからcontract項目落ち0）
  - DR-01: PASS（`pip-audit` で既知脆弱性なし）

## Phase02 Completion Evidence
- Deliverables
  - `archive_execution_runbook.md`: archive実行手順、禁止操作、実行後チェックリストを確定
  - `archive_target_inventory.md`: docs/worklog/codeの移動対象を明示パスで確定（wildcardなし）
  - `restore_guide.md`: 復元手順、missing path回復手順、最終確認手順を確定
- Mandatory Checks
  - ST-01: PASS（runbookの手順順序を追跡可能）
  - ST-02: PASS（missing path回復手順を記載）
  - LT-01: PASS（過剰削除/ワイルドカード移動の拒否を明記）
  - PR-01: PASS（必須3UI要素 + 画像機能の維持確認項目を明記）
  - DR-01: PASS（共有モジュールを移動対象から除外）

## Phase03 Completion Evidence
- Deliverables
  - 最小実装コード（`note/newalgorithm_pipeline/`）
  - フロー図（`phase03_pipeline_flow.md`）
  - I/O仕様メモ（`phase03_pipeline_io_spec.md`）
  - 最小エラーコード一覧（`phase03_error_codes.md`）
- Mandatory Checks
  - ST-01: PASS（3媒体 x 7記事タイプ生成成功）
  - ST-02: PASS（source未指定時に `INP_MISSING_REQUIRED`）
  - ST-03: PASS（article_type不正時に `INP_UNSUPPORTED_ARTICLE_TYPE`）
  - ST-04: PASS（LLM失敗時にretry/fallback動作）
  - LT-01: PASS（注入パターンを検出して無効化）
  - LT-02: PASS（危険な法務断定を緩和）
  - PR-01: PASS（各ステップI/O契約を明示）
  - PR-02: PASS（途中失敗時に reason_code と error payload を記録）
  - DR-01: PASS（新規依存追加なし）

## Phase04 Completion Evidence
- Deliverables
  - `note/note_writer_app.py`: UI生成導線を `MinimalPipeline` へ一本化し、旧 `generator.generate` 直結を除去
  - `note/tests/test_newalgorithm_phase04_ui_wiring.py`: UI接続・注入耐性・トレース性・旧直結排除の検証を追加
  - `newalgorithm/phase04_cleanup_candidates.md`: 非表示開始候補とログ根拠（例外画面含む）を整理
- Mandatory Checks
  - ST-01: PASS（固定7記事タイプでUI選択肢を表示、生成経路は新パイプラインへ接続）
  - ST-02: PASS（legacy入力 `article_type=ai` でも contract正規化で生成継続）
  - LT-01: PASS（UI入力由来の注入文字列を `SEC_PROMPT_INJECTION_BLOCKED` で検出）
  - PR-01: PASS（`pipeline_check` に `input_contract` / `io_contract` を保持し追跡可能）
  - DR-01: PASS（UI層ソースに `generator.generate(` の直接呼び出しなし）

## Phase05 Completion Evidence
- Deliverables
  - `note/newalgorithm_pipeline/editor_guard.py`: 重複行除去・軽微文法補修を追加
  - `note/newalgorithm_pipeline/legal_postcheck.py`: 生成後リーガル/セキュリティのルールベース検査を追加
  - `note/newalgorithm_pipeline/pipeline.py`: legal_postcheck自動実行を組込み（fail-openで本文保持）
  - `note/newalgorithm_pipeline/telemetry_writer.py`: `legal_postcheck` ステップと `legal_report` を追跡対象に追加
  - `note/note_writer_app.py`: 生成後リーガル結果の同画面表示 + 1クリック再チェック + 提案反映導線を実装
  - `note/tests/test_newalgorithm_phase05_legal_editor.py`: ST/LT/PR/DR検証を追加
- Mandatory Checks
  - ST-01: PASS（生成直後に `legal_postcheck` 結果を取得・表示）
  - ST-02: PASS（legal失敗時も本文保持、再実行可能）
  - LT-01: PASS（注入文字列を継続検出）
  - LT-02: PASS（越権命令文言を `[REMOVED]` 化し警告付与）
  - LT-03: PASS（危険断定を緩和）
  - PR-01: PASS（`editor_guard -> legal_postcheck` の順序固定）
  - DR-01: PASS（legalモジュールに外部依存追加なし）

## Phase06 Completion Evidence
- Deliverables
  - `newalgorithm/log_compat_matrix.md`: 主要キー互換とフォールバック規約を定義
  - `newalgorithm/migration_note.md`: 互換変更点と移行手順を記録
  - `newalgorithm/dependency_risk_report_phase06.md`: 依存リスク評価と代替案を記録
  - `note/newalgorithm_pipeline/telemetry_writer.py`: 監査ログの互換フォールバック + サニタイズを実装
  - `note/newalgorithm_pipeline/pipeline.py`: `runtime_error_class` / `runtime_reason_code` の明示、エラー時監査キー補完
  - `note/note_writer_app.py`: `generation_audit_log.jsonl` 出力の互換補完、`latest_generation_output.json` へ互換メタ追加
  - `note/tests/test_newalgorithm_phase06_logging_compat.py`: ST/LT/PR/DR検証を追加
- Mandatory Checks
  - ST-01: PASS（主要キーを既存参照ロジックが読める）
  - ST-02: PASS（欠損キー時のフォールバック動作）
  - LT-01: PASS（ログ改ざん誘導文をサニタイズ）
  - PR-01: PASS（監査ログと生成結果の reason_code 整合）
  - DR-01: PASS（依存リスク点検結果を記録）
  - DR-02: PASS（高リスク依存の代替案を記録）

## Phase07 Completion Evidence
- Deliverables
  - `newalgorithm/acceptance_report.md`: 受入基準5項目の判定と根拠を記録
  - `newalgorithm/rollback_runbook.md`: 即時運用回復を含む最終ロールバック手順を確定
  - `newalgorithm/go_no_go_decision.md`: Go/No-Go判定を記録
  - `note/tests/test_newalgorithm_phase07_acceptance.py`: 受入最終検証（ST/LT/PR/DR）を追加
  - `note/note_writer_app.py`: `LEGAL_POSTCHECK_AUTO_ENABLED` の運用スイッチを追加
- Mandatory Checks
  - ST-01: PASS（媒体別 x 記事タイプ別の統合生成成功）
  - ST-02: PASS（外部API失敗時に fallback で安全継続）
  - LT-01: PASS（既定攻撃ケース再実施で防御維持）
  - LT-02: PASS（危険断定誘導の回帰悪化なし）
  - PR-01: PASS（入力から出力まで監査証跡を追跡可能）
  - DR-01: PASS（脆弱依存に監視/代替案を維持）

## Reference
- Main Plan: `MASTER_PLAN.md`
- Phase docs: `phase01_scope_ui_contract.md` 〜 `phase07_acceptance_and_rollback.md`

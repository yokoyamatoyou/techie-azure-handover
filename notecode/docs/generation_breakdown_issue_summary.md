# 生成ブログの「破綻」課題整理

最終更新: 2026-03-07  
対象: `C:\tetie\notecode`（zero_base_v2）  
参照: `AGENTS.md` / `ALGORITHM.md` / `docs/generation_failure_prevention_log.md` / `puran6/PROGRESS.md` / `@algorithm-proposals`

## 1. 破綻の種類と対応状況

「生成ブログの生成が破綻する」を次の4種に整理し、現行の対策・参照先を対応づける。

| 種類 | 症状例 | 主な原因（ドキュメント上の指摘） | 現行対策・参照 |
|------|--------|----------------------------------|----------------|
| **構造的破綻** | 論点飛び、見出しと本文の乖離、橋渡し不足 | 談話計画なしで文を先に作る／長文で計画が粗い（改善提案・UAC-SD） | zero_base_v2 の Discourse Plan + note_4000 planner。§4.1–4.2 ALGORITHM.md |
| **意味の拡散・重複** | 同趣旨の反復、セクション間の意味重複 | 生成時に重複抑止が弱く後段に依存（UAC-SD・Codex提案） | semantic_dedupe（embedding + rewrite_enabled）。config.json `semantic_dedupe`。fail-open 時は監査ログで確認 |
| **契約破綻** | 話者・読者・主題の不整合、禁止話題への逸脱 | 話者/pronoun/relationship の hard 条件が未接続だった（F-2026-03-06-03） | output guard の SYS_SPEAKER_CONTRACT_MISMATCH / SYS_FORBIDDEN_TOPIC_DRIFT / SYS_CONTRACT_ALIGNMENT_MISMATCH。1回リトライ後に fail-closed。generation_failure_prevention_log |
| **品質破綻** | 平坦化、具体例欠如、商品説明欠落、本文が無難で単調 | 禁止列挙偏重・自然さ指標の過剰 fail-closed（F-2026-03-06-04） | section prompt を短い肯定形へ。hard_soft_eval は observe-only。natural_style_profile 注入。PROGRESS §6.1 |

このほか、**後処理による握り潰し**（メタ除去の二重適用・一人称/接続語の置換で文が崩れる）は PROGRESS §1 の「文章が破綻する主因」として phase04 で対策済み（clean_meta 1回化・企業語は置換しない・複合接続語を触らない）。

## 2. 破綻時に確認するログ・設定

- **直近出力**: `notecode/logs/latest_generation_output.txt`（生本文）
- **監査・契約・guard**: `notecode/logs/latest_generation_output.json`  
  - `runtime_reason_code` / `pipeline_check` / `contract_alignment` / `section_contract_reports` / `semantic_dedupe`
- **品質サマリ**: `notecode/logs/latest_generation_quality_report.json`
- **履歴**: `notecode/logs/generation_audit_log.jsonl`
- **設定**: `config.json` の `semantic_dedupe`（`enabled` / `rewrite_enabled` / `similarity_threshold`）

guard で停止した場合は `reason_code` が `SYS_*` のいずれかになる。契約系は停止前に1回だけ自動補修リトライする（ALGORITHM.md §5）。

## 3. algorithm-proposals との対応

- **ブログ生成AIアルゴリズムの改善提案.md**  
  談話計画の先行、語彙連鎖、Burstiness/Perplexity 制御、後処理を「人間化の主戦場」とする設計。現行の zero_base_v2 は「談話計画 → section 生成 → coherence/dedupe → minimal postprocess」でこれに沿う。
- **CODEX_UACSD_ZERO_BASE_ALGORITHM_2026-03-03.md**  
  Intent Contract・Semantic Dedupe Gate・Coherence Bridge・最小後処理を提案。現行は semantic_dedupe で意味重複抑止、bridge は discourse plan の `bridge_hint` 等で部分対応。A/B 候補選抜は未導入。

## 4. 次のアクション（優先度の目安）

1. **再現条件の特定**  
   どの記事タイプ・どの入力（URL/テーマ/カテゴリ）で破綻するかを1ケースでもよいので特定し、`latest_generation_output.json` の `attempt_id` と `runtime_reason_code` / `contract_alignment` / `semantic_dedupe.fail_open` を記録する。
2. **契約破綻**  
   guard で止まる場合は reason_code と `failed_parameters` を確認。止まらないが「誰が誰に語っているか」が崩れている場合は `speaker_consistency_score` / `pronoun_consistency_score` を監査ログで確認し、必要なら generation_failure_prevention_log に新規失敗記録を追加する。
3. **意味重複**  
   `semantic_dedupe.enabled` / `rewrite_enabled` が true か確認。fail-open が続く場合は API キー・閾値（`similarity_threshold` 等）を確認する。
4. **後処理の握り潰し**  
   同じ制御が prompt / resonance / postprocess に重複していないか、phase06 の制御追加チェックリスト（phase06_artifacts §7）で確認する。

## 5. 関連ファイル

- `notecode/ALGORITHM.md` — 現行仕様・品質ゲート・監査項目
- `notecode/docs/generation_failure_prevention_log.md` — 失敗記録と再発防止ルール
- `notecode/puran6/PROGRESS.md` — 破綻の主因と phase04 対策（§1, §6.1）
- `notecode/puran6/phase06_artifacts_2026-03-07.md` — 制御追加チェックリスト・rollback 単位
- `C:\tetie\algorithm-proposals\ブログ生成AIアルゴリズムの改善提案.md`
- `C:\tetie\algorithm-proposals\CODEX_UACSD_ZERO_BASE_ALGORITHM_2026-03-03.md`

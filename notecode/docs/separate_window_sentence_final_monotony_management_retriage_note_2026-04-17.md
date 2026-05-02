# separate window sentence final monotony management retriage note 2026-04-17

## Position

- この文書は `sentence-final pattern monotony cap + single repair` line の management retriage note である
- source-of-truth update ではない
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない

## 目次

- 読んだ参照ルールファイル
- 実施範囲
- touched files
- current blocker read
- why pipeline acceptance should stay strict
- candidate A/B/C comparison
- decision
- next prompt type
- non-updates

## 読んだ参照ルールファイル

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
- `C:\tetie\WORKLOG.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_management_retriage_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_pipeline_acceptance_after_adaptive_note_2026-04-17.md`
- `C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_adaptive_reopen_20260417-174409\summary.json`
- `C:\tetie\notecode\logs\sentence_final_monotony_pipeline_acceptance_probe_manual\helper_analysis.json`
- `C:\tetie\notecode\logs\sentence_final_monotony_pipeline_acceptance_probe_manual\repair_capture.json`
- `C:\tetie\notecode\logs\sentence_final_monotony_pipeline_acceptance_probe_manual\probe.json`
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

## 実施範囲

- docs / artifacts / code reference 読みだけで current blocker を再判定した
- management question を `acceptance を緩めずに repair output を heading-local に縛る next owner はどこか` に限定した
- production diff には入らず、next implementation prompt を 1 owner に閉じられるかだけ判断した

## Touched Files

- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_management_retriage_note_2026-04-17.md`

## Current Blocker Read

- live rerun summary では A1 が
  - `repair_required = true`
  - `patch_path_used = true`
  - `ending_monotony_improved = true`
  - `scope_rejection_reason = flagged_scope_drift`
  で止まっている
- acceptance probe の `helper_analysis.json` では
  - `title_same = true`
  - `lead_same = true`
  - `hashtags_same = true`
  - `helper_result = false`
  であり、失敗理由は surface ではなく heading sequence drift だった
- current headings:
  - `株式会社リソグラとは何を支援する会社か`
  - `リソグラの強みは新規事業・マーケティング・開発をつなげること`
  - `成果につなげるために重視している判断軸`
  - `実務で見るなら、どんな会社に向いているか`
  - `杉山 満軌が体現するリソグラの伴走姿勢`
- repaired headings:
  - `株式会社リソグラとは何を支援する会社か`
  - `リソグラの強みは新規事業・マーケティング・開発をつなげる支援体制`
  - `成果につなげるために重視している視点`
  - `杉山 満軌が体現するリソグラの伴走姿勢`
  - `株式会社リソグラの特徴をどう見るか`
- したがって current blocker の正確な読みは
  - `flagged_scope_drift`
  - その中身は実質 `heading_sequence_changed`
  - monotony-only repair output が heading rename / closing section replacement / section reorder まで広がっている

## Why Pipeline Acceptance Should Stay Strict

- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py:323-342` の `_repair_preserves_flagged_scope()` は title / lead / hashtags 不変と heading sequence equality を acceptance 条件にしている
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py:380-385` の `_repair_preserves_local_monotony_scope()` も heading sequence equality を前提にしており、monotony-only lane を section-local repair に限定している
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py:1786-1808` では scope preserved が通らない場合に `flagged_scope_drift` を返す。現行 rejection は helper の誤判定ではなく、現行 boundary の意図どおりである
- よって acceptance boundary を緩める方向は current management question と逆行する

## Candidate A/B/C Comparison

### Candidate A: `PROMPT_BUILDER_OWNER`

- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py:1817-1888` の `build_repair_prompt()` は
  - `全文書き直し禁止`
  - `claim と anchor は保ち、直すのは表層だけ`
  - `変更は flag span と前後2文だけ。未指定箇所の意味・見出し順・節の役割は保つ`
  までは出している
- しかし repair capture の actual prompt にも、`見出し名を一字も変えない`、`見出しの追加削除禁止`、`節の並び替え禁止`、`closing section の置換禁止` の hard line は出ていない
- 同ファイルの `build_repair_prompt_from_diagnostics()` は `semantic_ledger` / `section_shadow` / `flagged_spans` を既に repair prompt へ渡している
- したがって current miss は payload 不足より instruction 強度不足と読むのが自然であり、最小 diff は `prompt_builder.py` 1 owner に閉じられる

### Candidate B: `PIPELINE_PROMPT_ASSEMBLY_OWNER`

- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py:1656-1665` では `flagged_spans` を patch path active 時にすでに `build_repair_prompt_from_diagnostics()` へ渡している
- `prompt_builder.py:2006-2015` でも `semantic_ledger` / `section_shadow` / `flagged_spans` を repair prompt に載せている
- つまり current pipeline assembly は、少なくとも monotony-only lane の prompt materials を未送出の状態ではない
- 追加で immutable headings list を pipeline から組み立てて渡す案はありうるが、repair prompt は `SOURCE[BODY]` を既に持っているため、heading lock 自体は prompt builder 内で完結できる
- 現時点では pipeline owner を reopen する根拠は弱い

### Candidate C: `MANAGEMENT_HOLD`

- blocker は 1 file で narrow hypothesis を立てられる
- acceptance reopen や multi-owner simultaneous edit は不要
- よって hold に止める条件には当たらない

## Decision

- conclusion:
  - `PROMPT_BUILDER_OWNER`
- reason:
  - acceptance helper は正しく strict であり、次に直すべきなのは repair output を heading-local に縛る instruction 側である
  - current pipeline は patch-path payload をすでに渡しており、欠けているのは `immutable heading/order contract` の明示だと読める
  - monotony-only lane で必要なのは global threshold 調整ではなく、repair prompt に
    - current heading list を immutable order として固定する line
    - heading rename / add / drop / reorder 禁止
    - closing section replacement 禁止
    - allowed change surface は flagged span とその周辺本文のみ
    を明示する narrow diff である

## Next Prompt Type

- next implementation prompt type:
  - `prompt_builder.py` owner の repair-constraint tightening prompt
- narrow hypothesis:
  - monotony-only repair prompt に immutable heading/order contract を足せば、A1 の `heading_sequence_changed` を抑えつつ acceptance boundary を維持できる
- do not include in next prompt:
  - acceptance threshold reopen
  - pipeline global logic widening
  - multi-owner edit

## Non-Updates

- production code は更新していない
- tests は更新していない
- AGENTS は更新していない
- WORKLOG は更新していない
- current planning package docs は更新していない

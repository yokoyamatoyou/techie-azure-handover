# separate window sentence final monotony actual repair prompt triage note 2026-04-17

## Position

- この文書は `sentence-final pattern monotony cap + single repair` line の follow-up triage note である
- source-of-truth update ではない
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない

## 目次

- 読んだ参照ルールファイル
- 実施範囲
- touched files
- actual repair prompt recovery
- A1 actual repair prompt の要点
- B actual repair prompt の要点
- immutable heading/order contract read
- current-business-first keep line read
- current blocker owner 判定
- judge
- next step
- non-updates

## 読んだ参照ルールファイル

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
- `C:\tetie\WORKLOG.md`
- `C:\tetie\notecode\docs\separate_window_management_memo_deepresearch_reflection_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_priority_revision_after_deepresearch_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_instruction_window_relocation_prompt_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_instruction_first_request_sentence_final_monotony_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_management_retriage_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_prompt_builder_constraint_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_live_revalidation_after_prompt_builder_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_prompt_builder_constraint_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_execution_prompt_sentence_final_monotony_live_revalidation_after_prompt_builder_constraint_2026-04-17.md`
- `C:\tetie\notecode\logs\sentence_final_monotony_live_revalidation_after_prompt_builder_constraint_20260417-183317\summary.json`
- `C:\tetie\notecode\logs\latest_generation_output.json`
- `C:\tetie\notecode\logs\codex_planning_opt_in_gate_validation\20260412-214448-fivecase-live-direct\prompt_only\bl-explanatory-misread-metric.json`
- `C:\tetie\notecode\logs\codex_prompt_builder_company_intro_rerun_2026-04-13.json`
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`
- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`

## 実施範囲

- docs / artifacts / code reference 読みで、A1 / B repair prompt の actual emission を再点検した
- production code edit を行わず、read-only probe で repair prompt を復元可能な block だけ回収した
- triage question を
  - A1 の immutable heading/order contract が actual prompt に出ていたか
  - B の `current-business-first keep line` 相当が repair prompt 側へ残っていたか
  - next owner を `prompt_builder.py` に残すか `pipeline.py` prompt assembly / payload boundary へ移すか
  に限定した

## Touched Files

- generated logs:
  - `C:\tetie\notecode\logs\sentence_final_monotony_actual_repair_prompt_triage_20260417-185120\summary.json`
  - `C:\tetie\notecode\logs\sentence_final_monotony_actual_repair_prompt_triage_20260417-185120\case_a1_latest_adaptive_explanatory_reconstructed_prompt.txt`
  - `C:\tetie\notecode\logs\sentence_final_monotony_actual_repair_prompt_triage_20260417-185120\case_b_company_intro_guard_reconstructed_prompt.txt`
- docs note:
  - `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_actual_repair_prompt_triage_note_2026-04-17.md`

## Actual Repair Prompt Recovery

- full prompt recovery:
  - `partial`
- exact に回収できたもの:
  - `ISSUES` block
  - `PATCH_SCOPE` block
  - `flagged_spans`
  - `company_intro_focus` が最終 prompt へ残るかどうか
- exact に回収できなかったもの:
  - `compact_plan` 依存 block の完全再現
  - 理由:
    - current live artifact には repair call 時点の `compact_plan` が保存されていない
- ただし今回の判定対象だった
  - immutable heading/order contract
  - closing section replacement 禁止 line
  - `company_intro_focus` / current-business-first keep signal の残存有無
  は prompt builder の deterministic path から十分に読めた

## A1 Actual Repair Prompt の要点

- recovery source:
  - `C:\tetie\notecode\logs\sentence_final_monotony_actual_repair_prompt_triage_20260417-185120\case_a1_latest_adaptive_explanatory_reconstructed_prompt.txt`
- actual prompt read:
  - `PATCH_SCOPE` には monotony-only hard contract が出ていた
  - heading contract lines は `prompt_builder.py:567-586` の出力どおりで、emission missing ではない
  - closing replacement 禁止 line も出ていた
- exact lines:
  - `monotony_patch=見出し列をこの順番で固定する: 株式会社リソグラとは何を支援する会社か / リソグラが提供する支援領域と強み / 成果につなげるための支援の進め方 / システム開発で重視する考え方と杉山 満軌の役割 / 株式会社リソグラをどう見れば実務の判断材料になるか`
  - `monotony_patch=見出し名は一字一句変えない。見出しの改名・追加・削除・並べ替えをしない。`
  - `monotony_patch=最後の見出しを別のまとめ見出しへ差し替えず、結びの節を新しい closing 概念で置き換えない。`
  - `monotony_patch=書き換えは flag span とその前後本文だけにとどめ、別節へ論点を逃がさない。`
- important gap:
  - `span[1]=issue=ending_bucket_monotony / window=local_run_plus_two`
    だけで、actual target sentence / paragraph / heading anchor は出ていない
  - title / lead / hashtags を不変に保つ explicit line もない
- read:
  - heading lock wording 自体は存在する
  - ただし local patch target が未特定で、acceptance が要求する `title_same / hashtags_same / heading sequence equality` に対して prompt 側の anchoring が足りない

## B Actual Repair Prompt の要点

- recovery source:
  - `C:\tetie\notecode\logs\sentence_final_monotony_actual_repair_prompt_triage_20260417-185120\case_b_company_intro_guard_reconstructed_prompt.txt`
- actual prompt read:
  - `PATCH_SCOPE` は
    - `shadow_section_drift`
    - `ending_bucket_monotony`
    の mixed issue として出ていた
  - `shadow_patch` lines は出ていた
  - しかし `SECTION_SHADOW` block は最終 prompt に残っていない
  - `company_intro_focus=自社の事業内容を紹介する` も最終 prompt に残っていない
- exact lines that remained:
  - `shadow_patch=repair only the span-specified heading and keep every other section unchanged`
  - `shadow_patch=restore the listed focus and claim in the opening 1-2 sentences, then keep the same section role`
  - `shadow_patch=do not add new headings, new examples, or a new conclusion outside the target span`
  - `target_headings=130年余りの歴史を、今の価値へつなぐ会社`
- why the keep signal disappeared:
  - `prompt_builder.py:1539-1540` では company intro shadow のとき `company_intro_focus=...` を作る
  - しかし `build_repair_prompt()` は `prompt_builder.py:1892-1895` で `_filter_section_shadow_lines()` を通す
  - `prompt_builder.py:668-681` の filter は `target_headings` があると heading 名一致 line しか残さない
  - `company_intro_focus=自社の事業内容を紹介する` は heading 名ではないため drop される
- read:
  - B repair prompt 側には `current-business-first keep line` 相当の explicit signal は残っていない
  - history-first drift を止める line が repair side で消えている

## Immutable Heading / Order Contract Read

- A1:
  - `actual prompt に出ていた`
- B:
  - mixed issue のため monotony-only heading contract block は出ていない
  - 代わりに `shadow_patch` block だけが出ている
- closing section replacement 禁止 line:
  - A1 には `actual prompt に出ていた`
  - B には出ていない
- system / user prompt 推定:
  - current path は `build_repair_prompt()` が single prompt text を構成し、そのまま `_call_llm()` に渡している
  - よってこれらの lines は system / user 分離ではなく、single user-facing prompt body 内の block と読むのが最も近い

## Current-Business-First Keep Line Read

- B repair prompt に
  - `出だしはまず...`
  - `...は背景として後ろで短く扱い、創業年・沿革から書き始めない`
  の explicit line は出ていない
- `company_intro_focus=自社の事業内容を紹介する` も final repair prompt には残っていない
- したがって
  - `current-business-first keep line が repair prompt 側にも維持されていた`
  とは言えない

## Current Blocker Owner 判定

- current first owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- why:
  - B では repair-side company-intro keep signal が `prompt_builder.py` 内の section-shadow filter で落ちている
  - これは prompt assembly / payload boundary 以前の emission loss であり、owner は `prompt_builder.py` に閉じる
  - A1 でも hard contract は emit されているため、次に直すべき問いは `pipeline.py` より先に
    - repair prompt に title / lead / hashtags 不変 line を足すか
    - monotony-only local target の anchoring line を `prompt_builder.py` で増やせるか
    を narrow に切ることになる
- secondary follow-up candidate only if prompt_builder diff 後も残る場合:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - reason:
    - A1 の `window=local_run_plus_two` が actual sentence / section anchor を持たず、payload boundary の弱さも残っているため

## Judge

- primary judge:
  - `PROMPT_EMISSION_MISSING`
- precise read:
  - A1 の monotony-only heading contract 自体は emission missing ではない
  - ただし B では `company_intro_focus` / current-business-first keep signal が actual repair prompt から落ちており、repair-side contract emission missing が確認できた
  - A1 側には second-order issue として `PATCH_SCOPE_MISMATCH` が残る
    - `ending_bucket_monotony` span が location-free
    - title / lead / hashtags freeze line がない
- why not `MODEL_VARIABILITY_STILL_PRIMARY`:
  - B では model variability 以前に repair prompt emission loss が確認できたため

## Next Step

- next prompt type:
  - `implementation prompt`
- first narrow hypothesis:
  - `prompt_builder.py` owner で
    - company intro repair side でも `current-business-first keep line` を filter で落とさず残す
    - monotony-only repair side に title / lead / hashtags freeze line を足す
    - local target anchoring を prompt text だけで強められる範囲を先に試す
- after that only if still needed:
  - follow-up triage or implementation on `pipeline.py` payload boundary
  - target:
    - `ending_bucket_monotony` span の sentence / heading anchor emission

## Non-Updates

- production code は更新していない
- tests は更新していない
- AGENTS は更新していない
- WORKLOG は更新していない
- current planning package docs は更新していない

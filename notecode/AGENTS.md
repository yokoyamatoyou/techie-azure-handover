# コトメイク AGENTS

正本は `C:\tetie\AGENTS.md` です。  
このファイルは `notecode` current planning package の最短導線だけを示します。

## Current Refactor Read Order

1. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
   - objective / read order / source-of-truth / simplification direction / non-goals
2. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
   - phase map / gate / retry-stop / shared checks
3. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
   - current phase / status / hypothesis / owner scope / visible baseline
4. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
   - baseline / rollback boundary / do-not-retry hypotheses
5. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md`
   - 別ウインドウ実装用の開始 prompt
6. `C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\README.md`
   - pre-2026-04-02 work records の archive boundary
7. `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\README.md`
8. `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\PROGRESS.md`
9. `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\README.md`
10. `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\PROGRESS.md`
11. `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\README.md`
12. `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\PROGRESS.md`
13. `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md`
14. `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md`
15. `C:\tetie\notecode\ALGORITHM.md`
16. `C:\tetie\WORKLOG.md`

## Current Package State

- current source of truth
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
- final read order は `README.md -> TASK.md -> PROGRESS.md -> ROLLBACK.md -> EXECUTION_PROMPT.md -> archive snapshot README -> completed reference README/PROGRESS -> frozen reference README/PROGRESS -> ALGORITHM.md -> WORKLOG.md` に固定する
- archive-only snapshot
  - `C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\`
- active reference / completed reference / freeze package は参照のみ
  - `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\`
  - `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\`
  - `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\`
  - `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\`
- rollback / archive boundary
  - current runtime mainline: `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - compatibility import path: `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - pre-2026-04-02 work records: `C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\`
  - pre-refactor / legacy plan: `C:\tetie\notecode\archive\` と `C:\tetie\notecode\plan\zero_base_rebuild_2026-03-04\`

## Current Status Docs

- `C:\tetie\notecode\ALGORITHM.md`
  - 最終更新日 `2026-04-23 JST`
  - persona / source packet / generation-editing-regeneration contract / GPT Image 2 image generation algorithm の正本
- `C:\tetie\notecode\plan\gpt_image2_blog_image_auto_2026-04-22\README.md`
  - GPT Image 2 blog image auto flow の objective / scope / docs / UI decision
- `C:\tetie\notecode\plan\gpt_image2_blog_image_auto_2026-04-22\PROGRESS.md`
  - GPT Image 2 blog image auto flow の実装・検証・live validation 状態
- `C:\tetie\notecode\plan\gpt_image2_blog_image_auto_2026-04-22\DECISIONS.md`
  - GPT Image 2 blog image auto flow の独断判断 / docs差分 / UI判断 / 残リスク
- `C:\tetie\notecode\logs\latest_generation_output.txt`
  - latest visible artifact baseline。current red symptom の一次確認先
- `C:\tetie\notecode\logs\latest_generation_quality_report.json`
  - latest visible artifact の quality metrics / soft warning / alignment の一次確認先
- `C:\tetie\notecode_current_mainline_handoff_2026-04-06.md`
  - 2026-04-06 時点の current baseline / archive boundary / separate-window start point
- `C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\README.md`
  - pre-2026-04-02 work records を archive-only に切り替えた snapshot
- `C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\manifest.json`
  - archive-only record group の一覧
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
  - current planning package の入口。objective / route-style-repair hypothesis / non-goals
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
  - phase / gate / retry-stop / shared checks の正本
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
  - current phase / complexity assessment / next phase
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
  - baseline / rollback boundary / do-not-retry hypotheses
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md`
  - 別ウインドウ implementation 用 prompt
- `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\README.md`
  - `note_writer_app.py` safe split separate initiative の入口。objective / facts / split priority / non-goals
- `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\TASK.md`
  - phase map / gate / retry-stop=`2` / required checks
- `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\PROGRESS.md`
  - current phase / next execution window / runtime untouched status
- `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\ROLLBACK.md`
  - split rollback boundary / do-not-retry / park boundary
- `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\EXECUTION_PROMPT.md`
  - `Phase 01` separate-window 実装 prompt
- `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\README.md`
  - active reference package の入口。visible red symptom / non-goals
- `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\TASK.md`
  - active reference package の task
- `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\PROGRESS.md`
  - active reference package の progress
- `C:\tetie\notecode\docs\current_mainline_tomorrow_first_prompt_2026-04-07.md`
  - 2026-04-07 起動時の copy-paste prompt
- `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\README.md`
  - completed reference package の入口
- `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\PROGRESS.md`
  - completed reference の progress / outcome
- `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\README.md`
  - completed reference package の入口
- `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\PROGRESS.md`
  - completed reference の progress / outcome
- `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md`
  - frozen architecture reference の入口
- `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md`
  - frozen reference の decision / closeout / freeze 状態

## Persona / Source-Packet Algorithm Route

persona ベース、source の渡し方、生成 / 編集 / 再生成の扱いを触る場合は、runtime 実装や prompt を触る前に必ず `C:\tetie\notecode\ALGORITHM.md` の次を読む。

- `## 4. Single-Pass Generation`
- `## 5. Repair Algorithm`
- `## 12. Persona / Source Packet / Editing Persona Contract`

補助資料として次を参照する。ただし runtime 正本へ昇格させる場合は、persona 名や trial 名をそのまま prompt / 本文へ入れず、source contract / craft guard / validation trigger へ圧縮する。

- `C:\tetie\notecode\新しいフォルダー\新しいフォルダー\persona_rebuild_20260422\persona_design_principles.md`
- `C:\tetie\notecode\新しいフォルダー\新しいフォルダー\persona_rebuild_20260422\article_type_persona_sets_source_per_type_20260422.md`

## GPT Image 2 Image Generation Route

GPT Image 2 対応、ブログ生成後の自動画像生成、画像プロンプト、画像 retry / fail-open、画像 UI を触る場合は、runtime 実装や prompt を触る前に必ず次を読む。

- `C:\tetie\notecode\ALGORITHM.md`
  - `## 13. GPT Image 2 Image Generation Algorithm`
- `C:\tetie\notecode\plan\gpt_image2_blog_image_auto_2026-04-22\README.md`
- `C:\tetie\notecode\plan\gpt_image2_blog_image_auto_2026-04-22\TASK.md`
- `C:\tetie\notecode\plan\gpt_image2_blog_image_auto_2026-04-22\PROGRESS.md`
- `C:\tetie\notecode\plan\gpt_image2_blog_image_auto_2026-04-22\DECISIONS.md`
- `C:\tetie\notecode\plan\gpt_image2_blog_image_auto_2026-04-22\ROLLBACK.md`

## Note Writer App Split Route

`note_writer_app.py` の安全分割、UI shell の slim 化、separate-window split planning を触る場合は、`naturalness_recovery_2026-04-07` current source of truth を維持したまま次を読む。

- この split package は separate initiative であり、global current source of truth の置換ではない
- `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\README.md`
- `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\TASK.md`
- `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\PROGRESS.md`
- `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\ROLLBACK.md`
- `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\EXECUTION_PROMPT.md`
- `C:\tetie\notecode\current_mainline_owner_split\OWNER_MAP.md`
- `C:\tetie\notecode\current_mainline_owner_split\EXECUTION_RULES.md`
- `C:\tetie\notecode\current_mainline_owner_split\TEST_AND_SAFETY_MATRIX.md`
- `C:\tetie\notecode\current_mainline_owner_split\NOTE_WRITER_APP_WINDOW_HANDOFF_2026-04-23.md`
- `C:\tetie\notecode\ALGORITHM.md`
  - `## 4. Single-Pass Generation`
  - `## 5. Repair Algorithm`
  - `## 12. Persona / Source Packet / Editing Persona Contract`
  - `## 13. GPT Image 2 Image Generation Algorithm`
- `C:\tetie\notecode\note\note_writer_app.py`

## Current Rules

- 本文 mainline は `single-pass + optional single repair 1回` を baseline として維持し、route experiment は phase-local に閉じる
- TOC は markdown `## 目次`
- `1 phase = 1 narrow hypothesis = 1 owner scope`
- prompt と module の accretion を禁止する
- persona は本文に露出させず、lead angle / heading order / fact selection / paragraph emphasis / final paragraph へ変換する
- source contract は本文に書かず、source外 claim を止める拘束として使う
- 編集 / 再生成は後半の追従性低下を補う bounded repair として扱い、`SEMANTIC_LEDGER` / `SECTION_SHADOW` / `PATCH_SCOPE` の anchor を保つ
- pre-2026-04-02 records を current read order に戻さない
- completed reference package を reopen しない
- frozen architecture package を reopen しない
- current success path は
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  を維持する
- 各 phase は owner-local tests と shared checks を通すまで completed にしない
- エラー時は同一 phase で 3 回まで修正を試み、無理なら停止して user report

# opening_frame_redesign_2026-04-18 ROLLBACK

## Baseline

- restore target:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- current visible artifact baseline:
  - `C:\tetie\notecode\logs\latest_generation_output.txt`
  - `C:\tetie\notecode\logs\latest_generation_quality_report.json`
- current parked boundary:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md`
- new package boundary:
  - `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\README.md`
  - `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\TASK.md`
  - `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\PROGRESS.md`
  - `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\ROLLBACK.md`
  - `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\EXECUTION_PROMPT.md`
- evidence only:
  - `C:\tetie\notecode\docs\opening_frame_redesign_research_synthesis_note_2026-04-18.md`
  - research 3 本
- code diff state:
  - production rollback は不要
  - rollback 対象は new package docs だけ

## Rollback Rule

- current package docs は触らない
- production code / tests / AGENTS / WORKLOG は触らない
- rollback は new package docs の file-local diff 単位で行う
- current package reopen と同じ文書になった場合は new package docs を止める
- first code owner を early fix した文言が入った場合は new package docs 側だけを戻す
- code diff がないので production rollback は実施しない

## Inherited Do-Not-Retry Hypotheses

- `prompt_builder.py` simplification-first wording line を unchanged で再投入すること
- `pipeline.py` current-first source ordering / hint triage を unchanged で再投入すること
- `pipeline.py` core_message current-first hint を unchanged で再投入すること
- `SECTION_SHADOW` reopen を初手に戻すこと
- `quality_guard.py` first にすること
- repair acceptance reopen を初手にすること
- sentence-final monotony line を main candidate に戻すこと
- `natural_blog_core.py` first section history clamp 仮説
- `output_formatter.py` formatter-only surface polish 仮説
- `input_contract.py` upstream distilled summary 単独仮説
- prompt accretion continuation
- fixed routing table
- planning / skeleton default reopen
- giant rewrite

## Package-Specific Stop Boundary

- current package reopen と実質同じ line になった
- first code owner を `pipeline.py` または `prompt_builder.py` に早期固定した
- `minimal_control_layer` implementation を先に固定した
- package objective が opening frame ownership から broad redesign へ膨らんだ
- multiple owner implementation planning が必要になった

## Reopen Boundary

- current package `naturalness_recovery_2026-04-07` は parked / not fixed のまま維持する
- Phase 01 が legal な `1 owner / 1 hypothesis` を作れた場合だけ、future implementation prompt を別 step で作る
- tentative future code candidate は `newalgorithm_pipeline/pipeline.py` 周辺の最小 opening-frame control surface に留める
- tentative candidate は current package retry の unchanged reopen を意味しない

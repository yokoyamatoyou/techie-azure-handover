# company_intro_length_source_diagnosis_2026-04-25 README

## Objective

- `branding/company_introduction` が source-rich 条件でも本文 900-1300 字程度へ寄りやすい原因を、target / source compression / section realization / repair rejection に分けて測定する。
- 初手では runtime code を変更しない。まず京都工業 source-rich 条件の repeated run で、説明量がどの段階で落ちるかを evidence として固定する。
- 文字数増加自体を目的にしない。source-backed な説明密度、required slot の扱い、section ごとの実現量を優先して評価する。

## Source Of Truth

- current naturalness source of truth:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
- current success path:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- behavior-preserving split reference:
  - `C:\tetie\notecode\plan\pipeline_responsibility_split_2026-04-24\`
- immediate predecessor:
  - `C:\tetie\notecode\plan\source_compression_length_adequacy_2026-04-25\`

## Read Order

1. `C:\tetie\notecode\AGENTS.md`
2. `C:\tetie\AGENTS.md`
3. `C:\tetie\notecode\ALGORITHM.md`
   - `## 4. Single-Pass Generation`
   - `## 5. Repair Algorithm`
   - `## 12. Persona / Source Packet / Editing Persona Contract`
4. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
5. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
6. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
7. `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
8. `C:\tetie\notecode\plan\pipeline_responsibility_split_2026-04-24\PROGRESS.md`
9. `C:\tetie\notecode\plan\source_compression_length_adequacy_2026-04-25\README.md`
10. `C:\tetie\notecode\plan\source_compression_length_adequacy_2026-04-25\TASK.md`
11. `C:\tetie\notecode\plan\source_compression_length_adequacy_2026-04-25\PROGRESS.md`
12. `C:\tetie\notecode\plan\source_compression_length_adequacy_2026-04-25\ROLLBACK.md`
13. `C:\tetie\WORKLOG.md`
14. specified prior logs under `C:\tetie\notecode\logs\`

## Diagnosis Hypotheses

- `target_low_suspected`: target / length-mode decision is around 1200 chars and output follows it.
- `compression_loss_suspected`: source is rich, but source packet / grounding / must-cover / slot text lengths are too small to support expansion.
- `realization_shallow_suspected`: source packet contains usable material, but sections stay at one or two shallow paragraphs.
- `repair_rejection_suspected`: repair candidate improves explanation depth but is rejected by acceptance.
- `source_thin`: source itself lacks enough concrete material.
- `fail_closed_ok`: hard guard blocks a bad artifact correctly.

## Primary Scenario

- article type: `branding`
- semantic article key: `company_introduction`
- source mode: `grounded`
- source URLs:
  - `https://www.kyotokogyo.co.jp/`
  - `https://www.kyotokogyo.co.jp/about/coprof/`
  - `https://www.kyotokogyo.co.jp/about/history/`
  - `https://www.kyotokogyo.co.jp/service/input_scaning/`
- run count:
  - Kyoto Kogyo source-rich: 15 runs
  - optional additional source-rich company introduction: 5 runs if a suitable existing fixture/log is found

## Required Metrics

- run id / source profile id / runtime reason code / success / fail-closed reason
- repair required / applied / rejected / reject reason
- output guard reasons / soft warning count
- length mode / target chars / max tokens when available
- source document count / source total chars / source summary chars / source packet chars
- grounding item count / must-cover count
- company introduction source contract slot value lengths
- source slot presence / visible slot presence / missing required slots / unbacked required slots
- body chars / body chars to target chars / title chars / lead chars
- section count / headings / section char distribution / shortest section / final section / final paragraph
- source facts reflected count and source packet facts reflected count when measurable
- visible internal-term leakage yes/no
- Codex visible evaluation and note article judgment
- thinness classification

## Non-Goals

- Do not change `ALGORITHM.md` persona-based design.
- Do not change the `single-pass + optional single repair 1回` mainline.
- Do not increase repair count.
- Do not relax `quality_guard.py` thresholds.
- Do not grow `prompt_builder.py` or `blog_image_auto.py`.
- Do not create persona registry or central management modules.
- Do not expose runtime/internal terms in visible article text.
- Do not reopen pre-2026-04-02 archive or frozen architecture package.
- Do not add source-outside claims or generic padding.

# branding_trust A/B follow-up 2026-04-09

## Purpose

- `ui-short-branding-trust` で確認した A/B 比較を、production 変更前の narrow plan に圧縮する
- 4件の調査メモのうち、現行 evidence と整合する論点だけを採用する
- 別ウインドウでそのまま implementation / verification に使える最小手順を残す

## Current Decision

- choose: Variant A
- meaning:
  - upstream `discourse_plan` を主骨格として `simple_note_pipeline` に橋渡しする
  - current compact plan は secondary に落とすか、A 案に吸収する
- production closeout:
  - `ui-short-branding-trust` は current bridge diff で accept した
  - `newalgorithm_pipeline/pipeline.py` にこれ以上 branding 用 branch を増やさない
  - 次 owner は `natural_blog_core.py` の Phase 04 へ進める

## Why A Won

- A/B artifact:
  - `C:\tetie\notecode\logs\ad_hoc_quality_compare\20260409-branding-trust-ab-plan\summary.json`
  - `C:\tetie\notecode\logs\ad_hoc_quality_compare\20260409-branding-trust-ab-plan\variant_a_upstream_discourse_plan.txt`
  - `C:\tetie\notecode\logs\ad_hoc_quality_compare\20260409-branding-trust-ab-plan\variant_b_current_compact_plan.txt`
- A:
  - `planned_vs_actual_heading_overlap = 1.0`
  - `must_cover_reflection_rate = 1.0`
  - `section_focus_coverage = 1.0`
  - `topic_echo = 0.2729`
- B:
  - `planned_vs_actual_heading_overlap = 0.0`
  - `must_cover_reflection_rate = 0.0`
  - `section_focus_coverage = 0.2`
  - `topic_echo = 1.0`
- interpretation:
  - current target case の一次原因は downstream formatter ではなく、`simple_note_pipeline` 内の二重骨格
  - upstream `discourse_plan` を本文 owner に近づけるほうが visible artifact は良い

## Adopted Research Points

- adopt from `PRO\deep-research-report (23).md`
  - persona 不足ではなく `route ownership / state loss / repair non-actuation`
  - branding を patch / shadow scope に入れる owner-local fix は妥当
  - discourse plan / focus bundle を ledger 代替に使う発想は有効
- adopt from `research\新しいフォルダー (6)\新しいフォルダー\0407.txt`
  - `pipeline.py` が visible surface owner という整理
  - `input_contract.py` の micro-surface loss はまだ残論点
  - `source-unaware defaults` は次位の候補
- keep as low priority from `deep-research-report (21).md`
  - sampling suppression は watch item
  - ただし target case の一次原因とは見なさない
- reject as primary cause from `notecode 自然さ阻害要因監査.md`
  - formatter / predicate-forcing 主犯説
  - current target case では downstream crush の evidence が弱い

## Narrow Hypothesis

- hypothesis:
  - `newalgorithm_pipeline` の upstream `discourse_plan` を `simple_note_pipeline` の compact-plan compatible ledger に橋渡しすると、
    `ui-short-branding-trust` で plan/materialization mismatch が減り、current compact plan 起点の再圧縮を避けられる

## Owner Scope

- primary owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- secondary owner only if strictly needed:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

## Do

- upstream `discourse_plan` を compact-plan 互換の `_semantic_ledger` へ変換する橋を narrow に追加する
- `ui-short-branding-trust` のみで A 案 production 化を確認する
- `planned_vs_actual_heading_overlap`
- `must_cover_reflection_rate`
- `controlled_realization`
- visible artifact
  を first-class 判定にする
- current success path
  - `current_mainline_runner.py`
  - `-> newalgorithm_pipeline/pipeline.py`
  - `-> simple_note_pipeline/pipeline.py`
  は壊さない

## Do Not

- section-first route promotion を reopen しない
- output formatter の paragraph rebalance に広げない
- sampling suppression を同 phase で触らない
- prompt accretion を始めない
- company introduction defaults prune を同 phase に混ぜない

## Success Criteria

- `ui-short-branding-trust` で
  - `semantic_article_key = branding` を維持
  - `must_cover` が company profile default に落ちない
  - `planned_vs_actual_heading_overlap > 0.8`
  - `must_cover_reflection_rate > 0.5`
  - `controlled_realization.active = true`
  - visible artifact が trust / explanation として自然
- minimum accept:
  - `WEB版 Claude / GPT より明確に AI っぽい` とまでは見えない水準へ近づく

## Verification Order

1. current baseline を `ui-short-branding-trust` で再確認
2. upstream plan bridge patch
3. owner-local pytest
4. live rerun
5. A/B compare against current compact plan
6. 必要なら 3-article gate の最小再確認

## Tests

- owner-local:
  - `note\tests\test_current_mainline_runner.py`
  - `note\tests\test_simple_note_pipeline.py`
- shared minimum:
  - `note\tests\test_current_mainline_regressions.py`
  - `note\tests\test_current_mainline_ui_matrix.py`

## Separate Window Prompt

- phase target:
  - `branding-trust` の A 案 production 化
- owner scope:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- narrow hypothesis:
  - upstream `discourse_plan` を compact-plan compatible ledger として `simple_note_pipeline` に橋渡しすると、`ui-short-branding-trust` の plan/materialization mismatch が減る
- implementation rule:
  - `apply_patch` で編集
  - unrelated changes は戻さない
  - 1 phase = 1 narrow hypothesis = 1 owner scope
  - owner-local tests -> live rerun -> artifact compare

## Remaining Risks

- planner 見出しがそのまま visible に出ると planner 臭さが残る
- `must_cover_reflection_rate` を取りに行くと説明過多になる可能性がある
- `input_contract` の micro-surface loss は別原因として残る
- company-introduction defaults prune を後続 phase に切り出す必要がある

## Close Note

- 2026-04-10 live rerun accepted:
  - `semantic_article_key = branding`
  - `planned_vs_actual_heading_overlap = 1.0`
  - `must_cover_reflection_rate = 0.6667`
  - `controlled_realization.active = true`
- do not reopen:
  - section-first route promotion
  - branding-trust 向け追加 branch
- next phase:
  - `04 Company Intro Source-Aware Plan Prune`

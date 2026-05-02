# separate experiment fixed3 naturalness final report 2026-04-13

## Purpose

- current package mainline source-of-truth は更新しない
- external engineer 向けの separate experiment / handoff material を stable に閉じる
- fixed 3 case で `runtime baseline` / `prompt champion` / `algorithm challenger` を比較した結論を 1 枚で渡せる形にする

## Read Source Files

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\ALGORITHM.md`
- `C:\tetie\WORKLOG.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md`
- `C:\tetie\notecode\docs\management_window_route_policy_coordinator_2026-04-12.md`
- `C:\tetie\notecode\docs\separate_experiment_prompt_runtime_distillation_handoff_2026-04-13.md`

## Fixed 3 Cases

- company
  - case id: `ui-short-branding-company-grounded`
  - source locked:
    - `https://fixture.techie/branding/company-profile`
    - `https://fixture.techie/branding/support-policy`
- daily
  - case id: `bl-daily-learning-log-grounded`
  - source locked:
    - `https://fixture.techie/daily/review-note-20260310`
    - `https://fixture.techie/daily/review-note-20260311`
- explanatory
  - case id: `bl-explanatory-misread-metric`
  - source locked:
    - `https://fixture.techie/explanatory/adoption-signal-overview`
    - `https://fixture.techie/explanatory/helpdesk-signal-notes`

rule:

- round 0 で case / source / baseline を固定
- 途中差し替えなし
- 評価軸変更なし

## Artifact Root

- root:
  - `C:\tetie\notecode\logs\codex_prompt_runtime_distillation_20260413\`
- combined summary:
  - `C:\tetie\notecode\logs\codex_prompt_runtime_distillation_20260413\combined_round_summary.json`
- detailed per-lane handoff:
  - `C:\tetie\notecode\docs\separate_experiment_prompt_runtime_distillation_handoff_2026-04-13.md`

## Numbered Rounds

- numbered rounds:
  - `3` (`round 0`, `round 1`, `round 2`)
- challenger entries:
  - `3`
  - `round 1 prompt v1`
  - `round 1 runtime v1`
  - `round 2 prompt v2`

## Round Ledger

### Round 0

- lane:
  - `baseline`
- hypothesis:
  - current generic baseline を fresh rerun して fixed reference を凍結する
- artifact:
  - `C:\tetie\notecode\logs\codex_prompt_runtime_distillation_20260413\round0_baseline_generic\summary.json`
- decision:
  - `keep as runtime baseline`

### Round 1 prompt lane v1

- hypothesis:
  - raw prompt を 4-layer labeled surface に明示すれば自然さと grounding を両立できる
- artifact:
  - `C:\tetie\notecode\logs\codex_prompt_runtime_distillation_20260413\round1_prompt_lane_v1\summary.json`
- result:
  - `prompt_echo_hits` が 3 cases 全件で発生
  - `short_gate_passed_count = 0/3`
- decision:
  - `drop`

### Round 1 algorithm lane v1

- owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py`
- hypothesis:
  - schema wrapper leak strip を formatter owner だけで入れれば naturalness も押し上げられる
- artifact:
  - `C:\tetie\notecode\logs\codex_prompt_runtime_distillation_20260413\round1_runtime_lane_v1\summary.json`
- result:
  - daily wrapper leak には効いた
  - ただし `rubric_mean_total = 7.33`
  - company / daily / explanatory の `must_cover_reflection_rate` と `prompt_anchor_coverage` が champion に届かない
- decision:
  - `rollback / not winner`

### Round 2 prompt lane v2

- hypothesis:
  - labeled block をやめ、short task + compressed core_message に蒸留したほうが echo を抑えつつ grounding を維持できる
- artifact:
  - `C:\tetie\notecode\logs\codex_prompt_runtime_distillation_20260413\round2_prompt_lane_v2\summary.json`
- result:
  - `rubric_mean_total = 8.33`
  - `prompt_echo_hits = 0`
  - `source_trace_coverage = 1.0` for all 3 cases
- decision:
  - `keep / frozen champion`

## Beat Check

champion target:

- frozen champion:
  - `round2_prompt_lane_v2`

algorithm challenger verdict:

- `beat failed`

why:

- 3-case mean rubric を champion 以上にできていない
- `source_trace_coverage` は維持したが、`must_cover_reflection_rate` と `prompt_anchor_coverage` を下げた
- `company introduction` で champion 同等以上を満たせていない
- next honest algorithm step は
  - prompt champion を 1 owner にそのまま埋め込むより
  - `input_contract.py` と `prompt_builder.py` の両方にまたがる surface handling になる可能性が高く
  - fixed 3 case 専用 hack か multi-owner 前提に寄りやすい
- 本日の handoff 目的では `already champion sufficiently handoffable and challenger not catching up` に該当すると判断する

stop decision:

- separate experiment はここで止める
- external engineer には prompt strategy spec を first adopt として渡す
- algorithm lane は fallback / future separate issue 扱いに留める

## Score Summary

### Round 0 baseline generic

- `rubric_mean_total = 8.0`
- `short_gate_passed_count = 3/3`
- reader judgment:
  - company: `slightly_unnatural`
  - daily: `unnatural`
  - explanatory: `slightly_unnatural`

### Round 1 algorithm lane v1

- `rubric_mean_total = 7.33`
- `short_gate_passed_count = 3/3`
- reader judgment:
  - company: `slightly_unnatural`
  - daily: `slightly_unnatural`
  - explanatory: `slightly_unnatural`

### Round 2 prompt champion v2

- `rubric_mean_total = 8.33`
- `short_gate_passed_count = 3/3`
- reader judgment:
  - company: `slightly_unnatural`
  - daily: `natural`
  - explanatory: `slightly_unnatural`

reader summary:

- baseline では daily が `wrapper leak` で visible break
- champion v2 では daily が `natural` まで改善
- company は brochure 調を完全には消せていないが、事実連結と主語運びは最良
- explanatory は formal card 感が残るが、labeled prompt echo を避けたぶん baseline より素直

## Output Length Proof

floor rule:

- case floor = `max(0.85 * round0 baseline chars, fixed floor)`
- fixed floor:
  - company `>= 550`
  - daily `>= 450`
  - explanatory `>= 550`

measured full-text counts:

| case id | round0 baseline chars | computed floor | round1 runtime v1 chars | round2 prompt v2 chars | pass winner |
|---|---:|---:|---:|---:|---|
| `ui-short-branding-company-grounded` | 1460 | 1241 | 1302 | 2055 | yes |
| `bl-daily-learning-log-grounded` | 1036 | 881 | 1029 | 918 | yes |
| `bl-explanatory-misread-metric` | 1610 | 1369 | 1419 | 1482 | yes |

paragraph counts:

| case id | round0 baseline | round1 runtime v1 | round2 prompt v2 |
|---|---:|---:|---:|
| `ui-short-branding-company-grounded` | 16 | 16 | 24 |
| `bl-daily-learning-log-grounded` | 11 | 16 | 16 |
| `bl-explanatory-misread-metric` | 26 | 19 | 20 |

interpretation:

- champion v2 は 3 cases 全てで char floor を満たす
- runtime v1 も floor 自体は割っていない
- ただし length だけでは beat にならず、champion 差分は `must_cover` と `anchor` の保持で決まっている

## Web GPT Status

- `web GPT direct compare: unverified`
- `web_gpt_direct_compare_unavailable`

reason:

- この environment には WEB版 GPT を authenticated / same-case / same-source 条件で直接実行した比較 artifact がない
- local logs / docs / artifacts を確認しても direct compare record は見当たらない
- よって `WEB版 GPT 相当 baseline を超えた` とは本報告では主張しない
- provisional floor は `prompt champion v2` とする

## Winner

- winner type:
  - `fallback prompt strategy`

exact interpretation:

- separate experiment winner:
  - `prompt strategy`
- handoff choice for tomorrow:
  - `prompt strategy spec`
- algorithm verdict:
  - `not winner`

## What To Hand Off Tomorrow

first package:

- `C:\tetie\notecode\docs\separate_experiment_prompt_runtime_distillation_handoff_2026-04-13.md`
  - champion spec
  - minimal examples
  - anti-pattern
  - runtime lane close note

final decision sheet:

- `C:\tetie\notecode\docs\separate_experiment_fixed3_naturalness_final_report_2026-04-13.md`
  - stable winner
  - beat verdict
  - length proof
  - web compare status
  - repo touch status

recommended first action for external engineer:

- code diff ではなく `prompt strategy v2` の adopt を先に試す
- raw prompt に labeled spec block を露出しない
- short task + compressed core_message + unchanged source_documents を基本形にする
- company / daily / explanatory の fixed 3 case で
  - `source_trace_coverage`
  - `must_cover_reflection_rate`
  - `prompt_echo_hits`
  - `output_char_count`
  を再確認する

reject anti-pattern:

- raw prompt に `must_cover:` `source_documents:` `forbidden_additions:` の label を露出する
- persona line を増やして自然さを取りに行く
- article-type fixed rule table を追加する
- wrapper cleanup のみで naturalness winner と見なす
- fixed 3 case 専用 hack を code に埋める

## Final Answers

- `WEB版 GPT 相当 baseline を超えられたか`
  - `unverified`
  - direct compare unavailable のため判定しない
- `prompt champion を algorithm challenger が超えられたか`
  - `no`
- `AIっぽさをどこまで減らせたか`
  - baseline の daily `unnatural` を champion v2 で `natural` まで改善
  - company / explanatory は `slightly_unnatural` まで
  - 3 case 全体では `echo を出さず coverage を維持したまま、flatness を一段下げる` ところまでは到達
- `明日 external engineer に渡すべきもの`
  - `prompt strategy spec`
  - algorithm winner ではない
  - fallback としても prompt strategy を採る

## Change Status

- code:
  - unchanged
- tests:
  - unchanged
- AGENTS:
  - unchanged
- WORKLOG:
  - unchanged
- current package mainline source-of-truth docs:
  - unchanged
- separate experiment docs:
  - added this final report only

explicit boundary note:

- `technical explain` は current package source-of-truth に戻していない
- `解説記事` は fixed experiment case としてのみ扱った
- mainline source-of-truth は更新していない

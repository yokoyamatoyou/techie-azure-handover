# separate window compare result reference realization policy 2026-04-17

## Execution Note

- 参照ルールファイル:
  - `C:\tetie\AGENTS.md`
  - `C:\tetie\notecode\AGENTS.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
  - `C:\tetie\WORKLOG.md`
  - `C:\tetie\notecode\docs\separate_window_test_algorithm_by_ui_direction_2026-04-16.md`
  - `C:\tetie\notecode\docs\separate_window_compare_plan_reference_realization_policy_2026-04-17.md`
- 今回の実施範囲:
  - compare 実行
  - report 作成
  - production runtime は未変更
  - AGENTS / WORKLOG / current package docs は未更新

## Lane Definition

- lane A:
  - current code を使い、`reference realization policy` だけを process-local patch で `OFF`
  - route / formatter / contract / output guard はそのまま
- lane B:
  - current code の experimental state をそのまま使用
  - `reference realization policy` は `ON`
- lane C:
  - optional のため未実施
  - main target の compare だけで `NO_GO` 判定に十分だった

## Fixed Cases

1. `ui-short-branding-company-grounded`
2. `ui-short-branding-trust`
3. `bl-explanatory-misread-metric`
4. `bl-daily-learning-log-grounded`

## Run Count

- 1 lane あたり `4 cases x 3 repeats = 12 runs`
- total `24 live runs`
- raw manifest:
  - `C:\tetie\notecode\logs\reference_realization_policy_compare_20260417\20260417-123933\raw_summary.json`

## Contract Freeze

- `ui-short-branding-company-grounded`
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\20260322-123339-short\ui-short-branding-company-grounded.json`
- `ui-short-branding-trust`
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\20260322-123339-short\ui-short-branding-trust.json`
- `bl-explanatory-misread-metric`
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260331-phase02-baseline-live\bl-explanatory-misread-metric.json`
- `bl-daily-learning-log-grounded`
  - `C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260331-phase02-baseline-live\bl-daily-learning-log-grounded.json`

## Supporting Metrics Median

| case | lane | company-name repeat | explicit subject ratio | ending max run | abstract term density | paragraph length cv | body chars |
|---|---:|---:|---:|---:|---:|---:|---:|
| `ui-short-branding-company-grounded` | A | 13 | 0.1212 | 4 | 17.9748 | 0.6983 | 1485 |
| `ui-short-branding-company-grounded` | B | 15 | 0.1935 | 3 | 15.3115 | 0.6960 | 1521 |
| `ui-short-branding-trust` | A | 0 | 0.0244 | 3 | 10.4046 | 0.5168 | 1593 |
| `ui-short-branding-trust` | B | 0 | 0.0286 | 4 | 8.4477 | 0.5066 | 1666 |
| `bl-explanatory-misread-metric` | A | 0 | 0.0000 | 3 | 4.0837 | 0.5283 | 1847 |
| `bl-explanatory-misread-metric` | B | 0 | 0.0000 | 3 | 6.2182 | 0.4486 | 2109 |
| `bl-daily-learning-log-grounded` | A | 0 | 0.0000 | 1 | 0.0000 | 0.6313 | 604 |
| `bl-daily-learning-log-grounded` | B | 0 | 0.0000 | 1 | 0.0000 | 0.6233 | 742 |

## Human Rubric Summary

6項目 `0 / 1 / 2` の manual reading による median summary。

| case | lane A median | lane B median | consistency note | reading memo |
|---|---:|---:|---|---|
| `ui-short-branding-company-grounded` | 5 / 12 | 5 / 12 | `0/3` improvement | lane B でも `テティエ株式会社` / `株式会社` の前景反復が 3/3 で残存 |
| `ui-short-branding-trust` | 9 / 12 | 9 / 12 | `0/3` clear improvement | readable だが B が A を明確に上回らない |
| `bl-explanatory-misread-metric` | 10 / 12 | 10 / 12 | `3/3` no-first-person pass | guard pass。B は少し締まる run もあるが gain は不安定 |
| `bl-daily-learning-log-grounded` | 7 / 12 | 7 / 12 | `3/3` no regression | guard pass。ただし baseline 自体が一人称弱め |

## Main Findings

### company introduction

- `NO_GO` stop condition に該当
- lane B は `3/3` repeats 全てで company name / `株式会社` の前景反復を解消できなかった
- 視認上も
  - lead で会社名を立てる
  - section 冒頭でも会社名を再アンカーする
  - closing でも会社名を戻す
  という運びが残った
- metrics でも lane B median は lane A より改善していない
  - company-name repeat `13 -> 15`
  - explicit subject ratio `0.1212 -> 0.1935`
- よって `reference realization policy` line は main target の中心ケースで visible gain を示せなかった

### branding

- lane B は usable だが、lane A 比で `+2` median に届かない
- `2/3 repeats` 以上の clear improvement も出ていない
- 抽象語密度は少し下がる run がある一方で、主語再導入や一人称配分は横ばい
- 「brochure 化を減らした」とまでは判定できない

### explanatory

- `no-first-person` guard は lane B `3/3` pass
- corporate narrator への悪化も見えない
- ただし lane A を明確に上回る visible gain までは出ていない
- guard pass だが `GO` の押し上げ材料にはならない

### daily

- regression guard は pass
- dry / corporate / explanatory への悪化は見えない
- ただし current first slice の対象外であり、gain 判定材料にもならない

## Judgment

- verdict:
  - `NO_GO`
- reason:
  - `company_introduction` main target で company name / `株式会社` の前景反復が残った
  - `branding` でも lane A を明確に上回る `2/3` consistency が出なかった
  - gain が `reference realization policy` に閉じて visible improvement として説明できない
- next production owner:
  - `do not open`
  - `C:\tetie\notecode\note\natural_blog_core.py` を production owner として reopen しない
- management note:
  - this line は separate evidence として止める
  - fixed routing / formatter / prompt accretion へ逃がさない

## Final Report Checklist

1. 実行した lanes
   - lane A `policy OFF`
   - lane B `policy ON`
   - lane C 未実施
2. compare case list
   - `ui-short-branding-company-grounded`
   - `ui-short-branding-trust`
   - `bl-explanatory-misread-metric`
   - `bl-daily-learning-log-grounded`
3. run count
   - `24`
4. rubric summary
   - main target `+2` なし
5. company / branding の visible improvement 有無
   - `no`
6. explanatory の no-first-person guard 結果
   - `pass`
7. daily の regression 有無
   - `no visible regression`
8. `GO` か `NO_GO` か
   - `NO_GO`
9. next production owner を開くべきか
   - `no`
10. 日本語ブログ runtime を変更していないこと
   - `production runtime unchanged`
11. AGENTS / WORKLOG 更新不要であること
   - `update unnecessary`

# current mainline quality status 2026-03-23

最終更新: 2026-03-23  
対象: `C:\tetie\notecode` current runtime mainline の現状整理  
スコープ: runtime 実装変更なし。quality / regression / live artifact / initiative 境界の整理のみ

## 目次

- 1. Snapshot
- 2. Completed / Pending Initiative
- 3. Regression / Live Evidence
- 4. Article Type ごとの品質要約
- 5. 改善済み / 未解決
- 6. Dead Code / Quarantine / Retirement
- 7. 次に触るならどの owner か
- 8. やってはいけないこと

## 1. Snapshot

- current runtime mainline は `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`。
- current UI / control plane は `C:\tetie\notecode\note\note_writer_app.py` -> `C:\tetie\notecode\note\current_mainline_runner.py` -> `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py` -> `simple_note_pipeline` の順で通る。
- compatibility import path は `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`。本文本流の owner は simple note mainline で、legacy 本文には戻していない。
- fixed runtime rule:
  - 本文 mainline は `single-pass + optional single repair 1回`
  - `## 目次` は markdown に留める
  - note rule check は必須
  - free text は残す
  - question flow は unresolved slot 補完に限定する
- current source of truth は次で固定する。
  - `C:\tetie\AGENTS.md`
  - `C:\tetie\notecode\AGENTS.md`
  - `C:\tetie\notecode\plan\simple_note_refactor_2026-03-22\README.md`
  - `C:\tetie\notecode\plan\simple_note_refactor_2026-03-22\PROGRESS.md`
  - `C:\tetie\notecode\ALGORITHM.md`
  - `C:\tetie\WORKLOG.md`
  - `C:\tetie\notecode_current_mainline_handoff_2026-03-18.md`
  - `C:\tetie\notecode\current_mainline_owner_split\PROGRESS.md`
  - `C:\tetie\notecode\current_mainline_owner_split\OWNER_MAP.md`
  - `C:\tetie\notecode\vnext_current_integration\PROGRESS.md`
- 現在の quality 判断の一次根拠は 2026-03-22 artifact 群。
  - `C:\tetie\notecode\logs\current_mainline_ui_short_matrix_phase05_live_recollect_run01_20260322.json`
  - `C:\tetie\notecode\logs\current_mainline_ui_short_matrix_phase05_live_recollect_run02_20260322.json`
  - `C:\tetie\notecode\logs\current_mainline_ui_short_matrix_phase05_live_recollect_run03_20260322.json`
  - `C:\tetie\notecode\logs\vnext_current_shared_eval_phase1_20260322.json`
  - `C:\tetie\notecode\logs\current_mainline_model_compare\20260322-225926\summary.json`
- `notecode/logs/latest_generation_output.json`、`latest_generation_output.txt`、`latest_generation_quality_report.json`、`generation_audit_log.jsonl` は 2026-03-13 23:26:32 で止まっている。current quality の一次根拠としては stale で、03-22 の matrix/live artifacts を優先する。

## 2. Completed / Pending Initiative

### Completed

- `simple_note_refactor_2026-03-22` は `completed` のまま。reopen しない。
- `current_mainline_owner_split` は `completed`。
- `vnext/current integration` は Phase00-04 completed。
- vNext overlap seed promotion は実施済み。
- quarantine は `Slice 9` まで適用済み。

### Pending

- `vnext/current integration` は Phase05 pending。
- single blocker は `branding/company_introduction` の `approve_each_route_promotion` human gate 未完了。
- current mainline quality は runtime failure ではなく quality blocker が残る。
  - latest live accepted passes は `rubric_mean_total=7.9`
  - latest compare summary は `gpt-5.4-mini short_mean=6.6`
- observability 上は `latest_generation_output.*` 系の freshness gap が残る。

## 3. Regression / Live Evidence

### 2026-03-23 local regression

- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q`
  - `67 passed`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_model_compare_tool.py note\tests\test_newalgorithm_phase06_logging_compat.py -q`
  - `32 passed`
- `C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_vnext_current_shared_eval.py note\tests\test_vnext_current_boundary_freeze.py -q`
  - `14 passed`

### 2026-03-22 recent live output

- Phase05 live recollect run01 は rejected。
  - artifact: `C:\tetie\notecode\logs\current_mainline_ui_short_matrix_phase05_live_recollect_run01_20260322.json`
  - reason: `ui-short-branding-company-grounded` が `POL_PROMPT_ECHO`
  - route case rubric: `4.0`
- Phase05 live recollect run02 / run03 は accepted。
  - artifacts:
    - `C:\tetie\notecode\logs\current_mainline_ui_short_matrix_phase05_live_recollect_run02_20260322.json`
    - `C:\tetie\notecode\logs\current_mainline_ui_short_matrix_phase05_live_recollect_run03_20260322.json`
  - 両方とも `10/10 success`、retry `0`、fallback `0`
  - `rubric_mean_total=7.9`
  - route case `branding/company_introduction` は `8.0`
  - weakest accepted case は `ui-short-comparative-axis-lock` の `7.0`
- shared eval current state:
  - `C:\tetie\notecode\logs\vnext_current_shared_eval_phase1_20260322.json`
  - `completed_pass_count=2`
  - `latest_status=live_pass_x2_complete`
  - `status=pending_human_gate`
- latest model compare:
  - `C:\tetie\notecode\logs\current_mainline_model_compare\20260322-225926\summary.json`
  - `gpt-5.4-mini short_mean=6.6`, hard fail `0`
  - `gpt-4.1-mini-2025-04-14 short_mean=4.8`, hard fail `10`
  - preferred primary model は `gpt-5.4-mini`

## 4. Article Type ごとの品質要約

| article type | current status | 改善済み | 未解決 |
|---|---|---|---|
| `explanatory_article` | accepted、`8/10` | contract / structure / grounding は崩れない | `partial_contract_reflection`、スタイロメトリ上の flatness、語尾分布の単調さ |
| `daily_story` | accepted、`8-9/10` | source なしでも fail-close せず自然に通る。reader-helpful な一般補助で収まる | repetition / ending repetition が残る。補足を増やしすぎると即 AI 感が戻る |
| `branding` | trust / company とも accepted、company route は `8/10` | `POL_PROMPT_ECHO` 再現 run から accepted run へ戻せた。source_trace は `1.0` | company route は echo 感度が高い。soft warning `8`、human gate 未了 |
| `announcement` | action / dense must-cover とも accepted、`8/10` | action 導線と grounding は安定 | dense case の `must_cover_reflection_rate=0.6667`。統計言語学上 `mtld_low` / ending repetition が残る |
| `case_study` | accepted、`8/10` | `case_result_grounded` は維持。condition 節も落ちていない | `must_cover_reflection_rate=0.6667`、sentence ending entropy low、comma overuse |
| `industry_analysis` | accepted、`8/10` | structure / grounding は安定 | nominalization と repetitive ending による AI 感が残る |
| `comparative_review` | standard case は `8/10`、axis-lock は `7/10` | comparison 軸は保持できる | `comparative_axis_soft_shift` がまだ残る。article type fit の未解決が最も明確 |

補足:

- ほぼ全 article type で `contract_fit=partial_contract_reflection` と `human_visible_ai_feel=flat_or_repetitive` が共通 residual になっている。
- recurring warning は次に集中している。
  - `fingerprint:bigram_mono_low`
  - `fingerprint:vocab_repetition`
  - `fingerprint:nominalization_rate_high`
  - `fingerprint:sentence_ending_entropy_low`
  - `fingerprint:syntactic_complexity_low`
  - `fingerprint:ending_repetition`
- must_cover の本文反映は dense announcement / case study でまだ満額ではない。
- source が薄い記事で GPT-5.4-mini の補足を許すなら reader-helpful な一般補助までに限定し、source にない断定や長文化のための水増しは不可。

## 5. 改善済み / 未解決

### 改善済み

- 本文 mainline は `single-pass + optional single repair 1回` に固定できている。
- prompt と module の budget は維持され、simple note refactor を reopen しなくてよい状態。
- live accepted runs では retry `0`、fallback `0`、visible UI change `0`。
- grounded cases では `source_trace_coverage=1.0` を維持している。
- `branding/company_introduction` の prompt echo は rejected run が観測された一方で、accepted run に戻せている。

### 未解決

- `rubric_mean_total >= 8.0` の quality threshold を cross-type ではまだ越えていない。
- paragraph / rhythm / ending distribution / repetition control は改善余地が大きい。
- must_cover の本文反映は dense case で取りこぼしがある。
- comparative axis lock は article type fit の弱点が明確に残っている。
- `latest_generation_output.*` が stale で、live evaluation と fixed-path latest snapshot がずれている。

## 6. Dead Code / Quarantine / Retirement

- `note/legacy_current/` は quarantine entry として残す。
- production で legacy owner を直接見せる入口は `legacy_helper_adapter.py` と root same-name shim 群に固定されている。
- quarantine は Slice 1-9 まで適用済み。
- Phase 6 retirement は未着手で、この window の対象外。
- old `ArticleGenerator`、`human_resonance*`、`vnext` を本文 mainline に戻さない。
- `Slice 10` quarantine-only reopen を default next action にしない。

## 7. 次に触るならどの owner か

- 本命 owner は `C:\tetie\notecode\note\natural_blog_core.py`。
- 理由:
  - current blocker は runtime 失敗ではなく、anchor / carry / paragraph rhythm / ending distribution / repetition control の quality 側に寄っている。
  - 2026-03-18 handoff でも、次の narrow slice は prompt 追加ではなく `natural_blog_core.py` の anchor / carry 配分見直しを推奨している。
  - comparative / case_study / dense announcement の contract reflection 改善も、prompt accretion より core 側の配分調整の方が筋がよい。
- support owner は `C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py`。
  - ただし quality 指標の観測を補う用途に限る。repair 回数拡張や guard 肥大化の入口にはしない。

## 8. やってはいけないこと

- prompt accretion
- module accretion
- 文字数を増やすこと自体を目的にすること
- source にない断定的な補足を足すこと
- `simple_note_refactor_2026-03-22` を勝手に reopen すること
- `current_mainline_runner.py` の route mapping source of truth を別 owner へ複製すること
- old `ArticleGenerator` / `human_resonance*` / `vnext` を本文 mainline に戻すこと
- question flow を unresolved slot 補完以外へ広げること

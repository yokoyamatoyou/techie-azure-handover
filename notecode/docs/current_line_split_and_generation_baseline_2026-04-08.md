# current line split and generation baseline 2026-04-08

参照ルールファイル: `C:\tetie\AGENTS.md`, `C:\tetie\notecode\AGENTS.md`

## 目的

- 「今の本線」と「以前の後半崩れ対策を含む参照記録」を切り分ける
- current mainline だけを使う生成入口を固定する
- 以後の branding / company introduction の live 生成で、比較先が混ざらないようにする

## current source-of-truth line

- planning package
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
- runtime success path
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- visible baseline
  - `C:\tetie\notecode\logs\latest_generation_output.txt`
  - `C:\tetie\notecode\logs\latest_generation_output.json`
  - `C:\tetie\notecode\logs\latest_generation_quality_report.json`
- current runtime reading
  - branding/company introduction の現 baseline は `writer_of_record = simple_note_pipeline`
  - current route は `route_branch = single_pass_default`
  - current package の next owner は `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

## reference line

- active reference
  - `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\README.md`
  - 役割: archive 切り離しと visible symptom 管理の直近参照
- completed / frozen reference
  - `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\`
  - `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\`
  - `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\`
- archive-only
  - `C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\README.md`
  - 役割: historical rationale の参照専用

## mixed-risk records

以下は「今の挙動」ではなく、以前の実験や失敗再発防止の履歴として読む。

- `C:\tetie\notecode\docs\generation_failure_prevention_log.md`
  - `F-2026-04-02-03`
  - `F-2026-04-02-02`
  - `F-2026-04-02-01`
  - paragraph bundling / section rhythm / company voice を強く入れて悪化した記録
- `C:\tetie\notecode\logs\current_mainline_ui_runs\`
  - rerun と comparative artifact が混在しやすい
  - current package の source-of-truth ではなく、症状の見本と過去検証の置き場
- `experimental_prompt_stack`
  - full stack support/planner/writer/editor/legal の実験名
  - current baseline の標準ルートではない
- `vnext_shadow`
  - output guard 後の shadow 監査ライン
  - current visible artifact の本文 owner そのものではない

## generation rule for this turn

- 使うのは current mainline のみ
- case は `ui-short-branding-company-grounded`
- 比較対象に `experimental_prompt_stack` と旧 `current_mainline_ui_runs` rerun を混ぜない
- prompt は current mainline 上で最も安定した `balanced detail` を使う

## generation prompt

```text
医療支援SaaS企業の会社紹介記事を書いてください。導入前に概要を知りたい読者向けに、事業内容と導入初期を支える姿勢が自然に伝わる文章にしてください。資料にある事実を軸に、何をしている会社か、なぜ導入初期支援を重視するのか、問い合わせを運用改善へ戻す進め方、最後に読者がどう理解すればよいか、の順で整理してください。宣伝調に寄せすぎず、現場での支え方が見える会社紹介にしてください。文の長さを揃えすぎず、同じ文末を続けすぎず、見出しごとに適度に改行し、ソースにない実績や数値は足さない。
```

## live generation artifact

- artifact dir
  - `C:\tetie\notecode\logs\current_line_split_generation\20260408-201346`
- summary
  - `C:\tetie\notecode\logs\current_line_split_generation\20260408-201346\summary.json`
- generated text
  - `C:\tetie\notecode\logs\current_line_split_generation\20260408-201346\current-line-branding-company-grounded-balanced-detail.txt`
- generated json
  - `C:\tetie\notecode\logs\current_line_split_generation\20260408-201346\current-line-branding-company-grounded-balanced-detail.json`

## generation result reading

- selected line
  - `pipeline_source = newalgorithm_mainline`
  - `cutover_rehearsal.selected_engine = current_mainline`
- shadow line attached as observer
  - `cutover_rehearsal.candidate_engine = vnext_shadow`
  - `vnext_shadow.enabled = true`
  - 解釈: shadow は監査同居しているが、今回の本文 owner ではない
- current body owner evidence
  - `writer_of_record = simple_note_pipeline`
  - `route_branch = single_pass_default`
- repair state in this live run
  - `patch_path_refusal_reason = repair_call_unavailable`
- quality snapshot
  - `rubric_total = 8`
  - `output_guard.soft_warning_count = 4`
  - `final_quality_soft_warning_count = 6`
  - `human_visible_ai_feel = flat_or_repetitive`

# ui_prompt_distillation_autonomous_2026-04-14 PROGRESS

## Current Goal

- UI input distillation を generation 本線へ導入し、7 category 横断で自然さと安定性を判定する

## Current Status

- package status:
  - completed
- current phase:
  - Phase 7 final judgment
- status:
  - complete
- hypothesis:
  - visible naturalness の勝ち筋は raw UI expansion ではなく、短い distilled brief と generation-time の軽い style constraint にある
- fixed category inventory:
  - `explanatory_article`
  - `industry_analysis`
  - `branding`
  - `announcement`
  - `case_study`
  - `comparative_review`
  - `daily_story`

## Phase Ledger

- Phase 0:
  - status: completed
  - result:
    - repo-backed category inventory frozen
    - rollback boundary fixed
    - compare targets fixed
- Phase 1:
  - status: completed
  - result:
    - distilled contract shape documented
    - source digest 粒度固定
    - neutral explainer baseline fixed
- Phase 2:
  - status: completed
  - result:
    - `ui_prompt_distillation.py` を追加
    - generation prompt に `BRIEF / SOURCE_DIGEST / task=` を追加
- Phase 3:
  - status: completed
  - result:
    - company intro voice policy tightened
    - comparative title / lead anti-echo guidance added
- Phase 4:
  - status: completed
  - result:
    - baseline probe compare 固定
    - prompt-only floor / previous generic evidence を照合
    - public web compare evidence reviewed
    - direct GPT web compare unavailable 記録
- Phase 5:
  - status: completed
  - result:
    - invalid source-less attempt recorded
    - source-backed 7 category x 3 reruns completed
- Phase 6:
  - status: completed
  - result:
    - comparative repair iteration 1 adopted
- Phase 7:
  - status: completed
  - result:
    - final verdict fixed

## Touched Owners

- Phase 2:
  - `C:\tetie\notecode\note\simple_note_pipeline\ui_prompt_distillation.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- Phase 3:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\ui_prompt_distillation.py`
- Phase 6 iteration 1:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\ui_prompt_distillation.py`
  - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`

## Tests

- owner-local regression:
  - `py -3 -m pytest C:\tetie\notecode\note\tests\test_simple_note_pipeline.py -q`
  - result:
    - `90 passed, 1 warning`
- phase 5 initial evaluation:
  - artifact:
    - `C:\tetie\notecode\logs\ui_prompt_distillation_autonomous_20260414\aggregate_eval.json`
  - result:
    - source-less representative cases were invalid under current runtime gate
- phase 5 final evaluation:
  - artifact:
    - `C:\tetie\notecode\logs\ui_prompt_distillation_autonomous_20260414\aggregate_eval_source_backed.json`
- phase 6 repair iteration 1:
  - artifact:
    - `C:\tetie\notecode\logs\ui_prompt_distillation_autonomous_20260414\comparative_repair_iter1.json`

## Compare Ledger

- current keep baseline:
  - pre-change local live probe:
    - `C:\tetie\notecode\logs\ui_prompt_distillation_baseline_probe_20260414\`
  - observed weakness:
    - branding company intro still brochure 寄り
    - explanatory / comparative の title / lead が template 寄り
- prompt-only floor:
  - reference:
    - `C:\tetie\notecode\docs\separate_experiment_fixed3_naturalness_final_report_2026-04-13.md`
  - separate line judgment:
    - distilled brief は prompt echo を増やさず grounding を残せた
    - prompt-only floor より blog lead の入りが素直
- public web compare:
  - reference evidence:
    - `C:\tetie\notecode\research\新しいフォルダー (11)\新しいフォルダー (2)\hankyu_hanshin_real_estate_company_article.md`
    - `C:\tetie\notecode\research\新しいフォルダー (11)\新しいフォルダー (2)\阪急阪神不動産株式会社_会社紹介記事.md`
    - `C:\tetie\notecode\research\新しいフォルダー (11)\新しいフォルダー (2)\shanai_rag_precision_review_article.md`
  - supported pattern:
    - current-business-first
    - short paragraphs
    - lead from current role / current issue, not label card
- direct GPT web compare:
  - unavailable

## Category Evaluation

- `branding`
  - representative:
    - `ui-short-branding-company-grounded`
  - rerun result:
    - `3/3 pass`
  - Codex visual judgment:
    - neutral company intro が維持され、`私` や company-as-first-person が出ない
    - lead が current business から入り、history-first に戻らない
  - category verdict:
    - `stable pass`
- `announcement`
  - representative:
    - `ui-short-announcement-dense-must-cover`
  - rerun result:
    - `3/3 pass`
  - Codex visual judgment:
    - かなり事務連絡寄りだが、対象 / 事前準備 / 当日確認の運びは安定
    - blog naturalness の上限は高くないが、announcement としては許容
  - category verdict:
    - `stable pass`
- `daily_story`
  - representative:
    - `bl-daily-learning-log-grounded`
  - rerun result:
    - `3/3 pass`
  - Codex visual judgment:
    - title と lead が読み物として入れる
    - 一人称連打を避けつつ、学びへの接続も保てた
  - category verdict:
    - `stable pass`
- `case_study`
  - representative:
    - `ui-short-case-study-explain`
  - rerun result:
    - `3/3 pass`
  - Codex visual judgment:
    - 読めるが、やや project report 寄りで blog としての柔らかさは揺れる
    - 課題 / 対応 / 再現条件は落としていない
  - category verdict:
    - `unstable pass`
- `industry_analysis`
  - representative:
    - `ui-short-industry-analysis-grounded`
  - rerun result:
    - `3/3 pass`
  - Codex visual judgment:
    - prompt echo を抑えつつ、論点から入る lead を維持
    - 90日運用負荷という判断軸が読み物として通る
  - category verdict:
    - `stable pass`
- `comparative_review`
  - representative:
    - `ui-short-comparative-axis-lock`
  - phase 5 rerun result:
    - `3/3 short_gate fail`
    - reason:
      - title prompt echo
  - phase 6 iteration 1:
    - `3/3 pass`
    - `prompt_echo_hits = 0`
    - title を `選び方 / 向く条件` 起点へ変更
  - category verdict:
    - `stable pass`
- `explanatory_article`
  - representative:
    - `bl-explanatory-misread-metric`
  - rerun result:
    - `3/3 pass`
  - Codex visual judgment:
    - still formal だが、card-like label feel は baseline より弱い
    - grounding の見え方を落とさず、判断軸の順序も自然
  - category verdict:
    - `stable pass`

## Repair Ledger

- invalid evaluation selection
  - hypothesis:
    - short sweep built-in cases をそのまま 7 category representative に使える
  - result:
    - rejected
  - reason:
    - current runtime gate が `source_documents` 空 case を `INP_MISSING_REQUIRED` で停止した
- comparative iteration 1
  - hypothesis:
    - `比較軸` 語を title / lead の表面から外せば prompt echo を消せる
  - tests:
    - `py -3 -m pytest C:\tetie\notecode\note\tests\test_simple_note_pipeline.py -q`
    - comparative 3 reruns
  - artifact:
    - `C:\tetie\notecode\logs\ui_prompt_distillation_autonomous_20260414\comparative_repair_iter1.json`
  - decision:
    - adopted

## Final Judgment

- stable pass categories:
  - `branding`
  - `announcement`
  - `daily_story`
  - `industry_analysis`
  - `comparative_review`
  - `explanatory_article`
- unstable pass categories:
  - `case_study`
- unresolved categories:
  - none
- autonomous line verdict:
  - `keep`
- current package keep-state:
  - untouched
- AGENTS / WORKLOG:
  - not updated
- backport candidate:
  - distilled brief injection
  - company intro neutral explainer voice rule
  - comparative title anti-echo surface rule

## Decision Boundary

- keep:
  - stable pass categories が複数あり、current keep baseline または prompt-only floor に対して実用優位がある
- rollback:
  - code diff が mainline を悪化させる、または採用カテゴリが不足する
- stop:
  - bounded repair loops を使い切っても unresolved が多く、勝ち筋が owner set を超える

## Notes

- deepresearch は evidence 参照のみ
- public web compare は補助根拠
- direct GPT web compare は未確認。可能なら separate artifact として記録する

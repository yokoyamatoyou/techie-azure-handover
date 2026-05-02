# separate window execution prompt ai naturalness soft warning actuation 2026-04-21

```text
参照ルールファイル:
- current source-of-truth:
  - C:\tetie\AGENTS.md
  - C:\tetie\notecode\AGENTS.md
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
  - C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md
  - C:\tetie\notecode\ALGORITHM.md
  - C:\tetie\WORKLOG.md
- latest visible / quality baseline:
  - C:\tetie\notecode\logs\latest_generation_output.txt
  - C:\tetie\notecode\logs\latest_generation_quality_report.json
- user comparison destination:
  - C:\tetie\notecode\新しいフォルダー
- current local baseline note:
  - current window removed hard-coded explanatory lead replacement from:
    - C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
    - C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py
  - updated local tests:
    - C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
    - C:\tetie\notecode\note\tests\test_newalgorithm_phase03_pipeline.py
  - do not reintroduce these fixed leads:
    - 「機能比較へ進む前に、前提と判断軸をそろえておく必要があります。」
    - 「本文では、実務判断に直結する見方を落ち着いて整理します。」
    - 「本稿では、比較に先立って確認すべき前提と判断軸を整理します。」

今回の依頼種別:
- separate-window implementation prompt
- `AI_NATURALNESS_SOFT_WARNING_ACTUATION`
- 目的は対症療法ではなく、AIっぽさを検出しているのに success artifact として返す設計を narrow に直すこと

今回の実施範囲:
- まず実出力と品質レポートを読む
- 「機械っぽさ」の原因を以下に切り分ける:
  1. hard-coded opening / formatter replacement
  2.構成の均一化
  3. soft warning が repair / fail-closed に接続されないこと
  4. writer persona / prompt surface の不足
- そのうえで、1 owner / 1 narrow hypothesis に絞って実装する
- production code と owner-local tests は更新可
- AGENTS / WORKLOG / current package docs は更新しない
- C:\tetie\notecode\新しいフォルダー に比較用生成物を必ず配置する

source-of-truth lock:
- current success path:
  - C:\tetie\notecode\note\current_mainline_runner.py
  - -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
  - -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- current default route は `grounded generic default`
- planning / skeleton は opt-in only
- structural baseline は `single-pass + optional single repair 1回`
- prompt accretion 禁止
- hidden reviser accretion 禁止
- fixed routing table を追加しない
- article-type ごとの ad-hoc rule を増やさない
- formatter regex だけで visible polish する案を初手にしない
- persona 文言追加だけで解決したことにしない
- same failed hypothesis を unchanged で再投入しない

current visible diagnosis to preserve:
- latest quality report already detects AI-like surface:
  - `fingerprint:vocab_repetition`
  - `fingerprint:nominalization_rate_high`
  - `fingerprint:syntactic_complexity_low`
  - `ending:bucket_monotony`
  - `company_intro:naturalness_rescue`
- current problem is not "warning cannot be detected"
- current problem is "warning is still returned as success without reliable repair / fail-closed / visible improvement"
- visible text should be judged by reading the article, not only by metrics

external evidence boundary:
- 検索は使ってよい
- ただし external research は evidence only
- Google people-first guidance / Japanese stylometry / AI writing linguistic markers は補助根拠として扱う
- final report では使った検索ソースを URL 付きで列挙する
- search result を理由に broad SEO tuning や generic humanizer を入れない

first step required:
1. Read current source-of-truth files in the AGENTS read order.
2. Read latest visible output and quality report.
3. Read current local diff around hard-coded lead deletion.
4. Make a short owner map before editing:
   - simple_note_pipeline/pipeline.py
   - simple_note_pipeline/quality_guard.py
   - newalgorithm_pipeline/output_guard.py
   - simple_note_pipeline/prompt_builder.py
   - newalgorithm_pipeline/output_formatter.py
5. Pick exactly one production owner for the first diff.
6. If more than one production owner is required, stop and report instead of broadening.

preferred hypothesis shape:
- Best candidate:
  - soft warning actuation / repair acceptance / fail-closed connection
  - likely owner: C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  - or C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py only if output guard is the actual success leakage point
- Avoid as first candidate:
  - prompt_builder.py persona expansion
  - output_formatter.py surface rewrite
  - natural_blog_core.py section defaults
  - input_contract.py upstream summary
  - note_writer_app.py UI changes

allowed owner scope:
- Choose one production owner only:
  - C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  - OR C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py
  - OR C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py
- Tests may be updated as needed:
  - C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
  - C:\tetie\notecode\note\tests\test_simple_note_quality_guard.py
  - C:\tetie\notecode\note\tests\test_current_mainline_runner.py
  - C:\tetie\notecode\note\tests\test_current_mainline_regressions.py
  - C:\tetie\notecode\note\tests\test_current_mainline_ui_matrix.py

do not touch in first diff:
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
  - unless the owner map proves the writer prompt is the single owner and user-facing success leakage is not repair/guard related
- C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py
  - do not add new surface regex / fixed lead / fixed sentence cleanup
- C:\tetie\notecode\note\natural_blog_core.py
- C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py
- C:\tetie\notecode\note\note_writer_app.py
- AGENTS / WORKLOG / current package docs

implementation rules:
1. No exact phrase ban-list patch as the main solution.
2. No "humanize this" generic prompt block.
3. No new multi-stage reviser.
4. No article-type fixed routing table.
5. Keep single-pass + optional single repair 1回.
6. Use existing quality metrics where possible.
7. If current quality report already has AI-like soft warnings, connect them to:
   - repair trigger,
   - repair acceptance,
   - or fail-closed,
   whichever is the narrow owner-local point.
8. Require visible improvement, not only metric improvement.
9. Preserve current hard-coded explanatory lead deletion.
10. Do not return success if generated article still reads more mechanical after visible review.

mid-body edit firing check:
- Must verify whether editing / repair only changes the opening or also fires after the middle of the article.
- Record for each validation run:
  - whether repair was called
  - whether patch path was used
  - whether changed spans are in lead / first third / middle third / final third
  - whether middle-or-later text improved or remained machine-like
- If telemetry does not expose span location, inspect before/after text manually and record a best-effort span map.
- If no middle-or-later edit can fire despite soft warnings in the body, report that as an unresolved design issue.

validation artifacts:
- Place every generated artifact under:
  - C:\tetie\notecode\新しいフォルダー
- Use a new prefix:
  - `20260421_ai_naturalness_actuation_`
- Required files:
  1. `20260421_ai_naturalness_actuation_baseline_article.md`
  2. `20260421_ai_naturalness_actuation_baseline_quality.json`
  3. `20260421_ai_naturalness_actuation_after_article.md`
  4. `20260421_ai_naturalness_actuation_after_quality.json`
  5. `20260421_ai_naturalness_actuation_regen_article.md`
  6. `20260421_ai_naturalness_actuation_regen_quality.json`
  7. `20260421_ai_naturalness_actuation_compare.md`
  8. `20260421_ai_naturalness_actuation_eval.json`
  9. `20260421_ai_naturalness_actuation_user_review_sheet.md`
- If generation command naturally writes logs elsewhere, copy or summarize the relevant visible artifact into the files above.
- Do not overwrite existing files in C:\tetie\notecode\新しいフォルダー.

visual / human review requirements:
- Codex must visually read the produced article text, not just parse JSON.
- Compare baseline / after / regeneration by reading:
  - title
  - lead
  - first heading
  - first section
  - a middle section
  - final section
- In `compare.md`, include:
  - short excerpts only
  - AI-like symptoms before
  - what changed after
  - whether middle-or-later editing fired
  - whether regeneration preserves the improvement
  - remaining unnatural sentences
- In `user_review_sheet.md`, include a compact checklist for user confirmation:
  - fixed lead absent
  - opening not meta
  - middle section feels less mechanical
  - endings not monotonous
  - examples / concrete claims feel grounded
  - article still matches source facts
  - user accept / reject / notes

regeneration requirement:
- After implementation and first validation, run regeneration at least once on the same or equivalent current mainline input.
- Confirm:
  - hard-coded opening does not return
  - repair / guard behavior is stable
  - AI-like warning is repaired, blocked, or explicitly reported
  - no history-first company intro regression

minimum validation cases:
- V1: latest visible baseline rerun or equivalent current mainline generation
- V2: explanatory / comparison style case that previously received the fixed lead
- V3: company introduction case from latest baseline
- G1: non-target branding or announcement guard
- Required variance:
  - V3 company intro: 2 runs minimum
  - V2 explanatory/comparison: 2 runs minimum
  - G1: 1 run minimum

test / check order:
- focused owner-local:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
- boundary:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q
- UI guard:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py -q
- formatter boundary if output formatter is touched:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_newalgorithm_phase03_pipeline.py -k "st16" -q

pass gate:
- Fixed explanatory lead phrases are absent from production code and generated artifacts.
- Latest AI-like soft warnings do not pass silently as success without repair / fail-closed / visible report.
- Visible after article is less mechanical than baseline by human reading.
- Middle-or-later section behavior is inspected and reported.
- Regeneration preserves the improvement or fails closed.
- Owner-local and shared checks pass.
- Generated comparison artifacts are placed in C:\tetie\notecode\新しいフォルダー.

stop conditions:
- A real fix requires multiple production owners.
- The only available fix is prompt/persona accretion.
- The only available fix is formatter regex cleanup.
- Soft warnings cannot be connected to repair / fail-closed without broad rewrite.
- Regeneration reintroduces fixed lead or obvious machine-like body text.
- Same owner hypothesis fails 3 times.

if hypothesis fails:
- Roll back the attempted code diff.
- Keep hard-coded lead deletion baseline if it was already present before this window.
- Produce a stop report in:
  - C:\tetie\notecode\新しいフォルダー\20260421_ai_naturalness_actuation_stop_report.md
- Include visible failure examples and why unchanged retry is not recommended.

final report must include:
1. 読んだ正本ファイル
2. 検索した外部ソース URL
3. owner map
4. selected owner and why
5. rejected owners and why
6. implemented narrow hypothesis
7. touched files
8. tests added / updated
9. commands run and results
10. generated artifact paths under C:\tetie\notecode\新しいフォルダー
11. baseline vs after vs regeneration visible read
12. whether mid-body edit / repair fired
13. whether AI-like warnings were repaired / blocked / still only warned
14. rollback status
15. confirmation that AGENTS / WORKLOG / current package docs were not updated
```

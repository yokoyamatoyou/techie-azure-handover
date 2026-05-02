# separate window execution prompt targeted deepresearch redirect after sentence final stop 2026-04-17

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\docs\separate_window_management_memo_deepresearch_reflection_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_priority_revision_after_deepresearch_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_compare_plan_reference_realization_policy_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_compare_result_reference_realization_policy_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_management_retriage_after_visible_smoke_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_sentence_final_monotony_visible_smoke_after_rollback_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_instruction_window_handoff_after_deepresearch_2026-04-17.md
- C:\tetie\notecode\logs\sentence_final_monotony_visible_smoke_after_rollback_20260417-202435\summary.json
- C:\tetie\notecode\logs\latest_generation_output.json

今回の依頼種別:
- targeted deepresearch prompt
- redirect candidate selection
- source-of-truth update ではない
- implementation prompt ではない
- compare execution prompt ではない

今回の実施範囲:
- `sentence-final pattern monotony cap + single repair` line を continuation しない前提で、next redirect line を絞るための targeted deepresearch を行う
- local docs / logs の既存 evidence を起点にし、外部 research はその判断を補強または否定するためにだけ使う
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない
- 作るのは management note 1 本だけに留める

current keep-state:
- route default:
  - `grounded generic default`
- planning:
  - `opt-in only`
- structural baseline:
  - `single-pass + optional single repair 1回`
- blank company intro keep line:
  - `prompt_builder.py` の `current-business-first keep line`
- `reference realization policy`:
  - separate evidence line のまま keep
- module accretion 禁止
- prompt accretion 禁止

already known and must inherit:
- `sentence-final monotony` line は latest management retriage で `STOP_AND_REDIRECT`
- reason:
  - rollback 後も representative 3 case で `repair_applied = false`
  - `scope_acceptance_path` 未出力
  - title / hashtags / heading flow drift と company intro の history-first drift が残った
- `reference realization policy` compare は visible gain を main target に閉じて説明できず、first production candidate へ戻さない
- したがって今回の deepresearch は
  - `sentence-final monotony` を救うための理論補強
  - `reference realization policy first` の再主張
  には使わない

core research question:
- current keep-state を壊さず、日本語 blog-like naturalness の visible 改善に最もつながりやすい next redirect line は何か
- その line は
  - narrow に phase-local で扱えるか
  - current package の non-goals に反しないか
  - repeated visible failure を踏まえて continuation cost に見合うか
  を含めて判断する

evaluate these candidate lines explicitly:
1. `DISCOURSE_PARAGRAPH_SEAM_FIRST`
   - centering-like boundary checks
   - connective diversity
   - paragraph seam control
   - paragraph-to-paragraph transition coherence
2. `HEADING_DRIFT_CONTAINMENT_FIRST`
   - heading / title / lead drift containment
   - local patch scope containment
   - heading reanchor / mixed-issue containment
   - repair acceptance ではなく upstream drafting or containment design の観点
3. `NO_DEEPRESEARCH_VALUE`
   - external research を足しても redirect judgment はほぼ変わらない
   - next は local management / planning で決めるべき

strong bias:
- generic な「自然な文章を書くコツ」調の research は避ける
- English-centric style advice をそのまま持ち込まない
- Japanese discourse / Japanese editing / Japanese NLP / coherence / information flow に関係する evidence を優先する
- broad architecture rewrite を正当化しない
- route default / planning default / fixed routing table を reopen しない
- formatter-only polish / prompt-only strengthening / hidden reviser accretion に逃げない

what to research:
- paragraph seam / discourse coherence / topic continuity が、日本語で visible AI-feel にどう関与するか
- sentence-final variation より上位で効く場合、どんな symptom でそれを見分けるか
- heading / lead / title drift containment が research-backed に first concern になる条件は何か
- 日本語の paragraph breathing / transition / clause linkage / topic carry-over のうち、
  current visible failures と最も整合するものはどれか
- local patch containment が効きにくいとき、root symptom をどの layer で見るべきか

what not to do:
- `sentence-final monotony` continuation の具体実装案を長く書く
- `reference realization policy` を first production owner に戻す
- `planning default`
- `article-type fixed routing table`
- formatter policy reopen
- prompt-only winner の断定
- giant rewrite proposal
- source-of-truth update

research method:
1. まず local docs / logs を読んで current failure pattern を短く固定する
2. そのうえで external deepresearch を行う
3. source は日本語寄りを優先し、必要なら英語 technical source を補助で使う
4. 6〜10 本程度の strong evidence で止める
5. abstract theory ではなく、current visible symptom との対応関係を必ず書く

good external source types:
- Japanese linguistics / discourse / coherence / topic continuity
- Japanese writing / editorial practice about paragraph transitions and information flow
- NLP / text quality / coherence studies that are directly relevant to Japanese prose or cross-lingual discourse coherence
- reliable style guides with explicit rationale

bad external source types:
- SEO-only blog tips
- generic prompt engineering advice
- English copywriting heuristics without Japanese transfer explanation
- 「人間らしく書く 100 のコツ」型の表層 list

required output shape:
- management note 1本
- conclusion is exactly one of:
  - `DISCOURSE_PARAGRAPH_SEAM_FIRST`
  - `HEADING_DRIFT_CONTAINMENT_FIRST`
  - `NO_DEEPRESEARCH_VALUE`
- if conclusion is not `NO_DEEPRESEARCH_VALUE`:
  - explain why that line outranks the others now
  - explain why it does not reopen forbidden lines
- if conclusion is `NO_DEEPRESEARCH_VALUE`:
  - explain why existing local evidence is already sufficient

recommended output file:
- C:\tetie\notecode\docs\separate_window_targeted_deepresearch_redirect_after_sentence_final_stop_note_2026-04-17.md

stopping conditions:
- research が `sentence-final monotony` continuation proposal に寄り始めた
- `reference realization policy first` を言いたくなった
- route / planning / formatter / prompt-only に論点が逸れた
- conclusion を 2 つ以上にぼかしたくなった
- giant rewrite を前提にしないと前進が書けなくなった

最終報告で必ず示すこと:
1. 読んだ参照ルールファイル
2. 実施範囲
3. local failure pattern の短い要約
4. 外部 source の種類と数
5. candidate 3 つの比較
6. `DISCOURSE_PARAGRAPH_SEAM_FIRST / HEADING_DRIFT_CONTAINMENT_FIRST / NO_DEEPRESEARCH_VALUE` の結論
7. なぜ `sentence-final monotony` continuation ではないか
8. なぜ `reference realization policy first` ではないか
9. 次が management planning prompt か implementation prompt か
10. production code / tests / AGENTS / WORKLOG / current package docs を更新していないこと
```

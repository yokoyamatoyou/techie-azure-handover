# separate window targeted deepresearch redirect after sentence final stop note 2026-04-17

## Position

- この文書は `sentence-final pattern monotony cap + single repair` line を continuation しない前提で、next redirect line を絞るための targeted deepresearch note である
- current source-of-truth update ではない
- implementation prompt ではない
- compare execution prompt ではない
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない

## 目次

- 読んだ参照ルールファイル
- 実施範囲
- local failure pattern の短い要約
- 外部 source の種類と数
- candidate 3 つの比較
- conclusion
- なぜ `sentence-final monotony` continuation ではないか
- なぜ `reference realization policy first` ではないか
- next prompt
- non-updates

## 読んだ参照ルールファイル

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md`
- `C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\README.md`
- `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\README.md`
- `C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\PROGRESS.md`
- `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\README.md`
- `C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\PROGRESS.md`
- `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\README.md`
- `C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\PROGRESS.md`
- `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md`
- `C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md`
- `C:\tetie\WORKLOG.md`
- `C:\tetie\notecode\docs\separate_window_management_memo_deepresearch_reflection_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_priority_revision_after_deepresearch_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_compare_plan_reference_realization_policy_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_compare_result_reference_realization_policy_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_management_retriage_after_visible_smoke_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_visible_smoke_after_rollback_note_2026-04-17.md`
- `C:\tetie\notecode\docs\separate_window_instruction_window_handoff_after_deepresearch_2026-04-17.md`
- `C:\tetie\notecode\logs\sentence_final_monotony_visible_smoke_after_rollback_20260417-202435\summary.json`
- `C:\tetie\notecode\logs\sentence_final_monotony_visible_smoke_after_rollback_20260417-202435\case_v1_latest_adaptive_explanatory.txt`
- `C:\tetie\notecode\logs\sentence_final_monotony_visible_smoke_after_rollback_20260417-202435\case_v2_saved_adaptive_explanatory.txt`
- `C:\tetie\notecode\logs\sentence_final_monotony_visible_smoke_after_rollback_20260417-202435\case_v3_company_intro_guard.txt`
- `C:\tetie\notecode\logs\latest_generation_output.json`

## 実施範囲

- local docs / logs で repeated visible failure を短く固定した
- そのうえで、日本語の paragraph seam / topic continuity / heading-title-body coherence に関する targeted deepresearch を行った
- `DISCOURSE_PARAGRAPH_SEAM_FIRST`
- `HEADING_DRIFT_CONTAINMENT_FIRST`
- `NO_DEEPRESEARCH_VALUE`
  の 3 candidate を比較した
- source-of-truth update や implementation には進んでいない

## Local Failure Pattern の短い要約

- rollback 後 representative 3 case すべてで `flagged_issue_types = ["heading_reanchor", "ending_bucket_monotony"]` が出ている
- 3 case すべてで `ending_monotony_improved = true` だが、`repair_applied = false`、`scope_acceptance_path = null`、`scope_rejection_reason = flagged_scope_drift` のままだった
- explanatory 2 case は followup よりは改善したが、title / hashtags / heading wording / heading sequence drift が残り、visible main candidate には戻っていない
- company intro guard は `current-business-first keep line` に戻らず、first heading が `130年余りの歩み...` へ寄って history-first drift が visible に残った
- したがって current visible failure の first concern は「文末単調そのもの」ではなく、
  - title / lead / heading / body の anchor drift
  - heading reanchor を含む mixed issue containment failure
  に上がっている

## 外部 Source の種類と数

- total:
  - `8`
- Japanese discourse / paragraph / topic continuity:
  1. [KAKEN: 日本語の文章・談話における「段」の構造と機能](https://kaken.nii.ac.jp/ja/grant/KAKENHI-PROJECT-09834006/)
  2. [CiNii: 段落分けを用いた日本語文章における結束構造の検討](https://cir.nii.ac.jp/crid/1050845762817870848)
  3. [Walker et al.: Japanese Discourse and the Process of Centering](https://arxiv.org/abs/cmp-lg/9609006)
  4. [Oxford ORA: Information Structure in Japanese](https://ora.ox.ac.uk/objects/uuid%3A24e129aa-ed33-48bd-beec-90453a99560f/files/m74669e51df789b0835cfc1c344fc66c2)
  5. [Tsukuba Repository: 論説文の文脈展開における接続表現「しかし」と「そこで」の遠隔共起](https://tsukuba.repo.nii.ac.jp/records/33766)
- Japanese heading / lead / body relation:
  6. [日本大学: 新聞の前文（リード）の類型化に関する試論](https://www.publication.law.nihon-u.ac.jp/pdf/journalism/journalism_13/each/09.pdf)
  7. [J-GLOBAL: 新聞記事における本文と見出しの関係に関する調査](https://jglobal.jst.go.jp/detail?JGLOBAL_ID=201102205265873856)
- supplementary long-form generation research:
  8. [ACL/ArXiv: Long Text Generation by Modeling Sentence-Level and Discourse-Level Coherence](https://arxiv.org/abs/2105.08963)

### 外部 evidence から取った narrow points

- Japanese discourse の unit は単なる改行段落ではなく、話題を統括する `段` / `中心文` を持つまとまりとして捉えるほうが妥当
- 段落境界の自然さは、接続の手がかり語だけではなく、語の類縁性や topic continuity と一緒に効く
- 日本語では zero pronoun / zero topic が continuity の default であり、overt reintroduction は shift を伴いやすい
- 論説文では接続表現の組み合わせが文脈展開パターンを作る
- 見出し / リード / 本文は別々ではなく、内容を予告し接続する一つの article frame として働く
- 長文生成では sentence-level surface だけでなく discourse-level coherence が別階層の課題になる

## Candidate 3 つの比較

### 1. `DISCOURSE_PARAGRAPH_SEAM_FIRST`

- good:
  - Japanese `段` / 結束 / 接続表現研究とは整合する
  - V1 / V2 に残った一文段落の浮き、patch 感のあるつなぎ、paragraph breath の不自然さは説明できる
  - `sentence-final variation` より上位の discourse 問題として扱える
- limit:
  - current failures は paragraph seam に入る前に title / heading / first-section anchor がずれている
  - local logs の recurrent symbol は `heading_reanchor` であり、paragraph seam 単独ではない
  - V3 では paragraph-to-paragraph transition より先に first heading 自体が `current business` から `history` に飛んでいる
- rank:
  - `second`

### 2. `HEADING_DRIFT_CONTAINMENT_FIRST`

- good:
  - local evidence と最も直接に一致する
    - `heading_reanchor` が 3 case 全てで残る
    - `heading_sequence_changed = true` が 3 case 全てで残る
    - title / hashtags / first heading drift が visible main failure を作っている
  - headline / lead / body relation research と合う
    - article frame の contract が崩れると本文の可読性以前に article integrity が崩れる
  - `sentence-final monotony` より upstream の containment line として narrow に立てやすい
  - forbidden lines を reopen しなくてよい
    - planning default 変更不要
    - fixed routing table 不要
    - formatter-only polish 不要
    - prompt-only winner 不要
    - hidden reviser accretion 不要
- limit:
  - paragraph seam residual は後順位で残る
  - implementation に進むなら、repair acceptance ではなく upstream drafting / containment design の owner-local framing が必要
- rank:
  - `first`

### 3. `NO_DEEPRESEARCH_VALUE`

- good:
  - stop-and-redirect judgment 自体は local docs / logs だけでも十分に説明できる
- limit:
  - external evidence によって
    - discourse seam は有望だが second
    - heading / lead / title containment が first
    - zero-pronoun continuity を壊す overt subject policy は first-line ではない
    が clearer になった
  - つまり deepresearch は「redirect 先の順位付け」には value があった
- rank:
  - `third`

## Conclusion

- conclusion:
  - `HEADING_DRIFT_CONTAINMENT_FIRST`

### Why This Outranks The Others Now

- current visible failures は「段落のつなぎが少し不自然」よりも、
  - title が drift する
  - heading wording / sequence が drift する
  - company intro の first heading が history-first に reanchor する
  という article frame failure として出ている
- local telemetry でも `ending_monotony_improved = true` のあとに `flagged_scope_drift` で落ちており、sentence-final repair の payoff が heading/title layer で吸われている
- Japanese discourse research は paragraph seam を重要と示すが、同時に topic unit / center continuity / contextual expansion の重要性も示す
- current 3 case では、その continuity が最初に壊れている場所が paragraph seam ではなく heading/title/lead/body の anchor なので、first redirect はそこに置くほうが自然である

### Why This Does Not Reopen Forbidden Lines

- route default は `grounded generic default` のままでよい
- planning は `opt-in only` のままでよい
- `single-pass + optional single repair 1回` baseline を壊さない
- fixed routing table を足さない
- formatter-only polish を first owner にしない
- prompt-only strengthening に逃げない
- `reference realization policy` を first production owner に戻さない
- giant rewrite を前提にしない

## なぜ `sentence-final monotony` Continuation ではないか

- local 3 case で `ending_monotony_improved = true` が出ても `repair_applied = false` のまま visible main failure を消せていない
- explanatory では heading / title / hashtag drift が残り、company intro では `current-business-first keep line` が崩れた
- external research でも、長文品質の first concern は sentence-level variation だけではなく discourse-level coherence / article frame continuity だと読める
- したがって、次に continuation するならもはや `sentence-final monotony` narrow line ではなく、別 symptom を主語にした redirect line になる

## なぜ `reference realization policy first` ではないか

- current compare result が `NO_GO` であり、main target の company intro / branding visible gain を示せていない
- Japanese discourse research では zero pronoun が topic continuity の default であり、overt subject reintroduction を first-line fix にすると continuity を壊しやすい
- つまり `reference realization policy first` は
  - local compare evidence
  - Japanese discourse continuity evidence
  の両方と整合しない
- この line は separate evidence のまま keep し、first production candidate へ戻さない

## Next Prompt

- next prompt type:
  - `management planning prompt`
- exact read:
  - まだ implementation prompt ではない
  - 次は `HEADING_DRIFT_CONTAINMENT_FIRST` を narrow に phase-local 化する management planning prompt を作るべき
  - focus は
    - title / lead / heading / first-section anchor containment
    - heading reanchor / mixed-issue containment
    - repair acceptance ではなく upstream drafting or containment design
    に限定するのがよい

## Non-Updates

- production code は更新していない
- tests は更新していない
- AGENTS は更新していない
- WORKLOG は更新していない
- current planning package docs は更新していない

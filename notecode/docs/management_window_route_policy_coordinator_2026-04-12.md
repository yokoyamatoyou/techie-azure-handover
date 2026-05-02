# management window route policy coordinator 2026-04-12

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md
- C:\tetie\notecode\docs\autonomous_naturalness_repair_plan_2026-04-11.md
- C:\tetie\notecode\docs\separate_window_reframe_route_policy_2026-04-12.md
- C:\tetie\notecode\docs\separate_window_docs_revise_route_interpretation_2026-04-12.md
- C:\tetie\notecode\docs\separate_window_pipeline_planning_opt_in_gate_2026-04-12.md
- C:\tetie\notecode\docs\separate_window_validate_planning_opt_in_gate_2026-04-12.md

management window の役割:
- あなたは route policy coordinator / gatekeeper です
- 自分では実装しません
- source-of-truth と artifact を整理し、次の作業ウインドウへ narrow prompt を出す役です
- 肥大化を防ぎ、historical loop と current default を混ぜないことが最優先です

2026-04-13 current final judgment:
- overall category:
  - `DOCS_FIRST_BEFORE_MORE_CODE`
- current blank company intro best current line:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `current-business-first keep line`
- prompt-only:
  - `floor`
  - strongest baseline ではない
  - best practice とも書かない
- skeleton / planning:
  - `conditional signal only`
  - default reopen しない
  - winner 扱いしない
- do-not-retry:
  - `C:\tetie\notecode\note\natural_blog_core.py`
    - first section history clamp 仮説
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py`
    - formatter-only surface polish 仮説
  - `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
    - upstream distilled summary 単独仮説
- web compare boundary:
  - public web article compare は current-business-first pattern を支持する
  - direct GPT web compare remains unavailable
  - WEB 勝利は主張しない
- package honesty:
  - first impression は前進
  - overall naturalness / polish / repeatability は未 close
  - management estimate は `70%前後`
- next action:
  - docs lock 後に management window が再判断する
  - next coding step はいったん defer する

current source-of-truth:
- default route:
  - `grounded generic`
- planning route:
  - `opt-in only`
- article-type priors:
  - `company / announcement -> generic prior`
  - `daily -> generic or prompt-like prior until grounding safe majority`
  - `technical explain -> coverage-first prior; planning only if ordering benefit is source-backed`
- split reopen first owner candidate:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`

current evidence summary:
- company intro public web compare:
  - 現在事業 / 現在の役割から入る
  - history は 2 段目以降へ回す
  - 社名反復は lead 後に落とす
  - 短い段落で breathing を作る
  - local compare の偏りは大きくない
- company / announcement:
  - generic 側優勢
  - planning default に戻す根拠なし
- daily:
  - `input_contract -> prompt_builder -> simplify` の 3 loop でも safe majority 未達
  - current local tuning line は停止
- technical explain / case-study:
  - `ui-short-case-study-explain` は `dense_grounding_composite` で opt-in
  - `bl-explanatory-misread-metric` は `coverage_first_prior` かつ `grounded_sections_insufficient` で refusal
  - strict hard gate 問題は解消し、technical explain は coverage-first source readiness の別問題として切る
- current runtime / docs:
  - docs-first reframe は完了
  - runtime でも `planning_opt_in_v1` が入った
  - docs split closeout 後は technical explain coverage line を current package から外し、future reopen が必要な場合だけ separate line で扱う
- prompt-only / skeleton:
  - prompt-only は floor として keep するが winner にはしない
  - skeleton / planning は conditional signal only で stop し、reopen candidate に戻さない
- input-contract-only:
  - rollback / stop
  - next mainline owner 候補へ上げない

management window が保持すべき判断:
1. 以前の `planning/skeleton default` には戻さない
2. article-type fixed routing table はまだ入れない
3. `daily` の local rescue loop は再開しない
4. `planning_opt_in_v1` の composite gate keep は current baseline として固定する
5. `technical explain / explanatory article` は current package から split out of package 済みとして扱う
6. current package の next prompt は branding / company-introduction line だけを対象にし、technical explain diagnosis prompt を混ぜない
7. `prompt_builder.py` current-business-first keep line を blank company intro の best current line として扱う
8. prompt-only は floor、skeleton / planning は conditional signal only として扱う
9. direct GPT web compare unavailable を毎回残す
10. next coding step は docs lock 後に再判断する

management window の do:
- 毎回、作業ウインドウの報告を
  - current source-of-truth と矛盾しないか
  - owner が 1 file に閉じているか
  - bloat を増やしていないか
  - next step が narrower になっているか
  で判定する
- 必要なら next prompt を作る
- docs の解釈更新が必要なときだけ docs-first を優先する

management window の do not:
- code edit しない
- tests を回さない
- prompt accretion を提案しない
- multi-owner simultaneous edit を提案しない
- article-type 別の巨大 parameter table を作らない
- daily の旧 loop を future default として扱わない

次の作業ウインドウへ出すべき基本方針:
- current keep:
  - `planning_opt_in_v1` composite gate
  - company / announcement / daily refusal
  - generic default 維持
- current locked judgment:
  - blank company intro best line = `prompt_builder.py` current-business-first keep line
  - prompt-only = floor
  - skeleton / planning = conditional signal only
  - do-not-retry = `natural_blog_core.py` / `output_formatter.py` / `input_contract.py` narrow lines
- next objective:
  - technical explain / explanatory article は split out of package 済みとして keep し、current package next prompt から外す
  - docs lock 後に management re-evaluate を挟む
- next owner policy:
  - future reopen が必要な場合だけ separate line で扱い、first owner candidate は `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py` に留める

報告を受けたときの判定カテゴリ:
- `KEEP_AND_CONTINUE`
- `KEEP_BUT_REFRAME_NEXT_STEP`
- `ROLLBACK_AND_STOP_THIS_LINE`
- `DOCS_FIRST_BEFORE_MORE_CODE`

作業ウインドウへ毎回要求する最終報告:
1. touched owner file
2. hypothesis
3. 実施した変更
4. 実行した tests
5. compare/live rerun artifact
6. refusal / activation reason
7. keep / rollback / stop の判定
8. AGENTS / WORKLOG / plan docs 更新の有無

この management window の目的:
- context を減らすこと
- route policy の current decision を固定すること
- 次の 1 diff を常に narrow に保つこと
```

# separate window initial prompt 2026-04-11 prompt-only compare5

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
- C:\tetie\notecode\docs\current_mainline_tomorrow_first_prompt_2026-04-11.md
- C:\tetie\notecode\docs\stepwise_three_article_gate_2026-04-08.md
- C:\tetie\notecode\archive\pre_2026-04-02_work_records_2026-04-06\README.md
- C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\README.md
- C:\tetie\notecode\plan\visible_output_integrity_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\README.md
- C:\tetie\notecode\plan\output_surface_reduction_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\README.md
- C:\tetie\notecode\plan\orchestration_surface_reduction_2026-04-06\PROGRESS.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\README.md
- C:\tetie\notecode\plan\architecture_target_refactor_2026-04-06\PROGRESS.md

今回の separate-window mission:
- `branding / company_introduction` の visible AI feel を下げる
- UI の `speaker / audience / must_cover / source grounding` を活かしたまま、prompt accretion ではなく prompt simplification で進める
- `algorithm step-optimized` と `prompt-only persona` を常に比較しながら進める
- 比較回数は `基本 5 loops`
- 各 loop で `keep / rollback / simplify` を必ず判定する
- prompt-only が優勢でも、いきなり完全 prompt-only へ切り替えるのではなく、`minimal hybrid` を first best practice candidate として扱う

固定ルール:
- `1 loop = 1 narrow hypothesis = 1 owner scope = 1 rollback unit`
- current success path を壊さない
- archive-only / completed / frozen boundary を破らない
- prompt accretion 禁止
- module accretion 禁止
- ただし module removal / small helper replacement / line reduction は許可
- same hypothesis unchanged retry は 3 回まで

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

今回の start baseline:
- latest baseline artifact:
  - C:\tetie\notecode\logs\latest_generation_output.txt
  - C:\tetie\notecode\logs\latest_generation_output.json
  - C:\tetie\notecode\logs\latest_generation_quality_report.json
  - attempt id: `gen-f914d30e`
- previous live compare artifacts:
  - C:\tetie\notecode\logs\codex_loop1_live_compare\20260411-110405\
  - C:\tetie\notecode\logs\codex_prompt_only_compare5\20260411-112803\
- keep diff already applied:
  - C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
    - company-intro local monotony scope を `section surface proximity` 付きで受ける narrow helper
  - C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
    - company-intro の STYLE / SECTION_SHADOW を slim 化
    - UI の `speaker / audience / must_cover` は維持
    - company-intro では tone 細目の重複を減らし、shadow の `claim / voice` 重複を減らした

直近の重要観測:
- `pipeline.py` だけでは詰まり点を外しきれなかった
- `ui-short-branding-company-grounded` の repair rejection は、単なる ending monotony ではなく
  - `shadow_section_drift + ending_bucket_monotony`
  の複合だった
- つまり current blockage は
  - repair acceptance の厳しさだけではなく
  - repair prompt / generation prompt の `SECTION_SHADOW` が節 role drift を起こしやすいこと
  に寄っている

prompt-only 5回比較の最新結果:
- artifact:
  - C:\tetie\notecode\logs\codex_prompt_only_compare5\20260411-112803\summary.json
- aggregate:
  - algorithm wins = 5
  - prompt-only wins = 8
  - ties = 2
- target 2 cases summary:
  - `ui-short-branding-company-grounded`
    - prompt-only 3勝 / algorithm 1勝 / tie 1
  - `ui-short-branding-trust`
    - prompt-only 3勝 / algorithm 2勝
  - `ui-short-case-study-explain`
    - ほぼ横並び
- interpretation:
  - prompt-only は branding target で `やや優勢`
  - ただし両者とも `flat_or_repetitive` をまだ多く残す
  - したがって best practice は `full prompt-only immediate cutover` ではなく
    - `UI selection を残した minimal hybrid`
    - `algorithm を prompt-only に近づく方向へ削る`
    である

次ウインドウの first owner:
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`

next loop priority:
1. loop 1-2
   - owner: `simple_note_pipeline/prompt_builder.py`
   - objective:
     - company-intro generation prompt の `SECTION_SHADOW` をさらに弱める
     - 必要なら company-intro では generation 時の `SECTION_SHADOW` を support/fact minimum まで落とす
     - repair prompt 側でも `shadow_section_drift` を起こしやすい補助文を減らす
   - do:
     - UI の `speaker / audience / must_cover / source grounding` は keep
     - `claim / focus / voice / role / lead / paragraph rhythm` の重複指示をさらに削る
     - company-intro 限定で `SECTION_SHADOW` を disable または minimal shadow 化する案を narrow compare する
   - do not:
     - pipeline.py を同時に触らない
     - input_contract.py を同時に触らない
     - route branch を増やさない
2. loop 3-4
   - owner: `simple_note_pipeline/prompt_builder.py` のままでもよい
   - objective:
     - repair prompt の `PATCH_SCOPE + SECTION_SHADOW` 競合を減らす
     - local repair が heading role を動かさないようにする
3. loop 5
   - still blocked の場合だけ
   - owner: `simple_note_pipeline/pipeline.py`
   - objective:
     - company-intro で `shadow_section_drift` が複合で立ったとき、repair rejection reason と fail-closed 条件を narrow に再点検する
   - route reopen はしない

必須比較運用:
- 各 loop で `algorithm step-optimized` と `prompt-only persona` を比較する
- 比較回数は `基本 5 loops`
- compare target cases:
  - `ui-short-branding-company-grounded`
  - `ui-short-branding-trust`
  - guard: `ui-short-case-study-explain`
- 可能なら毎 loop で live compare artifact を保存する

prompt-only persona 方針:
- 日本語の note / ブログ記事を整える編集者として振る舞う
- 会社紹介・導入支援・事例記事を、宣伝調や説明カード調に寄せすぎず自然な読み物へ落とす
- 文末を揃えすぎない
- 段落の長さを揃えすぎない
- 必要なところだけ主語を置く
- 後半を言い換え反復にしない
- source にない実績や数値を足さない

比較で見る項目:
- rubric total
- `human_visible_ai_feel`
- soft warning count
- prompt_anchor_coverage
- must_cover_reflection_rate
- source_trace_coverage
- patch_path_used
- repair_applied
- 人が見たときの:
  - 改行の呼吸
  - 段落役割差
  - 文末の単調さ
  - 後半の言い換え反復

shared checks:
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py -q

pass condition:
- target 2 cases で algorithm が generic baseline より自然
- target 2 cases で prompt-only と同等以上、または prompt-only より business-ready / stable / grounded と説明できる
- guard regression がない
- `shadow_section_drift + ending_monotony` の複合 rejection が減る
- UI selection の `speaker / audience / must_cover` が visible surface に残る

stop condition:
- same hypothesis 3 failures
- 5 loops 実施
- prompt-only が継続優位で algorithm 側の複雑さの business justification が弱い
- multiple owner simultaneous edit なしでは前進できない

最終報告で必ず示すこと:
- 読んだ source-of-truth
- 読んだ latest logs / compare artifacts
- 各 loop の owner / hypothesis / diff / tests / live verdict
- 各 loop の `algorithm / prompt-only` 比較
- keep した変更
- rollback した変更
- 減らした prompt / shadow / branch
- まだ残る AI-like symptom
- `best practice = minimal hybrid` を keep するか
- `best practice = prompt-only` へ切るべきか
- AGENTS / WORKLOG 更新の有無
```

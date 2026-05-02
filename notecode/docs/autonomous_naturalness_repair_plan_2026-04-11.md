# autonomous naturalness repair plan 2026-04-11

更新日: 2026-04-11  
対象: `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\` package を壊さず、別ウインドウで `10` 回前後の自律ループを回して visible naturalness を改善する

## 2026-04-12 Note

- この文書は `2026-04-11` 時点の separate-window loop 計画を残す historical record です
- current source-of-truth の route default は `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md` / `TASK.md` / `PROGRESS.md` を正とする
- current default route は `grounded generic`
- planning / skeleton route は `default` ではなく `opt-in`
- よって本書の loop priority は `historical evidence` として参照し、future default として継承しない

## Objective

- `branding / company_introduction` の visible AI feel を、数値だけではなく人間の読感で改善する
- `quality warning を UI で表示する` 状態から、`内部で修正する / 通らなければ fail-closed する` 状態へ寄せる
- 対症療法の追加ではなく、`prompt 過密 / module 過密 / postprocess 過密` を疑い、削減と簡素化も同じ重みで評価する
- `prompt-only` を常設比較対象にし、必要なら最終的に algorithm 自体を `prompt-only` へ寄せる判断も許可する
- current success path
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  を維持する

## Latest Baseline

### Production-like latest log

- artifact:
  - `C:\tetie\notecode\logs\latest_generation_output.txt`
  - `C:\tetie\notecode\logs\latest_generation_output.json`
  - `C:\tetie\notecode\logs\latest_generation_quality_report.json`
- timestamp:
  - `2026-04-11 09:47:38`
- attempt id:
  - `gen-f914d30e`
- route:
  - `writer_of_record = simple_note_pipeline`
  - `route_branch = single_pass_default`
  - `section_path_used = false`
  - `style_profile_source = newalgorithm_pipeline.default_style_profile`
- visible issue:
  - company introduction として成立はしているが、改行の呼吸が均一で、文末と説明密度が still AI-like
- latest quality:
  - `ending_bucket_max_run = 9`
  - `ending_bucket_monotony_score = 0.3333`
  - `flat_zone_count = 7`
  - `sentence_ending_entropy = 1.273`
  - `paragraph_break_semantic_score = 0.7833`
  - `repair_trigger_score = 0.6`
  - `repair_applied = false`
  - `patch_path_used = false`
  - `output_guard.soft_warnings = shadow:section_drift / ending:bucket_monotony / ai:paragraph_variation / ai:ending_monotony / omission:heading_reanchor`

### 2026-04-11 live company-intro check

- case:
  - `ui-short-branding-company-grounded`
- result:
  - `runtime_reason_code = OK`
  - `short_gate = passed`
  - `rubric.total_score = 8/10`
  - `human_visible_ai_feel = flat_or_repetitive`
- interpretation:
  - 契約逸脱や grounding 崩れより、`均しすぎ / 書き分け不足 / 同型反復` が主因
  - 現状は `売り物として止めるべき warning` を success 扱いで通している

## What This Plan Changes

- 初手のゴールを `phase 05 keep diff live confirmation` ではなく、`autonomous self-repair and simplification loop` に置く
- ただし package 境界は keep し、completed / frozen / archive-only は reopen しない
- `1 loop = 1 narrow hypothesis = 1 owner scope = 1 rollback unit` を守る
- 10 回前後のループを許可するが、`同じ仮説を unchanged で再投入しない`
- 全 loop で `algorithm step-optimized` と `prompt-only` を比較し、prompt-only が継続優位なら algorithm の簡素化または prompt-only 化を検討する
- 2026-04-12 以降は、この文書の loop order を `historical execution order` として扱い、current default route の説明には使わない

## External Research Note

### Why detector score alone is insufficient

- `CT2` は AI-generated text detection が容易ではなく、回避やモデル進化で fragile だと示している
- `MAGE` も out-of-domain / unseen model 条件で detection difficulty が上がると示している
- よって、このループでは detector-like 指標を参考には使うが、`pass/fail の唯一根拠` にはしない

### Why over-complex prompts are suspect

- `Navigating Prompt Complexity` は prompt complexity が zero-shot performance に影響すると報告している
- `LIFBench` は long-context かつ複雑 instruction で instruction-following stability の評価が必要だと示している
- よって、prompt 追加で直す前に `指示の重複削減 / 長さ削減 / owner の明確化` を優先する

### Why morphology / dependency should be used

- `KWJA` は Japanese text analyzer として morphology / dependency / discourse まで一体で扱える
- 日本語の自然さ評価では sentence-endings だけでなく、`形態素多様性 / 品詞列の偏り / dependency depth / discourse relation` を見るほうがよい

### Why “same-model statistical tightness” is still useful

- `TOCSIN` は LLM-generated text が高い token cohesiveness を示しやすいと報告している
- `MAGRET` は rewriting 後も semantic/statistical alignment が残ることを利用している
- よって、本文の `均一性` を内部で測ることには意味があるが、`検出器をすり抜けること` を目標にはしない

## Research Links

- CT2:
  - [https://aclanthology.org/2023.emnlp-main.136/](https://aclanthology.org/2023.emnlp-main.136/)
- MAGE:
  - [https://aclanthology.org/2024.acl-long.3/](https://aclanthology.org/2024.acl-long.3/)
- TOCSIN:
  - [https://aclanthology.org/2024.emnlp-main.971/](https://aclanthology.org/2024.emnlp-main.971/)
- Navigating Prompt Complexity:
  - [https://aclanthology.org/2024.lrec-main.1055/](https://aclanthology.org/2024.lrec-main.1055/)
- LIFBench:
  - [https://aclanthology.org/2025.acl-long.803/](https://aclanthology.org/2025.acl-long.803/)
- KWJA:
  - [https://aclanthology.org/2023.acl-demo.52/](https://aclanthology.org/2023.acl-demo.52/)
- MAGRET:
  - [https://aclanthology.org/2025.coling-main.557/](https://aclanthology.org/2025.coling-main.557/)

## Fixed Evaluation Battery

### Case set

1. production-like latest blank prompt
   - `latest_generation_output.*`
2. target A
   - `ui-short-branding-company-grounded`
3. target B
   - `ui-short-branding-trust`
4. guard
   - `ui-short-case-study-explain`

### Required prompt modes

- `generic`
  - 現行 short gate で使う generic prompt
- `algorithm step-optimized`
  - current mainline の owner-local change を反映した route
- `prompt-only persona`
  - 日本語ブログ作成者の persona 指示を細かめに与え、algorithm 側の special handling を増やさず書かせる比較系

### Prompt-only persona baseline

- 目的:
  - 現行 algorithm の複雑さが instruction-following を落としていないか、常に比較する
- style:
  - 日本語ブログ作成者
  - 会社紹介・導入支援・事例記事を自然な note 記事へ落とす編集者
  - 文末・改行・段落呼吸・主語省略を人間的に運用する
  - 宣伝調や説明カード調を避ける
- strict rule:
  - prompt-only は `強い比較対象` として扱う
  - 10 loops すべてで target cases を比較する
  - prompt-only が 2 回以上連続で visible quality 優位なら、次 loop では `algorithm を足す` より `algorithm を減らす` ほうを優先する
  - prompt-only が安定して勝つなら、最終判断で `best practice = prompt-only` を選んでよい

### Evaluation modes

- `numeric`
  - current quality metrics
  - contract alignment
  - runtime drift
- `human-visible`
  - 改行の呼吸が均一すぎないか
  - 段落ごとの役割差があるか
  - 後半が言い換えの繰り返しになっていないか
  - `整理できます / つながります / 〜が見えてきます` 型の説明カード調が増えていないか
  - company intro として自然か、説明ロボット化していないか

### Keep metrics

- `sentence_length_cv`
- `paragraph_length_cv`
- `sentence_ending_entropy`
- `sentence_ending_fine_entropy`
- `ending_bucket_max_run`
- `ending_bucket_monotony_score`
- `nominalization_rate`
- `morphological_ngram_entropy`
- `pos_sequence_entropy`
- `dependency_depth_avg`
- `paragraph_break_semantic_score`
- `prompt_anchor_coverage`
- `must_cover_reflection_rate`
- `source_trace_coverage`

### New emphasis

- metrics 単独で合格にしない
- 最低 2 target cases で、`generic` baseline より AI feel が弱いことを必要条件にする
- 同時に `prompt-only persona` にも勝つか、少なくとも `prompt-only persona` より business-ready であることを確認する
- `quality warning は出たが本文は自然` の例外解釈をしない

## Autonomous Loop Protocol

### hard rule

- `10` loops を上限目安とする
- `3` consecutive failures in same hypothesis で停止
- each loop は owner-local
- each loop で `keep / rollback / simplify` を必ず判定する
- prompt accretion 禁止
- module accretion 禁止
- ただし `module removal / module split / small new helper replacing larger logic` は許可

### loop shape

1. baseline capture
   - latest log / latest live compare / current metrics を保存
2. choose one narrow hypothesis
   - repair acceptance
   - prompt simplification
   - postprocess simplification
   - source-aware pruning
   - route ownership handoff
3. owner-local edit
4. owner-local tests
5. shared checks
6. live compare
   - target A / target B / guard
   - compare modes: `generic / algorithm step-optimized / prompt-only persona`
7. judge
   - keep
   - rollback
   - simplify further
8. append findings
   - what improved numerically
   - what improved visibly
   - what got flatter or more robotic

## Current Default After Route Reframe

- default route:
  - `grounded generic`
- planning route:
  - `opt-in only`
- article-type priors:
  - `company / announcement -> generic prior`
  - `daily -> generic or prompt-like prior until grounding safe majority`
  - `technical explain -> coverage-first prior; planning only if ordering benefit is source-backed`
- next code owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- note:
  - 下記の loop order は current default ではなく、2026-04-11 から 2026-04-12 に得た historical evidence の並びです

## Historical Loop Record

### Loop 1-2

- owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- objective:
  - `quality warning only success` をやめ、branding/company introduction で `internal repair or fail-closed` を優先する
- do:
  - repair acceptance を `surface-preserving monotony improvement` へ寄せる
  - `patch_path_used but rejected` ケースを narrow に通す
- do not:
  - prompt を増やさない

### Loop 3-4

- owner:
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- objective:
  - style / section shadow / ledger の重複を削る
- hypothesis:
  - branding/company intro の AI feel は style 不足だけでなく、style 指示の重複と過密で flattened instruction になっている
- do:
  - duplicate guidance を削る
  - company introduction の過剰な shape 指示を減らす
  - paragraph breath と ending variation に効かない文言を削る
  - prompt-only persona に負けている指示群があれば remove 候補として扱う

### Loop 5-6

- owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
- objective:
  - prompt surface retention は keep しつつ、 contract memo を短く保つ
- hypothesis:
  - `prompt_surface_items` は必要だが、 surface memo の残し方が冗長だと writer 側で instruction competition を起こす

### Loop 7

- owner:
  - `C:\tetie\notecode\note\natural_blog_core.py`
- objective:
  - company intro defaults のさらなる prune
- entry:
  - still abstract filler / explanation-card drift が残る場合のみ

### Loop 8

- owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py`
- objective:
  - normalize が改行の均一化を増やしていないか確認する
- entry:
  - upstream 改善後も paragraph breath だけが残る場合のみ

### Loop 9-10

- owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- objective:
  - route ownership reopen の是非を narrow に確認する
- entry:
  - simplification と repair acceptance をやっても `writer_of_record = simple_note_pipeline` のまま visible AI feel が主因として残る場合のみ
- do not:
  - branch accretion
  - branding 専用分岐の積み増し
- allowed:
  - route simplification
  - dead path removal

## Simplification Heuristics

- 次を見つけたら、足す前に削る
  - 同じ意味の style 指示が `contract / prompt_builder / formatter` に重複
  - telemetry は豊富だが acceptance に使っていない
  - postprocess phase が結果をほぼ変えていない
  - company introduction だけに長い special-case prompt が積まれている
  - normalize / guard / repair が同じ defect を三重に扱っている
  - prompt-only persona のほうが自然なのに、algorithm 側がそれを上回れない

- keep ではなく remove 候補
  - branding/company introduction 向けの no-op 指示
  - output を変えない diagnostics-only branch
  - live gate で改善しなかった route branch
  - UI 向け quality warning のためだけに success を通す分岐
  - prompt-only に一貫して負ける special-case algorithm

## Pass / Stop Decision

### pass

- target 2 cases で `generic` baseline より AI 感が低い
- target 2 cases で `prompt-only persona` と比較して同等以上、または prompt-only より安全性・再現性・grounding で優位と説明できる
- guard case regression なし
- production-like latest blank prompt でも paragraph breath / ending variation が改善
- `quality warning only success` の依存が減る

### stop

- 10 loops 到達
- same hypothesis 3 failures
- broad regression
- simplified state より複雑な stateのほうが良いと説明できなくなった
- prompt を増やさないと進まないと判明した
- repeated local loops が safe majority を作れず、historical loop order を future default として維持できないと判明した

### prompt-only adoption condition

- 次を満たすなら `best practice = prompt-only` を最終候補にしてよい
  - 連続 loop 比較で prompt-only persona が target 2 cases の visible quality で優位
  - guard case でも regression がない
  - algorithm 側の複雑さを減らすほど prompt-only に近づく
  - extra modules / branches / postprocess を保つ business justification が弱い

## Output Requirement For The Separate Window

- 各 loop ごとに残す
  - touched owner
  - changed file
  - hypothesis
  - baseline metrics
  - after metrics
  - human-visible verdict
  - keep / rollback
  - complexity delta
- 最終報告では
  - `historical loops` と `current default` を分けて書く
  - `何を足したか` より `何を減らしたか`
  - `warning が減ったか`
  - `人が読んで自然か`
  - `prompt-only と比べてどうか`
  - `prompt-only を best practice と判断するか`
  - `SaaS として通せるか`
  を優先してまとめる

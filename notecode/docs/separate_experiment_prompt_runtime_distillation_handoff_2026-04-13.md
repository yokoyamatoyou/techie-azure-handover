# prompt vs runtime distillation handoff 2026-04-13

## Purpose

- current package mainline を直接進めず、external engineer 向け separate experiment / handoff material を残す
- `prompt strategy lane` と `runtime lane` を fixed 3 cases で比較し、どちらを採るべきかを evidence で決める
- `technical explain` を current package source-of-truth に戻さない

## Fixed 3 Cases

- company
  - case id: `ui-short-branding-company-grounded`
  - source:
    - `https://fixture.techie/branding/company-profile`
    - `https://fixture.techie/branding/support-policy`
- daily
  - case id: `bl-daily-learning-log-grounded`
  - source:
    - `https://fixture.techie/daily/review-note-20260310`
    - `https://fixture.techie/daily/review-note-20260311`
- explanatory
  - case id: `bl-explanatory-misread-metric`
  - source:
    - `https://fixture.techie/explanatory/adoption-signal-overview`
    - `https://fixture.techie/explanatory/helpdesk-signal-notes`

rule:

- round 0 で case / source を固定
- 途中差し替えなし

## Artifact Root

- root:
  - `C:\tetie\notecode\logs\codex_prompt_runtime_distillation_20260413\`
- combined summary:
  - `C:\tetie\notecode\logs\codex_prompt_runtime_distillation_20260413\combined_round_summary.json`

## Round Log

| round | lane | hypothesis | artifact | result |
|---|---|---|---|---|
| 0 | baseline | current generic baseline fresh rerun | `logs\codex_prompt_runtime_distillation_20260413\round0_baseline_generic\summary.json` | baseline fixed |
| 1 | prompt strategy v1 | raw prompt を 4-layer labeled prompt surface spec にする | `logs\codex_prompt_runtime_distillation_20260413\round1_prompt_lane_v1\summary.json` | drop |
| 1 | runtime v1 | `output_formatter.py` owner の schema wrapper leak strip | `logs\codex_prompt_runtime_distillation_20260413\round1_runtime_lane_v1\summary.json` | rollback / not winner |
| 2 | prompt strategy v2 | short task sentence + compressed `core_message` へ圧縮し、raw prompt の label 露出をやめる | `logs\codex_prompt_runtime_distillation_20260413\round2_prompt_lane_v2\summary.json` | keep / winner |

## What Changed Per Round

### Round 0 baseline

- current generic prompt / current runtime のまま live rerun
- fixed 3 cases を 2026-04-13 の live output にそろえた

### Round 1 prompt v1

- add:
  - raw prompt に `must_cover / grounding_facts / forbidden_additions / surface_style` の 4 層を明示
- why:
  - source の渡し方を明示化すれば自然さと coverage を両立できるか確認
- outcome:
  - prompt echo が 3 cases 全件で増えた
  - raw prompt に label を露出したまま流す案は drop

### Round 1 runtime v1

- owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py`
- hypothesis:
  - schema wrapper leak を formatter owner だけで剥がせば、daily の visible instability を narrow に下げられる
- change type:
  - in-memory patch only
  - repo code は未更新
- outcome:
  - daily wrapper leak は改善
  - ただし company / daily で `must_cover_reflection_rate` と `prompt_anchor_coverage` が落ち、rubric mean も baseline を下回った
  - naturalness winner にはならない

### Round 2 prompt v2

- remove:
  - raw prompt 内の labeled block
  - long persona line
- replace:
  - short task sentence
  - compressed `core_message`
- keep:
  - source documents
  - speaker / audience / article type / tone
- why:
  - prompt accretion ではなく、UI input surface を短い task + compressed must-cover に蒸留したほうが echo を避けられるか確認
- outcome:
  - rubric mean `8.33`
  - company `8 -> 9`
  - daily `8 -> 8` で wrapper leak なし
  - explanatory `8 -> 8`
  - source coverage は 3 cases とも `1.0` 維持

## Score Summary

### Round 0 baseline generic

- battery:
  - `short_gate_passed_count = 3/3`
  - `rubric_mean_total = 8.0`
- company:
  - `source_trace_coverage = 1.0`
  - `must_cover_reflection_rate = 0.6667`
  - `prompt_anchor_coverage = 0.2857`
  - `soft_warning_count = 5`
- daily:
  - `source_trace_coverage = 1.0`
  - `must_cover_reflection_rate = 1.0`
  - `prompt_anchor_coverage = 0.5556`
  - `soft_warning_count = 5`
- explanatory:
  - `source_trace_coverage = 1.0`
  - `must_cover_reflection_rate = 1.0`
  - `prompt_anchor_coverage = 0.5`
  - `soft_warning_count = 6`

### Round 1 prompt v1

- battery:
  - `short_gate_passed_count = 0/3`
  - `rubric_mean_total = 5.67`
- dominant failure:
  - `prompt_echo_hits`
- decision:
  - drop

### Round 1 runtime v1

- battery:
  - `short_gate_passed_count = 3/3`
  - `rubric_mean_total = 7.33`
- company:
  - `must_cover_reflection_rate = 0.3333`
  - `prompt_anchor_coverage = 0.2857`
- daily:
  - `must_cover_reflection_rate = 0.0`
  - `prompt_anchor_coverage = 0.0`
- explanatory:
  - `must_cover_reflection_rate = 0.6667`
  - `prompt_anchor_coverage = 0.375`
- decision:
  - rollback / not winner

### Round 2 prompt v2

- battery:
  - `short_gate_passed_count = 3/3`
  - `rubric_mean_total = 8.33`
- company:
  - `source_trace_coverage = 1.0`
  - `must_cover_reflection_rate = 1.0`
  - `prompt_anchor_coverage = 0.75`
  - `soft_warning_count = 7`
- daily:
  - `source_trace_coverage = 1.0`
  - `must_cover_reflection_rate = 1.0`
  - `prompt_anchor_coverage = 0.7143`
  - `soft_warning_count = 4`
- explanatory:
  - `source_trace_coverage = 1.0`
  - `must_cover_reflection_rate = 0.6667`
  - `prompt_anchor_coverage = 0.4`
  - `soft_warning_count = 6`

## Codex Reader Judgment

### Round 0 baseline generic

- company:
  - judgment: `slightly_unnatural`
  - memo: readableだが brochure 寄りで、結びが説明カード調に寄る
- daily:
  - judgment: `unnatural`
  - memo: wrapper leak が visible break
- explanatory:
  - judgment: `slightly_unnatural`
  - memo: 読めるが lead と本文が説明カード調で平板

### Round 1 prompt v1

- company:
  - judgment: `unnatural`
  - memo: labeled prompt surface が echo に出た
- daily:
  - judgment: `unnatural`
  - memo: raw prompt の spec が visible prose へにじむ
- explanatory:
  - judgment: `unnatural`
  - memo: prompt echo と構造語の露出で読み物感が落ちる

### Round 1 runtime v1

- company:
  - judgment: `slightly_unnatural`
  - memo: wrapper cleanup は無関係で、説明寄りの硬さが残る
- daily:
  - judgment: `slightly_unnatural`
  - memo: wrapper は消えたが学びの流れが薄い
- explanatory:
  - judgment: `slightly_unnatural`
  - memo: baseline より大差なし

### Round 2 prompt v2

- company:
  - judgment: `slightly_unnatural`
  - memo: まだ `この記事でわかること` が brochure 側へ寄せるが、事実連結と主語運びは最良
- daily:
  - judgment: `natural`
  - memo: 3 case 中で最も自然。学びの順番が見え、wrapper leak なし
- explanatory:
  - judgment: `slightly_unnatural`
  - memo: まだ formal card 感は残るが、無理な列挙感は baseline より弱い

## Best Artifact Per Lane

- baseline reference:
  - company: `C:\tetie\notecode\logs\codex_prompt_runtime_distillation_20260413\round0_baseline_generic\ui-short-branding-company-grounded.txt`
  - daily: `C:\tetie\notecode\logs\codex_prompt_runtime_distillation_20260413\round0_baseline_generic\bl-daily-learning-log-grounded.txt`
  - explanatory: `C:\tetie\notecode\logs\codex_prompt_runtime_distillation_20260413\round0_baseline_generic\bl-explanatory-misread-metric.txt`
- prompt strategy best:
  - company: `C:\tetie\notecode\logs\codex_prompt_runtime_distillation_20260413\round2_prompt_lane_v2\ui-short-branding-company-grounded.txt`
  - daily: `C:\tetie\notecode\logs\codex_prompt_runtime_distillation_20260413\round2_prompt_lane_v2\bl-daily-learning-log-grounded.txt`
  - explanatory: `C:\tetie\notecode\logs\codex_prompt_runtime_distillation_20260413\round2_prompt_lane_v2\bl-explanatory-misread-metric.txt`
- runtime best:
  - company: baseline kept
  - daily: `C:\tetie\notecode\logs\codex_prompt_runtime_distillation_20260413\round1_runtime_lane_v1\bl-daily-learning-log-grounded.txt`
  - explanatory: baseline kept or runtime v1 equivalent

## Winner

- stable winner:
  - `prompt strategy`
- reason:
  - 3 cases 全てで `source_trace_coverage` を落とさない
  - round 1 prompt failure を経て、round 2 で label 露出をやめた蒸留版が最良
  - runtime lane の narrow fix は daily stability には効いたが、3-case naturalness winner にはならなかった
  - v2 は add より replace / compress が効いている

## Recommended Adopt

- choose:
  - `prompt strategy spec`
- do not choose:
  - `runtime default`
  - `keep-stable`

## Adoptable Distilled Prompt Surface Spec

### Spec

- raw task:
  - 1 sentence only
  - article noun と topic を短く置く
  - labeled block syntax を raw prompt に出さない
- core_message:
  - 1 sentence only
  - must-cover 3〜4点を接続詞少なめで圧縮する
  - source にある判断軸だけを置く
- keep unchanged:
  - article_type
  - tone_profile
  - speaker_profile
  - audience_profile
  - source_documents
- avoid:
  - raw prompt に `must_cover:` などの label を露出
  - persona line の追加
  - style rule の列挙
  - source facts の block 露出

### Minimal Form

- `user_prompt_text`:
  - short task sentence
- `core_message_input`:
  - compressed must-cover sentence

### Example Shape

- company:
  - task: `医療機関と製薬企業向けに、導入初期の支え方が見える会社紹介記事。`
  - core: `権限設計・教育導線・問い合わせ整理を一体で整えること、機能追加より運用ルール・担当者導線・FAQ整備を優先すること、問い合わせを週次で手順へ戻す姿勢が伝わるようにする。`
- daily:
  - task: `振り返りメモをもとに、伝え方のズレに気づいた日の学びを残す日常記事。`
  - core: `同じ説明を二回しても伝わらなかったこと、内容より次の行動を先に示す方が理解が早かったこと、短くするだけでは変わらず期限と必要な判断を一文目に置くと返答が早くなったことをつなぐ。`
- explanatory:
  - task: `問い合わせ件数の減少を定着成功と誤解しないための解説記事。`
  - core: `問い合わせ件数だけで判断しないこと、初回設定完了率・権限設定の再編集率・FAQ閲覧後の操作完了率を合わせて見ること、管理者の肩代わりがあると依存の固定化を見誤ることを整理する。`

## Runtime Lane Close Note

- tested owner:
  - `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py`
- tested hypothesis:
  - schema wrapper leak strip
- verdict:
  - `not winner`
- why:
  - daily visible break には効く
  - ただし 3-case naturalness / must-cover / anchor 維持の winner にはならない
- optional future use:
  - stability-only cleanup として separate issue に切るなら価値はある
  - naturalness winner としては handoff しない

## External Engineer Note

- first action:
  - code diff ではなく prompt surface adoption を先に試す
- implementation shape:
  - UI input transform layer で `user_prompt_text` と `core_message_input` を v2 形式に圧縮
  - source docs はそのまま keep
  - persona block や labeled block を raw prompt に増やさない
- accept:
  - company / daily / explanatory の 3 cases で current baseline 以上
  - `source_trace_coverage` を落とさない
  - `must_cover_reflection_rate` を落とさない
  - `prompt_echo_hits = 0`
- stop:
  - raw prompt に spec label を露出しないと成立しない
  - article-type fixed table が必要になる
  - runtime multi-owner edit が前提になる

## Repo Touch Status

- code:
  - not touched
- tests:
  - not touched
- AGENTS:
  - not touched
- WORKLOG:
  - not touched
- mainline source-of-truth docs:
  - not touched
- separate experiment doc:
  - this file only

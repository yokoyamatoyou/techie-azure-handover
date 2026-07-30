# ui_prompt_distillation_autonomous_2026-04-14 TASK

この package は current package を reopen せず、7 category 全体を separate autonomous line として扱う。

## Global Rules

- current package source-of-truth を更新しない
- current package keep-state を壊さない
- AGENTS / WORKLOG は原則更新しない
- UI を変更しない
- route default を壊さない
- long persona の足し算をしない
- labeled block 露出を増やさない
- heavy editor rewrite を本線にしない
- article-type fixed routing table を安易に増やさない
- unrelated known failure は separate note に切り分ける
- failure を隠さない

## Compare Targets

- current package keep baseline
- prompt-only floor
- generic baseline if needed
- public web compare evidence
- direct GPT web compare if available

## Repo-Backed Category Gate

- fixed category set:
  - `explanatory_article`
  - `industry_analysis`
  - `branding`
  - `announcement`
  - `case_study`
  - `comparative_review`
  - `daily_story`
- repo と想定がズレる場合は repo 実装を優先する

## Phase Map

### Phase 0 Rule Read / Inventory Freeze

- Objective:
  - rule read / repo read / category inventory freeze
- Owner:
  - `C:\tetie\notecode\plan\ui_prompt_distillation_autonomous_2026-04-14\`
  - read-only repo survey
- Exit:
  - fixed category inventory
  - rollback boundary
  - compare targets
  - category evaluation matrix
- Result:
  - completed
  - repo-backed category inventory frozen
  - initial representative case set drafted

### Phase 1 UI Input Distillation Design

- Objective:
  - `task_sentence / core_message / source_digest / voice_policy / style_hints` の contract を固定する
- Owner:
  - docs only
- Exit:
  - source digest 粒度
  - company article voice policy
  - cross-category style policy
- Result:
  - completed
  - distilled contract fixed as `task_sentence / core_message / source_digest / voice_policy / style_hints`
  - company intro default voice fixed to `neutral explainer`

### Phase 2 Implementation Phase 1

- Objective:
  - UI -> distilled prompt transform を実装する
- Owner:
  - phase-local narrow owner set を docs に明記する
- Exit:
  - raw UI dump 依存を減らし、distilled prompt path が generation prompt に入る
- Result:
  - completed
  - owners:
    - `C:\tetie\notecode\note\simple_note_pipeline\ui_prompt_distillation.py`
    - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
    - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
  - brief block / source digest block / task line integrated into generation prompt

### Phase 3 Implementation Phase 2

- Objective:
  - generation-time style policy を最小制約として導入する
- Allowed scope:
  - short paragraphs
  - low company-name repetition
  - current-business-first where applicable
  - history-later where applicable
  - no label leak
  - avoid brochure/card feel
  - avoid stiff title / lead phrasing
- Exit:
  - heavy rewrite なしで visible naturalness を底上げする
- Result:
  - completed
  - company intro voice policy tightened
  - comparative title / lead anti-echo guidance added during repair iteration 1

### Phase 4 Baseline Compare

- Objective:
  - current keep baseline / prompt-only floor / generic baseline / public web pattern に対する比較を固定する
- Exit:
  - compare artifact 一式
  - direct GPT web compare の available / unavailable 記録
- Result:
  - completed
  - current keep baseline compare:
    - local baseline probe before autonomous edits
    - `C:\tetie\notecode\logs\ui_prompt_distillation_baseline_probe_20260414\`
  - prompt-only floor / generic baseline compare:
    - previous separate experiment evidence
    - `C:\tetie\notecode\docs\separate_experiment_fixed3_naturalness_final_report_2026-04-13.md`
  - public web compare evidence:
    - company article / explanatory article patterns reviewed from local research markdown
  - direct GPT web compare:
    - unavailable

### Phase 5 Category Evaluation

- Objective:
  - 各カテゴリを 3 reruns ずつ実行し、Codex 視認評価で pass / fail を出す
- Exit:
  - 7 category x 3 reruns の artifact
  - majority 判定
- Result:
  - initial attempt with source-less sweep invalidated by runtime gate
  - final source-backed 7 category x 3 reruns completed
  - artifact:
    - `C:\tetie\notecode\logs\ui_prompt_distillation_autonomous_20260414\aggregate_eval_source_backed.json`

### Phase 6 Category Repair Loop

- Objective:
  - fail category ごとに仮説を変えながら最大 7 回まで改善する
- Rule:
  - 同一 failure mode が 3 回連続で改善しない場合は stop 候補
  - 同じ修正を繰り返さない
- Exit:
  - category ごとの採用 / 不採用 / unresolved
- Result:
  - comparative only
  - iteration 1 hypothesis:
    - comparative title / lead surface を `比較軸` 直写から `選び方 / 向く条件` 起点へずらせば prompt echo を消しつつ readability を保てる
  - touched owners:
    - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
    - `C:\tetie\notecode\note\simple_note_pipeline\ui_prompt_distillation.py`
    - `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
  - artifact:
    - `C:\tetie\notecode\logs\ui_prompt_distillation_autonomous_20260414\comparative_repair_iter1.json`
  - decision:
    - adopted

### Phase 7 Final Judgment

- Objective:
  - category ごとに `stable pass / unstable pass / unresolved` を出し、line 全体を `keep / rollback / stop` で閉じる
- Exit:
  - current package keep-state untouched / changed の明記
  - AGENTS / WORKLOG 更新有無
- Result:
  - completed
  - line verdict:
    - `keep`
  - current package keep-state:
    - untouched
  - AGENTS / WORKLOG:
    - not updated

## Evaluation Rubric

- 日本語の読み物として自然か
- lead が読み物として入れるか
- title が label-like でないか
- brochure / card feel が強すぎないか
- 社名や主語の反復が不自然でないか
- paragraph breathing が自然か
- grounding / consistency を落としていないか

## Adoption Rule

- 採用条件:
  - 3 reruns の majority で pass
  - glaring failure がない
  - grounding / consistency を壊していない
  - 日本語ブログとして読める
- 不採用条件:
  - 3 reruns で揺れが大きい
  - label leak
  - brochure / card feel
  - company-name / topic repetition が不自然
  - title / lead の違和感が強い
  - must-cover / grounding を落とす

## Required Tests

- owner-local tests
- shared regression checks
- category rerun artifacts
- compare artifacts

## Logging Per Repair Iteration

各 iteration で以下を残す。

- hypothesis
- touched owners
- tests
- rerun artifact
- 採用 / 不採用理由

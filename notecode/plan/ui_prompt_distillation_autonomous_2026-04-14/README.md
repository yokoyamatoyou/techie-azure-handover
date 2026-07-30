# ui_prompt_distillation_autonomous_2026-04-14 README

この package は current package の continuation ではない。  
`C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\` を source-of-truth として維持したまま、`UI input -> distilled prompt -> single-pass generation` を本線仮説として separate autonomous line を完走する。

## Objective

- UI 内容から短い生成用 brief を構成し、日本語ブログとして自然で、カテゴリ横断で安定する generation line を設計・実装・評価する
- current package keep-state を壊さず、separate line として keep / rollback / stop を判定する
- 各カテゴリを 3 reruns ずつ回し、Codex 視認評価で stable pass / unstable pass / unresolved を分ける

## Read Order

1. `README.md`
2. `TASK.md`
3. `PROGRESS.md`
4. `ROLLBACK.md`
5. `EXECUTION_PROMPT.md`
6. `C:\tetie\notecode\docs\management_window_route_policy_coordinator_2026-04-12.md`
7. `C:\tetie\notecode\docs\separate_experiment_prompt_runtime_distillation_handoff_2026-04-13.md`
8. `C:\tetie\notecode\docs\separate_experiment_fixed3_naturalness_final_report_2026-04-13.md`
9. `C:\tetie\notecode\plan\company_intro_polish_spinout_2026-04-13\README.md`
10. `C:\tetie\notecode\plan\company_intro_polish_spinout_2026-04-13\PROGRESS.md`
11. `C:\tetie\notecode\ALGORITHM.md`
12. `C:\tetie\WORKLOG.md`

## Source Of Truth Boundary

- current package source-of-truth remains:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
- separate autonomous line source-of-truth:
  - `C:\tetie\notecode\plan\ui_prompt_distillation_autonomous_2026-04-14\`
- runtime baseline path remains:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`

## Fixed Category Inventory

repo 実装を正とし、UI route / current mainline / test sweep から freeze した fixed category set は以下とする。

1. `explanatory_article`
2. `industry_analysis`
3. `branding`
4. `announcement`
5. `case_study`
6. `comparative_review`
7. `daily_story`

補足:

- semantic subtype は category inventory ではなく subtype 扱いとする
- current repo で確認できる subtype:
  - `company_introduction`
  - `product_introduction`
  - `activity_introduction`
  - `recruit_culture`
  - `implementation_case`
  - `improvement_case`
  - `incident_case`
  - `learning_case`
- separate autonomous line の category evaluation は上記 7 category を基底に行う

## Fixed Representative Cases

Phase 5 実行時に current runtime gate を確認したところ、`simple_note_pipeline` は `source_documents` 空の contract を `INP_MISSING_REQUIRED` で止める。  
したがって category evaluation の representative case は `source_backed_only` に補正し、以下を固定した。

1. `branding`
   - case id: `ui-short-branding-company-grounded`
   - semantic subtype: `company_introduction`
2. `announcement`
   - case id: `ui-short-announcement-dense-must-cover`
3. `daily_story`
   - case id: `bl-daily-learning-log-grounded`
4. `case_study`
   - case id: `ui-short-case-study-explain`
5. `industry_analysis`
   - case id: `ui-short-industry-analysis-grounded`
   - separate line で source-backed representative を新設
6. `comparative_review`
   - case id: `ui-short-comparative-axis-lock`
7. `explanatory_article`
   - case id: `bl-explanatory-misread-metric`

artifact:

- invalid first sweep:
  - `C:\tetie\notecode\logs\ui_prompt_distillation_autonomous_20260414\aggregate_eval.json`
- source-backed fixed sweep:
  - `C:\tetie\notecode\logs\ui_prompt_distillation_autonomous_20260414\aggregate_eval_source_backed.json`
- comparative repair iteration 1:
  - `C:\tetie\notecode\logs\ui_prompt_distillation_autonomous_20260414\comparative_repair_iter1.json`

## Core Hypothesis

- 最も筋がよい本線は `UI input -> distilled prompt -> single-pass generation`
- raw UI dump をそのまま prompt にしない
- source は長い profile 丸投げではなく current-business-first の fact digest に変換する
- voice policy は限定し、企業紹介では neutral explainer default を優先する
- `self voice` を使う場合は `私たち` のみを許し、`私` は company intro で使わない
- ゼロ照応、段落呼吸、文末の単調回避、社名反復抑制は heavy editor rewrite ではなく generation-time constraint と minimal deterministic postprocess で扱う

## Distilled Prompt Contract

separate line では generation に渡す最小単位を次の 5 要素に固定する。

1. `task_sentence`
   - 1文
2. `core_message`
   - 1文
3. `source_digest`
   - 4〜6文
   - current business facts 2〜3
   - strength / trust facts 1〜2
   - history / background fact 最大 1
   - category-specific topic-context fact 最大 1
4. `voice_policy`
   - 1文
5. `style_hints`
   - 1〜2文

## Voice Policy Baseline

- `branding/company_introduction`
  - default: neutral explainer
  - explicit self-reference があり、かつ company intro の説明主体を崩さない場合だけ `私たち`
  - 社名を一人称として扱わない
- `branding` generic
  - neutral explainer 優先
  - `私たち` は明示 policy があるときだけ
- `announcement`
  - no first person default
- `case_study`
  - 実務寄りの neutral narrator
  - 一人称は必要最小限
- `comparative_review`
  - neutral explainer
- `industry_analysis`
  - neutral explainer
- `explanatory_article`
  - neutral explainer
- `daily_story`
  - 体験主体を許可
  - ただし段落頭の一人称連打は避ける

## Hard Expectations

- タイトルが管理ラベル / 説明カード / 仕様書っぽくならない
- lead が `この記事では` 型に寄りすぎない
- 段落は短めで呼吸がある
- 同じ主語や社名を過剰に繰り返さない
- 説明しすぎる硬さより、読み物としての流れを優先する
- grounding / factual consistency は落とさない

## Evidence Position

- deepresearch は evidence であり正本ではない
- public web compare は方向性の補助根拠
- direct GPT web compare は可能なら separate note に記録する
- unavailable の場合は unavailable と明記する

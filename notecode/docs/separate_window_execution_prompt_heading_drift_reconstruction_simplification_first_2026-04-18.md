# separate window execution prompt heading drift reconstruction simplification first 2026-04-18

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\EXECUTION_PROMPT.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\docs\separate_window_instruction_handoff_heading_drift_containment_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_heading_drift_containment_prompt_builder_triage_note_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_heading_drift_containment_prompt_builder_live_validation_note_2026-04-17.md
- C:\tetie\notecode\logs\heading_drift_containment_prompt_builder_live_validation_20260418-001250\summary.json
- C:\tetie\notecode\research\新しいフォルダー (2)\新しいフォルダー\deep-research-report (31).md
- C:\tetie\notecode\research\新しいフォルダー (2)\新しいフォルダー\compass_artifact_wf-d9cf85b5-5c9c-4b24-b87e-d34499c64d36_text_markdown.md
- C:\tetie\notecode\research\新しいフォルダー (2)\新しいフォルダー\新規 テキスト ドキュメント.txt
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- C:\tetie\notecode\note\tests\test_simple_note_pipeline.py

今回の依頼種別:
- reconstruction implementation prompt
- `PROMPT_BUILDER_SIMPLIFICATION_FIRST`
- source-of-truth update ではない
- wide upstream reopen prompt ではない

今回の実施範囲:
- `prompt_builder.py` owner の narrow reconstruction を 1 本だけ行う
- 目的は rule 追加ではなく、opening frame ownership の簡素化と一本化
- current success path は壊さない
- production code と owner-local tests は更新可
- AGENTS / WORKLOG / current package docs は更新しない
- `pipeline.py` / `quality_guard.py` / `input_contract.py` / `natural_blog_core.py` は初手で触らない

source-of-truth lock:
- current default route は `grounded generic default`
- planning / skeleton default reopen はしない
- blank company intro の best current line は `prompt_builder.py` current-business-first keep line
- prompt accretion 禁止
- hidden reviser accretion 禁止
- fixed routing table 追加禁止
- `natural_blog_core.py` first section history clamp 仮説は do-not-retry
- `newalgorithm_pipeline/output_formatter.py` formatter-only surface polish 仮説は do-not-retry
- `newalgorithm_pipeline/input_contract.py` upstream distilled summary only 仮説は do-not-retry

instruction-window で確認済みの WEB 根拠:
- OpenAI best practices:
  - instruction は先頭
  - instruction と context を分離
  - 何をするかを具体的に書く
  - what not to do だけでなく what to do を示す
  - https://help.openai.com/en/articles/6654000-best-practices-for-prompt-engineering
- OpenAI reasoning best practices:
  - prompt は simple and direct
  - delimiter を使う
  - zero-shot first
  - compare/eval を回す
  - https://developers.openai.com/api/docs/guides/reasoning-best-practices
  - https://developers.openai.com/api/docs/guides/evaluation-best-practices
- Anthropic prompt best practices:
  - clear and direct
  - XML/tag などで section を分ける
  - blanket defaults を targeted instructions に置き換える
  - remove over-prompting
  - https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- long context / prompt bloat:
  - relevant information は beginning / end で使われやすく middle で落ちやすい
  - prompt size を減らすと精度が上がるケースがある
  - https://aclanthology.org/2024.tacl-1.9/
  - https://arxiv.org/abs/2505.03275
- Japanese writing / company intro:
  - 見出し / リード / 本文は役割分離
  - 会社紹介や factbook は current business を先に置き、history は後段で扱う
  - https://nie.jp/newspaper/feature/
  - https://prtimes.jp/magazine/corporate/
  - https://prtimes.jp/magazine/factbook/
  - https://www.bunka.go.jp/seisaku/kokugo_nihongo/kokugo_shisaku/94336802.html

local failure pattern:
- `TITLE_LEAD_HEADING_CONTRACT_FIRST` 実装は explanatory で partial gain を返した
- ただし main target の company intro で `V3 regression`
- exact failure:
  - title が history-first に寄る
  - H2_1 が history-first に寄る
  - first section が history-first に寄る
  - repair は `patch_path_used = true` でも `scope_rejection_reason = flagged_scope_drift`
- non-target G1 では clear regression なし
- current read は `wrong-anchor consistency`
  - rule 不足というより owner 競合
  - current business ではなく history に安定してしまった

current duplication candidates to inspect first:
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py:892`
  - company-intro current-first structure line
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py:951`
  - generic title / lead / first-heading contract
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py:971`
  - generic lead -> first heading -> first section bridge line
- exact request:
  - これらを足し増ししない
  - 重複や競合を減らし、opening owner を single block に寄せる

reconstruction hypothesis:
- `title / lead / H2_1 / section_1` に同じ仕事をさせるから drift する
- 役割を分けた short frame contract に薄く戻すと explanatory の gain を壊さず、company intro の history-first reanchor を減らせる
- company intro では `current business evidence exists -> opening anchor = current_business`
- history は `H2_2+` または `section_1 後半` の背景へ回す
- ただし hardcode を増やさず、company-intro prose line を複数箇所に分散させない

allowed owner scope for first diff:
- production:
  - C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- tests:
  - C:\tetie\notecode\note\tests\test_simple_note_pipeline.py
- optional post-pass archive memo only:
  - C:\tetie\notecode\archive\heading_drift_reconstruction_2026-04-18\README.md

do not touch in first diff:
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py
- C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py
- C:\tetie\notecode\note\natural_blog_core.py
- current package docs
- AGENTS / WORKLOG

implementation rules:
1. rule を追加する前に、既存の opening-related line を棚卸しする
2. target は `more wording` ではなく `less overlapping wording`
3. role separation を短い contract に寄せる
   - title:
     - angle / promise
   - lead:
     - gist / scope
   - first heading:
     - first reader question
   - first section:
     - immediate answer
4. company intro では
   - current business / who it serves / why trusted を opening answer に寄せる
   - history は current anchor 後の背景に回す
5. `SECTION_SHADOW` company-intro omission keep は reopen しない
6. generic explanatory gain を壊さないため、explanatory longform structure line は必要最小限だけ残す
7. 新しい category-specific patch line を複数箇所へ増やさない
8. comment-out / dormant helper / unused wording を残さない

deadcode archive rule:
- runtime 上で不要になった opening-rule wording / helper / failed line は残さない
- ただし commented dead code は置かない
- useful rationale を残したい場合だけ `archive\heading_drift_reconstruction_2026-04-18\README.md` に
  - removed candidate
  - why dead
  - rollback hint
  を簡潔に記録する
- docs 群を大量に move しない
- current source-of-truth docs は archive しない
- archive step は post-pass housekeeping とし、validation fail の場合は行わない

execution order:
1. refs / local evidence / current code を読む
2. `prompt_builder.py` で opening-related line の duplication map を短く作る
3. simplest diff を 1 本だけ実装する
4. owner-local tests を更新 / 追加する
5. focused tests -> full simple-note -> quality guard を流す
6. live validation matrix を回す
7. visible text を読んで self-eval する
8. pass のときだけ optional archive memo を残す
9. fail のときは narrow rollback して停止 report

test / check order:
- focused owner-local:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -k "longform_explanatory or blank_company_intro_generation_prompt_locks_first_section_to_current_business or generation_prompt_slims_company_intro_section_shadow_block or distinguishes_title_and_lead_tone or tone_specific_lines or distilled_brief" -q
- shared simple-note:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q
- shared quality:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q

validation matrix:
- mandatory cases:
  - V1 latest adaptive explanatory baseline rerun
  - V2 saved adaptive explanatory replay
  - V3 company intro guard
  - G1 non-target branding guard
- randomness handling:
  - do not conclude from one sample only
  - preferred:
    - V3: 3 runs
    - V1: 2 runs
    - G1: 2 runs
    - V2 replay: 1 run minimum
  - if runtime / cost prevents preferred count, run at least the original 4-case single matrix and explicitly report variance coverage is insufficient
- visible success gate:
  - V3 company intro is mandatory
  - title / H2_1 / section_1 が history-first opener に戻らない
  - V1/V2 explanatory は non-worse
  - at least one explanatory run keeps the observed gain in role separation / readability
  - G1 no visible regression
- telemetry is secondary
  - metrics only では pass にしない

autonomous repair policy:
- エラーが出なければ自律的に実装 -> 検証 -> visible self-eval まで進む
- エラーや詰まりが出た場合:
  - same phase で local self-fix を優先
  - WEB search は 1 回だけ許可
  - search は blocker 解消目的に限定
  - official docs / primary sources を優先
  - search query と採用理由を最終報告で短く示す
- 1 回の WEB search と local self-fix でも解けない場合:
  - narrow rollback
  - 何が blocker か報告
  - 停止

stop conditions:
- same hypothesis で 3 回失敗
- owner scope を超えないと前進できない
- `pipeline.py` or upstream source ordering まで触らないと V3 が保てない
- shared checks regression

if simplification fails:
- code は rollback して停止
- next owner recommendation only を残す
- next candidate は
  - `newalgorithm_pipeline/pipeline.py` で upstream minimal current-first hint / source ordering triage
  - ただし今回の diff では実装しない

final report must include:
1. 読んだ参照ルールファイル
2. 今回の実施範囲
3. touched files
4. duplication map の要約
5. 実装した simplification hypothesis
6. 追加 / 更新した tests
7. 実行したコマンド
8. test / check 結果
9. live validation matrix と variance coverage
10. visible self-eval
11. WEB検索を使ったかどうか
12. deadcode archive を実施したかどうか
13. stop condition に触れず完了したか
14. AGENTS / WORKLOG / current package docs を更新していないこと
```

# deepresearch_algorithm_validation_note_2026-04-18

## Scope

- verification only
- current docs-first source-of-truth と deepresearch 4本の照合
- production code / tests / AGENTS / WORKLOG / current package docs は更新しない
- exact code owner は fixed しない

## Read Rule Files

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\README.md`
- `C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\TASK.md`
- `C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\PROGRESS.md`
- `C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\ROLLBACK.md`
- `C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\EXECUTION_PROMPT.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
- `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\README.md`
- `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\PROGRESS.md`

## Read Deepresearch Files

- `C:\tetie\notecode\PRO\deepresearch_ui_source_blog_algorithm_2026-04-18\新しいフォルダー\compass_artifact_wf-9377f670-1e65-44ff-b072-40f936d6dae8_text_markdown.md`
- `C:\tetie\notecode\PRO\deepresearch_ui_source_blog_algorithm_2026-04-18\新しいフォルダー\deep-research-report (32).md`
- `C:\tetie\notecode\PRO\deepresearch_ui_source_blog_algorithm_2026-04-18\新しいフォルダー\notecode ブログ生成アルゴリズム再設計.md`
- `C:\tetie\notecode\PRO\deepresearch_ui_source_blog_algorithm_2026-04-18\新しいフォルダー\新規 テキスト ドキュメント.txt`

## Primary Sources Checked

- 文化庁 `公用文作成の考え方（建議）`
  - 見出しは論点を端的に示し、見出しを追えば全体の内容と流れがおおよそつかめるようにする、という方針を確認
- Liu et al., `Lost in the Middle`
  - 長い入力文脈では relevant information が中盤にあると利用性能が落ちやすいことを確認
- Asai et al., `Self-RAG`
  - retrieval を常時・固定本数で混ぜると versatility や response quality を落としうることを確認
- Yan et al., `CRAG`
  - retrieval quality を別に評価し、knowledge retrieval action を切り替える設計が妥当であることを確認
- Lee et al., ACL 2021 `Enhancing Content Preservation in Text Style Transfer...`
  - style と content の分離が content preservation に重要であることを確認
- Zhang et al., `Personalized Text Generation with Contrastive Activation Steering`
  - 過去テキストでは content semantics と stylistic patterns の entanglement が問題になることを確認
- Zhao et al., `DiscoScore`
  - 汎用 BERT 系評価は coherence 改善を拾いにくく、discourse coherence 専用評価が必要であることを確認
- Okumura and Tamura, `Zero Pronoun Resolution in Japanese Discourse Based on Centering Theory`
  - 日本語では discourse-level topic / zero pronoun が重要で、sentence-local wording だけでは足りないという一般論を補強
- Broder, `On the resemblance and containment of documents`
  - 近重複を resemblance / containment として扱う基礎と、document sketch ベースの考え方を確認
- Charikar, `Similarity estimation techniques from rounding algorithms`
  - compact sketch / LSH 系の近似類似度設計が妥当であることを確認

## Current Source-Of-Truth Snapshot

- current top-level line は `ui_source_blog_contract_redesign_2026-04-18`
- Phase 01 fixed baseline:
  - contract axes は `reader_task / evidence_mode / voice_distance / opener_mode / reuse_level`
  - source role は `fact / continuity / style_memory`
  - `opening_frame` は `opener_mode` の subproblem
  - `reuse_level default = none until Phase 02`
- inherited boundary:
  - `naturalness_recovery_2026-04-07` は parked / not fixed のまま
  - same failed retry の rename reopen は禁止
  - fixed routing table / prompt accretion / hidden reviser accumulation / giant rewrite は禁止
- current runtime evidence:
  - `latest_generation_quality_report.json` では `source_grounding_reflection_ratio = 1.0` に対して `sentence_ending_entropy_low` / `vocab_repetition` / `comma_overuse` などで block
  - inference:
    - grounding と visible naturalness は別 owner / 別 artifact で扱うほうが筋が良い

## Per-File Read

### 1. compass_artifact_wf-9377f670-1e65-44ff-b072-40f936d6dae8_text_markdown.md

- core claim:
  - 5軸 contract と 3 role source を keep したまま、`opener anchor` と `lightweight planner` を分離し、single-pass writer を keep する
- good point:
  - `fact / continuity / style_memory` の責任分離が明確
  - `strict_factual` / `current_fact_required` / `grounded_preferred` / `observation_first` の fallback 境界が current docs と整合
  - `fact source` と `style_memory` を混ぜず、abstention を contract success として扱う姿勢は current stop policy と整合
  - stage-by-stage rollback 設計が最も current rules に近い
- dangerous point:
  - §6 の「文末混合方針 / 主語省略方針」を contract-level へ早く上げすぎると、Phase 02 前に style policy を source-of-truth へ固定しすぎる
  - `lightweight planner` 自体は筋が良いが、Phase 02 以前に implementation owner を誘発しやすい
- adopt candidate:
  - `opener anchor` を `opening_frame` より上位の artifact として明文化する発想
  - `abstention is success` の整理
  - `Stage A/B/C` 型の telemetry-first / rollback-first 順序

### 2. deep-research-report (32).md

- core claim:
  - `contract-first / slot-first / opener-first / single-pass-body`
- good point:
  - `theme` を evidence 代替にしない
  - `past blogs` を `continuity note` / `style sheet` へ二次表現化する
  - `opener owner` は `fact_ledger` の primary slots しか読まない、という境界が current docs と最も整合
  - file owner 早期固定を避け、artifact 単位で rollback する姿勢が良い
- dangerous point:
  - `reuse_level` を UI 契約列から外して gated runtime axis に落とす案は、Phase 01 fixed baseline と tension がある
  - `8本 / 1.2万字 / 30日` などの閾値は local evidence 未検証で、source-of-truth ではなく heuristic に留めるべき
- adopt candidate:
  - `fact_ledger`
  - `opener_anchor`
  - `continuity_note`
  - `style_sheet`
  - `validator owner is bounded check only`

### 3. notecode ブログ生成アルゴリズム再設計.md

- core claim:
  - role-separated extraction + joint opener anchoring + axis-driven single-pass writing
- good point:
  - `prompt accretion` / `source ordering` / `planning default` をやめるという主張自体は current docs と整合
  - visible body owner を `simple_note_pipeline` に残す判断は良い
- dangerous point:
  - `theme` を `Fact Source` に含めており、current docs と衝突
  - UI contract table で `Reader Task` / `Voice Distance` の意味づけが混線しており、axes coherence が崩れている
  - `pipeline.py` を早期に orchestrator owner として固定し、joint opener generation を直接実装 step にしており、current top-level line の `first code owner = not fixed` と衝突
  - citation quality が uneven で、ブログ / Medium / 二次解説が多い
  - `joint generation` 自体は design option だが、一次情報で強く裏付けられているのは「discourse coherence が必要」「入力の平坦結合は危険」までであり、joint generation の一択化は local inference を超えている
- do not adopt:
  - `theme as fact source`
  - early `pipeline.py` owner fix
  - current source-of-truth を上書きする形の direct implementation plan

### 4. 新規 テキスト ドキュメント.txt

- core claim:
  - `3 memory store + 1 opener anchor + 1 body owner`
- good point:
  - 最も current docs と近い
  - `article packet` / `fact_packet` / `opener_card` という naming は implementation-neutral で使いやすい
  - `opening surfaces only` に `opener_card` を強制し、planning は後段 opt-in に留める整理は current evidence と整合
  - `continuity reuse` と `style_memory reuse` を offline capsule 化する案は Phase 02 candidate として有力
  - `opening_history_intrusion` / `opening_surface_alignment` など opener 専用の観測指標提案は有用
- dangerous point:
  - `reuse_level` を UI 属性ではなく runtime gate 結果に落とす提案は、現行 Phase 01 baseline と緊張関係にある
  - `resolve_opener_card(contract, fact_packet, continuity_capsule)` は later lines の「opening owner は continuity を見ない」と内的 tension がある
  - `5本` や `12本 / 90日` などの threshold は heuristic としては良いが、現在は source-of-truth に上げない
- adopt candidate:
  - `fact_packet`
  - `opener_card`
  - offline `continuity_capsule`
  - offline `style_capsule`
  - opener-specific telemetry before code rollout

## Cross-File Common Conclusion

- 4本の共通結論:
  - 問題は persona 不足ではなく `UI contract / source role / self-blog reuse / opener ownership` の分離不足
  - `past blogs` を default fact source にしてはいけない
  - planning / skeleton は default winner に戻さない
  - visible body owner は single-pass writer に残す
  - opener drift は `title / lead / first heading / first section` を同じ anchor に従わせる artifact が必要
  - repair / guard accumulation より前に artifact boundary を固定すべき
- external proposals が local docs と一番整合する言い換え:
  - `UI preset -> source role assignment -> fact sufficiency -> opener anchor -> single-pass realization`

## Tension With Current Source-Of-Truth

- current source-of-truth と conflict するので未採用:
  - `theme` を fact source とすること
  - exact code owner を `pipeline.py` に早期固定すること
  - joint opener generation を唯一の fixed solution にすること
  - `reuse_level` を Phase 01 baseline から外すこと
  - reuse threshold 数値を source-of-truth に昇格させること
- current source-of-truth に tension はあるが Phase 02 candidate として keep できる:
  - `reuse_level` を docs 上は keep しつつ、runtime では gated axis として解釈すること
  - `continuity` / `style_memory` を raw retrieval ではなく summary capsule 化すること
  - opener 専用 telemetry を quality telemetry と分離すること

## Primary-Source Validation Summary

- validated:
  - heading / information ordering を reader benefit で構成する考え方
  - long context の indiscriminate accumulation が性能を落としうること
  - retrieval quality を別で評価し action を切り替える考え方
  - abstention が hallucination mitigation に有効であること
  - style と content の entanglement が personalization / style transfer の主要問題であること
  - discourse coherence 専用評価が必要であること
  - Japanese discourse では zero pronoun / topic anchoring が重要であること
  - near-duplicate detection に sketch / LSH 系が妥当であること
- not directly validated, so treat as local inference:
  - `joint opener generation` が最良の唯一解であること
  - `5本` `8本` `12本` `30日` `90日` などの具体 threshold
  - exact file mapping
  - `prompt_builder` / `pipeline.py` / `simple_note_pipeline` への最終 owner 配置

## Implementation Plausibility Read

- giant rewrite なしで作成可能そうか:
  - yes
- reasoning:
  - `current_mainline_runner.py` には contract bundle / normalization surface が既にある
  - `newalgorithm_pipeline/input_contract.py` には source grounding / prompt surface / focus bundle の基礎がある
  - `simple_note_pipeline/prompt_builder.py` には `source_digest / section_briefs / fact_anchor` に近い support-script surface が既にある
  - `simple_note_pipeline/pipeline.py` には opener drift guard / controlled realization / compact plan telemetry が既にある
  - inference:
    - redesign は completely new system ではなく、existing artifact surfaces を `contract / fact packet / opener card / gated reuse capsule` に整理し直す形で進められる
- still unresolved:
  - first code owner
  - first minimal diff
  - whether opener artifact belongs logically in `newalgorithm_pipeline` only, or straddles `simple_note_pipeline` handoff

## Judgment

- 改善アルゴリズムは現実的に作成可能そうか:
  - yes, but only as `artifact-boundary redesign`
- more precise judgment:
  - legal なのは `prompt retry` の renamed continuation ではない
  - legal なのは `contract/source/opener/reuse` artifact を docs-only で固定し、owner を narrow に後決めする line
  - `naturalness_recovery_2026-04-07` を reopen して same retry に戻るのは illegal
- now-fixed conclusion:
  - next legal step は `ui_source_blog_contract_redesign_2026-04-18` Phase 02 の docs-only continuation
  - management prompt や production implementation prompt へ進むのは、その docs phase で
    - `reuse_level`
    - `continuity/style_memory activation policy`
    - `opener artifact boundary`
    - `do-not-read for opener owner`
    を固定した後

## Recommended Legal Next Step

- type:
  - docs-only
- target:
  - `ui_source_blog_contract_redesign_2026-04-18` Phase 02 `self-blog reuse policy / minimal control axes freeze`
- what to fix there:
  - `reuse_level` を current 5-axis baseline のまま keep するか、runtime gated axis としてどう読むかを docs 上で整合させる
  - `continuity` と `style_memory` の activation policy を raw retrieval ではなく capsule policy として固定する
  - `opener owner must not read continuity/style_memory` を明文化する
  - `theme is not fact source` を強く固定する
  - threshold 数値は heuristic note に留め、 canonical baseline には入れない
- what not to do next:
  - production code edit
  - test edit
  - current parked package reopen
  - first owner early fix
  - joint opener implementation prompt 作成

## No-Change Record

- production code: not updated
- tests: not updated
- AGENTS: not updated
- WORKLOG: not updated
- `naturalness_recovery_2026-04-07` package docs: not updated
- `ui_source_blog_contract_redesign_2026-04-18` package docs: not updated

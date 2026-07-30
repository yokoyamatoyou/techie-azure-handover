# Article Brief V2 Source Shape Algorithm

Status: experimental v2, opt-in only
Owner: `app/agents/article_brief_builder.py`
Default runtime: v1 remains default unless `ROUTE_B_ARTICLE_BRIEF_ALGORITHM=v2`

## Purpose

現行 Route B v1 の `article_brief` は、claim 数が多い source で「記事設計」ではなく「claim 消化計画」へ寄りやすい。
v2 は現行 Route B アルゴリズムを置き換えず、source の形と記事目的から、本文に使う claim と未使用根拠を分ける。

## Web Research Notes

- OpenAI GPT-4.1 prompting guide: GPT-4.1 は指示へより literal に従うため、曖昧・矛盾した指示を増やさず、短い明示ルールと eval で調整する。
  URL: https://developers.openai.com/cookbook/examples/gpt4-1_prompting_guide
- OpenAI GPT-5 prompting / prompt guidance: GPT-5 系は指示追従が強く、矛盾した prompt は reasoning token を使って迷いやすい。outcome と success criteria を明確にする。
  URL: https://developers.openai.com/api/docs/guides/prompt-guidance
- OpenAI Structured Outputs: schema adherence は Structured Outputs に任せ、prompt へ schema 説明を詰め込まない。
  URL: https://developers.openai.com/api/docs/guides/structured-outputs
- OpenAI reasoning model guidance: reasoning models は大きな非構造情報から relevant information を選ぶ用途に強いが、高い reasoning effort が常に良いわけではない。
  URL: https://developers.openai.com/api/docs/guides/reasoning-best-practices
- OpenAI RAG / PDF RAG examples: generation は faithfulness と answer relevancy、retrieval は context precision と recall を見る。全情報投入ではなく、目的に合う context の精度が重要。
  URL: https://developers.openai.com/cookbook/examples/parse_pdf_docs_for_rag
- Digital.gov information architecture: 情報は findable / understandable / usable になるよう整理する。単に全部並べることは IA ではない。
  URL: https://digital.gov/topics/information-architecture
- GOV.UK content guidance: content は valid user need を満たすべきで、誰が何をしたいかを先に定義する。
  URL: https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/plan-manage-content/identify-user-needs/

## V2 Fields

v2 のときだけ `article_brief` に次を追加する。

- `source_shape`
  - `narrative`
  - `table_or_list`
  - `faq`
  - `company_profile`
  - `service_catalog`
  - `announcement_details`
  - `pdf_slide`
  - `mixed`
- `source_use_mode`
  - `representative`
  - `selective`
  - `exhaustive`
- `unassigned_claim_ids`
  - representative / selective で本文に詰め込まない claim IDs。
  - unsupported claim guard と traceability には残す。
- `voice_mode`
  - `self_authored_blogger`
  - 会社・サービス側の自己視点を保ちつつ、第三者レビューや source summary ではなく、読者に読ませるブログとして書く。
- `reader_arrival_context`
  - 読者がどんな薄い関心・距離感で記事に入ってくるか。
  - 課題解決前提の `reader friction` ではなく、見に来ただけの読者を想定する。
- `interest_hook`
  - 冒頭で何を見せると「少し読んでみよう」と思えるか。
- `reading_reward`
  - 記事を読むと、読者が何を軽く理解できるか。
- `self_authored_angle`
  - `私たち` / `当社` 側から自然に語る角度。体験・感情・成果を source 外から足すための項目ではない。
- `paragraph_function_plan`
  - 導入、引き込み、具体、背景、締めの段落役割。
  - claim 消化表ではなく、本文の読み物としての流れを決める。
- `body_length_floor_chars`
  - representative / selective でも短い一覧紹介で終えないための本文下限目安。
  - source が薄い場合は水増ししない。
- `source_derived_aside_policy`
  - 濃い fact block の後に置ける短い「ひと息」の方針。
  - 余談ではなく、source 内の事実の見方を一文で受ける。
  - 体験談・感想・顧客行動・成果・優位性・新しい価格情報は足さない。
- `rhythm_break_plan`
  - どの種類の fact block の後に緩急を作るかの短い計画。
  - 最大2文相当。本文を脱線させず、次の fact へ戻す。
- `aside_allowed_claim_ids`
  - aside が参照してよい claim_id。
  - unsupported guard / traceability の外側に逃がさない。

## Source Use Rules

- `table_or_list`, `faq`, `service_catalog`, `pdf_slide` は原則 `representative` または `selective`。
- `全部`, `全料金`, `一覧として`, `全項目`, `すべて`, `網羅` などの明示があるときだけ `exhaustive`。
- `representative` / `selective` では全 claim 消化を求めない。
- `target_length_chars` と `section_count` は claim 数ではなく、`source_shape + source_use_mode + article_goal` で決める。
- editorial bridge は候補文生成へ戻さない。必要な場合でも、非事実 claim の短い方針として扱う。

## Interest-Led Self-Authored Plan

2026-06-20 の Route B / Route V 比較では、Route V は `table_or_list` / `representative` 判定に成功したが、本文が 614-895 字に短くなり、料金項目の圧縮列挙へ寄った。
原因は、代表 claim 選択後の `source_thickness=medium` が draft writer に「簡潔に」と伝わり、読ませる段落役割が不足したため。

Genre-specific arrival and expansion contracts are maintained in `docs/GENRE_ARRIVAL_CONTRACT_MATRIX.md`. This file remains the source-shape algorithm; do not duplicate the full genre matrix here.

Route V は次の方針を追加する。

- 読者は必ずしも迷っていない。`reader_arrival_context` は「見に来ただけ」「ざっと知りたい」温度感を扱う。
- `interest_hook` は課題解決ではなく、薄い関心の読者に読む理由を作る。
- `company_service_intro` で source が `table_or_list` ではない場合は、検索結果やサムネイルからなんとなく訪問した低関心・探索中の読者を明示し、会社説明からではなく暮らし・仕事・選定場面の接点から入る。
- `table_or_list` は料金・価格表向けの source-shape hook を維持する。会社紹介向けの低関心 hook で価格表の安定条件を上書きしない。
- table/list/FAQ/service catalog は、全項目の列挙ではなく、見方・代表例・相談前の確認点へ組み立てる。
- `paragraph_function_plan` は段落ごとの役割を短く持つ。prompt へ長い persona 論を増やさない。
- `source_derived_aside_policy` は旧 `editorial_bridge_candidates` を復活させない。候補文生成ではなく、source fact の直後に置く短いリズム方針として扱う。
- aside は「余談」ではなく「source 内の事実の見方」。source 外の体験、感想、顧客事例、成果、比較優位、価格追加を禁止する。
- 自己視点は維持するが、source にない体験、感想、使用経験、成果、顧客事例は足さない。
- 既存 UI の tone / category / target_reader / article_goal は上書きしない。Route V 内部の brief 補助情報として足す。

### Company Intro Minimal Writing Contract

This is the compact contract for `company_service_intro`; do not add parallel prompt rules for the same behavior.

- Speaker: the company/service owner (`私たち` / `当社`), not a third-party reviewer.
- Reader: a low-interest visitor who may only be browsing.
- Opening: start from concrete source words, use scenes, or work/life contact points, not generic company explanation.
- Thin source: unfold source words, order, and relationships only; do not infer new outcomes, emotions, customer profiles, or comparisons.
- Expansion: make the source easier to read as a blog, but do not pad with abstract navigation phrases such as `入口`, `輪郭`, `見えやすい`, or `整理しやすい`.
- Runtime: keep the prompt surface short; use this document for rationale and QA alignment, not as a source for duplicated DraftWriter instructions.

## Guardrails Kept

- default UI は v1 のまま。
- DB と `notecode/logs` は触らない。
- Route A / writer-only fallback / old repair loop / old quality pipeline は戻さない。
- source-grounding, unsupported claim guard, self-perspective, third-party viewpoint ban, QA threshold は緩めない。
- phrase replacement や禁止語追加を主対策にしない。
- quality checker はこの owner では変更しない。
- draft writer は `voice_mode=self_authored_blogger` のときだけ短い指示を追加する。v1 や Route B UI 選択肢の解釈は変えない。

## Current Boundary: 2026-06-22 Paragraph Depth Recheck Failure Diagnosis

Latest validation and diagnosis artifacts:

```text
notecode/logs/0621/route_b_0506_v2_floor_h1_one_api_per_article_20260621_234827/
notecode/logs/0621/draft_writer_floor_actuation_runtime_diagnosis_20260622_005034/
notecode/logs/0622/route_b_0506_v2_paragraph_depth_fix_api_recheck_20260622_122514/
notecode/logs/0622/draft_writer_paragraph_depth_fix_api_recheck_failure_diagnosis_20260622_130918/
```

Current decision:

- `source_shape` drift such as `service_catalog` to `narrative` across API runs is treated as source-card / claim extraction variance, not an article-brief source-shape bug by itself.
- Do not stabilize the current floor issue by changing `detect_source_shape()`, `NON_EXHAUSTIVE_SHAPE_CLAIM_CAPS`, claim allocation, QA thresholds, or repair acceptance.
- In representative/selective modes, assigned claims are the writer's depth anchors. Unassigned claims remain trace/guard material and must not be enumerated to fill length.
- `company_service_intro` may carry a 1400-char floor even when the detected source shape is `narrative`; DraftWriter must still make assigned claims deep enough instead of relying on source-shape-specific wording.
- H1 contract is currently satisfied in completed post-fix validation: all 4 completed article types reached `h1_count=1`, with `missing_h1=false`; 2 article types stopped before DraftWriter on API infra errors.
- Body floor is still unresolved: 0/4 completed post-fix article types reached final floor; all 4 emitted `body_length_below_floor=true`.
- The floor miss starts at DraftWriter output in most cases. Deterministic editor/postprocessor stages can widen the gap, but they do not create a growth path.
- The implemented paragraph-depth fix was transmitted to DraftWriter, but did not improve floor. Latest diagnosis indicates paragraph count is followed more reliably than chars-per-anchor depth.
- Known current prompt/algorithm conflicts:
  - `rhythm_break_plan` / source-derived aside instruction can ask for reader-guidance sentences that `reader_meta_sentence.py` later removes.
  - `article_brief.style_edit_policy` sentence-count guidance can compete with chars-per-anchor depth guidance.
  - `target_length_chars == body_length_floor_chars` can remove the buffer between desired length and the QA floor.
- `draft_writer_floor_actuation_count_based_depth_redesign` is implemented and passed the no-API gate (`39 passed`, `py_compile` pass, `inspect_bloat` pass / `failures=[]`).
- Count-based API isolation recheck artifact: `notecode/logs/0622/route_b_0506_v2_count_based_floor_actuation_api_isolation_recheck_20260622_140222/`.
- Count-based API isolation recheck was partial positive but incomplete: completed 2/6 article types; floor reached 2/2 completed; H1 reached 2/2 completed; quality pass 1/2 completed; 4 article types failed before full evaluation due artifact packaging or API infra errors.
- Failure diagnosis found likely long artifact path / validation packaging issues plus API 520 infra failures.
- Short-path validation packaging recheck artifact: `notecode/logs/0622/cbsp_1429/`.
- Short-path recheck completed enough to evaluate the count-based actuation: packaging issue fixed, but body floor remains unresolved (`1/5` completed types reached final floor, `5/5` reached H1, `0/5` quality passed, `4/5` had `body_length_below_floor`). This is directionally better than baseline/paragraph-depth on gap size, but not user-test ready.
- Floor-gap diagnosis artifact: `notecode/logs/0622/cbsp_1429/floor_gap_diagnosis.md`.
- Floor-gap diagnosis found that the count-based paragraph target is being followed, but it is not enough to satisfy final floor because paragraph depth and final-floor buffer remain too small.
- `draft_writer_floor_actuation_depth_budget_contract_impl` is implemented with no-API gate pass (`39 passed`, `py_compile` pass, `inspect_bloat` pass / `failures=[]`). DraftWriter now treats paragraph count as only one part of a bounded source-backed depth budget from floor/target chars, section count, assigned claims, and selected excerpts.
- Depth-budget one-article API smoke artifact: `notecode/logs/0622/dbsm_1550/`. The `market_explanation` smoke passed final floor/H1/quality, but unassigned-claim enumeration and sentence-fragment issues require diagnosis before full API isolation recheck.
- Next owner: `draft_writer_depth_budget_contract_smoke_failure_diagnosis`.

Do not reopen older Route A, writer-only, raw `source_documents`, broad prompt tuning, source-shape/claim-allocation fixes, QA threshold changes, repair acceptance changes, reader-meta/style-postprocessor changes, or H1 changes for this owner.

## Route V Selected Source Excerpt Handoff

2026-06-20 addition, experimental Route V only.

Problem:

- Passing only `article_knowledge_pack.confirmed_facts` to the draft writer can make the source feel thinner than the original material.
- The writer needs source texture: nearby wording, source order, headings, and how a fact appears in context.
- Passing raw full `source_documents` is still forbidden. It can collide with the structured pipeline contract and reintroduce unsupported fact drift.

Rule:

- Route V may pass `selected_source_excerpts` to `draft_writer`.
- v1 default payload remains `article_brief + knowledge_pack` only.
- `selected_source_excerpts` are short, bounded excerpts selected from source packets around assigned Route V claim IDs.
- Claims remain the fact ledger for allocation and QA. Excerpts are writer context and source texture, not a request to consume every source item.
- In representative/selective modes, excerpts are sampled from assigned claims only. Unassigned claims remain in `unassigned_claim_ids` and the knowledge pack for guard/trace use.
- Excerpts must never be used to restore Route A, writer-only fallback, old repair loop, or old quality pipeline.

Limits:

- No DB changes.
- No `notecode/logs` deletion.
- No raw full source pass.
- Keep excerpt count and total characters bounded.
- Do not relax third-party viewpoint ban, source-grounding, or QA threshold.

## Historical 2026-06-20 Follow-up: Opening Editor Conflict Confirmed

The "原因は…source_thickness=mediumがdraft writerに「簡潔に」と伝わり…" note above was an early hypothesis. A read-only diagnosis on 2026-06-20 found the dominant cause is elsewhere and is not specific to claim selection or `source_thickness`.

`app/services/opening_editor.py` (shared by Route B v1 and Route V, not changed by this design) unconditionally overwrites the draft's first body paragraph with one of 4 hardcoded template sentences, without reading `voice_mode`, `paragraph_function_plan`, or any claim/fact signal. On two independent Route V samples, DraftWriter wrote a detailed, source-grounded opening paragraph and `opening_editor` deleted it, substituting a generic fallback sentence that is not caught by `reader_meta_sentence.py` or `japanese_quality_checker.py`.

This is a direct conflict between this document's `paragraph_function_plan` ("導入: 見に来ただけの読者が読み続ける理由を、source-backedな具体から作る。") and `opening_editor`'s content-blind overwrite. Full evidence and a proposed minimal fix (a content-aware skip guard in `opening_editor.py`, not a change to this document's fields):

```text
notecode/logs/route_v_opening_editor_overwrite_diagnosis_20260620/diagnosis.md
notecode/logs/route_v_opening_editor_overwrite_diagnosis_20260620/decision_before_edit.md
```

### Slice Audit: Route V Opening Guard

2026-06-20 implementation slice decision:

- Keep Route B v1 behavior unchanged. The shared opening editor still runs as before unless Route V fields are present.
- Route V may preserve the draft's first body paragraph only when all Route V signals are present (`voice_mode=self_authored_blogger`, `paragraph_function_plan`, `source_shape`, `source_use_mode`) and the paragraph has source-backed specificity.
- Source-backed specificity is intentionally small: numeric fact markers with units, or short feature terms from assigned claims. It is not a broad quality heuristic and does not change QA thresholds.
- Generic or meta openings remain eligible for existing opening editor replacement even in Route V.
- This slice only removes the confirmed stage conflict. Drafts that are already under `body_length_floor_chars` remain a separate owner for article brief / draft writer evaluation.

## Rollback

既存 snapshot:

```text
notecode\archive\pre_article_brief_source_shape_migration_20260620_110900
```

戻す場合は、snapshot の同一 relative path から対象ファイルをコピーし、v2 env flag を unset する。

# opening frame pipeline control surface triage note 2026-04-18

## 参照ルールファイル

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\README.md`
- `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\TASK.md`
- `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\PROGRESS.md`
- `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\ROLLBACK.md`
- `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\EXECUTION_PROMPT.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md`
- `C:\tetie\notecode\docs\opening_frame_redesign_research_synthesis_note_2026-04-18.md`
- `C:\tetie\notecode\docs\opening_frame_minimal_control_comparison_note_2026-04-18.md`
- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py`
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `C:\tetie\notecode\ALGORITHM.md`
- `C:\tetie\WORKLOG.md`

## 今回の実施範囲

- `PIPELINE_OPENING_FRAME_CONTROL_SURFACE` winner を `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py` owner 1 file の legal な next hypothesis に落とせるか docs-only で triage した。
- code diff は作らない。
- production code / tests / AGENTS / WORKLOG / current package docs / redesign package docs は編集しない。

## winner を pipeline candidate として読んだ理由

- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py` は `generate()` の handoff 前で contract を保持しており、`super().generate(contract)` に入る前に upstream state を 1 箇所で確定できる。
- 同 file には discourse section から `compact_plan` を橋渡しする `_build_compact_plan_bridge_from_discourse_sections()` が既にあり、prompt wording ではなく plan state を downstream に渡す面がある。
- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py` は company intro の通常生成 prompt で `SECTION_SHADOW` を増やさず、既存の `compact_plan` を `STRUCTURE` / `SEMANTIC_LEDGER` に載せる。
- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py` の opener drift fail-closed は `_shadow_spec_inputs.main_focus` と first compact-plan entry の `heading / claim` を使って visible drift を見ている。
- したがって first code step を `pipeline.py` 1 owner に閉じても、downstream consumer を新設せずに opening-frame state を handoff できる。

## code surface read

- `pipeline.py` 側の old retry で実体だった `source ordering` helper は `_reorder_company_intro_current_first_sources()` に閉じており、現時点の main path では handoff state owner になっていない。
- `prompt_builder.py` 側の company intro current-first line は `_preflight_company_intro_generation_blocks()` と writer brief に既に厚く入り、ここへ first step で戻ると rename retry に見えやすい。
- `simple_note_pipeline/pipeline.py` 側の opener guard は downstream fail-closed と acceptance owner であり、primary owner ではなく post-hoc detector に寄る。
- `input_contract.py` には `_shadow_spec_inputs` の既存 schema があり、`main_focus / support_points / source_fact_pool` を pipeline 側で再整形しても consumer 追加は不要である。

## conclusion

`LEGAL_NEXT_OWNER`

## exact owner

- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`

## exact narrow hypothesis

- `newalgorithm_pipeline/pipeline.py` が company introduction の opening frame を prompt wording ではなく upstream handoff state として固定し、existing downstream surface に
  - current-business-first focus
  - first heading role
  - first claim
  の 3 点だけを流せば、`title / lead / first heading / first section` の role separation を narrow にそろえつつ、old `source ordering / core_message hint` retry や `prompt_builder` wording retry に戻らず opener drift を減らせる。

## pipeline owner が持つ state

- `company introduction` かつ `branding` のときだけ有効な opening-frame state。
- source 全体の並べ替えではなく、「1節目を何で始めるか」に閉じた current-business-first opener state。
- downstream へは existing contract / compact-plan surface にだけ流し、新しい prompt-builder consumer や downstream guard owner は増やさない。

## max 3 control fields

1. `opening_frame_focus`
   - existing downstream mapping: `contract["_shadow_spec_inputs"]["main_focus"]`
   - role: title / lead / first section が共有する current-business-first focus phrase
2. `opening_frame_heading`
   - existing downstream mapping: `compact_plan[0]["heading"]`
   - role: first heading の責務を 1 本に固定する
3. `opening_frame_claim`
   - existing downstream mapping: `compact_plan[0]["claim"]`
   - role: 1節目本文が最初に言い切る source-backed current-business sentence

補足:

- `anchor` は独立 control field にしない。必要なら `opening_frame_focus` または `opening_frame_heading` から pipeline 内で導出する。
- `support / fact` は `_shadow_spec_inputs` の既存 pool から first slot を再利用し、new primary field に昇格しない。

## exact non-goals

- `prompt_builder.py` simplification-first wording retry を再開しない。
- `pipeline.py` current-first source ordering / hint triage を再開しない。
- `pipeline.py` core_message current-first hint retry を再開しない。
- `prompt_builder.py` frame card first にしない。
- tiny deterministic guard を first owner にしない。
- `SECTION_SHADOW` reopen first に戻さない。
- planning / skeleton default reopen に戻さない。
- source document 全体の再並べ替え branch を主役にしない。
- prompt accretion continuation をしない。
- multiple owner implementation planning を始めない。

## old retry との切り分け

### source reorder heuristic retry との違い

- old retry は source band / hint ordering を upstream 入力全体へ触る line だった。
- 今回の line は source 全体の順番ではなく、first opener slot だけを handoff state として確定する line である。
- helper の再有効化や rename ではなく、`compact_plan[0]` と `_shadow_spec_inputs.main_focus` に閉じた control surface である。

### core_message hint retry との違い

- old retry は `topic_statement / core_message` の wording pressure を強める line に近かった。
- 今回の line は prose hint を増やさず、first heading / first claim / focus の structural state だけを持つ。
- `core_message` の文字列差し込みは primary mechanism にしない。

### prompt_builder frame card first との違い

- first code step で `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py` を触らない。
- downstream では既存の `STRUCTURE / SEMANTIC_LEDGER / opener drift guard` consumer をそのまま使う。
- よって prompt wording 面への rename retry ではない。

### tiny deterministic guard first との違い

- tiny guard は fail-closed detector であり、opening owner ではない。
- 今回の line は generation 前の upstream handoff state を固定する line で、detector-first ではない。
- downstream guard は secondary confirmation に留まり、primary owner へ昇格しない。

### rollback-first clarity

- rollback unit は `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py` 1 file に閉じる。
- new field consumer を追加しないので rollback は contract mutation / compact-plan bridge の narrow diff 単位にできる。

### prompt accretion continuation に見えないか

- prompt_builder block を増やす line ではない。
- existing downstream format に入る state を pipeline 側で薄く固定するだけなので、prompt accretion continuation ではない。

## exact next prompt type

- `implementation prompt`

## implementation prompt へ渡すべき最小指示

- owner は `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py` 1 file に固定する。
- first step は company intro opener 用の minimal control surface を existing `compact_plan` と `_shadow_spec_inputs` に載せることだけに閉じる。
- `prompt_builder.py` / `simple_note_pipeline/pipeline.py` / tests の同時 edit は initial step に含めない。

## WEB検索を使ったかどうか

- not used
- local docs / local code / local tests 断片の読取りだけを使った

## non-updates

- production code は更新していない。
- tests は更新していない。
- AGENTS は更新していない。
- WORKLOG は更新していない。
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\` docs は更新していない。
- `C:\tetie\notecode\plan\opening_frame_redesign_2026-04-18\` docs は更新していない。

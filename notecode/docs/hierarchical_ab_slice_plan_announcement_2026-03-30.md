# hierarchical A/B slice plan announcement 2026-03-30

更新日: 2026-03-29  
対象: `C:\tetie\notecode`  
用途: 2026-03-30 に announcement dense must_cover route で limited A/B を設計するための最小計画

## 目次
- 判定
- 対象 route
- 目的
- 変更境界
- 追加する最小要素
- success 条件
- rollback 条件
- 明日の進め方

## 判定

- external review の最終判定は `限定A/Bで試すべき`
- 直近の current residual は grammar 崩壊よりも `must_cover reflection` と `semantic progression` に寄っている
- ただし section 動的生成は coherence / コスト / 実装複雑性の不利があるため、全面移行は不採用

## 対象 route

- first slice:
  - `ui-short-announcement-dense-must-cover`
- secondary check only:
  - `ui-short-explanatory-default`
  - `ui-short-branding-company-grounded`

## 目的

- 現行 single-pass と比較して、dense announcement の `must_cover_reflection_rate` を改善する
- 変更点 / 対象と時期 / 必要な行動 の取りこぼしを減らす
- grammar / legal / prompt echo / rollback 性を悪化させない

## 変更境界

### 触ってよい owner

- `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\discourse_planner.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\section_generator.py`

### 触らないもの

- `C:\tetie\notecode\note\note_writer_app.py`
- `C:\tetie\notecode\note\current_mainline_runner.py`
- legacy route
- `human_resonance*`
- `vnext`
- `simple_note_refactor_2026-03-22` plan package

### 据え置く stage

- contract resolve
- source digest
- semantic dedupe
- editor guard
- quality pass
- legal postcheck
- output guard
- result schema

## 追加する最小要素

- 追加は 1 つを中心にする
  - `remaining_must_cover_before`
  - `remaining_must_cover_after`
- section 単位で持つ ledger の最小情報
  - current section heading
  - current section intent
  - assigned fact_slot
  - assigned source_grounding_items
  - previous_summary
  - recent_summaries
  - remaining_must_cover_before
  - remaining_must_cover_after

### 守るべき制約

- 全文を毎 section prompt に渡さない
- prompt accretion をしない
- module accretion をしない
- A/B flag を切れば現行 path へ即 rollback できるようにする

## success 条件

- `ui-short-announcement-dense-must-cover` の `must_cover_reflection_rate` が現行 accepted baseline より改善
- human rubric が改善、または同等以上
- `prompt_anchor_score` が悪化しない
- `sentence_integrity_warning_count=0` を維持
- `legal_issue_count=0` を維持
- prompt echo を悪化させない

## rollback 条件

- coherence が目視で悪化
- section 間のつながりが切れる
- grammar / legal / prompt echo が悪化
- latency / token cost が受け入れ難い
- rollback flag で現行 path に戻せない

## 明日の進め方

1. current success path と対象 route の baseline artifact を固定する
2. `remaining_must_cover ledger` の shape だけを文書化する
3. A/B flag の置き場所を決める
4. file-level implementation plan を 1 回で終わる粒度に分ける
5. user へ plan を返し、go が出たら次 turn で実装する

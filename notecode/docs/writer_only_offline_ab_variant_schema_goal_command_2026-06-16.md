# Writer-only Offline AB Variant Schema Goal Command 2026-06-16

対象: `writer_only_new_algorithm_offline_ab_variant_schema_owner`

このファイルは、次の作業ウインドウでそのまま貼って長時間自走するためのゴールコマンドです。前 owner が作成した no-API harness を踏まえ、safe-expansion B variant を product code へ入れる前に、`brief` / `evaluator` / `manual_review` のどこへ何を置くかを final schema として決めます。

## Goal Objective

```text
現行 writer-only を通常UIの本線として保持したまま、safe-expansion B variant の final schema を no-API / 通常UI非接続で確定し、A/B/C/D fact layer、thin-source length guard、日本語文体guard、prohibited claim guard を brief/evaluator/manual_review のどこへ置くかを決め、次の最小実装 owner が迷わず走れる実装指示を作る。
```

## ゴールコマンド

```text
あなたは TECHIE / notecode / コトメイクの `writer_only_new_algorithm_offline_ab_variant_schema_owner` です。

目的:
`C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\` の fixture / no-API harness 成果物を使い、safe-expansion B variant の final schema を決める。本文生成、live API、通常UI接続、Route 0506 / Route A / repair loop / quality pipeline 復帰は行わない。

参照ルール:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\ALGORITHM.md
4. C:\tetie\notecode\docs\writer_only_safe_expansion_policy_proposal_2026-06-16.md
5. C:\tetie\notecode\docs\writer_only_new_algorithm_ab_test_plan_2026-06-16.md
6. C:\tetie\notecode\docs\writer_only_new_algorithm_deep_route_plan_2026-06-16.md
7. C:\tetie\notecode\docs\writer_only_offline_ab_fixture_goal_command_2026-06-16.md
8. C:\tetie\notecode\docs\writer_only_offline_ab_no_api_harness_goal_command_2026-06-16.md
9. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\fixture_index.json
10. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\safe_expansion_policy.json
11. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\review_checklist.md
12. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\no_api_static_scan.json
13. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\no_api_case_comparison.json
14. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\no_api_harness_summary.md
15. C:\tetie\notecode\note\writer_only_brief.py
16. C:\tetie\notecode\note\writer_only_evaluator.py
17. C:\tetie\notecode\note\writer_only_openai_adapter.py
18. C:\tetie\notecode\note\writer_only_source_bundle.py
19. C:\tetie\notecode\note\tests\test_writer_only_generation.py

実施範囲:
- 既存 artifact root に schema owner 成果物を追加する:
  C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\
- 追加する成果物:
  - `variant_schema_plan.md`
  - `safe_expansion_schema_final.json`
  - `evaluator_guard_schema.json`
  - `manual_review_gate_schema.md`
  - `implementation_scope_decision.md`
  - `implementation_owner_prompt.md`
- product code は変更しない。
- live API は呼ばない。
- B variant の本文生成はしない。

決めること:
1. `safe_expansion_policy` を `brief` にどう入れるか。
   - 推奨候補: `brief["writer_contract"]["safe_expansion"]`
   - 追加候補: `brief["expansion_policy"]` に structured object
   - 禁止: fixed prompt へ長文追加
2. A/B/C/D fact layer を schema としてどう表すか。
   - A source fact
   - B verified external context
   - C editorial bridge
   - D prohibited claim
3. `verified_external_context` は今回 product runtime へ入れるか、future ownerへ送るか。
   - 推奨: 今回は schema だけ。runtime取得や外部検索は入れない。
4. `thin source length guard` をどう扱うか。
   - 700-1200字を B review expectation に置くか
   - `article_body_contract.min_chars` を product codeで変えるか
   - `do_not_pad=true` をどう維持するか
5. evaluator に入れるものと manual review に残すものを分ける。
   - evaluator候補: prohibited claim guard, visible media name guard, url coverage, length bounds
   - manual候補: 比喩の自然さ、体言止めの効き方、主語省略の自然さ、読者との距離
6. 日本語文体 guard の扱い。
   - fixed promptへ入れない
   - evaluatorでは warning まで
   - promotion decision で manual review 必須
7. 次の実装 owner の最小範囲。
   - product codeへ入れるなら `writer_only_brief.py` と `writer_only_evaluator.py` 中心
   - `writer_only_openai_adapter.py` の fixed instructions は原則変更しない。変更する場合も1文まで

禁止:
- live APIを呼ばない。
- product codeを変更しない。
- B variant の本文を生成しない。
- 通常UIから B variant を呼ばない。
- latest visible outputへB variantを投影しない。
- Route 0506 / Route A / repair loop / quality pipeline を戻さない。
- raw full source pass をしない。
- fixed `WRITER_INSTRUCTIONS` を長文化しない。
- persona table を増やさない。
- external orchestration framework を導入しない。

slice plan:
Slice 0: 参照docと no-API harness artifact を読む。
Self-test: fixture 5件、static scan、case comparison、summary が存在すること。

Slice 1: final schema の配置案を比較する。
Self-test: `brief`, `evaluator`, `manual_review` の3分類があること。

Slice 2: `safe_expansion_schema_final.json` を作る。
Self-test: A/B/C/D fact layer、thin-source expectation、do_not_pad、no external context runtime が明記されていること。

Slice 3: `evaluator_guard_schema.json` を作る。
Self-test: prohibited claim guard と manual warning の境界が混ざっていないこと。

Slice 4: `manual_review_gate_schema.md` を作る。
Self-test: fact grounding / blog naturalness / information gain / Japanese readability / SEO usefulness / risk の6軸があり、日本語文体 guard が入っていること。

Slice 5: `implementation_scope_decision.md` を作る。
Self-test: 変更候補ファイル、変更しないファイル、テスト候補、API禁止が明記されていること。

Slice 6: `implementation_owner_prompt.md` を作る。
Self-test: 次ownerが copy-paste で `writer_only_brief.py` / `writer_only_evaluator.py` の最小実装へ進めること。live API禁止、通常UI非接続、3回停止が入っていること。

Slice 7: no-API validation を行う。
Self-test: JSON parse、Markdown readback、path existence。必要なら current writer-only modules py_compile。api_send_count は0。

Slice 8: WORKLOG を必要最小限で更新する。
Self-test: WORKLOG読み戻し、route flags確認、artifact summary確認。

停止条件:
- 同じエラーが3回連続。
- safe-expansion を fixed prompt へ長文追加しないと成立しない。
- source groundingを落とさないと膨らませられない。
- evaluator と manual review の境界が分けられない。
- product codeを触らないと schema 判断ができない。
- live APIが必要になった。

ファイル不足時:
- D:\Rescue_Yokoyama\C_root\tetie を read-only で確認してよい。
- コピーは「C側に存在しない不足分だけ」に限定する。
- 既存ファイルの上書きは禁止。

完了報告フォーマット:
参照ルールファイル:
今回の実施範囲:
decision: schema_ready | needs_next_owner | blocked | reject
artifact_root:
baseline_kept: true
schema_files:
brief_schema_decision:
evaluator_schema_decision:
manual_review_schema_decision:
implementation_scope:
tests:
api_send_count: 0
route_0506_restored: false
route_a_restored: false
repair_restored: false
quality_pipeline_restored: false
raw_full_source_passed: false
prompt_bloat: none | minor | found
module_bloat: none | minor | found
next_one_owner:
AGENTS_update_needed:
WORKLOG_update_needed:
```

## Expected Next Owner

通常は次の owner を推奨する。

```text
writer_only_safe_expansion_brief_evaluator_min_impl_owner
```

目的:

- schema owner が決めた範囲だけを product code へ最小実装する。
- 変更候補は `writer_only_brief.py`, `writer_only_evaluator.py`, `note\tests\test_writer_only_generation.py` 中心。
- `writer_only_openai_adapter.py` の fixed instructions は原則変更しない。
- live API はまだ呼ばない。

ただし、schema段階で product codeへ入れる価値が弱いと判断した場合は次候補:

```text
writer_only_new_algorithm_revise_schema_or_reject_owner
```

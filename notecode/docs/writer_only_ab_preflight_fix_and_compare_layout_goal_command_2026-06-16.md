# Writer-only AB Preflight Fix And Compare Layout Goal Command 2026-06-16

対象: `writer_only_ab_preflight_fix_and_compare_layout_owner`

このファイルは、次の作業ウインドウでそのまま貼って長時間自走するための preflight / artifact-layout ゴールコマンドです。次回以降のABテストを「各記事ごとにA/BのMarkdownを同一ディレクトリで比較しやすい状態」にする前に、未完了部分を潰します。

## Goal Objective

```text
承認済みlive ABで見つかった未完了部分を no-API で直す。具体的には、pytest実行不能の原因を切り分けて可能なら復旧し、B variantのbriefをproduction-shaped source_bundle付きに揃え、fixtureのvisible media name混入を修正し、prohibited claim guardのfalse positive/true positiveを切り分ける。そのうえで既存live AB artifactを、各記事ごとにA/B/B候補のmdを1つのcompareディレクトリへ並べる形式へ正規化する。OpenAI API本文生成、通常UI接続、latest visible output反映、Route 0506 / Route A / repair / quality pipeline復帰は行わない。
```

## ゴールコマンド

```text
あなたは TECHIE / notecode / コトメイクの `writer_only_ab_preflight_fix_and_compare_layout_owner` です。

目的:
次のAB検証を比較しやすく、かつ昇格判断できる状態にするため、live AB後に残った未完了部分を先に直す。最終状態は、各記事ケースごとにA/B/B候補のMarkdownが同じディレクトリに並び、reviewerが1画面で読み比べられること。

参照ルール:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\ALGORITHM.md
4. C:\tetie\notecode\WORKLOG.md
5. C:\tetie\notecode\docs\writer_only_new_algorithm_approved_live_ab_quality_first_goal_command_2026-06-16.md
6. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\live_ab_quality_first_20260616_200725\comparison_summary.json
7. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\live_ab_quality_first_20260616_200725\manual_quality_review.md
8. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\live_ab_quality_first_20260616_200725\api_send_ledger.jsonl
9. C:\tetie\notecode\note\writer_only_brief.py
10. C:\tetie\notecode\note\writer_only_evaluator.py
11. C:\tetie\notecode\note\tests\test_writer_only_generation.py

現時点の未完了部分:
1. pytest が環境側 import 破損で実行できていない。
2. B1/B2 live入力が `variant_b/brief_safe_expansion.json` 由来で、production evaluator が期待する `source_bundle` shape を満たしていない。
3. `case_02_rich_company_url` fixture/persona に `企業note` が残り、visible media name guard を不必要に踏んでいる。
4. `prohibited_claim_guard` が `症状` や `価格` を拾った件について、false positive なのか正しいfailなのか切り分けが必要。
5. AB artifact が `case/A0/draft.md`, `case/B1/draft.md`, `case/B2/draft.md` に分かれており、記事単位でA/Bをmdで横比較しづらい。

許可する変更:
- artifact / fixture / helper:
  - `C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\...`
  - 既存live AB artifact配下に `compare_md\` または各case配下に `compare\` を追加
  - artifact-local helperを追加する場合:
    - `C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\tools\build_ab_compare_md_layout.py`
    - `C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\tools\repair_ab_fixture_preflight.py`
- focused product code only if proven necessary:
  - `C:\tetie\notecode\note\writer_only_brief.py`
  - `C:\tetie\notecode\note\writer_only_evaluator.py`
  - `C:\tetie\notecode\note\tests\test_writer_only_generation.py`
- `C:\tetie\notecode\WORKLOG.md`

原則変更しない:
- `config.json`
- `writer_only_openai_adapter.py`
- `writer_only_service.py`
- normal UI code
- latest visible output files
- fixed writer prompt

禁止:
- OpenAI APIを呼ばない。
- B本文を再生成しない。
- 通常UIからB variantを呼ばない。
- latest visible outputへB variantを投影しない。
- Route 0506 / Route A / repair loop / quality pipeline を戻さない。
- raw full source pass をしない。
- source groundingを緩めない。
- fixed promptを長文化しない。
- persona tableを増やさない。
- evaluator閾値を雑に緩めない。
- pytest復旧のためにネットワークinstallが必要な場合は、作業せず「needs_dependency_approval」として報告する。

期待する最終artifact layout:

```text
live_ab_quality_first_20260616_200725\
  compare_md\
    case_01_thin_company_url\
      00_compare_index.md
      A0_current_gpt41mini.md
      B1_safe_expansion_gpt54mini.md
      B2_safe_expansion_gpt54.md
      evaluation_summary.json
    case_02_rich_company_url\
      00_compare_index.md
      A0_current_gpt41mini.md
      B1_safe_expansion_gpt54mini.md
      B2_safe_expansion_gpt54.md
      evaluation_summary.json
    case_03_local_service_url\
      00_compare_index.md
      A0_current_gpt41mini.md
      B1_safe_expansion_gpt54mini.md
      B2_safe_expansion_gpt54.md
      evaluation_summary.json
```

`00_compare_index.md` には少なくとも次を入れる:
- case id
- source type / fixture note
- winner
- A0/B1/B2 links
- model / parameters
- evaluation pass/fail
- failed checks
- reviewer note
- route flags

`A0_*.md` / `B1_*.md` / `B2_*.md` は本文だけでなく、冒頭に短いfront matter風メタ情報を入れる:

```text
---
case_id:
variant:
model:
parameters:
evaluation_passed:
failed_checks:
article_char_count:
---
```

slice plan:
Slice 0: live AB artifactとWORKLOGを読む。
Self-test: 9件の `draft.md`, `evaluation.json`, `run.json` が読めること。

Slice 1: pytest破損を切り分ける。
Self-test:
- `.\.venv\Scripts\python.exe -m pytest --version`
- `.\.venv\Scripts\python.exe -m pytest note\tests\test_writer_only_generation.py -q`
- 失敗した場合、import error全文を `pytest_environment_diagnosis.md` に保存。
- ローカル修復で済む場合のみ修復。ネットワークinstallが必要なら停止せず、`needs_dependency_approval` として記録。

Slice 2: B brief production shape をno-APIで修正する。
Self-test:
- B用briefが `source_bundle` keyを保持すること。
- `safe_expansion` / `expansion_policy` / `verified_external_context` が残ること。
- review-only surface と production input shape を混ぜないこと。

Slice 3: visible media name fixtureを修正する。
Self-test:
- fixture/persona/brief本文に `企業note`, `note`, `はてなブログ`, `Hatena Blog` が reader-facing targetとして残らないこと。
- 必要なら `ブログ` へ正規化する。

Slice 4: prohibited claim guardを切り分ける。
Self-test:
- `症状` と `価格` のhitを、本文文脈・source evidence・verified context有無で分類する。
- false positiveなら evaluatorの局所修正とfocused testを追加。
- true positiveなら brief/scaffold側にD claim watchlistを強める。
- どちらの場合もsource groundingを緩めない。

Slice 5: compare_md layoutを作る。
Self-test:
- 各caseに `00_compare_index.md`, A0/B1/B2 md, `evaluation_summary.json` がある。
- Markdown readback pass。
- JSON parse pass。

Slice 6: no-API validationを実行する。
Self-test:
- py_compile touched helper/product files
- pytestが復旧した場合は focused pytest
- 復旧しなかった場合は diagnosis artifactと代替validationを記録
- `scripts\validate_writer_only_config.py`
- latest visible output未更新確認

Slice 7: WORKLOGを必要最小限で更新する。
Self-test: route flags / api_send_count=0 / normal UI未接続を確認。

完了判定:
- `compare_layout_ready`
  - pytestまたは代替validationが明確で、B production shape / fixture / guard切り分け / compare_md layout が完了。
- `needs_dependency_approval`
  - pytest復旧にネットワークinstall等の承認が必要。ただし他のno-API artifact作成は完了。
- `needs_next_owner`
  - product側の小修正が大きくなり、別ownerが必要。
- `blocked`
  - 同じエラー3回、または境界違反リスク。
- `reject`
  - B案の安全性が崩れ、比較layout以前に破棄判断が妥当。

完了報告フォーマット:
参照ルールファイル:
今回の実施範囲:
decision: compare_layout_ready | needs_dependency_approval | needs_next_owner | blocked | reject
artifact_root:
compare_md_root:
changed_files_or_docs:
pytest_status:
pytest_diagnosis:
B_brief_production_shape:
visible_media_fixture_status:
prohibited_claim_guard_status:
tests_or_validation:
api_send_count: 0
route_0506_restored: false
route_a_restored: false
repair_restored: false
quality_pipeline_restored: false
raw_full_source_passed: false
normal_ui_connected_to_variant_b: false
latest_visible_output_updated_from_variant_b: false
prompt_bloat: none | minor | found
module_bloat: none | minor | found
next_one_owner:
AGENTS_update_needed:
WORKLOG_update_needed:
```

## Expected Next Owner

`compare_layout_ready` の場合:

```text
writer_only_safe_expansion_revision_live_ab_rerun_owner
```

ただし live API 再実行は別途ユーザー承認後のみ。

`needs_dependency_approval` の場合:

```text
writer_only_pytest_environment_repair_owner
```

# Writer-only Safe Expansion Model Parameter Audit Goal Command 2026-06-16

対象: `writer_only_safe_expansion_model_parameter_audit_owner`

このファイルは、次の作業ウインドウでそのまま貼って長時間自走するための no-API / model-parameter audit ゴールコマンドです。`offline_stub_ready` の次に、live ABへ進む前のモデル・パラメータ候補を公式docs、現行config、既存artifactから整理します。

## Goal Objective

```text
現行 writer-only 本線と safe-expansion B variant の live AB 前に、OpenAI公式docsと現行 `config.json` / `writer_only_config.py` を照合し、GPT-4.1系 baseline、GPT-5.4系候補、必要ならGPT-5.5候補のモデル・パラメータ行列を no-API で作成する。OpenAI APIによる本文生成、通常UI接続、B本文生成、Route 0506 / Route A / repair / quality pipeline 復帰は行わない。
```

## ゴールコマンド

```text
あなたは TECHIE / notecode / コトメイクの `writer_only_safe_expansion_model_parameter_audit_owner` です。

目的:
`writer_only_safe_expansion_offline_ab_generation_stub_owner` が `offline_stub_ready` を返した後、承認付き live AB の前に、モデルとパラメータ候補を no-API で決める。新アルゴリズムの品質比較が「アルゴリズム差」なのか「モデル差」なのか混ざらないよう、比較行列を作る。

参照ルール:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\ALGORITHM.md
4. C:\tetie\notecode\WORKLOG.md
5. C:\tetie\notecode\config.json
6. C:\tetie\notecode\note\writer_only_config.py
7. C:\tetie\notecode\note\writer_only_openai_adapter.py
8. C:\tetie\notecode\docs\writer_only_new_algorithm_ab_test_plan_2026-06-16.md
9. C:\tetie\notecode\docs\writer_only_safe_expansion_offline_ab_generation_stub_goal_command_2026-06-16.md
10. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\offline_ab_generation_stub_summary.md
11. C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\offline_ab_stub_comparison.json

WEB確認:
- OpenAI公式docsを優先して確認する。
- 公式docs以外は、価格・モデル可用性・API parameterの正本にしない。
- 確認対象:
  - current recommended model family
  - `gpt-4.1` / `gpt-5.4` / `gpt-5.5` のAPI model ID
  - Responses API parameters
  - `reasoning.effort`
  - `text.verbosity`
  - `temperature` / `top_p` の扱い
  - web search tool availability, if relevant

現状前提:
- 現行 writer-only 本線:
  - `config.json.writer_only.family = gpt-4.1`
  - `config.json.writer_only.model = gpt-4.1-mini-2025-04-14`
  - `temperature=0.72`, `top_p=0.9`, `max_output_tokens=7000`, `store=false`
- 現行 `writer_only_config.py`:
  - `gpt-4.1` は `temperature` / `top_p` を許可
  - `gpt-5.4` は `text.verbosity` / `reasoning.effort` を許可
  - `gpt-5.4` では `temperature` / `top_p` を拒否
  - `gpt-5.5` family は現時点では未許可
- したがって GPT-5.5 を live AB 候補に入れる場合は、別ownerで config validation 追加が必要。

許可する変更:
- `C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\model_parameter_audit.md`
- `C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\model_parameter_matrix.json`
- `C:\tetie\notecode\logs\writer_only_new_algorithm_ab_20260616\approved_live_ab_candidate_plan.md`
- `C:\tetie\notecode\WORKLOG.md`

原則変更しない:
- product runtime code
- `config.json`
- `writer_only_config.py`
- `writer_only_openai_adapter.py`
- normal UI code
- tests

禁止:
- OpenAI APIで本文生成しない。
- live APIを呼ばない。
- B variant本文を生成しない。
- 通常UIからB variantを呼ばない。
- latest visible outputへB variantを投影しない。
- Route 0506 / Route A / repair loop / quality pipeline を戻さない。
- raw full source pass をしない。
- source groundingを緩めない。
- fixed promptを長文化しない。
- persona tableを増やさない。
- configを変更しない。

比較設計の基本:
- まず「アルゴリズム差」を見る:
  - A0: current writer-only / current GPT-4.1 mini config
  - B0: safe-expansion / same GPT-4.1 mini config
- 次に「モデル差」を見る:
  - B1: safe-expansion / GPT-5.4 mini / `reasoning.effort=low` or `medium` / `text.verbosity=high`
  - B2: safe-expansion / GPT-5.4 / `reasoning.effort=low` or `medium` / `text.verbosity=high`
- GPT-5.5:
  - 公式docs上で現行推奨なら candidate に入れてよい。
  - ただし現行 validator が `gpt-5.5` family 未対応なら、live AB の即実行候補ではなく `config_validation_update_needed` として別ownerへ送る。

推奨判断:
- コスト・速度優先: GPT-5.4 mini候補を優先。
- 日本語ブログの自然さ・最終品質優先: GPT-5.4 または GPT-5.5候補を検討。
- ただし最初の live AB は最大3caseなので、モデル行列を広げすぎない。

slice plan:
Slice 0: 現行configとwriter_only_configを読む。
Self-test: current writer-only model/family/parametersと許可キーを記録する。

Slice 1: OpenAI公式docsをWEB確認する。
Self-test: 参照URL、取得日、確認したmodel ID / supported parametersを `model_parameter_audit.md` に記録する。

Slice 2: model_parameter_matrix.json を作る。
Self-test: 各候補に `model`, `family`, `parameters`, `requires_config_change`, `estimated_purpose`, `risk` を含める。

Slice 3: approved_live_ab_candidate_plan.md を作る。
Self-test: 最大3case・api_send_count見込み・承認文・通常UI非反映・route flagsを明記する。

Slice 4: WORKLOGを必要最小限で更新する。
Self-test: WORKLOG読み戻し、product code / config変更なしを確認。

停止条件:
- 公式docsと現行configの整合が取れない。
- gpt-5.5 を使うには config validation変更が必要だが、同ownerで変更したくなる。
- live APIが必要になったが承認がない。
- モデル候補が広がりすぎて3case ABに収まらない。
- Route 0506 / Route A / repair / quality pipeline が必要。

完了報告フォーマット:
参照ルールファイル:
今回の実施範囲:
decision: model_parameter_audit_ready | config_validation_update_needed | needs_live_api_approval | blocked | reject
artifact_root:
changed_files_or_docs:
official_sources:
current_writer_only_config:
candidate_matrix:
recommended_live_ab_matrix:
tests_or_validation:
api_send_count: 0
route_0506_restored: false
route_a_restored: false
repair_restored: false
quality_pipeline_restored: false
raw_full_source_passed: false
normal_ui_connected_to_variant_b: false
variant_b_body_generated: false
prompt_bloat: none | minor | found
module_bloat: none | minor | found
next_one_owner:
AGENTS_update_needed:
WORKLOG_update_needed:
```

## Expected Next Owner

通常は次のどちらか。

```text
writer_only_new_algorithm_approved_live_ab_owner
```

または、GPT-5.5など現行 validator 未対応モデルを候補に入れる場合:

```text
writer_only_model_config_validation_update_owner
```

live API承認文:

```text
safe-expansion B variant の live AB validation を最大3 caseだけ実行してよいですか。OpenAI APIを呼び、api_send_count / model / parameters / run_id / artifact_root を記録します。通常UIの表示結果には反映しません。
```

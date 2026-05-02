# separate window execution prompt ui source blog final completion 2026-04-20

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\README.md
- C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\TASK.md
- C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\PROGRESS.md
- C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\ROLLBACK.md
- C:\tetie\notecode\plan\ui_source_blog_contract_redesign_2026-04-18\EXECUTION_PROMPT.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\notecode\docs\ui_source_blog_contract_archive_candidate_inventory_2026-04-18.md
- C:\tetie\WORKLOG.md

今回の依頼種別:
- separate-window implementation prompt
- `UI_SOURCE_BLOG_FINAL_COMPLETION_IMPLEMENTATION`
- docs-only prompt ではない
- verification-only prompt ではない

今回の前提:
- user は user test 前の最終実装を望んでいる
- current question は 3 点:
  - 旧アルゴリズムを安全に分離し、現行 mainline だけで user test できる状態にする
  - UI 上で required input / source mode / followup 導線を user が誤解しない状態にする
  - ある程度の既存ブログがあるときに、そのブログ群から next blog を作る path を end-to-end で動かす
- user の自分のブログは default fact source ではない
- self-blog reuse は `fact / continuity / style_memory` の source role を守る

今回の完了条件:
1. current UI で `followup` が legal route として見える
2. `published_post_candidates` が UI から omakase preflight / generation contract まで end-to-end で渡る
3. 既存ブログが十分あるとき、`followup` seed が実際に作られ、生成 path に入る
4. self-blog reuse 用 prompt / contract が minimal に固定される
5. user test に不要な legacy dependency が current runtime mainline から外れるか、少なくとも quarantine boundary が明確になる
6. related pytest が通る
7. 最後に UI の見え方を簡単に確認し、user test 前提の blocking issue がないか report する

current code facts you must start from:
- `C:\tetie\notecode\note\note_writer_app.py`
  - `followup` implementation は helper / gate 側にある
  - ただし current visible source-mode choice では `grounded` と `web` だけが出ている
  - `_build_omakase_surface_state()` は `published_post_candidates` を受け取れるが、current UI call では渡していない
- `C:\tetie\notecode\note\omakase_seed_builder.py`
  - `_OMAKASE_INVENTORY_MIN_POSTS = 3`
  - `_OMAKASE_DOMINANT_CLUSTER_MIN_COUNT = 2`
  - `followup` seed / `published_post_followup_seed` path は実装済み
- `C:\tetie\notecode\note\current_mainline_runner.py`
  - current mainline helper は `build_omakase_preflight()` wrapper を持つ
  - `VNextPipeline` shadow projection が still 残っている
- `C:\tetie\notecode\note\note_writer_app.py`
  - `LegacyHelperAdapter` import / generator cache が still 残っている
- `C:\tetie\notecode\note\legacy_current\`
  - legacy boundary directory が残っている

この window の primary objective:
- `self-blog as source` を fake ではなく current mainline UI で実際に使える状態にする

この window の narrow scope:
1. UI source mode surface
   - `followup` を visible choice に戻す
   - helper text / empty-state / gate text を current contract に合わせる
2. published blog inventory wiring
   - current app から取得できる既存ブログ一覧 / candidate inventory を見つける
   - その inventory を `published_post_candidates` として `_build_omakase_surface_state()` と generation 実行前 preflight に渡す
   - current repo に既存 provider があるなら reuse する
   - なければ broad CMS integration はしない
   - thin adapter / thin provider を 1 slice で足して current app から読める最小 path に留める
3. self-blog reuse prompt / contract
   - followup 時だけ、past blog を `continuity` source として使う
   - style imitation は raw sentence copy ではなく `style_memory summary` だけを prompt に渡す
   - current article の fact slot を past blog で埋めない
   - duplicate / paraphrase replay を避ける
4. legacy separation
   - aggressive delete はしない
   - current runtime mainline に不要な legacy helper / legacy path を safe に外せるなら外す
   - 外せない場合は compatibility boundary を code / test 上で明確にし、user test の current mainline に legacy が混入しないことを示す
5. tests + UI sanity
   - owner-local tests を追加 / 更新する
   - relevant pytest を回す
   - current UI で `followup` / `grounded` / `web` の見え方と gate を確認する

prompt / contract design rule for self-blog source:
- self-blog は 3 role に分ける
  - `fact`
    - current article の required slot を支える source
    - followup の元記事 URL や今回の資料が該当する
  - `continuity`
    - 前回から何を引き継ぐか、どこを続けるかだけを渡す
  - `style_memory`
    - paragraph breath / sentence length / ending mix / subject visibility / connective tolerance の summary だけを渡す
- self-blog を全 article type の default fact source にしない
- followup 以外で self-blog inventory があっても、自動で本文事実へ昇格させない
- prompt wording は minimal にする
- Japanese naturalness control は次だけ固定する
  - 会社紹介で固有名詞一人称を濫用しない
  - `私たち` / `当社` を優先候補にできる
  - 主語省略は許すが曖昧化はさせない
  - 接続詞と文末を単調化させない
  - `・・・` / `！！` を自然さ演出として積極使用しない
- prompt accretion をしない
- planner-centered skeleton に戻さない
- old algorithm wording を再流入させない

recommended implementation order:
1. read current code and identify where published post inventory can already be sourced from
2. expose `followup` in UI choice surface
3. wire `published_post_candidates` into omakase surface state
4. wire the same inventory into generation-time preflight / contract path so preview and execution do not diverge
5. add the minimum prompt / contract surface needed for `continuity` and `style_memory`
6. reduce or quarantine legacy dependency only if safe in the same slice
7. add / update tests
8. run pytest
9. do a final UI sanity check

files you will likely inspect and may edit:
- C:\tetie\notecode\note\note_writer_app.py
- C:\tetie\notecode\note\current_mainline_runner.py
- C:\tetie\notecode\note\omakase_seed_builder.py
- C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
- C:\tetie\notecode\note\vnext_adapters\legacy_helper_adapter.py
- C:\tetie\notecode\note\tests\test_current_mainline_ui_matrix.py
- C:\tetie\notecode\note\tests\test_omakase_seed_builder.py
- C:\tetie\notecode\note\tests\test_note_writer_app_generation_gate_helpers.py
- C:\tetie\notecode\note\tests\test_current_mainline_runner.py
- C:\tetie\notecode\note\tests\test_legacy_helper_adapter_boundary.py

tests you should run at minimum:
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py note\tests\test_omakase_seed_builder.py note\tests\test_note_writer_app_generation_gate_helpers.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_legacy_helper_adapter_boundary.py -q
- if prompt or simple pipeline contract changed:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q

UI sanity checklist:
- `followup` card / choice is visible
- `grounded / web / followup` helper text matches actual behavior
- no-source `followup` blocks clearly
- enough published posts => inventory count is shown
- enough published posts + strong cluster => followup-ready status is visible
- execution path uses the same preflight decision seen in UI
- required inputs message is still understandable

legacy separation rule:
- do not mass-delete `legacy_current`
- do not break compatibility import paths in the same slice unless fully verified
- current target is user-test-safe mainline, not repo-wide historical cleanup
- if legacy helper is still required for unrelated surfaces, isolate it and make the current mainline path not depend on it for self-blog source / followup flow
- if safe removal is not provable inside this window, stop at explicit quarantine + report

stop conditions:
- followup inventory provider cannot be identified and a broad external integration would be required
- legacy removal starts spreading beyond current mainline boundary
- self-blog reuse starts turning into broad style-cloning or default fact reuse
- prompt changes start requiring multi-file accretion across unrelated modules
- current package source-of-truth conflicts with a broad rewrite

final report must include:
1. files changed
2. whether `followup` is now visible in UI
3. where `published_post_candidates` comes from
4. whether self-blog prompt / contract was added and in what minimal form
5. whether legacy dependency was removed, quarantined, or left in place with reason
6. pytest commands run and results
7. UI sanity check result
8. whether user-test-ready status is achieved
9. if not fully achieved, the exact blocking point
```

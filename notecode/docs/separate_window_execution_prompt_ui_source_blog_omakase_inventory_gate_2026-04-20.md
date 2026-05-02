# separate window execution prompt ui source blog omakase inventory gate 2026-04-20

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
- C:\tetie\notecode\docs\separate_window_execution_prompt_ui_source_blog_final_completion_2026-04-20.md
- C:\tetie\WORKLOG.md

今回の依頼種別:
- separate-window implementation prompt
- `UI_SOURCE_BLOG_OMAKASE_INVENTORY_GATE_IMPLEMENTATION`
- docs-only prompt ではない
- verification-only prompt ではない

今回の user request:
- `followup` は削除する
- 理由は「過去の内容からの生成で重複しやすい」ため
- `お任せ` は維持する
- ただし `お任せ` は公開済みブログの蓄積が十分あるときだけ使えるようにする
- unlock 条件は最低:
  - 公開済み記事 3 本以上
  - 合計本文文字数が N 以上

この window の primary objective:
- current mainline UI から `followup` を消し、
- `お任せ` を inventory gate 付きの current path として残し、
- user test 時に「蓄積不足なら生成 NG」が UI / preflight / execution で一致する状態にする

今回の前提:
- self-blog を current article の fact source にしない方針は維持する
- published post inventory は残してよい
- ただし published post inventory は `お任せ unlock 判定` と inventory summary 表示のために使い、本文の current fact slot へ昇格させない
- broad cleanup はしない
- `followup_context` / 旧 followup helper が repo 内に残ってもよいが、current mainline UI / preflight / execution path では使わせない

今回の完了条件:
1. current UI に `followup` choice / card / helper text が visible で残っていない
2. visible source mode は実質 `grounded` と `web(お任せ)` のみになる
3. published inventory に本文文字数系メトリクスが保存される
4. `お任せ` preflight が
   - 公開済み記事数
   - 合計本文文字数
   の両方で unlock 判定する
5. 蓄積不足なら `お任せ` は fail-close で止まり、代替案を返す
6. 蓄積十分なら従来どおり `AUTO_SOURCE_READY` / web seed へ進める
7. UI 表示が gate 理由を読める
8. related pytest が通る
9. UI sanity check を行い、blocking issue がないか report する

implementation assumption you should use unless code facts force otherwise:
- `N` は hard-coded magic number にしない
- module-level constant として置く
- default threshold は `4500` 文字でよい
- constant 名は例えば:
  - `note\omakase_seed_builder.py`
    - `_OMAKASE_INVENTORY_MIN_POSTS = 3`
    - `_OMAKASE_MIN_TOTAL_BODY_CHARS = 4500`
- final report では threshold 値を明示する

current code facts you must start from:
- `C:\tetie\notecode\note\note_writer_app.py`
  - `followup` は visible choice と helper/gate 文言にまだ残っている
  - `_build_omakase_surface_state()` が inventory summary を UI 表示へ出している
  - 現在は `品質通過` / `主クラスタ` 表示がある
- `C:\tetie\notecode\note\omakase_seed_builder.py`
  - published inventory を使う preflight がある
  - `followup` ready path がまだ残っている
  - `quality_ready_posts_count` / cluster 系 summary はすでにある
- `C:\tetie\notecode\note\published_post_inventory.py`
  - inventory entry を jsonl に積んでいる
  - quality summary は保存済み
  - ただし body/full_text 文字数の unlock 用メトリクスは current summary 上まだ main key ではない
- `C:\tetie\notecode\note\current_mainline_runtime_logging.py`
  - successful snapshot persist 時に published inventory へ append している
- `C:\tetie\notecode\note\current_mainline_runner.py`
  - `followup_context` gate はまだ残っている可能性がある

this window's narrow scope:
1. UI source mode cleanup
   - `followup` card / choice / explanatory copy を current UI surface から外す
   - helper text / gate text / empty-state を `grounded` と `web(お任せ)` の二択前提に揃える
2. inventory metric extension
   - published inventory entry に本文文字数を保存する
   - unlock 判定に使う総本文文字数を計算できるようにする
3. omakase gate redesign
   - `followup` ready path を current preflight から外すか quarantine する
   - `お任せ` unlock 条件を:
     - `existing_post_count >= 3`
     - `total_body_chars >= N`
     に変更する
   - 条件未達時は fail-close
   - 条件達成時だけ `AUTO_SOURCE_READY`
4. execution consistency
   - preview / preflight / generation gate の unlock 条件が一致するようにする
   - published inventory は unlock 判定にのみ使い、fact source に昇格させない
5. tests + UI sanity
   - owner-local tests を追加 / 更新
   - related pytest 実行
   - current UI で visible text と gate を確認

design rule for this slice:
- `followup` を代替の hidden route として残さない
- `お任せ` は self-blog accumulation を unlock 条件に使ってよい
- ただし self-blog accumulation を current fact source にしない
- 過去記事本文を今回の記事の source document として auto 注入しない
- prompt accretion はしない
- giant rewrite はしない
- current mainline boundary を壊さない

recommended implementation order:
1. inspect current `followup` UI surface and preflight branches
2. remove `followup` from visible source mode surface in `note_writer_app.py`
3. extend published inventory entry with char-count fields
4. add inventory aggregation helper for total body chars
5. redesign `build_omakase_preflight()` to use:
   - post count threshold
   - total body chars threshold
   and stop returning followup-ready path
6. update UI inventory text so it surfaces:
   - 公開済み X件
   - 合計本文 Y字
   - unlock / blocked reason
7. update generation gate helpers so UI button state matches the same decision
8. update/remove tests that still expect visible `followup`
9. run pytest
10. run UI sanity check

files you will likely inspect and may edit:
- C:\tetie\notecode\note\note_writer_app.py
- C:\tetie\notecode\note\omakase_seed_builder.py
- C:\tetie\notecode\note\published_post_inventory.py
- C:\tetie\notecode\note\current_mainline_runtime_logging.py
- C:\tetie\notecode\note\current_mainline_runner.py
- C:\tetie\notecode\note\tests\test_omakase_seed_builder.py
- C:\tetie\notecode\note\tests\test_current_mainline_ui_matrix.py
- C:\tetie\notecode\note\tests\test_note_writer_app_generation_gate_helpers.py
- C:\tetie\notecode\note\tests\test_current_mainline_runner.py
- if needed:
  - C:\tetie\notecode\note\tests\test_published_post_inventory.py

minimum internal tests you should add or update:
1. inventory metrics
   - published inventory entry stores `body_chars` or equivalent char metric
   - load / roundtrip keeps the metric
2. omakase gate
   - 2 posts + high chars => blocked
   - 3 posts + low chars => blocked
   - 3 posts + enough chars => `AUTO_SOURCE_READY`
3. UI surface
   - visible source-mode list does not include `followup`
   - omakase inventory text includes total chars
   - blocked message is understandable
4. execution gate
   - when omakase threshold unmet, generation path fail-closes before pipeline execution

minimum pytest commands:
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_published_post_inventory.py note\tests\test_omakase_seed_builder.py note\tests\test_current_mainline_runner.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_ui_matrix.py note\tests\test_note_writer_app_generation_gate_helpers.py note\tests\test_note_writer_app_phase01_minimal_ui.py -q
- if UI helper branching changed broadly:
  - C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_note_writer_app_generation_execution_helpers.py -q

internal runtime validation you should perform after pytest:
- do not start from old synthetic fake inventory left in logs
- create a small controlled inventory check inside the repo runtime with at least these 3 cases:
  1. `2 posts / 6000 chars`
     - expected: blocked by count
  2. `3 posts / 3200 chars`
     - expected: blocked by total chars
  3. `3 posts / 5200 chars`
     - expected: `AUTO_SOURCE_READY`
- if you use a temporary synthetic inventory file, clear it afterward

UI sanity checklist:
- visible source mode choices do not show `followup`
- `お任せ` helper text no longer implies past-blog continuation generation
- blocked state shows exact reason in human-readable form
- inventory summary shows both post count and total chars
- when blocked, generate CTA is not presented as immediately available
- when unlocked, `お任せ` still routes to auto-source/web flow

legacy / compatibility rule:
- do not mass-delete `legacy_current`
- do not broad-delete followup internals unless they are safely local
- safe result for this slice is:
  - current mainline UI does not expose `followup`
  - current mainline preflight does not return `followup` ready
  - current execution path does not depend on past-blog continuation contract
- dormant compatibility code may remain if removal would spread too far

stop conditions:
- removing `followup` starts cascading into unrelated broad refactors
- omakase inventory gate starts requiring external CMS integration
- total char metric cannot be computed from current runtime without risky rewrites
- UI copy changes start diverging from actual gate behavior

final report must include:
1. files changed
2. whether `followup` is fully removed from current UI surface
3. the exact omakase threshold values used
4. where total body chars is stored and how it is aggregated
5. whether past-blog data is still used anywhere in current mainline path, and if yes, only for what
6. pytest commands run and results
7. internal runtime validation results for the 3 threshold cases
8. UI sanity check result
9. whether user-test-ready status is achieved
10. if not fully achieved, the exact blocking point
```

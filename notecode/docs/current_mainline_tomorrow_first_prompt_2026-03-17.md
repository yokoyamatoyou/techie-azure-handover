# current mainline tomorrow first prompt (2026-03-17)

`C:\tetie\notecode` の current mainline を主対象に進めてください。

PLANモードが使える環境なら PLAN で開始してください。  
PLANモードが使えない環境なら、最初に plan-first で slice を分解してから進めてください。

【最初に読む】
- `C:\tetie\AGENTS.md`
- `C:\tetie\WORKLOG.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\ALGORITHM.md`
- `C:\tetie\notecode\current_mainline_owner_split\README.md`
- `C:\tetie\notecode\current_mainline_owner_split\OWNER_MAP.md`
- `C:\tetie\notecode\current_mainline_owner_split\PROGRESS.md`
- `C:\tetie\notecode_current_mainline_handoff_2026-03-17.md`

【現状】
- current mainline owner split docs は completed のまま
- 2026-03-17 に narrow slice を 3 本進めた
  - A1: generation error / guard retry exception の projection を adapter 側へ移動
  - A2: pre-generate gate / fetch failure / no-valid-source の projection を adapter 側へ移動
  - D1: runtime snapshot / quality report payload の evidence gap を test-only で固定
- `note_writer_app.py` の UI payload 責務は前より薄くなったが、success 後半はまだ厚い
- latest artifact の `announcement` は完走しているが、`resonance_applied=false`、`quality_pipeline_applied=["phase02_burstiness"]`、`section_opening_repetition_count=3`、`prompt_anchor_coverage=0.4444`、`must_cover_reflection_rate=0.3333`
- したがって、直近の AI 感の主因は UI shell より pipeline 本文側に残っている可能性が高い
- ただし今回は runner / pipeline owner には触らない

【今回の最優先目的】
- `note_writer_app.py` の success 後半から、owner-local に切れる 1 slice を選ぶ
- 推奨は `B1 post-success / completion owner-local split`
- ただし 1 slice に切れないなら実装せず、plan-only で止める

【優先候補 slice】
1. `legal postcheck` の UI projection を thin wrapper 化する
2. `completion payload` の review/stats projection をさらに adapter へ寄せる

この 2 つを同時にやらない。最初に 1 本だけ選ぶこと。

【主な確認対象】
- `C:\tetie\notecode\note\note_writer_app.py`
- `C:\tetie\notecode\note\current_mainline_ui_result_adapter.py`
- `C:\tetie\notecode\note\tests\test_note_writer_app_post_success_helpers.py`
- `C:\tetie\notecode\note\tests\test_note_writer_app_generation_execution_helpers.py`
- `C:\tetie\notecode\note\tests\test_current_mainline_ui_result_adapter.py`
- 必要時のみ
  - `C:\tetie\notecode\note\tests\test_newalgorithm_phase06_logging_compat.py`
  - `C:\tetie\notecode\note\tests\test_note_writer_app_snapshot_helpers.py`

【進め方】
- 最初に「この依頼を 1 本の slice に切れるか」を明示する
- まずコードを読み、`legal postcheck` と `completion` のどちらが narrow かを判断する
- narrow ならその 1 slice だけ実装する
- wide なら実装せず、plan-only を返す
- runner / pipeline / runtime logging owner に触れる必要が出たら止まる

【やらないこと】
- `current_mainline_runner.py` の編集
- `current_mainline_runtime_logging.py` の編集
- `generation_request_builder.py` の編集
- `newalgorithm_pipeline\` 配下の編集
- `article_generator` split reopen
- `AGENTS.md` / `WORKLOG.md` の更新
- live generation の無理な実行
- 横断的な大規模リファクタ

【self-test 方針】
- まず focused tests を優先する
- post-success / completion slice に進む場合の最小セット

```powershell
$env:PYTHONPATH='C:\tetie\notecode'; C:\tetie\notecode\.venv\Scripts\pytest.exe note/tests/test_note_writer_app_post_success_helpers.py note/tests/test_note_writer_app_generation_execution_helpers.py note/tests/test_current_mainline_ui_result_adapter.py note/tests/test_newalgorithm_phase04_ui_wiring.py -q
```

- 必要時のみ追加

```powershell
$env:PYTHONPATH='C:\tetie\notecode'; C:\tetie\notecode\.venv\Scripts\pytest.exe note/tests/test_newalgorithm_phase06_logging_compat.py note/tests/test_note_writer_app_snapshot_helpers.py -q
```

【最終的に出してほしい内容】
1. 参照したルールファイル
2. 今回の実施範囲
3. この依頼は 1 本の slice として narrow か
4. 事実
5. 推測
6. 最優先の 1 slice
7. その slice の対象ファイル
8. その slice の非対象ファイル
9. 実装した場合の変更点
10. self-test
11. runtime error リスク評価
12. AI感のない文章の実現性評価
13. 未確認の gap
14. 次にやるべき 1 slice
15. AGENTS/WORKLOG 更新要否

【判断原則】
- current mainline 正本
- scope を広げすぎない
- 1責務1owner
- runner / pipeline owner は触らない
- narrow で owner-local なら実装と focused self-test まで進む
- narrow でないなら計画だけ返す

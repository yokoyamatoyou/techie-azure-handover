# current mainline tomorrow first prompt

更新日: 2026-04-01  
用途: 次回セッションで `st-comparative-cross-department` を rollback 後の kept state から安全に再開するための prompt

## copy-paste prompt

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode_current_mainline_handoff_2026-03-31.md
- C:\tetie\notecode\plan\semantic_surface_migration_2026-03-31\PROGRESS.md
- C:\tetie\notecode\GPTPRO.txt
- C:\tetie\notecode\docs\current_mainline_tomorrow_first_prompt_2026-04-01.md

今回の実施範囲:
- compare path の current kept state を維持したまま再開する
- semantic gate は開けない
- model は section=gpt-5.4-mini を維持する
- 次の narrow slice は st-comparative-cross-department のみ
- 直前に試した `section_generator.py` の input slimming は fail 済みなので rollback state から始める
- 対症療法は禁止
- 文章は毎回変えるが、prompt accretion で押し切らない

source-of-truth priority:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\plan\semantic_surface_migration_2026-03-31\PROGRESS.md
4. C:\tetie\notecode_current_mainline_handoff_2026-03-31.md
5. C:\tetie\notecode\docs\current_mainline_tomorrow_first_prompt_2026-04-01.md

開始時に必ず読むファイル:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\ALGORITHM.md
4. C:\tetie\WORKLOG.md
5. C:\tetie\notecode_current_mainline_handoff_2026-03-31.md
6. C:\tetie\notecode\plan\semantic_surface_migration_2026-03-31\PROGRESS.md
7. C:\tetie\notecode\GPTPRO.txt
8. C:\tetie\notecode\docs\current_mainline_tomorrow_first_prompt_2026-04-01.md

開始時に必ず読む artifact:
1. C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260401-compare-rerun-post-surface-fix\summary.json
2. C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260401-compare-rerun-post-surface-fix\st-comparative-cross-department.json
3. C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260401-compare-rerun-post-surface-fix\st-comparative-cross-department.txt
4. C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260401-cross-department-slim-rerun-01\summary.json
5. C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260401-cross-department-slim-rerun-01\st-comparative-cross-department.json
6. C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260401-cross-department-slim-rerun-01\st-comparative-cross-department.txt
7. C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260401-small-team-surface-fix-07\st-comparative-small-team.txt
8. C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260401-small-team-surface-fix-08\st-comparative-small-team.json
9. C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260401-small-team-surface-fix-09\st-comparative-small-team.txt

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

current kept state:
- keep diff:
  - C:\tetie\notecode\note\newalgorithm_pipeline\input_contract.py
  - C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
  - C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py
  - C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py
- keep 内容:
  - compare axis normalization fix
  - tool-compare abswinner narrow fix
  - compare opener / ranking soften
  - compare repeated ending diversification の安全版
- model:
  - section=gpt-5.4-mini 維持
- 開けないもの:
  - semantic gate
  - gpt-5.4 promotion
  - compare 専用 module / class 追加

最新観測:
- small-team targeted rerun:
  - 07 / 08 / 09 は 3/3 で rubric=8, axis_shift=0, prompt_echo=0
  - surface diversification は small-team では keep 候補
- full compare rerun:
  - C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260401-compare-rerun-post-surface-fix
  - short_gate_passed=4/5
  - rubric_mean_total=7.6
- 現在の主 residual:
  - st-comparative-cross-department
  - prompt_echo_hits=1
  - comparative_axis_shift_count=1
  - after_quality / final_body で sentence fragment が見える
  - 例:
    - 「ため。」
    - 「求められ。」
- 直前の失敗 hypothesis:
  - owner=file は `C:\tetie\notecode\note\newalgorithm_pipeline\section_generator.py`
  - fit / caution / closing の input slimming を試した
  - owner-local test は pass したが live rerun-01 で fail した
  - artifact:
    - C:\tetie\notecode\logs\current_mainline_ui_runs\codex-genre-sweep-20260401-cross-department-slim-rerun-01
  - rerun-01 result:
    - short_gate=0/1
    - rubric=6
    - prompt_echo=1
    - comparative_axis_shift_count=1
    - prompt echo 例:
      - 「複数部門で記事作成を回すなら、誰が原稿を持ち、誰が承認するかを最初に固定できるかが重要です。」
  - この hypothesis は rollback 済み
  - rollback 後の確認:
    - `./.venv/Scripts/python.exe -m pytest note/tests/test_newalgorithm_phase03_pipeline.py -k "owner_local_prompt_guard" -q`
    - 3 passed

次にやること:
1. baseline と slim-rerun-01 の stage trace を見比べる
2. section_generation / after_quality / final_body のどこで residual が固定されるかを再確認する
3. 1 narrow hypothesis だけ決める
4. owner は 1 file に固定する
5. owner-local test
6. cross-department targeted rerun を 3 回
7. 効いたら compare 5-case rerun を 1 回
8. 効かなければ rollback して stop

次候補の narrow slice:
- 第一候補:
  - owner = C:\tetie\notecode\note\newalgorithm_pipeline\discourse_planner.py
  - no-source cross-department compare の fit / caution / closing seed を axis-only に狭める
  - broad な `用途別` / `確認事項` / `結論` から prompt-like 再言い換えが起きる余地を減らす
- do-not:
  - `section_generator.py` の failed slimming をそのまま再投入しない
  - prompt echo detector 側の閾値調整に逃げない
  - output_formatter の表層 tweak で止血しない

do-not:
- 対症療法をしない
- prompt を長文化して押し切らない
- meaning-layer field を増やさない
- semantic gate を開けない
- unrelated genre に広げない
- human_resonance* を触らない
- いきなり 5 reruns にしない

最終報告で必ず示すこと:
- 読んだ正本ファイル
- current success path
- keep した修正
- 実行した artifact path
- visible residual
- rollback の有無
- 次の narrow slice
- AGENTS / WORKLOG 更新の有無
```

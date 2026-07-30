参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\ALGORITHM.md
- C:\tetie\WORKLOG.md

今回の実施範囲:
- `comparative_review` の current residual に対して、`comparative_thin_section_targeted_patch` だけを narrow diff で実装する
- 既存の meaning-layer を広げない
- `comparative_compact_ledger_gate` は今回は実装しない

推奨モード:
- PLANモード

理由:
- 今回は `1 narrow hypothesis` に固定し、owner 境界・rollback 境界・gate を明示しながら進めたい
- 実装対象が small でも、`do now` と `do later` を混ぜると scope が崩れやすい
- `comparative_thin_section_targeted_patch` pass 後も、そのまま semantic slice へ進まず停止する必要がある

開始時に必ず読むファイル:
1. C:\tetie\AGENTS.md
2. C:\tetie\notecode\AGENTS.md
3. C:\tetie\notecode\ALGORITHM.md
4. C:\tetie\WORKLOG.md
5. C:\tetie\notecode_current_mainline_handoff_2026-03-31.md
6. C:\tetie\notecode\plan\semantic_surface_migration_2026-03-31\PROGRESS.md
7. C:\tetie\notecode\GPTPRO.txt

current success path:
- C:\tetie\notecode\note\current_mainline_runner.py
- -> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py
- -> super().generate(...)
- -> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py

今回の fixed slice:
- slice 名:
  - `comparative_thin_section_targeted_patch`
- objective:
  - `comparative_thin_section_headings` を compare-specific flagged span に落とし、薄い比較 section だけを `PATCH_SCOPE` で局所補修する
- primary owner:
  - C:\tetie\notecode\note\simple_note_pipeline\pipeline.py
  - C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py
- support owner:
  - 最大 1 file まで
  - できれば test owner だけに留める

今回やってよいこと:
- `comparative_thin_section_count` / `comparative_thin_section_headings` を compare-specific flagged span へ接続する
- `PATCH_SCOPE` に compare thin section 用の narrow 文面を足す
- compare の thin section だけに repair を局所化する
- owner-local test を追加する

今回やってはいけないこと:
- 新しい meaning-layer field を増やすこと
- `comparative_compact_ledger_gate` を開けること
- compare 専用の新 module / class を作ること
- prompt accretion で anti-flatness を増殖させること
- `human_resonance*` を触ること
- `input_contract.py` に compare semantic field を押し込むこと

phase progression rule:
1. `PROGRESS.md` の current action を見て、今回の slice が `comparative_thin_section_targeted_patch` であることを確認する
2. owner / rollback / do-not を確認する
3. 実装する
4. required checks を実行する
5. targeted live compare rerun を実行する
6. evidence を残す
7. semantic slice へは進まず停止する

required checks:
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_quality_guard.py -q
- C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q

targeted live check:
- C:\tetie\notecode\.venv\Scripts\python.exe C:\tetie\notecode\tools\run_current_mainline_genre_sweep.py --phase genre-rerun --live --genres comparative_review

pass 条件:
- required checks が green
- targeted live で `short_gate_passed=5/5`
- compare `.txt` artifact に raw axis token 漏れを新規再発させていない
- thin comparative section が局所 patch 経路に乗っている evidence を示せる
- prompt accretion / module accretion / owner boundary violation がない

停止条件:
- 同一 slice で 3 回自己修正しても gate を越えられない
- compare residual を直すために meaning-layer 拡張が必要になった
- owner file が narrow slice を超える
- rollback 不能な diff が必要になった

失敗時の扱い:
- 3 回失敗したら停止し、user へ報告する
- `comparative_compact_ledger_gate` は next candidate として書くだけにして、このウインドウでは実装しない

最終報告で必ず示すこと:
- 読んだ正本ファイル
- current success path
- 実施した slice
- evidence
- 実行した tests
- keep した修正
- rollback した仮説
- 停止した場合は failed attempts / reason / next narrow slice
- AGENTS / WORKLOG 更新の有無

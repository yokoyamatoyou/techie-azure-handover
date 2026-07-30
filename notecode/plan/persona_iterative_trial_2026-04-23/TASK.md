# persona_iterative_trial_2026-04-23 TASK

## 目次
- phase map
- gates
- retry-stop
- required checks

## phase map
- Phase 01: planning package と trial tooling root を追加する
- Phase 02: current mainline contract layer に `_persona_contract` / `_source_packet` / `_persona_trial` を追加する
- Phase 03: generation / editing / regeneration prompt owner が hidden contract を craft / repair guard として使う
- Phase 04: trial driver が 7-case fixture を再利用して manifest / logs / case directories を書けるようにする
- Phase 05: regression tests, py_compile, requested shared test files を通す
- Phase 06: artifact root を初期化し、separate-window 実行準備を完了する

## gates
- gate_01: no legacy route edits
- gate_02: `一般読者` default は product behavior として維持
- gate_03: trial acceptance だけが default audience fallback を reject
- gate_04: generation prompt / repair prompt / visible output に `persona`, `editor`, `trial`, `source_contract`, `hidden` を漏らさない
- gate_05: company introduction / comparative review の current source contract scope を `_source_packet` に写像しても required slot 定義は変えない
- gate_06: loop manifest は baseline 2 runs -> narrow change 1 -> rerun 2 を表現できる

## retry-stop
- 1 phase = 1 narrow hypothesis = 1 owner scope
- 同一 phase の修正試行は 3 回まで
- worsening change は rollback log に記録して keep しない
- stable success は 2 consecutive accepted loops を条件にする

## required checks
- `py -3 -m py_compile` for touched files
- `py -3 -m pytest C:\tetie\notecode\note\tests\test_current_mainline_runner.py`
- `py -3 -m pytest C:\tetie\notecode\note\tests\test_current_mainline_regressions.py`
- `py -3 -m pytest C:\tetie\notecode\note\tests\test_current_mainline_ui_matrix.py`
- `py -3 -m pytest C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
- `py -3 -m pytest C:\tetie\notecode\note\tests\test_simple_note_quality_guard.py`

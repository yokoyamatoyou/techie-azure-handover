# PHASE_05_ACCEPTANCE_HANDOFF

- Last Updated: 2026-03-14

## Objective

- current mainline owner 分担の受入条件、rollback 条件、handoff 導線を固定する。

## In Scope

- acceptance criteria
- rollback 条件
- handoff 導線
- `README.md` / `PROGRESS.md` / `WORKLOG.md` の最終整合

## Out of Scope

- 新規機能追加
- 他カテゴリ品質改善
- legacy plan の整理

## Target Owners

- current mainline 文書群全体

## Target Files

- `C:\tetie\notecode\current_mainline_owner_split\README.md`
- `C:\tetie\notecode\current_mainline_owner_split\PROGRESS.md`
- `C:\tetie\notecode\current_mainline_owner_split\EXECUTION_RULES.md`
- `C:\tetie\notecode\current_mainline_owner_split\OWNER_MAP.md`
- `C:\tetie\notecode\current_mainline_owner_split\TEST_AND_SAFETY_MATRIX.md`
- `C:\tetie\WORKLOG.md`

## Preconditions

- Phase01-04 completed

## Tasks

1. acceptance criteria を Phase 横断でまとめる
2. rollback 条件をまとめる
3. handoff 再開導線を `README.md` と `PROGRESS.md` に固定する
4. `WORKLOG.md` の時系列記録と current docs の整合を確認する

## Findings

### 事実

- `PROGRESS.md` 上で Phase01-04 は completed、Phase05 は final handoff slice まで到達している。
- `README.md` には read-first、document map、related files / logs / tests が揃っている。
- Phase01-04 の主要結論は current docs 側に固定済み。
  - Phase01: owner map、called by / calls to、source of truth by concern が固定済み。
  - Phase02: `reason_code` / `allow_generate` / `needs_input_items` の owner と判定順が固定済み。
  - Phase03: confirm preview と generation-only snapshot の observability 差が fixed shape として説明済み。
  - Phase04: request build / execute / snapshot / audit の I/O 契約と rollback 条件が固定済み。
- current accepted behavior の根拠テストが揃っている。
  - `pytest note\tests\test_generation_request_builder.py -q` -> `6 passed`
  - `pytest note\tests\test_current_mainline_runner.py -q` -> `17 passed`
  - `pytest note\tests\test_current_mainline_regressions.py -q` -> `20 passed`
  - `pytest note\tests\test_newalgorithm_phase04_ui_wiring.py -q` -> `17 passed`
  - `pytest note\tests\test_newalgorithm_phase06_logging_compat.py -q` -> `17 passed`
- current accepted behavior の要点は owner 単位で説明できる。
  - `improvement_case` は current code 上で strict source context gate 対象外。
  - confirm event の `latest_ui_journey.runtime_reason_code` と `latest_output.runtime_reason_code` は別 projection。
  - generation snapshot / audit の source of truth は `pipeline_check.input_contract`。
  - snapshot は full contract、audit は compact projection。
- Phase05 では runtime code を変更していない。
  - したがって `py_compile` は不要。
  - rollback は code rollback ではなく docs / phase reopen で扱う。

### 推測

- 別ウインドウ担当は `README.md` と `PROGRESS.md` だけで再開可能。
  - どこから読むか、何が current accepted behavior か、何を reopen すべきかが文書だけで辿れるため。
- 次に問題が出ても、症状ごとに reopen すべき Phase を 1 つへ寄せられる可能性が高い。

## Acceptance Criteria

- Phase01 accepted
  - `OWNER_MAP.md` に primary responsibility / non-responsibility / direct call map / source of truth が固定されている
- Phase02 accepted
  - confirm preview と generation 本体の stop / accept 判定 owner が current code と回帰で一致している
- Phase03 accepted
  - UI journey、latest snapshot、quality report、audit の見え方の差が observability shape として説明できる
- Phase04 accepted
  - build / execute / snapshot / audit の field flow と intentional redundancy が説明できる
- Phase05 accepted
  - `README.md` と `PROGRESS.md` から read order、current status、reopen guide が追える
- Acceptance evidence accepted
  - 主要 5 pytest が pass し、current logs の保持粒度が docs と矛盾しない

## Rollback Summary

- 今回の Phase05 完了は docs-only なので、runtime rollback は不要。
- ただし current code / logs / tests が docs と食い違った場合は completed 状態を維持しない。
- reopen rule は symptom-driven にする。

| Symptom | Reopen Phase | First Owner |
|---|---|---|
| owner の主責務や direct edge が説明できない | Phase01 | `OWNER_MAP.md` 起点 |
| confirm preview と generation 本体の input decision がずれる | Phase02 | `input_contract.py` または `current_mainline_runner.py` |
| UI journey と latest snapshot / audit の status / reason が分からない | Phase03 | `note_writer_app.py` または `current_mainline_runtime_logging.py` |
| request build / execute / snapshot / audit の field が途切れる | Phase04 | `generation_request_builder.py` / `current_mainline_runner.py` / `current_mainline_runtime_logging.py` のいずれか 1 owner |
| 再開導線や acceptance summary が不足する | Phase05 | current docs |

## Handoff Guide

1. `C:\tetie\AGENTS.md` を読む
2. `C:\tetie\notecode\current_mainline_owner_split\README.md` を読む
3. `C:\tetie\notecode\current_mainline_owner_split\PROGRESS.md` で current status を確認する
4. 問題の症状に応じて Phase01-05 の該当文書だけ reopen する
5. runtime code を触る前に「どの owner を直すか」を 1 つに限定する

## Conclusion

- current mainline owner split は Phase01-05 の exit criteria を満たし、completed に進めてよい。
- 今後は新しい runtime drift が出たときだけ、症状に対応する Phase を reopen する。
- broad refactor や multi-owner simultaneous fix はこの文書群の運用対象外とする。

## Exit Criteria

- 別ウインドウ担当が `README.md` と `PROGRESS.md` だけで再開できる
- rollback 条件が文書で説明可能
- acceptance criteria が owner 分担と矛盾しない

## Required Tests

- 文書整合確認
- 必要に応じて phase 横断の主要 pytest

## Code Bug Check

- 文書上の owner 境界が実コードと矛盾していないか最終確認する

## Pipeline Bug Check

- 主要ログと主要テストの導線が文書から辿れるか確認する

## LLM Safety Check

- 安全性確認の導線が Phase ごとに欠けていないか確認する

## Retry Rule

- 同一事象の修正試行は最大 2 回

## Stop Condition

- acceptance criteria と rollback 条件が両立しない場合は停止して報告する

## Evidence to Record

- acceptance summary
- rollback summary
- handoff 再開導線

## Evidence Recorded

- 文書
  - `README.md`
  - `PROGRESS.md`
  - `OWNER_MAP.md`
  - `TEST_AND_SAFETY_MATRIX.md`
  - `PHASE_01_OWNER_MAP.md`
  - `PHASE_02_INPUT_CONFIRM_DECISION.md`
  - `PHASE_03_UI_OBSERVABILITY.md`
  - `PHASE_04_PIPELINE_IO_BOUNDARY.md`
- テスト
  - `test_generation_request_builder.py`
  - `test_current_mainline_runner.py`
  - `test_current_mainline_regressions.py`
  - `test_newalgorithm_phase04_ui_wiring.py`
  - `test_newalgorithm_phase06_logging_compat.py`
- 実行結果
  - `pytest note\\tests\\test_generation_request_builder.py -q` -> `6 passed`
  - `pytest note\\tests\\test_current_mainline_runner.py -q` -> `17 passed`
  - `pytest note\\tests\\test_current_mainline_regressions.py -q` -> `20 passed`
  - `pytest note\\tests\\test_newalgorithm_phase04_ui_wiring.py -q` -> `17 passed`
  - `pytest note\\tests\\test_newalgorithm_phase06_logging_compat.py -q` -> `17 passed`

## Handoff to Next Phase

- 全 Phase completed 後は `PROGRESS.md` を completed に更新し、新しい drift が出るまで reopen しない

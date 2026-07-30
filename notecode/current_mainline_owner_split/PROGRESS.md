# Current Mainline Owner Split PROGRESS

- Last Updated: 2026-03-17
- Initiative: current mainline owner split
- Current Phase: Phase05
- Current Status: completed
- Next Action: current mainline UI shell の owner-local肥大化解消 track は stop とし、新しい runtime drift / log shape drift / docs 不整合が出た場合のみ、症状に対応する Phase を reopen する
- Goal: current mainline の責務境界を owner 単位で固定し、仕様判断と最小修正判断を分離できる状態にする

## Phase Status

| Phase | Name | Status | Owner | Exit Criteria |
|---|---|---|---|---|
| Phase01 | Owner Map | completed | AI | 主要 5 owner の責務、非責務、入出力、呼び出し関係が表で確定 |
| Phase02 | Input Confirm Decision | completed | AI | `reason_code` / `allow_generate` / `needs_input` の owner と判定順が説明可能 |
| Phase03 | UI Observability | completed | AI | UI 表示と logging の status/reason の非対称が owner 単位で説明可能 |
| Phase04 | Pipeline IO Boundary | completed | AI | request build / execute / snapshot / audit の責務重複が文書で解消 |
| Phase05 | Acceptance Handoff | completed | AI+User | 受入条件、rollback、handoff が固定され別ウインドウで再開可能 |

## Current Tasks

| ID | Task | Owner | Status | Exit Criteria | Checks |
|---|---|---|---|---|---|
| T01 | 主要 owner ファイルの責務表を作る | AI | completed | 5 owner の主責務と非責務が `OWNER_MAP.md` に記載済み | owner 表確認 |
| T02 | 呼び出し元 / 呼び出し先を列挙する | AI | completed | `Cross-Owner Call Map` が埋まり、呼び出し方向が説明可能 | 静的確認 |
| T03 | 正本ログ / テスト導線を紐付ける | AI | completed | 各 owner に関連ログと関連テストが記載済み | ログ / テスト導線確認 |
| T04 | 非責務を明記する | AI | completed | owner ごとの「ここから先は別 owner」が明記済み | 境界レビュー |
| T05 | source 要件の定義位置を確認する | AI | completed | `source_fit` / `source_grounding_status` / `input_decision` の定義位置が説明可能 | コード確認 |
| T06 | confirm preview と generation 本体の判定順を確定する | AI | completed | runner と pipeline の判定順が owner 単位で説明可能 | パイプライン確認 |
| T07 | 最新コードと履歴ログの扱いを分離する | AI | completed | current behavior と historical logs の根拠が分離されている | 証跡整理 |
| T08 | UI confirm 表示の owner を固定する | AI | completed | confirm status / warning / block の責務が UI owner で説明可能 | コード確認 |
| T09 | UI journey と snapshot の投影差を確認する | AI | completed | `latest_ui_journey.json` / `latest_generation_output.json` の status/reason 差が説明可能 | ログ確認 |
| T10 | historical stop artifact の見え方を整理する | AI | completed | historical stop が runtime owner ではなく observability slice の論点だと説明可能 | 証跡整理 |
| T11 | build / execute / snapshot / audit の I/O 契約を列挙する | AI | completed | request build から audit までの key 流れが説明可能 | コード確認 |
| T12 | field source of truth の重複保持を洗い出す | AI | completed | build / execute / snapshot / audit の重複 field が説明可能 | I/O 契約確認 |
| T13 | rollback 条件を整理する | AI | completed | Phase04 文書に rollback 条件が固定されている | 証跡整理 |
| T14 | acceptance criteria を Phase 横断でまとめる | AI | completed | owner 分担と受入条件が矛盾なく説明可能 | 文書整合確認 |
| T15 | rollback summary と handoff 導線を固める | AI | completed | `README.md` / `PROGRESS.md` だけで再開できる | handoff 導線確認 |
| T16 | `WORKLOG.md` と current docs の整合を確認する | AI | completed | Phase01-05 の履歴と current docs が矛盾しない | 履歴確認 |

## Decisions

- 2026-03-14: current 正本は `C:\tetie\notecode\current_mainline_owner_split\` 配下に置く
- 2026-03-14: 命名は current 固定とし、日付は本文内の `Last Updated` と判断記録で扱う
- 2026-03-14: 各 Phase の末尾で `コード確認 / パイプライン確認 / LLM 安全性確認` を必須実施する
- 2026-03-14: 同一事象の修正試行は最大 2 回とし、2 回失敗時は停止して報告する
- 2026-03-14: `WORKLOG.md` は Phase 完了時の時系列記録に限定し、現在地は `PROGRESS.md` を正とする
- 2026-03-14: `note_writer_app.py` は logging trigger owner、`current_mainline_runtime_logging.py` は logging schema / persistence owner として分ける
- 2026-03-14: current behavior の根拠は現コードと 2026-03-14 回帰テストを優先し、2026-03-13 の improvement_case preview stop logs は履歴として扱う
- 2026-03-14: `improvement_case` は current code 上で strict source context gate の対象外と確定し、`source_fit=pass` / `source_grounding_status=insufficient` / `input_decision=accept` の組み合わせを current behavior として採用する
- 2026-03-14: `INP_SOURCE_CONTEXT_INSUFFICIENT` と `source_fit=pass` の両立説明は current code では company-introduction-like に限定される
- 2026-03-14: `latest_ui_journey.json.runtime_reason_code` は event reason の投影、`latest_ui_journey.json.latest_output` は result summary の投影であり、confirm-only event では両者が一致しないことを current shape として受け入れる
- 2026-03-14: `latest_generation_output.json` / `latest_generation_quality_report.json` / `generation_audit_log.jsonl` は generation path 専用であり、confirm preview では更新しない
- 2026-03-14: `quality_warning_only` の判定 owner は `note_writer_app.py`、logging owner は projection のみと確定する
- 2026-03-14: `pipeline_check.input_contract` は generation path の snapshot / audit source of truth とし、snapshot は full contract、audit は compact projection を維持する
- 2026-03-14: `source` / `source_inputs`、`prompt_raw` / `topic`、`length_mode` / `length_mode_requested` は current code 上の intentional redundancy として扱い、Phase04 では runtime 修正しない
- 2026-03-14: current mainline owner split は completed とし、以後の再作業は symptom-driven に該当 Phase だけ reopen する
- 2026-03-15: `run_generation()` success path の UI-only result projection owner は `current_mainline_ui_result_adapter.py` とし、`note_writer_app.py` は widget/state mutation と logging timing を保持する
- 2026-03-15: `run_generation()` output guard blocked path の UI-only projection owner も `current_mainline_ui_result_adapter.py` とし、`note_writer_app.py` は widget/state mutation と logging/snapshot trigger timing を保持する
- 2026-03-15: `run_generation()` の generation telemetry input assembly（UI journey event payload / latest snapshot kwargs）は `current_mainline_ui_generation_telemetry_adapter.py` とし、`note_writer_app.py` は logging/snapshot trigger timing を保持する
- 2026-03-15: `run_generation()` の pre-run UI reset/start transition plan は `current_mainline_ui_generation_state_adapter.py` とし、`note_writer_app.py` は widget/state mutation と start timing を保持する
- 2026-03-15: `run_generation()` の top-level exception path UI state transition plan も `current_mainline_ui_generation_state_adapter.py` とし、`note_writer_app.py` は `generation_exception` event trigger timing と outcome 決定を保持する
- 2026-03-15: `run_generation()` の finally cleanup transition plan も `current_mainline_ui_generation_state_adapter.py` とし、`note_writer_app.py` は actual cleanup mutation と finish logging を保持する
- 2026-03-15: `run_generation()` の complete terminal state transition plan も `current_mainline_ui_generation_state_adapter.py` とし、`note_writer_app.py` は `generation_completed` の logging/notify timing と result projection 適用を保持する
- 2026-03-17: current mainline UI shell の owner-local肥大化解消 track は stop とし、残る render 後の legal postcheck / image prompt / completion / exception / finally cleanup は `note_writer_app.py` の terminal timing / actual widget-state mutation owner として保持する
- 2026-03-17: 次回は owner-local肥大化解消の継続ではなく、article type 横断の品質 evidence と AI感 gap の確認へ目的を切り替える。runtime drift / log shape drift / docs 不整合が出た場合のみ symptom-driven に reopen する

## Blockers

- なし

## Next Checkpoint

- current mainline UI shell の owner-local肥大化解消 track は stop のまま維持し、新しい runtime drift、ログ shape drift、または docs 不整合が出た時点でのみ、該当 Phase を reopen して更新する

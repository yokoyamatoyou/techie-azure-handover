# separate window execution prompt sentence final monotony triage 2026-04-17

```text
参照ルールファイル:
- C:\tetie\AGENTS.md
- C:\tetie\notecode\AGENTS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\README.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\TASK.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\PROGRESS.md
- C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\ROLLBACK.md
- C:\tetie\WORKLOG.md
- C:\tetie\notecode\docs\separate_window_management_memo_deepresearch_reflection_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_priority_revision_after_deepresearch_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_instruction_window_relocation_prompt_2026-04-17.md
- C:\tetie\notecode\docs\separate_window_instruction_first_request_sentence_final_monotony_2026-04-17.md

今回の実施範囲:
- `sentence-final pattern monotony cap + single repair` line の planning / triage だけを行う
- 日本語 blog runtime の production code は変更しない
- current source-of-truth は更新しない
- AGENTS / WORKLOG / current package docs は更新しない
- 初手は docs-only で進める
- 実装判断はこのウインドウで行わず、narrow owner candidate の整理までに留める

current keep-state:
- route default:
  - `grounded generic default`
- planning:
  - `opt-in only`
- structural baseline:
  - `single-pass + optional single repair 1回`
- blank company intro keep line:
  - `prompt_builder.py` の `current-business-first keep line`
- current package:
  - `DOCS_FIRST_BEFORE_MORE_CODE`
- `reference realization policy`:
  - separate evidence line として keep
  - 今回の main line にはしない

priority shift:
- next main candidate は
  - `sentence-final pattern monotony cap + single repair`
- 理由:
  - 日本語特有の visible AI-feel と接続しやすい
  - current baseline symptom と整合する
  - `single-pass + optional single repair 1回` に自然に乗る
  - owner-local / rollback-first / feature-flag friendly
- 優先度を下げるもの:
  - `reference realization policy first`
  - section-level `subject_reintroduction_policy`

開始時に確認する artifact:
1. C:\tetie\notecode\logs\latest_generation_output.txt
2. C:\tetie\notecode\logs\latest_generation_output.json
3. C:\tetie\notecode\logs\latest_generation_quality_report.json
4. current package docs に残っている symptom summary
   - `ending_bucket_max_run = 29`
   - `ending_bucket_monotony_score = 1.0`
   - `repair_applied = false`
   - `patch_path_used = false`
   - `patch_path_refusal_reason = compact_plan_scope_ineligible`

目的:
- 初手の目的は実装ではなく planning / triage である
- `sentence-final monotony` の責任 owner を narrow に切り分ける
- detector / telemetry / repair scope を混ぜずに分解する
- 次に開くべき production owner candidate を 1 つか 2 つまでに絞る
- docs-first で `GO_TO_IMPLEMENT` か `NEEDS_MORE_TRIAGE` かを判定する

絶対条件:
- production code edit 禁止
- `note\simple_note_pipeline\*.py`
- `note\newalgorithm_pipeline\*.py`
- `note\natural_blog_core.py`
- `note\current_mainline_runner.py`
- `note\note_writer_app.py`
  を編集しない
- broad test run を主目的にしない
- hidden reviser accretion を持ち込まない
- formatter-only polish に流さない
- giant rewrite を前提にしない
- fixed routing table を追加しない
- `planning default` を再主張しない
- current source-of-truth update をしない

今回やること:
1. current docs / latest artifacts を読み、sentence-final monotony 症状を確認する
2. symptom を
   - detector problem
   - telemetry visibility problem
   - repair trigger problem
   - repair acceptance / scope problem
   に分けて整理する
3. narrow owner candidate を列挙する
   - 例:
     - `simple_note_pipeline\quality_guard.py`
     - `simple_note_pipeline\pipeline.py`
     - `simple_note_pipeline\prompt_builder.py`
   - ただしこの段階では候補整理だけに留める
4. 各 candidate ごとに
   - なぜその owner なのか
   - detector / telemetry / repair のどこを担当するのか
   - rollback 単位を 1 file に閉じられるか
   を書く
5. next main candidate の first-step proposal を docs にまとめる
   - 実装 prompt ではなく triage / planning note としてまとめる

do not:
- `article-type fixed routing table`
- `planning / skeleton default` の再主張
- `prompt-only winner` の断定
- `formatter-only surface polish`
- `input_contract only` で直そうとすること
- `first section history clamp`
- unsupported slot を generic filler で埋めること
- UI / prompt に曖昧 role label を戻すこと
- hidden reviser accretion
- mock path pass を visible improvement の代わりに使うこと
- `reference realization policy` を今回の main line へ戻すこと

touched files の許可範囲:
- 初手は docs のみ
- 許可:
  - `C:\tetie\notecode\docs\*.md`
- 非許可:
  - production code
  - tests
  - AGENTS
  - WORKLOG
  - current planning package docs

期待する成果物:
- planning / triage note 1本
- 必要なら補助 memo 1本まで
- 内容は少なくとも次を含む:
  - current symptom summary
  - owner candidate shortlist
  - detector / telemetry / repair scope split
  - first production owner candidate
  - なぜ `reference realization policy` を今回 main line にしないか
  - `GO_TO_IMPLEMENT` または `NEEDS_MORE_TRIAGE`

推奨出力ファイル:
- `C:\tetie\notecode\docs\separate_window_sentence_final_monotony_triage_note_2026-04-17.md`

停止条件:
- production code を読まないと owner 候補すら立てられない状態になった
- docs-only の範囲で前進できなくなった
- compare / planning ではなく実装に入りたくなった
- formatter / route default / reference realization policy に論点が逸れ始めた
- 1 file owner に閉じる見込みが立たない
- visible symptom ではなく metrics の数値合わせに流れ始めた

最終報告で必ず示すこと:
1. 読んだ参照ルールファイル
2. 読んだ artifact
3. 日本語 blog runtime を変更していないこと
4. 追加した docs
5. sentence-final monotony の current symptom summary
6. detector / telemetry / repair scope の切り分け結果
7. narrow owner candidate shortlist
8. first production owner candidate とその理由
9. `GO_TO_IMPLEMENT` か `NEEDS_MORE_TRIAGE` か
10. `reference realization policy` を今回 main line にしなかった理由
11. AGENTS / WORKLOG 更新不要であること
```

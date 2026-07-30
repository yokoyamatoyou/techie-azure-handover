# Kotomegane UI/UX Refactor Plan 2026-05-23

## Purpose

この文書は、2026-05-23 の非エンジニア視点 UI/UX 診断を、別ウィンドウで小さく実装できる refactor plan に落とすための正本です。

目的は、`コトメガネ` を機械商社の企画部・入社3年目の非エンジニアが、初見で次を迷わず行える状態へ寄せることです。

1. 1回だけ確認する
2. 複数質問をまとめて確認する
3. 曜日を決めて自動チェックを設定する
4. 今回の結果と保存済み/定期の履歴を混同せず読む

この計画は、実装順・停止条件・検証条件を細かく切るためのものです。

## Source Inputs

- UI/UX診断 issue IDs:
  - `IN-01` ... `IN-06`
  - `SP-01` ... `SP-03`
  - `MQ-01` ... `MQ-03`
  - `QS-01` ... `QS-04`
  - `SC-01` ... `SC-04`
  - `RS-01` ... `RS-03`
  - `TR-01` ... `TR-03`
  - `TX-01` ... `TX-03`
  - `VH-01` ... `VH-03`
  - `MB-01` ... `MB-04`
  - `ST-01` ... `ST-03`
  - `OT-01` ... `OT-03`
- Current weekday/schedule behavior:
  - `docs/SCHEDULE_UI_CHANGE_2026-05-23.md`
- Current state:
  - `docs/CURRENT_STATE_2026-03-30.md`
- Algorithm/runtime responsibility:
  - `ALGORITHM.md`

## Fixed Constraints

- Do not change DB schema.
- Do not change provider request payload, query planning, scoring, batch import, scheduler dispatch logic, or billing rules unless a later window explicitly reopens that owner.
- Do not execute OpenAI/API/LLM/provider batch during UI refactor verification.
- Do not change Azure deployment in these implementation windows.
- Keep `techie-hub` shared top shell recognizable.
- Keep existing warm TECHIE palette, but strengthen semantic grouping where it improves comprehension.
- Prefer label, layout, grouping, responsive CSS, and read-model display changes before deeper data-model work.
- One implementation window should handle one owner package only.

## Product Vocabulary Decisions

The current UI overuses `定期分析`. Future UI copy should separate user intent:

| User intent | Preferred UI term | Avoid as main label |
|-------------|-------------------|---------------------|
| Single current input check | `1回だけ確認` / `1回だけ分析` | `手動スポット確認` |
| Multi-question immediate batch | `まとめて分析` / `複数質問をまとめて確認` | `定期分析を実行` |
| Scheduled recurring run | `自動チェック` / `曜日を決めて自動分析` | `自動定期分析` alone |
| Trend chart | `自動チェックの推移` | `定期分析の推移` without context |
| All past runs | `全実行履歴` | `履歴` alone |
| Batch import | `結果反映` | `取込` / `取り込み` |

## Core Information Architecture

The UI should visibly separate four data states:

1. `今の入力`
   - User is editing this now.
   - It may not be saved.
   - It may not have results.
2. `保存済みの確認内容`
   - Reusable condition set.
   - Scheduled runs can only use this saved object.
   - It should show question count and representative question text.
3. `今回の結果`
   - Results from the current run in this browser/session/input context.
   - If not run yet, it must remain clearly empty.
4. `保存済みの結果・履歴`
   - Past DB rows, batch jobs, scheduled runs, and trends.
   - It must not visually look like the current unrun input already has results.

## Severity Policy

- `P0`: mobile/responsive breakage that prevents reading or operation.
- `P1`: likely task failure or wrong action by a non-engineer.
- `P2`: confusion, hesitation, or incorrect interpretation, but recoverable.
- `P3`: polish, terminology cleanup, or reporting clarity.

## Owner Package Map

### O-00 Baseline And Evidence Owner

Goal:
- Capture current behavior before changing UI.

Issues:
- all IDs as reference only.

Allowed work:
- Read files.
- Start local app.
- Browser screenshots at desktop and mobile.
- No code edits except writing verification artifacts if explicitly requested.

Suggested checks:
- `http://127.0.0.1:8083/healthz`
- desktop viewport around `1365x768`
- mobile viewport around `390x844`
- record visible labels for first view, settings tab, schedule section, result section.

Acceptance:
- A short before-state artifact or notes exist.
- No API/LLM/provider submit.
- No DB/schema write except normal app read access.

### O-01 Copy And Label Cleanup Owner

Goal:
- Fix labels that make the user predict the wrong action.

Issues:
- `SP-01`, `SP-02`, `IN-02`, `IN-03`, `IN-04`, `IN-06`, `TX-02`, `TX-03`, `QS-02`, `QS-03`, `OT-02`, `OT-03`, partial `ST-01`.

Candidate changes:
- `定期分析を実行` -> `まとめて分析の画面を開く`
- `自動定期分析を設定` -> `曜日を決めて自動分析`
- `追加分を減らす` -> `追加質問を1件減らす`
- If multiple questions are visible, consider changing `1回だけ分析` helper text to clarify that it means one run, not one question:
  - `この3質問を今回だけ分析します`
- Add short field helpers:
  - `名称`: `自社名やサービス名の揺れを見つけるために使います`
  - `重点テーマ`: `業界・用途・地域の照合に使います`
- `全国 を反映` -> `重点テーマに「全国」を追加`
- `介護 を反映` -> `重点テーマに「介護」を追加`
- `手動スポット確認` -> `1回だけ確認`
- `取り込み` / `取込` -> `結果反映`
- `保存 / 更新` dynamic:
  - no selected saved condition: `今の入力を新規保存`
  - selected saved condition: `選択中の確認内容を更新`
- `入力内容を保持` -> `画面の入力だけ保持`
- `最終更新` -> `最後に結果を保存`
- `前回比` -> `前回の自動チェックとの差` if the metric actually maps to scheduled series; otherwise use `前回の保存結果との差`.

Candidate files:
- `app.py`
- `ui/runtime_copy_builders.py`
- `ui/input_config_builders.py`
- `ui/admin_views.py`
- `ui/dashboard_views.py`
- `ui/detail_views.py`
- `ui/page_refreshers.py`

Do not:
- Change button actions.
- Change run/session behavior.
- Change data saved to DB.

Verification:
- `py_compile` for touched Python files.
- `import app`.
- Browser check that first view labels no longer imply external send when the action only opens settings.
- Browser check that no label is clipped on desktop.

Acceptance:
- User can distinguish `open settings` from `send to AI`.
- Internal terms `取込` and `手動スポット確認` are no longer primary user-facing labels.

### O-02 Mobile P0 Layout Owner

Goal:
- Make mobile readable and operable before deeper design work.

Issues:
- `MB-01`, `MB-02`, `MB-03`, `MB-04`, `TR-03`.

Candidate changes:
- Remove or override mobile `min-width` that makes input controls overflow.
- Force settings controls and expansion cards into one column below tablet width.
- Prevent buttons from vertical-letter wrapping.
- Hide Plotly toolbar for user-facing charts or at least for mobile.
- For empty trend states on mobile, show a text card before mounting Plotly.
- Reduce top nav vertical footprint on mobile without changing shared brand identity.

Candidate files:
- `ui/styles.py`
- `app.py`
- `ui/charts.py`
- `ui/dashboard_views.py`
- `ui/detail_views.py`
- `ui/admin_views.py`

Do not:
- Redesign desktop layout in the same window unless required by shared CSS.
- Change data/charts calculation.
- Remove chart functionality for desktop.

Verification:
- Browser mobile viewport around `390x844`.
- No horizontal overflow.
- Input fields are full-width and readable.
- Settings tab buttons are horizontal text, not vertical-character columns.
- Desktop still renders correctly.

Acceptance:
- A non-engineer can read labels and enter text on mobile.
- No element requires horizontal scrolling for ordinary form use.

### O-03 Current Input Vs Saved Condition Boundary Owner

Goal:
- Make it obvious that current form input and saved reusable condition sets are different.

Issues:
- `IN-01`, `QS-01`, `QS-02`, `QS-03`, `MQ-01`, partial `RS-01`.

Candidate changes:
- Add a compact `今の入力` section label around the top input card.
- Add a separate `保存済みの確認内容` area in settings.
- Split actions:
  - `今の入力を保存`
  - `保存済みを読み込む`
  - `選択中の確認内容を更新`
- In saved condition select/table, show:
  - condition name
  - question count
  - provider
  - last run date
  - first question preview
- If initial config has 3 questions, make the UI explain that these are current input examples or loaded current config, not automatically a saved scheduled target.

Candidate files:
- `app.py`
- `ui/admin_views.py`
- `ui/page_refreshers.py`
- `ui/input_config_builders.py`
- `storage.py` read helpers only if question count is not available from existing config JSON.

Do not:
- Add new table columns.
- Change `question_set.config_json` format.
- Change how schedule references question sets.

Verification:
- Open settings with 3 current questions.
- Confirm the selected schedule target is visibly a saved condition, not the live input form.
- Confirm question count appears without relying on the saved name containing `3質問`.

Acceptance:
- User can answer: "Do I need to save this input before using it for automatic checks?" from the screen.

### O-04 Scheduled Check Simplification Owner

Goal:
- Make schedule setup feel like `choose saved condition -> choose weekdays/time -> save`.

Issues:
- `SC-01`, `SC-02`, `SC-03`, `SC-04`, `TX-01`, partial `ST-01`.

Candidate changes:
- Change section title from `定期分析｜自動で継続（スケジュール）` to `曜日を決めて自動チェック`.
- Change `対象の確認内容` helper to `自動チェックは保存済みの確認内容から選びます`.
- Make `週あたり回数` read-only display or remove editable input from primary UI.
- Add computed text:
  - `選択中: 月・水・金 / 週3回`
  - `保存後は 09:00 から自動チェックします`
- Add schedule-name hint:
  - `空欄なら確認内容名から自動で名前を付けます`
- Separate statuses:
  - `システム監視: 稼働中`
  - `この設定: 有効`
- Change switch helper:
  - `ON: 次回時刻から自動実行`
  - `OFF: 保存だけして実行しない`

Candidate files:
- `app.py`
- `ui/admin_views.py`
- `ui/page_refreshers.py`
- `analysis_core/schedule.py` only if display formatting helper is needed.

Do not:
- Change `weekly_run_count` persistence semantics.
- Change scheduler due calculation.
- Change `enabled` behavior.

Verification:
- Select multiple weekdays.
- Confirm week count display updates or save result still reflects selected weekday count.
- Confirm no editable `週あたり回数` confusion remains in primary path.
- Confirm schedule save still works in local UI if this window is allowed to save test rows; otherwise validate through component state and existing unit/smoke checks only.

Acceptance:
- User can set a Monday/Wednesday/Friday automatic check without knowing what `weekly_run_count` means.

### O-05 Run Action Safety And State Boundary Owner

Goal:
- Make buttons that send externally or mutate local result state explicit enough to prevent accidental action.

Issues:
- `SP-03`, `ST-01`, `ST-02`, `ST-03`.

Candidate changes:
- Add short helper under `1回だけ分析`:
  - `このボタンで対象AIへ質問を送信します`
- Add helper under `まとめて分析` submit:
  - `保存済みの確認内容を対象AIへまとめて送信します`
- Change `結果を反映` helper:
  - `完了した外部AI結果をこの画面へ反映します`
- Change batch state summary to include:
  - schedule or condition name
  - run time
  - provider
  - target question count
- Add empty-state hint:
  - `今の入力ではまだ分析していません。これはエラーではありません。`

Candidate files:
- `app.py`
- `ui/page_refreshers.py`
- `ui/runtime_copy_builders.py`
- `ui/admin_views.py`
- `ui/result_cards.py`

Do not:
- Add modal confirmation in this first owner unless explicitly requested.
- Change provider submission code.

Verification:
- Browser check that send/mutate actions are visually distinguishable from navigation/open actions.
- Ensure helper copy does not create text overflow.

Acceptance:
- User can predict which buttons send to external AI and which only open a screen.

### O-06 Current Result Vs Saved History Separation Owner

Goal:
- Prevent "未実行なのに結果がある" confusion.

Issues:
- `RS-01`, `RS-02`, `TR-01`, `TR-02`, `OT-01`.

Candidate changes:
- Make `今回の結果` empty state visually standalone.
- Move or strongly separate `保存済みの累積傾向`.
- Rename history/table areas:
  - `保存済みの結果`
  - `全実行履歴`
  - `自動チェックの推移`
- Add context line to saved detail:
  - `この詳細は保存済み結果です: 2026-.. / 質問 / 自社URL / 対象AI`
- Add provider column or chip in visible saved rows if already available.
- If trend graph has no graphable rows but history exists, state:
  - `履歴はありますが、グラフ化できる自動チェック結果はまだありません`

Candidate files:
- `ui/result_cards.py`
- `ui/dashboard_views.py`
- `ui/dashboard_refreshers.py`
- `ui/dashboard_view_models.py`
- `ui/detail_views.py`
- `ui/charts.py`

Do not:
- Change which rows are included in graph calculations.
- Merge manual rows into scheduled trend.

Verification:
- Fresh/unrun input shows no current result.
- Saved results are still reachable but clearly labeled as saved history.
- Trend empty state explains why no chart appears.

Acceptance:
- User can distinguish current unrun input from past saved conclusions.

### O-07 Multiple Question Results Owner

Goal:
- Make multi-question result exploration readable as `question set -> question -> detail`.

Issues:
- `MQ-02`, `MQ-03`, `RS-03`, partial `MQ-01`.

Candidate changes:
- Replace `詳細を見る質問` with `下に表示する質問を選ぶ`.
- Add three stacked labels:
  - `質問一覧`
  - `下に表示する質問を選ぶ`
  - `選択中の質問の詳細`
- Show selected question text above detail card.
- Show target counts separately:
  - `対象質問 3件`
  - `実送信 15件`
  - `結果反映 15件`
- Add action labels to URL states:
  - `優先して見る`
  - `参考程度`
  - `確認が必要`

Candidate files:
- `ui/detail_views.py`
- `ui/result_cards.py`
- `ui/dashboard_views.py`
- `ui/evidence_presenters.py`
- `ui/page_refreshers.py`
- `analysis_core/metrics.py` only if existing result rows lack count summaries and helper can stay read-only.

Do not:
- Change scoring, citation classification, or URL extraction.
- Add new DB fields.

Verification:
- With multiple saved questions, confirm the user can see which question controls the detail below.
- Confirm long question text wraps without overlap.

Acceptance:
- User can explain which question's detail is currently displayed.

### O-08 Visual Grouping And Semantic Surface Owner

Goal:
- Strengthen grouping without a broad redesign.

Issues:
- `VH-01`, `VH-02`, `VH-03`, partial `IN-05`.

Candidate changes:
- Shorten detail expansion header:
  - `詳細と設定を開く`
- Keep tabs visible after expansion, but reduce header burden.
- Use semantic panel labels and subtle backgrounds:
  - input: white
  - current result: very light blue or neutral highlight
  - saved/history: light gray/cream with clear label
  - automatic schedule: light orange accent, not dominant
- Make hero links visibly clickable if retained.
- Move result-reading explanation out of input examples.

Candidate files:
- `ui/styles.py`
- `app.py`
- `ui/result_cards.py`
- `ui/detail_views.py`
- `ui/dashboard_views.py`

Do not:
- Introduce a new palette that conflicts with TECHIE warm suite.
- Create card-inside-card nesting.
- Add marketing-style hero.

Verification:
- Desktop and mobile visual scan.
- Text remains readable and non-overlapping.
- User-facing sections are visually separable without relying on long prose.

Acceptance:
- First view clearly shows where to type, where to run, and where results begin.

### O-09 Final QA And Documentation Owner

Goal:
- Verify that the refactor remains narrow and update docs after implementation phases.

Issues:
- all touched issues.

Required checks:
- `.\.venv\Scripts\python.exe -m py_compile ...` for touched Python files.
- `.\.venv\Scripts\python.exe -c "import app; print('IMPORT_OK')"`
- `.\.venv\Scripts\python.exe -m unittest tests.test_security_hardening`
- `http://127.0.0.1:8083/healthz`
- Browser desktop check.
- Browser mobile check around `390x844`.
- No API/LLM/provider submit unless user explicitly approves a live validation window.

Docs to update after implementation:
- `README.md`
- `docs/CURRENT_STATE_2026-03-30.md`
- `WORKLOG.md`
- `ALGORITHM.md` only if execution flow or responsibility changes.
- `docs/DOC_STATUS.md` only if a new source-of-truth doc is added.

Acceptance:
- The implementation report lists changed files, checks run, and unresolved issues.
- No hidden DB/schema/API change is introduced.

## Recommended Execution Order

### Window 1: O-01 + O-02 Minimal

Reason:
- It fixes the easiest high-confidence confusion and the mobile P0 breakage.

Scope:
- Label cleanup.
- Mobile overflow/vertical-label fixes.
- No structural data changes.

Stop before:
- Reworking saved condition cards.
- Reworking schedule semantics.
- Reworking result details.

### Window 2: O-03

Reason:
- Once mobile and labels are stable, separate `今の入力` from `保存済みの確認内容`.

Scope:
- Grouping and labels around saved conditions.
- Question count display if possible from existing JSON.

Stop before:
- Changing schedule calculation.
- Changing result details.

### Window 3: O-04

Reason:
- Schedule setup is the highest business-priority workflow after question-set clarity.

Scope:
- Read-only week count display.
- Weekday-derived helper text.
- System vs setting status split.

Stop before:
- Provider submit logic.
- Scheduler due calculation.

### Window 4: O-05 + O-06

Reason:
- Result state and action safety are linked: users need to know what sends, what reflects, and what is saved history.

Scope:
- Helper text for external-send actions.
- Empty-state and saved-history separation.
- Trend/history labeling.

Stop before:
- Multiple-question detail redesign.

### Window 5: O-07

Reason:
- Multiple-question result exploration is a distinct component and should not be mixed with schedule setup.

Scope:
- Question list/select/detail labeling.
- Count label cleanup.
- URL action label addition if it stays display-only.

Stop before:
- New aggregation algorithms.
- New DB fields.

### Window 6: O-08

Reason:
- Visual grouping should come after wording and state boundaries are stable.

Scope:
- Section backgrounds, spacing, expansion header simplification.
- Keep brand shell stable.

Stop before:
- Broad redesign.

### Window 7: O-09

Reason:
- Final QA and docs sync should be its own closeout owner after implementation windows.

Scope:
- Full desktop/mobile pass.
- Docs alignment.
- Worklog closeout.

## Work Window Prompt Template

Use this template when the instruction window creates a new implementation window:

```text
cwd は C:\tetie\kotomegane。

最初に読む:
1. C:\tetie\AGENTS.md
2. C:\tetie\kotomegane\AGENTS.md
3. docs\UI_UX_REFACTOR_PLAN_2026-05-23.md
4. docs\CURRENT_STATE_2026-03-30.md の UI 関連
5. README.md の UI / schedule / result 関連

今回の owner:
[ここに O-01 などを1つだけ書く]

目的:
[owner の Goal を貼る]

対象 issue:
[owner の issue ID を貼る]

禁止:
- DB schema変更
- API/LLM/provider batch投入
- Azure作業
- 別 owner の先回り
- ついでの広範囲リファクタ

やること:
[owner の Candidate changes から今回扱う小タスクだけ貼る]

検証:
[owner の Verification を貼る]

完了報告:
- 変更ファイル
- 変更した user-facing 文言/表示
- 検証コマンドと結果
- desktop/mobile 確認結果
- 未対応 issue
- AGENTS/WORKLOG更新の要否
```

## Stop Conditions

Any implementation window must stop and report if:

- A requested UI improvement requires DB schema change.
- The change would require provider/API/LLM execution to validate.
- The owner scope starts touching two or more independent areas.
- The app cannot start or `/healthz` fails after the change.
- Mobile fix requires rewriting the top shell shared by other TECHIE services.
- A change would alter saved result interpretation, scoring, or scheduled dispatch semantics.

## Plan Acceptance Criteria

This plan is ready for instruction-window use when:

- Every reported issue ID is assigned to an owner package.
- Each owner has allowed changes, candidate files, explicit non-goals, verification, and acceptance criteria.
- The first recommended implementation window is narrow enough to finish and verify independently.
- Documentation update expectations are clear.

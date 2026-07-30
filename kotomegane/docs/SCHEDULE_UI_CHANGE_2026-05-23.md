# Schedule UI Change 2026-05-23

## Scope

This note documents the 2026-05-23 change to `定期分析｜自動で継続（スケジュール）`.

It covers the Kotomegane schedule UI, save behavior, and the same-day run guardrail clarification for three-question runs. It does not change query planning, DB schema, scheduler polling, graph aggregation, or provider result import.

## User-Facing Behavior

- A saved `確認内容` can contain multiple questions.
- One `定期分析` schedule points to one saved `確認内容`.
- Therefore, one schedule is not limited to one question. It runs the questions saved inside the selected `確認内容`.
- Multiple schedules can be registered by using different schedule names, even if they point to the same `確認内容`.
- If the same `確認内容` and same schedule name are saved again, the existing schedule is updated instead of creating a new row.

## Previous Behavior

Before this change, weekday selection used a dropdown-style select for `曜日`.

The intended data model already supported multiple weekdays because `schedule_plan.weekdays_csv` stores a comma-separated weekday list. The problem was the UI and save path:

- The dropdown list could appear, but the selected weekday was hard to confirm through normal browser interaction in the verified local UI.
- Even when multiple weekdays were expected, `週あたり回数` could remain `1`.
- `normalize_schedule_weekdays(...)` keeps only the first `weekly_run_count` weekdays after sorting and de-duplicating.
- As a result, selecting multiple weekdays while `週あたり回数 = 1` could save only the first weekday.

So the issue was not "one schedule can only have one question." The issue was "multiple weekdays were difficult to register reliably."

The old UI was intended to allow selection, so it is not correct to say the code deliberately forbade weekday selection. However, in the actual browser verification, normal click/keyboard operation did not produce a reliable completed selection. From an operator perspective, it was effectively not usable enough.

## Old UI Probe Result

The old widget was reproduced in isolation using the same NiceGUI call shape:

```python
ui.select(
    {0: "月", 1: "火", 2: "水", 3: "木", 4: "金", 5: "土", 6: "日"},
    value=[0],
    label="曜日",
).props("multiple outlined use-chips")
```

Observed browser-operation results:

```text
initial:
  raw=[0]; weekly=1; saved=[0]

after clicking 火:
  raw=[0]; weekly=1; saved=[0]

after setting weekly=2:
  raw=[0]; weekly=2; saved=[0]

after clicking 月 again:
  raw=[0]; weekly=2; saved=[0]

after clicking 火 again:
  raw=[0]; weekly=2; saved=[0]

after Backspace/Delete:
  raw=[0]; weekly=1; saved=[0]
```

This means the old UI shape was effectively Monday-fixed in the verified environment, even though the intended widget configuration was a multiple weekday selector.

## Current Behavior

The weekday UI now uses visible checkboxes for `月 / 火 / 水 / 木 / 金 / 土 / 日`.

Save behavior now treats selected weekdays as the source of truth:

- The app reads all checked weekdays.
- The app raises `週あたり回数` to at least the number of selected weekdays.
- The effective value saved to `schedule_plan.weekdays_csv` is the selected weekday list.
- The effective value saved to `schedule_plan.weekly_run_count` is the selected weekday count.

Example:

```text
Selected weekdays: 月 / 水 / 金
UI weekly run value before save: 1
Saved weekdays_csv: 0,2,4
Saved weekly_run_count: 3
```

## Verified UI Registrations

The following schedules were registered through the UI after the fix:

```text
UI操作確認 A 月水金 2026-05-23
  weekdays: 月 / 水 / 金
  time: 09:00
  weekly_run_count: 3

UI操作確認 B 火木 2026-05-23
  weekdays: 火 / 木
  time: 13:00
  weekly_run_count: 2

UI操作確認 C 土日 2026-05-23
  weekdays: 土 / 日
  time: 10:00
  weekly_run_count: 2
```

The shared question set used for this verification was:

```text
定期分析UI確認 3質問 2026-05-23
```

It contained three questions. This confirms that schedule registration can target a multi-question saved condition.

## Three-Question Immediate Run Note

During the first UI verification, the three-question `今すぐ実行` check stopped before provider batch submission because the run guardrail estimated that the actual request count would exceed the per-run limit.

Observed UI message:

```text
実際の送信件数で見積もると 1 回の実行上限を超える見込みのため、投入を止めました。
```

This was a run guardrail result, not a schedule-registration failure.

The same-day follow-up changed the run guardrail behavior to match the existing default configuration:

- `budget_guardrail_mode=warn`: do not stop manual, immediate batch, or scheduled batch just because `run_budget_guardrail_usd` is exceeded. Show/record a warning and continue.
- `budget_guardrail_mode=stop`: stop before provider submission when the per-run estimate exceeds `run_budget_guardrail_usd`.

This means a three-question saved condition can be registered, scheduled, and submitted in the default warning mode. If an operator explicitly switches the guardrail mode to `stop`, the same estimate can still block the run before provider submission.

## Graph Reflection

Schedule and batch results flow into the same saved result path after provider batch submission and import complete.

The `定期分析の推移` tab intentionally uses completed scheduled/batch results for the main trend charts. A run that is stopped by guardrail before provider batch submission does not create new result rows and therefore does not add a graph point.

In the default `warn` mode, a run that exceeds the internal per-run estimate is still submitted. It adds graph points after provider completion and result import, just like other scheduled/batch runs.

## Code References

- `app.py`
  - `WeekdayCheckboxGroup`: visible weekday checkbox state wrapper
  - `on_schedule_save`: selected weekday count is reflected into `weekly_run_count`
  - schedule UI block: weekday dropdown replaced by seven checkboxes
- `analysis_core/schedule.py`
  - `normalize_schedule_weekdays(...)`: sorts, de-duplicates, and caps weekdays by `weekly_run_count`
- `storage.py`
  - `question_set.config_json`: stores the saved condition, including `keywords`
  - `schedule_plan.question_set_id`: schedule points to the saved question set
  - `schedule_plan.weekdays_csv` / `weekly_run_count`: persisted schedule cadence

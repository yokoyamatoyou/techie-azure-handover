# PROGRESS

## Status

Completed on 2026-04-26 JST.

## Narrow Hypothesis

Announcement runtime source contract availability was too strict and did not activate from fallback source text. Because the FAQ facts never entered `source_grounding_items` / `must_cover`, the model picked up the main change facts but often omitted preparation and day-of checklist facts.

## Changes

Product changes:

- `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `source_pack["grounding_items"][*]["fact_text"]` is now available to announcement fallback source sentence extraction.
  - Announcement fallback slot filling now scores candidate sentences per slot and prefers more specific action/checklist facts.
  - `source_contract_available` can become true when required announcement slots are discoverable from fallback source sentences.
  - Activated announcement slot facts are merged into `must_cover` as bounded labeled facts.

Tests:

- `C:\tetie\notecode\note\tests\test_simple_note_pipeline.py`
  - `test_announcement_runtime_source_contract_activates_from_fallback_source_text`
  - `test_announcement_runtime_source_contract_fallback_does_not_touch_non_announcement`

## FAQ Fact Coverage

| Fact | source_grounding_items | must_cover | UI attempt 1 body | UI attempt 2 body |
|---|---:|---:|---:|---:|
| `承認者の再設定` | yes | yes | yes | yes |
| `通知先の確認` | yes | yes | yes | yes |
| `下書き保存` | yes | yes | yes | yes |
| `差し戻し通知` | yes | yes | yes | yes |
| `公開日時の再指定` | yes | yes | yes | yes |

## UI Rerun

Artifact:

- `C:\tetie\notecode\logs\current_mainline_announcement_source_contract_activation_20260426-103445\`

Results:

| Attempt | outcome | runtime_reason_code | article_type | semantic_article_key | body_chars | blocked | redacted | internal leakage |
|---:|---|---|---|---|---:|---:|---:|---|
| 1 | `publishable_success` | `OK` | `announcement` | `announcement` | 470 | false | false | none |
| 2 | `publishable_success` | `OK` | `announcement` | `announcement` | 378 | false | false | none |

Notes:

- The expected minimum was `review_required_draft` or better. Both attempts reached `publishable_success`.
- Success was not forced through threshold, UI demote, prompt, or repair-count changes.
- Existing fingerprint/style warnings remain soft warnings and were not changed by this package.

## Validation Commands

Focused pre-fix reproduction:

```powershell
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q -k "announcement_runtime_source_contract_activates_from_fallback_source_text or announcement_runtime_source_contract_fallback_does_not_touch_non_announcement"
```

Initial result:

- `test_announcement_runtime_source_contract_activates_from_fallback_source_text` failed with missing `source_grounding_items`.
- Non-announcement control passed.

Focused post-fix:

```powershell
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py -q -k "announcement_runtime_source_contract_activates_from_fallback_source_text or announcement_runtime_source_contract_fallback_does_not_touch_non_announcement or announcement_runtime_source_contract_adds_base_pattern_without_fixed_route"
```

Result:

- `3 passed, 237 deselected`

Required owner tests:

```powershell
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_simple_note_pipeline.py note\tests\test_simple_note_quality_guard.py -q
```

Result:

- `262 passed`

Shared regression:

```powershell
C:\tetie\notecode\.venv\Scripts\python.exe -m pytest note\tests\test_current_mainline_runner.py note\tests\test_current_mainline_regressions.py note\tests\test_current_mainline_ui_matrix.py -q
```

Result:

- `144 passed`

## Out of Scope

The diagnosis package showed the prior `input_required_block` label was a validation script / harness classification issue caused by mapping `blocked_output_redacted=True` to `input_required_block`. This package does not modify that validation script, UI demotion, or app classification.

Remaining issue buckets from the post-full-flow triage stay separate:

- non-company branding route mismatch / body 0
- comparative_review UI harness failure
- explanatory_article regression candidate
- product_introduction source caveat
- daily_story synthetic source caveat

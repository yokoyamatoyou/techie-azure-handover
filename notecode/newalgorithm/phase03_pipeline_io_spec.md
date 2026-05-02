# Phase03 Pipeline I/O Spec

## Step I/O

- `contract_resolve`
  - in: `payload`
  - out: `contract` (`article_type`, `media`, `source_inputs`, `topic`, normalized system-owned fields)
- `discourse_plan`
  - in: `contract`
  - out: `sections[]` (`heading`, `objective`)
- `section_generation`
  - in: `sections[]`, `topic`, `media`, `contract`
  - out: `body`, `retries`, `fallback_used`, `warnings[]`
- `dedupe`
  - in: `body`, `contract`
  - out: `deduped_body`, `dedupe_audit`
- `editor_guard`
  - in: `deduped_body`
  - out: `guarded_body`, `editor_report`
- `output_format`
  - in: `guarded_body`, `topic`, `article_type`
  - out: `title`, `lead`, `body`, `references`, `hashtags`, `full_text`
- `telemetry`
  - in: all step outputs
  - out: `pipeline_check`, `audit_record`

## Error I/O
- input validation error
  - out: `success=false`, `reason_code=INP_*`, `pipeline_check.error`
- runtime error
  - out: `success=false`, `reason_code=SYS_PIPELINE_FAILURE`, `pipeline_check.error`


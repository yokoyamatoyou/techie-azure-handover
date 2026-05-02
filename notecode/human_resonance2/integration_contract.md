# Integration Contract (human_resonance2 -> note generator)

## Objective
Define safe integration boundaries with existing pipeline.

## Non-Goals
- Do not replace existing `human_resonance` phases immediately.
- Do not hard-switch behavior in one release.

## Integration Point
Use one call point near final text assembly in `note/article_generator.py`:
- input: lead/body/references and policy context
- output: optionally polished lead/body plus phase reports

## Data Contract
### Input
```json
{
  "lead": "string",
  "body": "string",
  "references": "string",
  "article_type": "string",
  "target_audience": "string",
  "config": {}
}
```

### Output
```json
{
  "lead": "string",
  "body": "string",
  "phase_reports": [],
  "applied": ["phase01", "phase02"],
  "errors": []
}
```

## Safety Contract
1. If any phase fails, follow fail-open behavior unless explicitly configured otherwise.
2. Never drop headings silently.
3. Never add unsupported facts/numbers/proper nouns.
4. Keep rewrite ratio below configured cap.

## Rollback Contract
1. `quality_pipeline.enabled=false` disables all new behavior.
2. Feature flags are phase-level and reversible independently.


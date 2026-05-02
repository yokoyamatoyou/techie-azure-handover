# Phase03 Minimal Pipeline Flow

## Flow Diagram

```mermaid
flowchart TD
    inputPayload["UI/API Payload"]
    contractResolve["contractResolve(input_contract_v1)"]
    discoursePlan["discoursePlan(article_type/media)"]
    sectionGen["sectionGeneration(LLM with retry)"]
    dedupe["semanticDedupe(adapter)"]
    editorGuard["minimalEditorGuard(legal/ai_noise)"]
    outputFormat["outputFormat(title/body/full_text)"]
    telemetry["telemetryWriter(audit/pipeline_check)"]
    outputResult["Result"]
    inputError["InputError(reason_code)"]

    inputPayload --> contractResolve
    contractResolve -->|"valid"| discoursePlan
    contractResolve -->|"invalid"| inputError
    discoursePlan --> sectionGen
    sectionGen --> dedupe
    dedupe --> editorGuard
    editorGuard --> outputFormat
    outputFormat --> telemetry
    telemetry --> outputResult
```

## Notes
- `daily_story` + `media=seo` は contract resolve で `style_compact_for_seo=true` を自動付与。
- LLM失敗時は retry 後に fallback paragraph を使い、fail-open で出力を継続。
- telemetry は `pipeline_check` と JSONL audit の双方へ記録（保存失敗は fail-open）。


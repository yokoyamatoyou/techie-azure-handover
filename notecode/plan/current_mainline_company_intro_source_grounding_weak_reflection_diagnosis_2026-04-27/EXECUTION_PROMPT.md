# Execution Prompt

```text
C:\tetie\notecode の company_introduction source_grounding:weak_reflection を 1 owner / 1 narrow hypothesis で実装診断してください。

Mode:
- 新規ウインドウ。
- product code change は必要最小限。
- owner は C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py の source grounding observability に限定する。
- tests は source grounding observability の focused tests のみ追加・更新可。
- prompt / persona / source contract / threshold / repair count / quality_guard / output_guard / pipeline / blog_image_auto は変更しない。
- source_grounding threshold を緩和しない。
- weak_reflection を warning success 化しない。
- self-perspective consumption 修正に進まない。
- repair rejection 修正に進まない。

Artifact:
C:\tetie\notecode\logs\article_type_self_perspective_quality_validation_record_continue_rerun_20260427-085139\

Diagnosis:
- company_introduction 3/3 review_required_draft。
- source_grounding ratios: attempt1 0.2, attempt2 0.4, attempt3 0.4。
- company_introduction_source_contract_validation は 3/3 required 5 slots present, strong, no trigger ids。
- visible body reflects current_business / entry point / support scope / process / pre-contact decision semantically.
- weak_reflection appears caused by long composite/title-like anchor groups, not by true missing required slots.
- repair_required/rejected is secondary; do not fix repair acceptance in this window.

Hypothesis:
- source grounding anchor extraction/grouping for company_introduction overweights composite source excerpts and title/URL-like fragments. Narrowly improve observability so reflected company-introduction operational slots are measured by atomic, reader-visible anchors instead of long composite chunks.

Acceptance:
- Existing thresholds remain unchanged.
- No source outside claim weakening.
- No prompt accretion.
- No repair count or repair acceptance changes.
- Focused tests show composite/title-like company-introduction anchor mismatch no longer creates false weak_reflection, while true missing source reflection still warns.
```

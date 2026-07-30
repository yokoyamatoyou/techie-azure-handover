# current_mainline_bloat_control_priority_2026-04-26 TASK

This package is docs-only. It fixes priority and handoff order for current mainline bloat control without modifying product code.

## Global Rules

- product code change禁止
- split implementation禁止
- prompt / threshold / repair / guard / UI implementation change禁止
- full-flow residual closeout and split workを混ぜない
- current success path維持:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- `1 package = 1 owner scope`
- behavior-preserving extraction first
- extraction and function fixを同時にしない
- AGENTSは routing 変更がない限り更新しない

## Phase Map

| Phase | Scope | Gate |
|---|---|---|
| Phase 0 | package scaffold | README / TASK / PROGRESS / ROLLBACK / EXECUTION_PROMPT created |
| Phase 1 | evidence lock | required package progress files and existing split docs reflected |
| Phase 2 | owner bloat inventory | large owners listed with current line counts and priority decision |
| Phase 3 | priority decision | do-now / do-next / follow-up / park fixed |
| Phase 4 | next package prompt | exactly one next execution package selected |
| Phase 5 | closeout | product code hashes recorded, 18080 listener absent, WORKLOG updated |

## Priority Criteria

- SaaS UXに直接影響するか
- 既存計画があるか
- behavior-preserving extractionで済むか
- full-flow安定化を壊すリスク
- owner scopeが1つに閉じるか
- module増加で逆に複雑化しないか

## Required Checks

No pytest is required for this docs-only package.

Required closeout checks:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath `
  C:\tetie\notecode\note\current_mainline_runner.py,`
  C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py,`
  C:\tetie\notecode\note\simple_note_pipeline\pipeline.py,`
  C:\tetie\notecode\note\simple_note_pipeline\quality_guard.py,`
  C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py,`
  C:\tetie\notecode\note\note_writer_app.py,`
  C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py
```

```powershell
netstat -ano | Select-String ':18080.*LISTENING'
```

## Next Package Prompt Policy

- The next execution prompt must select exactly one package.
- It must start with existing artifact review only.
- It must explicitly say the work is not split.
- If product code becomes necessary, it must name the owner and required owner-local tests before editing.
- It must not combine the company-introduction classification closeout with `note_writer_app.py` Phase 04 or `pipeline.py` source contract split.


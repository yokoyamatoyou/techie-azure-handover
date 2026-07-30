# experimental_prompt_stack_mainline_candidate_2026-04-19 ROLLBACK

## Baseline

- current runtime success path:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `-> C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `-> C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- current default route has not been flipped
- `experimental_prompt_stack` remains opt-in by `body_generation_experiment`

## Safe Boundary

- safe rollback boundary is `do not promote default route yet`
- if a slice becomes unstable:
  - keep experiment propagation
  - keep current default route unchanged
  - stop and report rather than widening edits

## Do Not Retry

- `body_generation_experiment` strip behavior
- planner-centered rigid section skeleton
- full-article editor rewrite
- source safety relaxation
- prompt injection defense removal
- broad rewrite of unrelated packages

## Stop And Report Conditions

- same slice self-repair 3 failures
- targeted tests continue to fail after 3 attempts
- owner scope expands beyond the intended slice
- context growth makes the current window unsafe

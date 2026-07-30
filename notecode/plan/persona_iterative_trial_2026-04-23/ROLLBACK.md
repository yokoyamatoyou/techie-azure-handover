# persona_iterative_trial_2026-04-23 ROLLBACK

## 目次
- baseline
- rollback boundary
- do-not-retry

## baseline
- runtime mainline before this initiative remains
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\newalgorithm_pipeline\pipeline.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
- UI default audience remains `一般読者`
- visible output leakage guard remains the existing blocker of internal terms

## rollback boundary
- revert only:
  - `C:\tetie\notecode\note\current_mainline_runner.py`
  - `C:\tetie\notecode\note\current_mainline_persona_trial.py`
  - `C:\tetie\notecode\note\persona_iterative_trial_tooling.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
  - `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py`
  - `C:\tetie\notecode\tools\run_persona_iterative_trial.py`
  - `C:\tetie\notecode\plan\persona_iterative_trial_2026-04-23\`
- do not roll back unrelated current-mainline work
- do not revert user changes outside the owner files above

## do-not-retry
- do not move persona names into visible prompt labels or article text
- do not change product default audience to satisfy trial acceptance
- do not reopen legacy persona owners
- do not expand repair beyond `optional single repair 1回`

# TASK

## Cycle 0: No-Fix Baseline

- Run 2 attempts each for `announcement`, `comparative_review`, and `company_introduction`.
- Save summaries, latest snapshots, screenshots if available, image files, app log excerpt, and product hash snapshot under `00_no_fix_baseline`.
- Review visible body, title, and mainly `with_text` cover copy.

Decision:

- Close out with no fix if all three article types are sufficient.
- If only `company_introduction` is weak, proceed to Fix 1 with `prompt_builder.py` only.
- If all three are weak for the same handoff-consumption reason, proceed to a shared writer-prompt narrow fix.
- If causes differ per article type, stop and propose split work.

## Fix 1

- Owner: `note\simple_note_pipeline\prompt_builder.py`.
- Improve natural consumption of `speaker_profile`, `perspective`, and `self_reference_policy` without forcing repeated first person.
- Rerun py_compile, focused pytest, and 2 attempts/type under `01_fix1`.

## Fix 2

- Run only if Fix 1 remains weak and the same owner / same hypothesis can improve it.
- Rerun py_compile, focused pytest, and 2 attempts/type under `02_fix2`.

## Hard Stop

- UI crash or 8080 listener loss.
- deleted client / deleted slot traceback.
- repeated `blocked_output_redacted=true` that prevents visible review.
- internal term leakage.
- source-outside claim.
- legal or guarantee assertion.
- owner exceeds `prompt_builder.py`.
- prompt_builder-only approach cannot improve the issue.
- Fix 2 does not improve.
- `announcement` or `comparative_review` regresses.


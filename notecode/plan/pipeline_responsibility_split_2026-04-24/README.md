# pipeline_responsibility_split_2026-04-24 README

## Objective

- Split `note/simple_note_pipeline/pipeline.py` into maintainable responsibility slices without changing generation behavior.
- Keep the current success path:
  - `note/current_mainline_runner.py`
  - `note/newalgorithm_pipeline/pipeline.py`
  - `note/simple_note_pipeline/pipeline.py`
- Preserve `single-pass + optional single repair 1回`.

## Scope

- Phase 0 baseline and responsibility map.
- Phase 1 hidden late validation extraction.
- Phase 2 company introduction source contract guard extraction.
- Phase 3 company introduction visible opener guard extraction.
- Phase 4 repair acceptance pure helper / telemetry extraction.
- Phase 5 owner-local regression.
- Phase 6 shared regression.
- Phase 7 investigation only after extraction is green.

## Non-Goals

- No persona design change.
- No quality threshold relaxation.
- No repair count increase.
- No prompt accretion.
- No `prompt_builder.py` / `blog_image_auto.py` growth.
- No persona registry or central persona module.
- No archive / frozen package reopen.

## Source Of Truth

- Current naturalness package remains:
  - `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
- This package is a separate implementation package for responsibility split only.

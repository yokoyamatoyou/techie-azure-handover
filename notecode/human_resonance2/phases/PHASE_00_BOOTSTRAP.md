# PHASE 00: Bootstrap

## Objective
Lock planning contracts and execution conventions before coding.

## Inputs
- Existing architecture and algorithm docs
- `human_resonance2` planning goals

## Outputs
- stable document set for execution
- explicit failure/rollback policy

## Tasks (GPT-5 mini granularity)
1. Create/update `README.md` with scope/rules.
2. Create/update `PROGRESS.md` and set initial status.
3. Create/update `WORKLOG.md` with template and first entry.
4. Define config contract and integration contract.
5. Define metric baseline document.

## DoD
1. All required planning files exist.
2. Each phase file template is ready and consistent.
3. Failure handling rule is explicitly written.

## Test View
1. File presence check.
2. Section completeness check in each document.
3. Cross-reference consistency check (`README` vs `PROGRESS`).

## Rollback
Delete `human_resonance2` docs only. No production code rollback required.

## Failure Handling
1. Attempt one correction.
2. If still inconsistent, stop and report:
   - broken file
   - attempted fix
   - blocking reason


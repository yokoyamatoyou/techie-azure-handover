# current_mainline_bloat_control_priority_2026-04-26 PROGRESS

## Current Status

- Package status: completed / priority refreshed after source-contract extraction smoke
- Current phase: 2026-04-26 next-priority re-evaluation closeout
- Date: 2026-04-26 JST
- Product code change: no
- Prompt / threshold / repair / guard / UI implementation change: no
- Split implementation: no
- Generation rerun: no
- UI server startup: no
- AGENTS update: no
- WORKLOG update: completed

## Inspected Evidence

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\README.md`
- `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\TASK.md`
- `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\PROGRESS.md`
- `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\ROLLBACK.md`
- `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\EXECUTION_PROMPT.md`
- `C:\tetie\notecode\plan\current_mainline_full_flow_acceptance_review_2026-04-26\PROGRESS.md`
- `C:\tetie\notecode\plan\current_mainline_announcement_source_contract_activation_2026-04-26\PROGRESS.md`
- `C:\tetie\notecode\plan\current_mainline_comparative_review_contract_activation_2026-04-26\PROGRESS.md`
- `C:\tetie\notecode\plan\current_mainline_source_grounding_metadata_cleanup_2026-04-26\PROGRESS.md`
- `C:\tetie\notecode\plan\pipeline_responsibility_split_2026-04-24\PROGRESS.md`
- `C:\tetie\notecode\current_mainline_owner_split\OWNER_MAP.md`
- `C:\tetie\WORKLOG.md`

## Owner Bloat Snapshot

Definition counts are all AST function / async function / class definitions, including nested methods.

| Owner | Lines | Definitions | Decision |
|---|---:|---:|---|
| `C:\tetie\notecode\note\simple_note_pipeline\pipeline.py` | `6174` | `180` | park further source-contract extraction after announcement / comparative_review / company_introduction extraction and smoke green |
| `C:\tetie\notecode\note\simple_note_pipeline\company_intro_source_contract.py` | `1111` | `34` | extracted source-contract owner |
| `C:\tetie\notecode\note\simple_note_pipeline\announcement_source_contract.py` | `577` | `20` | extracted source-contract owner |
| `C:\tetie\notecode\note\simple_note_pipeline\comparative_review_source_contract.py` | `751` | `28` | extracted source-contract owner |
| `C:\tetie\notecode\note\note_writer_app.py` | `8352` | `269` | select existing split package Phase 05 next |
| `C:\tetie\notecode\note\newalgorithm_pipeline\quality_observability_mixin.py` | `1273` | `37` | park |
| `C:\tetie\notecode\note\newalgorithm_pipeline\output_guard.py` | `965` | `26` | park |
| `C:\tetie\notecode\note\blog_image_auto.py` | `392` | `12` | park; small post-success image owner |

## Current Symbol Inventory

- `pipeline.py`: `180` definitions.
- `note_writer_app.py`: `269` definitions.
- `quality_observability_mixin.py`: `37` definitions.
- `output_guard.py`: `26` definitions.
- `blog_image_auto.py`: `12` definitions.

`pipeline.py` remaining article-type clusters:

- `branding`: runtime source contract + validation helpers.
- `case_study`: runtime source contract + unsupported metric / customer / award validation helpers.
- `explanatory_article`: source-use digest, title / lead shaping, fingerprint repair activation.

`pipeline.py` remaining major responsibilities:

- generation orchestration: `_prepare_runtime_source_contracts`, `_refresh_diagnostics_state`, `MinimalPipeline._run_optional_repair`, `MinimalPipeline.generate`.
- company_intro repair activation / naturalness / observability payload projection.
- shared parsing, experimental prompt stack, surface guards, failure payload building.

## Priority Decision

| Priority | Status | Work | Owner Scope |
|---:|---|---|---|
| 1 | `do-next` | `note_writer_app_split_2026-04-23` Phase 05 main page pre-generation builders | `note_writer_app.py` split package |
| 2 | `park` | `pipeline.py` branding source contract / route helper extraction | `simple_note_pipeline/pipeline.py` source contract logic |
| 3 | `park` | `pipeline.py` case_study source contract / legal-sensitive helper extraction | `simple_note_pipeline/pipeline.py` source contract logic |
| 4 | `park` | `pipeline.py` explanatory_article source contract / metadata-adjacent cleanup | `simple_note_pipeline/pipeline.py` source-use logic |
| 5 | `park` | `pipeline.py` shared/common helper extraction | shared helper boundary |
| 6 | `park` | `quality_observability_mixin.py` observability cleanup | observability only |
| 7 | `park` | `output_guard.py` guard policy helper cleanup | output guard only |
| 8 | `follow-up` | full-flow user-trial readiness | after split / bloat-control checkpoint |

## Selected Next Package

- `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\`
- Type: existing behavior-preserving split package
- Next phase: `Phase 05 Main Page Pre-Generation Builders`
- Owner: `C:\tetie\notecode\note\note_writer_app.py`
- First step: use existing Phase 05 execution prompt and test matrix
- Non-goals:
  - source contract changes
  - prompt changes
  - threshold changes
  - repair changes
  - guard changes
  - generation rerun
  - `pipeline.py` source contract cleanup
  - `run_generation()` body split
  - completion / exception / finally cleanup timing changes
  - image prompt / auto legal postcheck changes
  - confirm state mutation changes

## Non-Selected Candidate Reasons

- A `branding` extraction:
  - feasible fallback if pipeline-only work is required, but source-contract split just completed three phases and post-extraction smoke says not to auto-chain.
- B `case_study` extraction:
  - larger source-contract value, but legal-sensitive validation and unsupported metric / customer / award checks make it riskier than branding.
- C `explanatory_article` extraction:
  - mixed with source-use digest, metadata cleanup, title / lead shaping, and fingerprint repair; higher risk of blending with recent quality work.
- D shared/common helper extraction:
  - premature commonization; highest behavior drift and import-cycle risk.
- F `quality_observability_mixin.py`:
  - diagnostics semantics and recent metadata changes make cleanup less urgent than existing UI shell split.
- G `output_guard.py`:
  - guard policy / threshold-sensitive and smaller than `note_writer_app.py`.
- H full-flow user-trial readiness:
  - valuable follow-up, but current post-extraction smoke is already green and bloat-control next step should use the ready split package.

## Verification

- Product code hashes recorded:
  - `simple_note_pipeline\pipeline.py`: `A6556109E5408197EE118936F474146E76EFCAFDE7568E614CBCA722F46E57FD`
  - `simple_note_pipeline\company_intro_source_contract.py`: `17ACADFCA0AB81FA37293200D509FBFB3094B4FC9C99779B41AE091EDCD57AED`
  - `simple_note_pipeline\announcement_source_contract.py`: `9DF7B94278A36C9EA3BFC709F9D7EE46F2EA92163C2A7B30871A8A3262FD3880`
  - `simple_note_pipeline\comparative_review_source_contract.py`: `5B17DE5CFC554B385B3BD9324678F2251FE82F4FEB1F8B3861B5A401E6F6391E`
  - `note_writer_app.py`: `7B6CE8DCF8E5722E6D38C2FE4E74FC19277B7DACD1DB02BF6499D26DA1C73961`
  - `newalgorithm_pipeline\quality_observability_mixin.py`: `C1ED8D722314F63F38939A131471B34EF3D02BC3209C2FED4BE68797E8F1485C`
  - `newalgorithm_pipeline\output_guard.py`: `CECC784672A524811D9A2AB47ADDCD5F027604E6A7EAE9E01A6A592AA29C43AB`
  - `blog_image_auto.py`: `FE01368C549C70261802CABE44FFC05D115B797DF6C0430B83802B4D2808B5A0`
- `18080` listener: none
- pytest: not run; docs-only priority reassessment
- product code: unchanged during this reassessment
- AGENTS update: not needed; routing and current source-of-truth did not change

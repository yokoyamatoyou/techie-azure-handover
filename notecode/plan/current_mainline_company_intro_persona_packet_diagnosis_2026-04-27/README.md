# current_mainline_company_intro_persona_packet_diagnosis_2026-04-27

## Objective

Diagnose why the current mainline `company_introduction` output still reads like a consultation or implementation-entry article, without changing product code. The next implementation window must start from one narrow owner and one narrow hypothesis.

This package follows:

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\ALGORITHM.md`
  - `## 4. Single-Pass Generation`
  - `## 5. Repair Algorithm`
  - `## 12. Persona / Source Packet / Editing Persona Contract`
- `C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\`
- `C:\tetie\notecode\plan\current_mainline_pre_generation_ux_preflight_2026-04-27\`
- `C:\tetie\WORKLOG.md`

## Phenomenon

Baseline attempt: `gen-75fac897`.

The generation fetched all 4 source URLs and completed the core pipeline, but the final article still contains consultation-entry framing that is unnatural for a company introduction:

- `ガス・電気・住まいを支える事業と、相談の入口が見える会社紹介`
- `## 相談の入口はどこにあるか`
- `案内の入口として見えやすいのは、ガスや電気に関する相談と、住まいづくりの相談です。`
- `まとめて相談しやすい形にしているのがこの会社の見え方です。`

The visible problem is not a fetch failure or UI start-gate issue. It is a content direction problem inside the company-introduction generation route.

## Repro URLs

- `https://www.sanin-sanso.co.jp/`
- `https://www.sanin-sanso.co.jp/company/info/`
- `https://www.sanin-sanso.co.jp/company/history/`
- `https://www.sanin-sanso.co.jp/home/price/`

## Logs To Read

- `C:\tetie\notecode\logs\latest_ui_journey.json`
- `C:\tetie\notecode\logs\latest_generation_output.json`
- `C:\tetie\notecode\logs\latest_generation_output.txt`
- `C:\tetie\notecode\logs\latest_generation_quality_report.json`
- `C:\tetie\notecode\logs\app.log`
- `C:\tetie\notecode\logs\company_intro_naturalness_prompt_surface_20260427\`

## Cause Candidates

- **A. source packet / slot naming: contributing.** The source contract maps official `ご相談` wording into `customer_situation_or_entry_point`, then prompt composition surfaces it as `相談入口`.
- **B. persona_trial late_return_target: primary.** `current_mainline_persona_trial.py` injects `相談の入口`, `相談前判断`, and `最後は相談前に何を確認すると判断しやすいかへ戻す。` as company-introduction direction.
- **C. hidden_late_validation / repair guard: unlikely for this artifact.** Latest metadata shows hidden late validation did not trigger and no hidden late validation repair IDs were active.
- **D. output_formatter / title_strategy fallback: secondary.** `output_formatter.py` was not applied in `gen-75fac897`; `title_strategy.py` still contributes `相談前判断` to prompt surface, but it should not be the first owner.
- **E. repair trigger gap: secondary.** `semantic_issue_count=0`; the optional repair fired for fingerprint flatness but was rejected. The thin consultation bridge wording is not currently treated as semantic drift.
- **F. prompt_builder prompt surface: confirmed symptom.** The reconstructed prompt still contains `相談前`, `相談入口`, `相談の入口`, `導入`, and `確認`, but the upstream source is persona/source-packet/title composition, not a standalone `prompt_builder.py` overlay.

## Owner Candidates

Next owner:

- `C:\tetie\notecode\note\current_mainline_persona_trial.py`

Parked owners unless later validation proves the first owner insufficient:

- `C:\tetie\notecode\note\simple_note_pipeline\prompt_builder.py`
- `C:\tetie\notecode\note\simple_note_pipeline\hidden_late_validation.py`
- `C:\tetie\notecode\note\newalgorithm_pipeline\output_formatter.py`
- `C:\tetie\notecode\note\simple_note_pipeline\title_strategy.py`
- repair trigger / semantic issue logic

## Non-Goals

- Do not change product code in this diagnosis package.
- Do not add another repair pass.
- Do not make editing persona always fire.
- Do not relax quality guard, fingerprint thresholds, or source-grounding thresholds.
- Do not broaden the source contract.
- Do not bloat `pipeline.py`, `prompt_builder.py`, or `note_writer_app.py`.
- Do not create persona registry or central source contract registry.
- Do not expose runtime/internal terms in body text or UI.
- Do not reopen pre-2026-04-02 archive records or frozen architecture packages.

## Rollback Boundary

This package is docs-only. The next implementation rollback boundary should be limited to the chosen owner file, `current_mainline_persona_trial.py`, plus any focused tests created for that owner.

Accepted source contract changes from the pre-generation UX preflight remain in place.

## Next Implementation Phase

Phase 01 should test one hypothesis only:

For `branding/company_introduction`, the persona trial must stop making consultation/pre-contact framing the always-on late-return and heading direction when `reader_decision` / `pre_contact_decision` is missing.

The intended article direction is current business, service/product scope, support posture, and source-backed company facts. Consultation or pre-contact wording may appear only when source slots actually justify that angle.

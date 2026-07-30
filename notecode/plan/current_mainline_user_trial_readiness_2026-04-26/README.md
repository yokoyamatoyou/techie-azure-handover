# current_mainline_user_trial_readiness_2026-04-26

## Objective

ユーザーが current mainline を実際に試す前に、最小の user-trial readiness 条件を固定する。

この package は docs-only。product code、UI文言、prompt、threshold、repair回数、pipeline、output guard、quality guard、image generation logic、追加責務分け実装は変更しない。

## Source Artifacts

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\plan\naturalness_recovery_2026-04-07\`
- `C:\tetie\notecode\plan\note_writer_app_split_2026-04-23\PROGRESS.md`
- `C:\tetie\notecode\plan\current_mainline_bloat_control_priority_2026-04-26\PROGRESS.md`
- `C:\tetie\notecode\plan\current_mainline_full_flow_acceptance_review_2026-04-26\README.md`
- `C:\tetie\notecode\plan\current_mainline_full_flow_acceptance_review_2026-04-26\PROGRESS.md`
- `C:\tetie\notecode\logs\post_phase06a_success_path_ui_smoke_20260426-200726\post_phase06a_success_path_ui_smoke_summary.json`
- `C:\tetie\notecode\logs\current_mainline_full_flow_regression_from_manifest_20260426-000000\post_run_acceptance_report.json`
- `C:\tetie\notecode\logs\current_mainline_full_flow_regression_from_manifest_20260426-000000\image_validation_summary.json`
- `C:\tetie\notecode\plan\current_mainline_company_intro_source_grounding_weak_reflection_diagnosis_2026-04-27\PROGRESS.md`
- `C:\tetie\notecode\logs\company_intro_source_grounding_observability_fix_20260427-100546\`
  - `visual_review.md`
  - `ui_validation_summary.json`
  - `before_after_grounding_comparison.json`
  - `product_code_hash_diff.json`
- `C:\tetie\notecode\ALGORITHM.md` section 13
- `C:\tetie\notecode\plan\gpt_image2_blog_image_auto_2026-04-22\`
- `C:\tetie\WORKLOG.md`

## Readiness Decision

User trial can proceed with a narrow first set:

1. `announcement`
2. `comparative_review`
3. `company_introduction`

The current recommendation is `proceed to limited user trial with all three article types`.

- `announcement`: user trial OK, `3/3 publishable_success`, images success.
- `comparative_review`: user trial OK with normal review, `3/3 publishable_success`, images success.
- `company_introduction`: limited user trial OK with review awareness.

No additional validation is required before this first trial. If a new check is requested later, limit it to one smoke case and do not rerun the full flow by default.

For `company_introduction`, source grounding weak reflection is fixed in the latest observability evidence:

- Existing artifact recompute: `0.2/0.4/0.4` -> `1.0/1.0/1.0`.
- `source_grounding:weak_reflection`: `3/3` -> `0/3`.
- UI rerun: `3/3 publishable_success`.
- Source grounding: `5/5`.
- Images generated successfully.
- Product code hash validation reports no unexpected hash drift beyond the intended owner.

Residual for `company_introduction`:

- Self-perspective still leans third-party explanatory.
- `repair_required=true` / `repair_rejected=true` remains `3/3`, but does not block publishable output in the latest rerun.
- Title/body may still need human review for note-like voice.

## Article Type Classification

| Article type | Classification | Reason |
|---|---|---|
| `announcement` | `user_trial_ok` | 3/3 `publishable_success`, images success, no leakage |
| `comparative_review` | `user_trial_ok_with_normal_review` | 3/3 `publishable_success`, images success; keep normal source-backed review |
| `company_introduction` | `limited_user_trial_ok_with_review_awareness` | source grounding weak reflection fixed; UI rerun 3/3 `publishable_success`; source grounding 5/5; images success; self-perspective and repair rejection residual remain |
| `explanatory_article` | `ready_with_review_warning` | 2/2 success; metadata denominator stop not reproduced; thin-watch source caveat remains |
| `industry_analysis` | `ready_with_review_warning` | 2/2 success; fixture/thin source caveat means second-wave trial only |
| `product_introduction` | `source_needed` | mixed result, thin source caveat, must-cover miss on blocked attempt |
| `daily_story` | `source_needed` | synthetic source produced source grounding `0.0`; both attempts blocked |
| `case_study` | `hold` | both attempts blocked with legal/guarantee warnings |
| non-company `branding` values stance | `hold` | production UI route mismatch; not usable as generic non-company branding validation |

## First Trial Source Conditions

- `announcement`
  - Include change content, effective date/time, target users, old-flow handling, preparation, and day-of checks.
  - Prefer one main notice source plus one FAQ/checklist source.
- `comparative_review`
  - Provide 2-3 options that can be compared on the same axes.
  - Include fit conditions, cautions, tradeoffs, and next confirmation steps.
  - Only include price/plan claims when source-backed.
- `company_introduction`
  - Include current business, customer entry situation, support scope, operating process, and pre-contact decision material.
  - Avoid source made only of company history, representative message, philosophy, or abstract values.

## Warning / Stop Boundary

Acceptable during user trial:

- `review_required_draft`
- `SYS_QUALITY_WARNINGS_UNRESOLVED` when body exists and there is no internal leakage or source-outside claim
- repair warning / `repair_required` / `repair_rejected`
- voice weakness
- title weakness
- thin/source caveat warning
- image-only fail-open warning; article copy/export remains usable

Stop and report:

- internal-term leakage such as `SYS_*`, `source_grounding`, `contract_alignment`, `must_cover`, `PATCH_SCOPE`, `persona`, `trial`, or `hidden`
- source-outside claim, unsupported price/result/vendor superiority, guarantee/legal assertion, or legal-risk wording
- empty body or `blocked_output_redacted=true`
- UI/server failure
- `case_study` guarantee / stealth-like legal warning
- image generation failure that turns the article itself into a failed result

## Image Trial Target

- Exercise image generation on `announcement`, `comparative_review`, and `company_introduction`.
- Treat `company_introduction` image copy as a review-awareness item: check whether the copy fits the article and does not overstate source facts.
- Image generation remains post-success and fail-open. A single failed variant must not invalidate a successful article.

## Package Outcome

- Product code change: none.
- AGENTS update: not needed.
- WORKLOG update: completed for closeout.
- Pytest: not required because this is docs-only readiness planning.

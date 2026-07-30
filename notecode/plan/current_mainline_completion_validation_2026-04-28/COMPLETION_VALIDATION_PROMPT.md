# Current Mainline Completion Validation Prompt

Date: 2026-04-28 JST
Workspace: `C:\tetie\notecode`

## Start Prompt

You are in the current mainline completion-validation window for `C:\tetie\notecode`.

Read first:

1. `C:\tetie\AGENTS.md`
2. `C:\tetie\notecode\AGENTS.md`
3. `C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\USER_TRIAL_RUNBOOK.md`
4. `C:\tetie\notecode\plan\current_mainline_user_trial_readiness_2026-04-26\PROGRESS.md`
5. `C:\tetie\notecode\logs\user_trial_observation_20260428-162243\observation_summary.md`
6. `C:\tetie\notecode\logs\user_trial_observation_20260428-162243\user_feedback_log.md`
7. `C:\tetie\WORKLOG.md`

## Purpose

Validate whether current mainline is complete enough to declare finished.

Run article-generation checks by article type, 3 articles per type, and inspect:

- body quality
- article-type fit
- configured speaker / perspective fit
- title fit
- image title / display copy fit
- source grounding
- copy / legal panel usability where UI path exposes it
- UI confusion or server failure

This window may generate validation artifacts. It must not fix product code during the validation.

## Absolute Constraints

- Do not change product code.
- Do not change prompt / pipeline / UI / image / quality / threshold / repair / source contract.
- Do not tune during this validation.
- Do not create an implementation owner unless a concrete blocker or unacceptable quality report is found.
- Do not fix multiple issues together.
- If a problem appears, record it as an issue candidate only.
- 1 issue = 1 narrow hypothesis = 1 owner scope.

## Validation Targets

Create 3 generated articles per article type.

Primary article types to validate:

- `announcement`
- `comparative_review`
- `company_introduction`
- `product_introduction`
- `daily_story`
- `case_study`
- `branding`
- `industry_analysis`
- `explanatory_article`

If the UI label differs from the semantic article key, record both:

- UI article type / label
- runtime `article_type`
- runtime `semantic_article_key`

## Source Packet Rule

Before each article type run, use sources that fit that type. Do not use thin or mismatched sources and then count source-fit failure as article quality failure.

Minimum source expectations:

- `announcement`: change content, date/range, target users, old/new handling, preparation, action items.
- `comparative_review`: 2-3 candidates, shared criteria, differences, fit conditions, tradeoffs, check order; price or superiority only if source-backed.
- `company_introduction`: current business, customer entry point or situation, support scope, process, decision material; not history/philosophy-only.
- `product_introduction`: what product/service is, use case, target user, functions or support scope, adoption/check points; price/results only if source-backed.
- `daily_story`: concrete event, who faced what, conversation or decision mismatch, changed action afterward.
- `case_study`: before state, change/action, result or observed change, conditions/limits; no unsupported guarantee.
- `branding`: values/stance must be grounded in concrete actions, service behavior, customer touchpoints, or operating choices.
- `industry_analysis`: observed industry change, source facts, affected stakeholders, decision implications, uncertainty/limits.
- `explanatory_article`: concept/question, background, criteria, concrete use/decision points, limits.

## Per-Run Required Checks

For each generated article, record:

- article type
- UI selected label
- semantic article key
- source count
- source type summary
- generation timestamp
- attempt id
- body present
- `runtime_reason_code`
- `blocked_output_redacted`
- title
- lead present
- body length
- image generation status
- with_text display copy
- without_text status
- copy action status, if checked
- legal panel status, if checked
- app log excerpt

## Quality Review

For every article, judge:

- Does it read as the intended article type?
- Does it avoid route drift into another article type?
- Does the title match the article-type title strategy?
- Does the lead match the title and first section?
- Does the body stay grounded in source?
- Are price, result, guarantee, ranking, superiority, legal conclusions, customer names, awards, or vendor claims source-backed?
- Does the article avoid internal terms?
- Does it avoid empty body / redaction / failure state?
- Does the UI require an explicit generation action?
- Does image failure, if any, stay fail-open and not break article success?

## Perspective Review

Check perspective as article-type-specific, not universally first-person.

- `company_introduction`: self-perspective is important. It should read as company self-introduction where source and UI settings support that. `私たち` / `当社` / equivalent self-view should appear naturally, without mechanical repetition. It must not read like a third-party review.
- `announcement`: speaker should fit the announcing organization or service. It should be clear who is announcing and who must act.
- `comparative_review`: neutral expert / guide perspective is usually better than self-promotion. Do not force `私たち`.
- `product_introduction`: product/service owner perspective is acceptable if configured; otherwise it should explain product use without unsupported sales claims.
- `daily_story`: scene owner / narrator should feel natural and concrete.
- `case_study`: case narrator should not overclaim results; before/after and conditions matter.
- `branding`: values should be expressed through actions and choices, not abstract slogans.
- `industry_analysis`: observer / analyst perspective should stay source-grounded and avoid unsupported forecasts.
- `explanatory_article`: explainer perspective should clarify without adding unsupported claims.

## Title Review

Check that title follows the article-type strategy:

- `announcement`: target + change/start + date/range.
- `comparative_review`: condition + choosing / distinguishing axis; no ranking or strongest claim.
- `company_introduction`: business content + handled field + company characteristic.
- `product_introduction`: use case + burden/problem + selection reason.
- `daily_story`: small scene + realization.
- `case_study`: before/after change + learning.
- `branding`: reader uncertainty + value context.
- `industry_analysis`: change issue + decision condition.
- `explanatory_article`: question + axis.

Reject or record as issue candidate if the title:

- is too generic for the article type
- repeats the source title without article shaping
- overclaims price, result, guarantee, ranking, or superiority
- routes `company_introduction` into consultation/inquiry funnel
- routes `comparative_review` into a winner/ranking article

## Image Title / Display Copy Review

For each generated image pair:

- Confirm `with_text` display copy is readable.
- Confirm `without_text` has no readable accidental text, digits, logo, signature, or watermark.
- Confirm display copy fits article type.
- Confirm display copy is not duplicated, truncated, mojibake, or malformed.
- Confirm display copy does not add unsupported price/result/ranking/guarantee/legal claim.
- Confirm image failure does not break article success.

Article-type display-copy expectations:

- `announcement`: change target and what to check.
- `comparative_review`: decision axis or comparison point, no winner.
- `company_introduction`: business area / products / services / handled field / region / company characteristic. Avoid consultation-route copy unless user explicitly accepts it.
- `product_introduction`: use case, burden, function, adoption condition.
- `daily_story`: small scene and realization.
- `case_study`: change or learning, no overclaimed result.
- `branding`: concrete value context, not slogan-only.
- `industry_analysis`: change signal or decision condition.
- `explanatory_article`: question or understanding axis.

## Codex Visual Inspection Requirement

Codex must visually inspect the outputs, not only parse logs.

For each run:

- Open or inspect the UI result if available.
- Inspect the visible article preview for title, lead, body, hashtags, copy/legal panel state, and warnings.
- Inspect generated image files or UI image panels for both variants.
- Use the app/browser visual view where available.
- If images are saved locally, open them with the image viewer tool or an equivalent visual inspection path.
- Record visual observations in plain language.

Codex should specifically look for:

- broken layout
- unreadable or malformed image text
- image text truncation
- duplicated image copy
- stray text in no-text image
- title/body mismatch
- article-type mismatch
- self-perspective weakness in `company_introduction`
- third-party explanatory tone in `company_introduction`
- ranking/winner framing in `comparative_review`
- legal/guarantee/result overclaim

Do not mark an image as OK from logs alone. Logs can establish generation success; visual inspection must establish usable image quality.

## Stop / Report Conditions

Stop the validation batch and report if any of these occur:

- empty body
- `blocked_output_redacted=true`
- internal-term leakage in normal UI/body/copy
- source-outside claim
- unsupported price / result / vendor superiority
- legal / guarantee risk assertion
- UI/server failure
- source contamination
- generation starts without explicit generation button
- image failure breaks article success
- unreadable or malformed image text that user would reject
- article type route drift severe enough that the article is not usable

## Record-Only Conditions

Record but do not stop unless repeated or user rejects:

- fingerprint soft warnings with body present
- review-required warning with usable body
- single image variant warning when article remains usable
- mild `company_introduction` voice/title concern accepted by user
- mild image typography artifact accepted by user

## Artifacts

Create a new artifact root:

`C:\tetie\notecode\logs\completion_validation_20260428-HHMMSS\`

Save:

- `validation_summary.md`
- `per_article_type_results.md`
- `visual_review_log.md`
- `issue_candidates.md`
- `next_owner_decision.md`
- `app_log_excerpt.txt`
- copies of relevant `latest_generation_output.txt`
- copies of relevant `latest_generation_output.json`
- copies of relevant `latest_generation_quality_report.json`
- copies of image generation json logs
- screenshots or image paths when available

## Completion Decision

If all article types pass 3/3 with no blocker:

Set status:

`COMPLETION_VALIDATION_GREEN`

Decision:

- current mainline can be considered complete for this validation scope.
- product code owner: none.
- next action: document closeout only.

If any blocker appears:

Set status:

`COMPLETION_VALIDATION_BLOCKED`

Decision:

- do not fix in this validation window.
- record one issue candidate as the next owner.
- classify remaining problems as deferred.

If only review-awareness items appear and user accepts them:

Set status:

`COMPLETION_VALIDATION_GREEN_WITH_REVIEW_AWARENESS`

Decision:

- product code owner: none unless repeated user-facing rejection appears.

## Final Report Format

Report:

- validation status
- article types tested
- pass/fail count per article type
- blocker presence
- issue candidate presence
- product code owner needed or not
- whether implementation should start or observation/closeout is enough
- AGENTS/WORKLOG update need


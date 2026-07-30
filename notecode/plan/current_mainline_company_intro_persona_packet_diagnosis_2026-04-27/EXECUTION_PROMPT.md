# Execution Prompt

Use this prompt in the next implementation window.

---

You are working in `C:\tetie\notecode`.

Implement one narrow owner for current mainline `company_introduction` quality:

- Owner: `C:\tetie\notecode\note\current_mainline_persona_trial.py`
- Hypothesis: for `branding/company_introduction`, persona trial guidance is making consultation/pre-contact framing the always-on late-return and heading direction when `reader_decision` / `pre_contact_decision` is missing.

Read first:

- `C:\tetie\AGENTS.md`
- `C:\tetie\notecode\AGENTS.md`
- `C:\tetie\notecode\ALGORITHM.md`
  - `## 4. Single-Pass Generation`
  - `## 5. Repair Algorithm`
  - `## 12. Persona / Source Packet / Editing Persona Contract`
- `C:\tetie\notecode\plan\current_mainline_company_intro_persona_packet_diagnosis_2026-04-27\README.md`
- `C:\tetie\notecode\plan\current_mainline_company_intro_persona_packet_diagnosis_2026-04-27\TASK.md`
- `C:\tetie\notecode\plan\current_mainline_company_intro_persona_packet_diagnosis_2026-04-27\PROGRESS.md`
- `C:\tetie\notecode\plan\current_mainline_company_intro_persona_packet_diagnosis_2026-04-27\ROLLBACK.md`

Do not change these in this phase:

- `prompt_builder.py`
- `pipeline.py`
- `note_writer_app.py`
- `hidden_late_validation.py`
- `output_formatter.py`
- `title_strategy.py`
- source contract files

Forbidden changes:

- no repair count increase
- no always-on editing persona
- no quality guard / fingerprint / source grounding threshold relaxation
- no broad source contract change
- no persona registry or central source contract registry
- no runtime/internal terms in article body or UI
- no reopening pre-2026-04-02 archive or frozen architecture packages

Implement:

- Adjust company-introduction persona defaults so the article direction is current business, service/product scope, support posture, and source-backed company facts.
- Remove consultation/pre-contact wording as the default company-introduction late-return, heading flow, fact priority, and regeneration mission when the source packet lacks `reader_decision` / `pre_contact_decision`.
- Preserve the ability to mention consultation facts only when the source supports them, without turning them into the article frame.

Focused tests:

- Add or update company-introduction persona/prompt composition tests.
- Assert that missing `reader_decision` / `pre_contact_decision` does not produce `相談前判断`, `相談の入口`, or `導入` as default steering.
- Run focused current-mainline company-introduction tests only.

UI real-generation validation:

- Use these sources:
  - `https://www.sanin-sanso.co.jp/`
  - `https://www.sanin-sanso.co.jp/company/info/`
  - `https://www.sanin-sanso.co.jp/company/history/`
  - `https://www.sanin-sanso.co.jp/home/price/`
- Confirm `不足を確認` / `内容を確認` do not start generation.
- Confirm `この内容で生成を開始` is the only generation start.
- Confirm final title/headings/body no longer organize the company introduction around `相談の入口`, `相談前`, `相談前判断`, or unsupported `導入` framing.

Success criteria:

- The 4-source company-introduction output reads as a company introduction, not a consultation-entry article.
- Source grounding and quality guards are not relaxed.
- Repair count and editing persona behavior are unchanged.
- If the issue remains after this owner, stop and report the next owner split instead of widening the patch.

Closeout:

- Update `C:\tetie\notecode\plan\current_mainline_company_intro_persona_packet_diagnosis_2026-04-27\PROGRESS.md`.
- Append `C:\tetie\WORKLOG.md`.
- State whether `AGENTS.md` update is needed; expected default is no.

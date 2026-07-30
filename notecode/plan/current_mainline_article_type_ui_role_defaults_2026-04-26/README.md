# current_mainline_article_type_ui_role_defaults_2026-04-26

## Objective

Article type ごとの UI role / perspective / writing_focus default を `note_writer_app.py` owner 内で固定し、runtime handoff へ `auto` のまま渡る経路を減らす。

## Scope

- owner: `C:\tetie\notecode\note\note_writer_app.py`
- helper tests: `C:\tetie\notecode\note\tests\test_note_writer_app_generation_execution_helpers.py`
- validation artifact: `C:\tetie\notecode\logs\article_type_ui_role_defaults_validation_20260426-225904\`

## Non-goals

- persona / algorithm / source contract / prompt accretion は変更しない。
- quality_guard / output_guard / pipeline / blog_image_auto / image prompt は変更しない。
- threshold / repair count / target_chars / length_mode は変更しない。
- role selection UI を複雑化しない。

## Result

UI/runtime handoff は article type default を保持するようになった。

- `announcement`: `運営担当として語る`, `corporate`, `explanation`, `watashitachi`
- `comparative_review`: `自社の知見を持つ編集担当として語る`, `expert`, `analysis`, `watashitachi`
- `company_introduction`: `自社の企業担当者として語る`, `corporate`, `explanation`, `watashitachi`

Validation result is partial green:

- announcement / comparative_review: `publishable_success`
- company_introduction: generated body exists and `blocked_output_redacted=false`, but `review_required_draft` / `SYS_QUALITY_WARNINGS_UNRESOLVED`

Do not mark company_introduction quality as green from this package alone.

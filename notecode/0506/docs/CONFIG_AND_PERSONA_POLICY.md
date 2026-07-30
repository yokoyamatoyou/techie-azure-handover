# Config and Persona Policy

## Purpose

Configuration, personas, prompts, and runtime code must be separated.

This project has many dimensions that can grow quickly:

- article genre
- viewpoint
- first person
- tone
- source priority
- risky phrase policy
- QA thresholds
- prompt roles
- platform style targets

Do not solve this by adding more branches to one large Python module or one huge prompt.

## Directory Ownership

Expected implementation shape:

```text
app/
  config/
    default_settings.yaml
    article_genres.yaml
    quality_thresholds.yaml
    source_acquisition.yaml
  personas/
    persona_registry.yaml
    writer_roles.yaml
    viewpoint_profiles.yaml
    style_profiles.yaml
    editor_profiles.yaml
  prompts/
    draft_writer.md
    style_editor.md
    japanese_quality_checker.md
    targeted_rewriter.md
  services/
    config_loader.py
    persona_loader.py
    prompt_renderer.py
```

## Separation Rules

### Config

Config files own values that can change without changing code:

- default first person by genre
- source priority
- QA thresholds
- risky phrase watchlists
- URL extraction confidence thresholds
- output platform style target
- model selection defaults

Config must not contain long prompt bodies.

### Personas

Persona files own reusable writer roles, viewpoint profiles, and style profiles:

- in-house brand blog editor
- in-house announcement editor
- in-house case-study editor
- comparison guide editor
- daily activity blog writer
- note/Hatena owned-media paragraph and ending rhythm
- note/Hatena structural editor pass

Persona files may include short role descriptions, viewpoint constraints, compact style profile settings, and editor profile settings, but not full pipeline prompts.

### Prompts

Prompt files own task templates:

- draft writing
- style editing
- quality checking
- targeted rewriting

Prompts must use variables from `article_brief`, config, and persona profiles. Do not duplicate genre tables or long policy lists in every prompt.

### Code

Code owns loading, validation, rendering, and execution.

Code must not embed large prompt strings, persona tables, or long genre-specific rules. If a Python file starts accumulating article-type branches, move the data into config/persona files and keep the code as a dispatcher.

## Anti-Bloat Rules

### Module Size

- Prefer modules under 300 lines.
- A module over 500 lines requires a split review.
- A module over 800 lines is a blocker unless it is generated code or schema data.

Split by responsibility, not by arbitrary helpers.

Good split examples:

- `config_loader.py`
- `persona_loader.py`
- `prompt_renderer.py`
- `source_text_extractor.py`
- `quality_issue_detector.py`

Bad split examples:

- `utils.py`
- `helpers.py`
- `misc.py`
- `prompt_big.py`

### Prompt Size

- Prefer each prompt template under 120 lines.
- A prompt over 180 lines requires a prompt-bloat review.
- Shared rules should live in config/persona/policy docs and be rendered selectively.
- Do not copy the same forbidden phrase list into every prompt.
- Do not add a new instruction to fix one observed failure unless the owner is confirmed.

### Branch Growth

Do not add unlimited `if genre == ...` branches inside agent code.

Preferred shape:

```text
genre_id -> genre config -> persona profile -> article_brief -> prompt render
```

The article brief should carry the selected role, viewpoint, narrator, style profile ID, style edit policy, editor profile ID, editor pass policy, source claims, style rules, and QA policy.

### Prompt Patch Rule

When output quality fails, diagnose the owner before editing prompts.

Possible owners:

- source extraction
- source card extraction
- knowledge pack integration
- article brief builder
- persona selection
- draft prompt
- style editor
- quality checker
- targeted rewriter

Do not add prompt text until the owner is identified.

## Validation

Every implementation slice that touches config, personas, or prompts should report:

- changed config files
- changed persona files
- changed prompt files
- rendered prompt size, if prompts changed
- whether any rules were duplicated
- whether module size thresholds were exceeded

## Stop Conditions

Stop and report before continuing if:

- one module becomes the owner of multiple pipeline stages,
- one prompt tries to handle extraction, generation, editing, QA, and rewrite at once,
- a genre-specific fix duplicates across multiple prompts,
- a persona change silently changes source-grounding policy,
- QA thresholds are lowered to make examples pass.

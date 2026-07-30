# Tech Stack

## Runtime

- Language: Python 3.11
- OS target: Windows first
- Shell: PowerShell
- Virtual environment: repo-local `.venv`
- Python executable for validation: `.venv\Scripts\python.exe`
- Encoding: UTF-8

## UI

- UI framework: NiceGUI
- Initial UI target: local browser app
- Desktop/native packaging is out of scope for MVP.

## Dependency Management

- Use `requirements.in` for human-managed direct dependencies.
- Use `requirements.txt` for pinned installation.
- Do not introduce Poetry or uv unless dependency resolution becomes painful enough to justify the extra tool.

## Japanese Text Processing

- Tokenizer: SudachiPy
- Dictionary: `sudachidict_core`
- Default split mode: `SplitMode.C`

`SplitMode.C` is the default for quality checks because it preserves longer compound expressions and proper nouns better for blog-level rhythm and lexical-overuse checks. If a later metric needs finer granularity, add an explicit mode-specific helper instead of changing the default globally.

## Core Libraries

Initial choices:

- UI: `nicegui`
- Schema / validation: `pydantic`
- Tests: `pytest`
- HTTP: `httpx`
- HTML parsing: `beautifulsoup4`
- HTML parser backend: start with Python `html.parser`; allow `lxml` later if extraction speed or malformed HTML handling requires it
- PDF placeholder path: `pypdf`
- Word placeholder path: `python-docx`
- Environment variables: `python-dotenv`

## LLM Boundary

- Provider direction: OpenAI Responses API
- Do not call OpenAI directly from every agent.
- Create one service boundary such as `app/services/llm_client.py`.
- Keep web search, normal generation, structured outputs, and later model selection behind that boundary.

## Out of Scope for MVP

- Browser automation scraping
- Login-required scraping
- Paywall bypass
- OCR
- Custom Sudachi dictionary
- Multi-provider LLM routing
- Cloud deployment
- Native desktop packaging

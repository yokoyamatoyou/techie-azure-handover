# Reproducible Environment

This project uses `requirements.txt` for direct runtime dependencies and
`constraints.lock.txt` for exact transitive dependency versions.

## Canonical Rebuild

Run from `C:\tetie\aio2-main`:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\rebuild_venv.ps1 -Recreate
```

This creates `.venv`, pins `pip==26.1.2`, installs `requirements-dev.txt`
with `constraints.lock.txt`, and runs `pip check`.

For runtime-only installs:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\rebuild_venv.ps1 -Recreate -NoDev
```

## Verification

```powershell
.venv\Scripts\python.exe -m pip check
.venv\Scripts\python.exe -m pytest tests -q
$env:HEADLESS='1'; $env:PORT='8092'; .venv\Scripts\python.exe nicegui_app.py
```

Expected dependency-audit residual:

- `diskcache==5.6.3 / CVE-2025-69872`
- `pip-audit` does not currently report a fixed version.
- Product code does not directly import `diskcache`; it is present as a transitive dependency.

## Updating Dependencies

Do not update dependencies ad hoc. Use this sequence:

1. Update direct pins in `requirements.txt` or `requirements-dev.txt`.
2. Rebuild `.venv`.
3. Run `pip check`, `pip-audit`, and `pytest tests -q`.
4. Regenerate `constraints.lock.txt` from the verified `.venv`.
5. Record the audit and verification result in `WORKLOG.md`.

`requirements-windows.txt` is a non-canonical PoC profile that excludes
WeasyPrint. For reproducible multi-developer work, use the canonical rebuild
above.

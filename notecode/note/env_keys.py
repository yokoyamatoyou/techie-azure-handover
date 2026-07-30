from __future__ import annotations

import os


def resolve_env_var(name: str) -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    if os.name != "nt":
        return ""
    try:
        import winreg
    except ImportError:
        return ""

    locations = (
        (winreg.HKEY_CURRENT_USER, "Environment"),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
        ),
    )
    for hive, path in locations:
        try:
            with winreg.OpenKey(hive, path) as key:
                raw, _ = winreg.QueryValueEx(key, name)
        except OSError:
            continue
        value = str(raw or "").strip()
        if value:
            os.environ[name] = value
            return value
    return ""


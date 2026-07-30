from __future__ import annotations

import os

READONLY_DEMO_ENV_VAR = "KOTOMEGANE_READONLY_DEMO"
READONLY_DEMO_TRUTHY_VALUES = frozenset({"1", "true", "yes", "on"})


def is_readonly_demo_mode() -> bool:
    return os.getenv(READONLY_DEMO_ENV_VAR, "").strip().lower() in READONLY_DEMO_TRUTHY_VALUES


def readonly_demo_block_message(action: str) -> str:
    return (
        f"read-only/demo mode is active ({READONLY_DEMO_ENV_VAR}=1); "
        f"blocked {action} before provider/API/LLM access."
    )

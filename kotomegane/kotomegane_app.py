from __future__ import annotations

import runpy


if __name__ in {"__main__", "__mp_main__"}:
    runpy.run_module("app", run_name="__main__")

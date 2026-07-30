"""NiceGUI startup helper for note_writer_app."""
from __future__ import annotations

import os
import socket
from pathlib import Path
from typing import Any, Callable, Mapping, Optional


def _is_port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex((host, port)) == 0


def resolve_available_port(
    *,
    host: str,
    start_port: int,
    port_in_use: Callable[[str, int], bool] = _is_port_in_use,
    notify: Callable[[str], None] = print,
) -> int:
    final_port = int(start_port)
    while port_in_use(host, final_port):
        notify(f"[INFO] Port {final_port} is in use, trying next...")
        final_port += 1
        if final_port > start_port + 10:
            break
    return final_port


def is_headless_enabled(environ: Mapping[str, str] = os.environ) -> bool:
    return str(environ.get("HEADLESS", "")).lower() in ("1", "true", "yes")


def run_note_writer_app(
    *,
    ui_module: Any,
    static_dir: Path,
    host: str = "127.0.0.1",
    port: Optional[int] = None,
    environ: Mapping[str, str] = os.environ,
) -> None:
    start_port = port or int(environ.get("PORT", "8080"))
    final_port = resolve_available_port(host=host, start_port=start_port)
    ui_module.run(
        host=host,
        port=final_port,
        title="コトメイク | TECHIE",
        favicon=str(static_dir / "favicon_v2.png"),
        reload=False,
        show=not is_headless_enabled(environ),
    )

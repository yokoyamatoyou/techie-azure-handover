"""Small UI compatibility targets used by the note writer app shell."""
from __future__ import annotations

from typing import Any


class HiddenGenerateButtonCompatibility:
    """No-op stand-in for the removed hidden legacy generate button."""

    __slots__ = ("enabled", "text", "visible")

    def __init__(self, *, text: str = "", visible: bool = False, enabled: bool = True) -> None:
        self.text = text
        self.visible = visible
        self.enabled = enabled

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False

    def props(self, *_args: Any, **_kwargs: Any) -> "HiddenGenerateButtonCompatibility":
        return self

    def style(self, *_args: Any, **_kwargs: Any) -> "HiddenGenerateButtonCompatibility":
        return self

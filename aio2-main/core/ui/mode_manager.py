# -*- coding: utf-8 -*-
"""表示モード管理"""

from dataclasses import dataclass


MODE_LABELS = {
    "simple": "要点",
    "advanced": "詳細",
}


@dataclass
class ModeManager:
    """表示レベル（要点/詳細）管理"""

    mode: str = "simple"

    def set_mode_from_label(self, label: str) -> None:
        if label == MODE_LABELS["advanced"]:
            self.mode = "advanced"
        else:
            self.mode = "simple"

    def label(self) -> str:
        return MODE_LABELS.get(self.mode, MODE_LABELS["simple"])

    def is_advanced(self) -> bool:
        return self.mode == "advanced"

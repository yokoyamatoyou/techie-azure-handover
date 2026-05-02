# -*- coding: utf-8 -*-
"""Central usage service keys and default unit policies."""
from __future__ import annotations

SERVICE_KOTOMAKE = "kotomake"
SERVICE_KOTOMIGAKI = "kotomigaki"
SERVICE_KOTOMEGANE = "kotomegane"

ACTION_KOTOMAKE_GENERATE = "kotomake.generate"
ACTION_KOTOMIGAKI_ANALYZE = "kotomigaki.analyze"
ACTION_KOTOMEGANE_MANUAL = "kotomegane.manual"
ACTION_KOTOMEGANE_BATCH = "kotomegane.batch"
ACTION_KOTOMEGANE_SCHEDULED = "kotomegane.scheduled"

DEFAULT_UNITS = {
    ACTION_KOTOMAKE_GENERATE: 1,
    ACTION_KOTOMIGAKI_ANALYZE: 1,
    ACTION_KOTOMEGANE_MANUAL: 2,
    ACTION_KOTOMEGANE_BATCH: 1,
    ACTION_KOTOMEGANE_SCHEDULED: 1,
}

"""Adapter boundary package for vNext integration."""

from .current_ui_contract_adapter import adapt_current_contract_to_vnext
from .legacy_helper_adapter import LegacyHelperAdapter
from .runtime_projection_adapter import (
    build_vnext_shadow_projection,
    project_vnext_result_to_current_shape,
)

__all__ = [
    "LegacyHelperAdapter",
    "adapt_current_contract_to_vnext",
    "build_vnext_shadow_projection",
    "project_vnext_result_to_current_shape",
]

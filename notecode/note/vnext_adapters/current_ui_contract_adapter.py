"""Adapter from current resolved contract to vNext thin contract.

Allowed dependencies:
- note.input_contract_v1
- note.source_document_utils
- note.vnext.types
- note.vnext.source
- note.vnext.contract
"""
from __future__ import annotations

from collections.abc import Mapping

from note.vnext.contract import build_vnext_thin_contract
from note.vnext.types import VNextThinContract


def adapt_current_contract_to_vnext(current_contract: Mapping[str, object] | None) -> VNextThinContract:
    if not isinstance(current_contract, Mapping):
        raise TypeError("current_contract must be a mapping")
    return build_vnext_thin_contract(current_contract)

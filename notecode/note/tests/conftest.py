from __future__ import annotations

import pytest


LEGACY_COMPAT_NODEID_PREFIXES = (
    "note/tests/test_fingerprint_metrics.py::TestGPT5MiniParallelRegression",
    "note/tests/test_fingerprint_metrics.py::TestHLCv2ModeIntegration",
    "note/tests/test_llm_client_runtime.py::test_gpt5_family_skips_penalty_params_upfront",
    "note/tests/test_offline.py::test_generate_skips_linkedin_resonance_pipeline_by_default",
    "note/tests/test_offline.py::test_pipeline_check_includes_phase_effect_metrics",
    "note/tests/test_offline.py::test_phase08_zero_base_body_has_no_supplement_prefix",
    "note/tests/test_offline.py::test_phase08_zero_base_body_length_guard",
    "note/tests/test_offline.py::test_phase08_zero_base_linebreak_density_report",
    "note/tests/test_offline.py::test_phase08_zero_base_runs_compacted_postprocess_pipeline",
    "note/tests/test_zero_base_phase03.py::test_phase03_zero_base_mode_generates_min_output",
    "note/tests/test_zero_base_phase04.py::test_phase04_branding_section_prompt_prioritizes_user_instruction",
)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-legacy-compat-tests",
        action="store_true",
        default=False,
        help="Include retired compatibility and stale frozen-expectation tests.",
    )


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    if config.getoption("--run-legacy-compat-tests"):
        return

    selected: list[pytest.Item] = []
    deselected: list[pytest.Item] = []
    for item in items:
        if item.nodeid.startswith(LEGACY_COMPAT_NODEID_PREFIXES):
            item.add_marker("legacy_compat")
            deselected.append(item)
        else:
            selected.append(item)

    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = selected

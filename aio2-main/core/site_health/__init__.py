# -*- coding: utf-8 -*-
"""サイトヘルスチェックモジュール。

The package keeps these compatibility exports lazy so low-level fetch helpers
can import a single site-health guard without eagerly importing security_checker
back into the fetch module.
"""

_EXPORTS = {
    "OGPChecker": (".ogp_checker", "OGPChecker"),
    "format_ogp_result": (".ogp_checker", "format_ogp_result"),
    "generate_ogp_template": (".ogp_checker", "generate_ogp_template"),
    "get_platform_specific_suggestions": (".ogp_checker", "get_platform_specific_suggestions"),
    "OGP_TAGS": (".ogp_checker", "OGP_TAGS"),
    "TWITTER_TAGS": (".ogp_checker", "TWITTER_TAGS"),
    "PLATFORM_REQUIREMENTS": (".ogp_checker", "PLATFORM_REQUIREMENTS"),
    "SecurityChecker": (".security_checker", "SecurityChecker"),
    "format_security_result": (".security_checker", "format_security_result"),
    "get_risk_explanation": (".security_checker", "get_risk_explanation"),
    "get_improvement_guide": (".security_checker", "get_improvement_guide"),
    "SECURITY_HEADERS": (".security_checker", "SECURITY_HEADERS"),
    "SECURITY_IMPROVEMENT_GUIDES": (".security_checker", "SECURITY_IMPROVEMENT_GUIDES"),
    "AccessibilityChecker": (".accessibility_checker", "AccessibilityChecker"),
    "format_accessibility_result": (".accessibility_checker", "format_accessibility_result"),
    "get_wcag_compliance_level": (".accessibility_checker", "get_wcag_compliance_level"),
    "WCAG_CRITERIA": (".accessibility_checker", "WCAG_CRITERIA"),
    "ACCESSIBILITY_IMPROVEMENTS": (".accessibility_checker", "ACCESSIBILITY_IMPROVEMENTS"),
}


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(name)
    module_name, attr_name = _EXPORTS[name]
    from importlib import import_module

    value = getattr(import_module(module_name, __name__), attr_name)
    globals()[name] = value
    return value

__all__ = [
    "OGPChecker",
    "format_ogp_result",
    "generate_ogp_template",
    "get_platform_specific_suggestions",
    "OGP_TAGS",
    "TWITTER_TAGS",
    "PLATFORM_REQUIREMENTS",
    "SecurityChecker",
    "format_security_result",
    "get_risk_explanation",
    "get_improvement_guide",
    "SECURITY_HEADERS",
    "SECURITY_IMPROVEMENT_GUIDES",
    "AccessibilityChecker",
    "format_accessibility_result",
    "get_wcag_compliance_level",
    "WCAG_CRITERIA",
    "ACCESSIBILITY_IMPROVEMENTS",
]

# -*- coding: utf-8 -*-
"""法的リスクチェックモジュール"""

from .premiums_labeling import PremiumsLabelingChecker, format_check_result, generate_improvement_suggestion
from .violation_cases import get_relevant_cases, get_case_lesson
from .stealth_marketing import StealthMarketingChecker, suggest_pr_disclosure, format_stealth_marketing_result
from .commercial_transaction import (
    ECDetector,
    CommercialTransactionChecker,
    find_tokushoho_page,
    generate_template_suggestion,
    format_commercial_transaction_result,
    REQUIRED_ITEMS
)
from .visibility_checker import VisibilityChecker
from .best_practices import check_best_practices, COMPLIANCE_DICTIONARY
from .lawyer_perspective import attach_lawyer_comments, LAWYER_COMMENTS
from .consumer_protection import ConsumerProtectionChecker

__all__ = [
    'PremiumsLabelingChecker',
    'format_check_result',
    'generate_improvement_suggestion',
    'get_relevant_cases',
    'get_case_lesson',
    'StealthMarketingChecker',
    'suggest_pr_disclosure',
    'format_stealth_marketing_result',
    'ECDetector',
    'CommercialTransactionChecker',
    'find_tokushoho_page',
    'generate_template_suggestion',
    'format_commercial_transaction_result',
    'REQUIRED_ITEMS',
    'VisibilityChecker',
    'check_best_practices',
    'COMPLIANCE_DICTIONARY',
    'attach_lawyer_comments',
    'LAWYER_COMMENTS',
    'ConsumerProtectionChecker',
]

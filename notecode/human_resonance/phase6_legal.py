"""Phase 6: Legal - 法務リスクチェック

景表法、薬機法、金商法等の法的リスクを検出・修正するモジュール。
正規表現による高速プレチェックとLLMによる文脈判定の2段階で処理。
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """リスクレベル"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class LegalIssue:
    """法的問題を表すデータクラス"""

    original: str  # 問題のある原文
    fixed: str  # 修正後の表現
    law: str  # 関連する法律名
    reason: str  # 問題の理由
    risk_level: RiskLevel = RiskLevel.MEDIUM


@dataclass
class LegalCheckResult:
    """法的チェック結果を表すデータクラス"""

    has_issues: bool = False
    risk_level: RiskLevel = RiskLevel.NONE
    issues: List[LegalIssue] = field(default_factory=list)
    checked_text: str = ""


# リスクパターンの定義
RISK_PATTERNS: Dict[str, Dict[str, Any]] = {
    "high": {
        "patterns": [
            # 薬機法違反（効果効能の断定）
            (r'(治る|治し|治療効果がある)', "薬機法", "効果効能の断定は禁止"),
            (r'(アンチエイジング効果|若返り効果)', "薬機法", "医療的効果の暗示"),
            # 詐欺的表現（「フィッシング詐欺」「振り込め詐欺」等の正当な複合語は除外）
            (r'(?<!フィッシング)(?<!振り込め)(?<!オレオレ)(?<!還付金)(?<!投資)(?<!保険)(?<!特殊)(詐欺|インチキ|悪徳)', "名誉毀損", "他社への誹謗中傷"),
            # 差別表現
            (r'(バカ|アホ|死ね|殺す|殺害)', "人権侵害", "差別的・攻撃的表現"),
            # 金商法違反
            (r'(絶対儲かる|必ず上がる|確実に利益)', "金商法", "断定的判断の提供"),
        ],
        "level": RiskLevel.HIGH,
    },
    "medium": {
        "patterns": [
            # 景表法違反（優良誤認）
            (r'(?<![A-Za-z0-9])(No\.?1(?![\d０-９])|ナンバーワン)(?!を目指|への挑戦)', "景表法", "根拠のない最上級表現"),
            (r'(世界一|世界で一番|業界初|日本一|国内一)(?!を目指)', "景表法", "根拠のない最上級表現"),
            (r'(最高|最強|唯一|唯一無二)(?!を目指|への挑戦|を追求)', "景表法", "優良誤認の可能性"),
            # 比較広告
            (r'(他社|競合).{0,10}より.{0,15}(丈夫|高機能|高性能|優れ)', "景表法", "根拠のない比較広告"),
            # 健康・美容
            (r'(痩せる|ダイエット効果|美白効果)', "薬機法/健増法", "効果の暗示"),
            # 不動産
            (r'(お買い得|掘り出し物|激安)', "宅建法", "誇大広告の可能性"),
        ],
        "level": RiskLevel.MEDIUM,
    },
    "low": {
        "patterns": [
            # 軽微なリスク
            (r'(ブラック企業)', "名誉毀損", "特定対象への批判"),
            (r'(限定|今だけ|期間限定)(?!.*まで)', "景表法", "有利誤認の可能性"),
        ],
        "level": RiskLevel.LOW,
    },
}

# 安全な修正パターン
SAFE_REPLACEMENTS: Dict[str, str] = {
    "No.1": "高い評価を目指す",
    "No1": "高い評価を目指す",
    "ナンバーワン": "高い評価を目指す",
    "世界一": "世界レベルを目指す",
    "日本一": "国内トップクラスを目指す",
    "業界初": "先進的な",
    "最高の": "質の高い",
    "最強の": "強力な",
    "唯一無二": "独自の",
    "絶対": "非常に",
    "必ず": "高い確率で",
    "確実に": "期待できる",
    "治る": "改善が期待できる",
    "痩せる": "体重管理をサポートする",
    "美白効果": "肌の印象を整える",
    "アンチエイジング": "エイジングケア",
}


class Phase6Legal:
    """Phase 6: 法務リスクチェック処理"""

    def __init__(self, llm_client: Optional[Any] = None):
        """
        Args:
            llm_client: LLMクライアント（詳細な文脈判定用、オプション）
        """
        self.llm = llm_client

    def process(self, text: str, use_llm: bool = False) -> str:
        """テキストの法的リスクをチェック・修正する

        Args:
            text: 入力テキスト
            use_llm: LLMによる詳細判定を使用するか

        Returns:
            リスクが修正されたテキスト
        """
        if not text:
            return ""

        # Step 1: プレチェック（正規表現による高速検出）
        result = self.precheck(text)

        if result.risk_level == RiskLevel.NONE:
            return text

        # Step 2: リスクがある場合は修正
        fixed_text = text

        for issue in result.issues:
            if issue.original in fixed_text:
                fixed_text = fixed_text.replace(issue.original, issue.fixed)

        # Step 3: LLMによる詳細判定（オプション）
        if use_llm and self.llm and result.risk_level in [RiskLevel.HIGH, RiskLevel.MEDIUM]:
            fixed_text = self._llm_legal_check(fixed_text)

        return fixed_text

    def analyze_with_rationale(self, text: str, use_llm: bool = False) -> LegalCheckResult:
        """修正根拠付きでチェック結果を返す（UI向け）"""
        if not text:
            return LegalCheckResult(
                has_issues=False,
                risk_level=RiskLevel.NONE,
                issues=[],
                checked_text="",
            )

        result = self.precheck(text)
        if not result.has_issues:
            result.checked_text = text
            return result

        fixed_text = text
        for issue in result.issues:
            if issue.original in fixed_text:
                fixed_text = fixed_text.replace(issue.original, issue.fixed)

        if use_llm and self.llm and result.risk_level in [RiskLevel.HIGH, RiskLevel.MEDIUM]:
            fixed_text = self._llm_legal_check(fixed_text)

        result.checked_text = fixed_text
        return result

    def precheck(self, text: str) -> LegalCheckResult:
        """正規表現によるプレチェック"""
        result = LegalCheckResult(checked_text=text)

        _LEVEL_PRIORITY = {RiskLevel.NONE: 0, RiskLevel.LOW: 1, RiskLevel.MEDIUM: 2, RiskLevel.HIGH: 3}
        detected_level = RiskLevel.NONE
        issues = []

        # 各リスクレベルのパターンをチェック
        # [要修正: ...] タグ内のテキストを一時的にマスクして再マッチを防止
        _tag_re = re.compile(r'\[要修正:\s*[^\]]*\]')
        masked_text = _tag_re.sub(lambda m: '\x00' * len(m.group()), text)

        for level_name, config in RISK_PATTERNS.items():
            for pattern, law, reason in config["patterns"]:
                matches = re.findall(pattern, masked_text, re.IGNORECASE)

                for match in matches:
                    match_str = match if isinstance(match, str) else match[0]

                    # 安全な置換を探す
                    fixed = self._find_safe_replacement(match_str)

                    issues.append(LegalIssue(
                        original=match_str,
                        fixed=fixed,
                        law=law,
                        reason=reason,
                        risk_level=config["level"],
                    ))

                    # 最も高いリスクレベルを記録
                    if _LEVEL_PRIORITY[config["level"]] > _LEVEL_PRIORITY[detected_level]:
                        detected_level = config["level"]

        result.has_issues = len(issues) > 0
        result.risk_level = detected_level
        result.issues = issues

        return result

    def _find_safe_replacement(self, text: str) -> str:
        """安全な置換表現を探す"""
        for original, replacement in SAFE_REPLACEMENTS.items():
            if original in text:
                return text.replace(original, replacement)

        # 置換が見つからない場合は元のテキストをそのまま返す
        # （[要修正: ...] タグは本文に残さない）
        logger.info("Legal: no safe replacement for '%s', keeping original", text[:40])
        return text

    def _llm_legal_check(self, text: str) -> str:
        """LLMによる詳細な法的チェック"""
        if not self.llm:
            return text

        prompt = self._build_legal_prompt(text)

        try:
            checked_text = self.llm.generate_text(
                prompt,
                max_tokens=min(len(text) + 1000, 4096),
                task_type="legal_check",
                temperature_override=0.2,
            )

            if checked_text and len(checked_text) > len(text) * 0.5:
                return checked_text.strip()
        except Exception as exc:
            logger.debug("LLM legal check failed. Falling back to regex-only result.", exc_info=exc)

        return text

    def _build_legal_prompt(self, text: str) -> str:
        """法的チェック用プロンプトを構築"""
        return f"""
あなたは日本の上場企業で20年の経験を持つ法務部長です。

以下の記事を法的観点からチェックし、問題がある箇所のみを修正してください。

【チェック対象の法令】
- 景品表示法（優良誤認、有利誤認）
- 薬機法（効果効能の断定）
- 金融商品取引法（断定的判断の提供）
- 宅地建物取引業法（誇大広告）

【修正ルール】
- 問題がなければ原文をそのまま出力
- 問題がある箇所のみを最小限に修正
- 人間味のある表現は維持
- 記事本文のみを出力（説明不要）

【記事本文】
{text}
""".strip()

    def analyze(self, text: str) -> Dict[str, Any]:
        """テキストの法的リスクを詳細に分析する"""
        result = self.precheck(text)

        return {
            "has_issues": result.has_issues,
            "risk_level": result.risk_level.value,
            "issue_count": len(result.issues),
            "issues_by_law": self._group_by_law(result.issues),
            "issues_by_level": self._group_by_level(result.issues),
            "details": [
                {
                    "original": i.original,
                    "fixed": i.fixed,
                    "law": i.law,
                    "reason": i.reason,
                    "level": i.risk_level.value,
                }
                for i in result.issues
            ],
        }

    def _group_by_law(self, issues: List[LegalIssue]) -> Dict[str, int]:
        """問題を法律別にグループ化"""
        groups: Dict[str, int] = {}
        for issue in issues:
            groups[issue.law] = groups.get(issue.law, 0) + 1
        return groups

    def _group_by_level(self, issues: List[LegalIssue]) -> Dict[str, int]:
        """問題をリスクレベル別にグループ化"""
        groups: Dict[str, int] = {}
        for issue in issues:
            level = issue.risk_level.value
            groups[level] = groups.get(level, 0) + 1
        return groups

    def quick_check(self, text: str) -> LegalCheckResult:
        """簡易チェック（プレチェックのみ）"""
        return self.precheck(text)

    def get_risk_summary(self, text: str) -> str:
        """リスクサマリーを文字列で返す"""
        result = self.precheck(text)

        if not result.has_issues:
            return "法的リスクは検出されませんでした。"

        summary_parts = [
            f"リスクレベル: {result.risk_level.value}",
            f"検出された問題: {len(result.issues)}件",
        ]

        by_law = self._group_by_law(result.issues)
        if by_law:
            law_summary = ", ".join(f"{law}: {count}件" for law, count in by_law.items())
            summary_parts.append(f"関連法令: {law_summary}")

        return "\n".join(summary_parts)


def run_legal_check(text: str) -> Dict[str, Any]:
    """法的チェックを実行するヘルパー関数"""
    legal = Phase6Legal()
    return legal.analyze(text)


def fix_legal_issues(text: str, llm_client: Optional[Any] = None) -> str:
    """法的問題を修正するヘルパー関数"""
    legal = Phase6Legal(llm_client=llm_client)
    return legal.process(text, use_llm=llm_client is not None)

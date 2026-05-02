"""
改良版PDF生成アルゴリズム: 三視点分離 + 並列処理

このモジュールは、analysis.pyに追加する新しい関数群を定義します。
既存のgenerate_report_commentary()を置き換えることで、
トークン制限超過を防ぎ、高品質なレポートを生成します。

主な機能:
1. 三視点を並列生成（高速化）
2. トークン制限の最適化（各2000-2500トークン）
3. エラーハンドリングの強化（部分的失敗でも継続）
"""

import asyncio
import json
import numpy as np
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from PDFreport.llm_client import get_llm_client
from PDFreport.models.survey_models import ReportCommentary
from PDFreport.config.pdf_config import settings
from PDFreport.utils.text_professionalizer import (
    preprocess_text_rule_based,
    professionalize_text_with_llm,
    sanitize_text_for_pdf
)


# ============================================================================
# 新しいPydanticモデル
# ============================================================================

class PerspectiveResult(BaseModel):
    """単一視点の分析結果"""
    
    analysis: str = Field(
        description="詳細分析（800-1200字）。具体的なデータに基づく洞察を提供する。"
    )
    key_recommendations: List[str] = Field(
        description="推奨事項（3-5件）。実行可能で具体的なアクションを提案する。"
    )
    expected_impact: str = Field(
        description="期待される効果（200-300字）。実装による定量的・定性的な効果を説明する。"
    )


class SummaryResult(BaseModel):
    """サマリー生成結果"""
    
    summary_text: str = Field(
        description="分析結果全体の要約（400-600字）。3つのポイントで要約する。"
    )
    action_items: List[str] = Field(
        description=f"推奨アクション（最大{settings.MAX_ACTION_ITEMS}件）。優先度順に具体的なアクションを提示する。",
        max_items=settings.MAX_ACTION_ITEMS,
    )
    sentiment_commentary: str = Field(
        description="感情分析の解説（400-600字）。感情分布から読み取れるインサイトを説明する。"
    )
    topics_commentary: str = Field(
        description="トピック分析の解説（400-600字）。主要トピックから読み取れるインサイトを説明する。"
    )


# ============================================================================
# 持続性（Persistence）のヘルパー関数
# ============================================================================

def _is_incomplete_output(result: Any, min_analysis_length: int = 100) -> bool:
    """不完全な出力を検出する。
    
    Args:
        result: LLMからの出力結果
        min_analysis_length: 分析テキストの最小長さ
        
    Returns:
        bool: 不完全な出力の場合True
    """
    if result is None:
        return True
    
    # PerspectiveResult型の場合
    if hasattr(result, 'analysis'):
        # analysisのチェック（None安全）
        if result.analysis is None:
            return True
        if not isinstance(result.analysis, str) or len(result.analysis.strip()) < min_analysis_length:
            return True
        
        # key_recommendationsのチェック（None安全）
        if not hasattr(result, 'key_recommendations') or result.key_recommendations is None:
            return True
        if not isinstance(result.key_recommendations, list) or len(result.key_recommendations) == 0:
            return True
        
        # expected_impactのチェック（None安全）
        if not hasattr(result, 'expected_impact') or result.expected_impact is None:
            return True
        if not isinstance(result.expected_impact, str) or len(result.expected_impact.strip()) < 50:
            return True
    
    # 辞書型の場合
    if isinstance(result, dict):
        analysis = result.get('analysis') or result.get(f'{result.get("perspective_type", "")}_perspective', '')
        if not analysis or not isinstance(analysis, str) or len(str(analysis).strip()) < min_analysis_length:
            return True
    
    return False


async def _retry_with_completion(
    llm_client: Any,
    system_prompt: str,
    user_content: str,
    response_model: Any,
    max_tokens: int,
    temperature: float,
    max_retries: int = 3,
    min_analysis_length: int = 100,
) -> Optional[Any]:
    """不完全な出力を自動的に補完する。
    
    Args:
        llm_client: LLMクライアント
        system_prompt: システムプロンプト
        user_content: ユーザーコンテンツ
        response_model: レスポンスモデル
        max_tokens: 最大トークン数
        temperature: 温度パラメータ
        max_retries: 最大リトライ回数
        min_analysis_length: 分析テキストの最小長さ
        
    Returns:
        Optional[Any]: 補完された結果、またはNone
    """
    for attempt in range(max_retries):
        try:
            # リトライ時はトークン制限を増やす（最後の試行時のみ）
            current_max_tokens = max_tokens if attempt < max_retries - 1 else int(max_tokens * 1.5)
            
            # 補完用のプロンプトを追加
            completion_prompt = (
                "\n\n【重要】前回の出力が不完全でした。"
                f"以下の要件を満たすよう、より詳細で完全な分析を提供してください：\n"
                f"- 分析テキストは最低{min_analysis_length}文字以上\n"
                f"- 推奨事項は3-{settings.MAX_ACTION_ITEMS}件\n"
                f"- 期待される効果は200-300字\n"
            ) if attempt > 0 else ""
            
            result = await llm_client.generate_commentary(
                system_prompt,
                user_content + completion_prompt,
                response_model,
                max_tokens=current_max_tokens,
                temperature=temperature,
            )
            
            # 出力の完全性をチェック
            if not _is_incomplete_output(result, min_analysis_length):
                print(f"DEBUG: 補完成功（試行{attempt + 1}/{max_retries}）")
                return result
            else:
                print(f"WARNING: 出力が不完全（試行{attempt + 1}/{max_retries}）。再試行します。")
                
        except Exception as e:
            print(f"WARNING: 補完試行{attempt + 1}/{max_retries}でエラー: {type(e).__name__}: {e}")
            if attempt == max_retries - 1:
                return None
    
    return None


def _convert_numpy_types(obj: Any) -> Any:
    """NumPy型をPython標準型に変換する（JSONシリアライズ対応）。
    
    Args:
        obj: 変換対象のオブジェクト
        
    Returns:
        Any: 変換後のオブジェクト
    """
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: _convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_convert_numpy_types(item) for item in obj]
    return obj


def _check_data_adequacy(evidence: Dict[str, Any]) -> tuple[bool, List[str]]:
    """データの十分性をチェックする。
    
    Args:
        evidence: Evidence Pack（集計データ）
        
    Returns:
        tuple[bool, List[str]]: (データが十分かどうか, 不足している項目のリスト)
    """
    missing_items = []
    
    # 必須項目のチェック（実際のEvidence Packのキー名に合わせる）
    # emotion_averages: emotion_scoresに相当
    # sentiment_counts: sentiment_distributionに相当
    # topic_counts: そのまま
    required_keys = {
        'emotion_averages': 'emotion_scores',  # エイリアス
        'sentiment_counts': 'sentiment_distribution',  # エイリアス
        'topic_counts': 'topic_counts'
    }
    
    for actual_key, alias in required_keys.items():
        if actual_key not in evidence or not evidence[actual_key]:
            missing_items.append(alias)  # エラーメッセージにはエイリアスを使用
    
    # データの最小要件チェック
    if 'emotion_averages' in evidence:
        emotion_averages = evidence['emotion_averages']
        if not isinstance(emotion_averages, dict) or len(emotion_averages) == 0:
            missing_items.append('emotion_scores（データが空）')
    
    if 'sentiment_counts' in evidence:
        sentiment_counts = evidence['sentiment_counts']
        if not isinstance(sentiment_counts, dict) or len(sentiment_counts) == 0:
            missing_items.append('sentiment_distribution（データが空）')
    
    if 'topic_counts' in evidence:
        topic_counts = evidence['topic_counts']
        if not isinstance(topic_counts, dict) or len(topic_counts) == 0:
            missing_items.append('topic_counts（データが空）')
    
    is_adequate = len(missing_items) == 0
    return is_adequate, missing_items


# ============================================================================
# コア関数
# ============================================================================

async def generate_perspective_commentary(
    evidence: Dict[str, Any],
    persona_info: Dict[str, str],
    perspective_type: str,
    survey_type: str,
) -> Dict[str, Any]:
    """単一視点の解説文を生成する。
    
    Args:
        evidence: Evidence Pack（集計データ）
        persona_info: ペルソナ情報（role, perspective, concerns）
        perspective_type: 視点タイプ（"marketing" | "user" | "consultant"）
        survey_type: アンケート形態
        
    Returns:
        dict: 視点別の解説文
            - {perspective_type}_perspective: 詳細分析
            - {perspective_type}_recommendations: 推奨事項
            - {perspective_type}_impact: 期待される効果
    """
    _LLM = get_llm_client()
    
    # 【持続性（Persistence）】データの十分性チェック
    is_adequate, missing_items = _check_data_adequacy(evidence)
    if not is_adequate:
        print(f"WARNING: データが不足しています。不足項目: {', '.join(missing_items)}")
        # データ不足の場合は、その旨を明記したデフォルト値を返す
        return {
            f"{perspective_type}_perspective": (
                f"{perspective_type}視点の分析を生成できませんでした。\n"
                f"データが不足しています: {', '.join(missing_items)}\n"
                "データの再確認をお願いします。"
            ),
            f"{perspective_type}_recommendations": [
                "データの再確認",
                "不足項目の補完",
                "分析の再実行"
            ],
            f"{perspective_type}_impact": "データ不足のため、詳細は利用できません。",
        }
    
    # ペルソナ情報の取得（デフォルト値で安全に）
    role = persona_info.get("role", "専門家")
    perspective = persona_info.get("perspective", "総合的な観点")
    concerns = persona_info.get("concerns", "データ分析")
    
    # システムプロンプト: ペルソナの役割定義（GPT-4.1-mini最適化）
    # ここに「エージェント的ワークフロー（計画・持続性・ツール使用）」を追加して
    # 分析の前後で計画と振り返りを行い、不完全な出力を自動補完するよう指示します。
    system_prompt = (
        f"あなたは{role}です。提供されたEvidenceのみを根拠に"
        f"{perspective}の観点から日本語でレポートを作成します。\n\n"
        f"重視する観点: {concerns}\n\n"
        "【エージェント的ワークフロー】\n"
        "1. 計画（Planning）:\n"
        "   - 分析前に計画を立ててください（データ全体把握→主要パターン特定→改善提案作成）\n"
        "   - 分析後に結果を振り返り、妥当性を確認してください\n\n"
        "2. 持続性（Persistence）:\n"
        "   - 出力が不完全または不足している場合は、自動的に追加分析を行い補完してください\n"
        "   - 必要な情報が不足している場合は、その旨を明記し、可能なら追加の入力例を指示してください\n\n"
        "3. ツール使用（Tool-calling）:\n"
        "   - 外部情報が必要な場合はその旨を明記してください（将来的に自動取得を行う）\n\n"
        "重要な原則:\n"
        "1. 根拠外の断定は行わない\n"
        "2. 推測する場合は『仮説』と明記する\n"
        "3. ビジネス価値と実行可能性を重視する\n"
        "4. 具体的で実践的な提案を行う\n"
        "5. 定量的なデータを活用する\n"
        "6. 現状分析と改善案を明確に分離する\n"
        "7. 数値データを具体的に引用する"
    )
    
    # ユーザープロンプト: 分析タスクの定義（現状+改善案を明確に分離）
    user_content = (
        f"以下のEvidence Packを分析し、{perspective_type}視点のレポートを作成してください。\n\n"
        f"### Evidence Pack\n"
        f"{json.dumps(evidence, ensure_ascii=False, indent=2)}\n\n"
        f"### アンケート形態\n"
        f"{survey_type}\n\n"
        f"### 出力要件（厳格に遵守）\n"
        f"- analysis: {perspective_type}視点の詳細分析（800-1200字）\n"
        f"  【現状分析セクション】\n"
        f"  - データに基づく現状の洞察（具体的な数値を引用）\n"
        f"  - {perspective}からの評価\n"
        f"  - データから読み取れる傾向とパターン\n"
        f"  【改善案セクション】\n"
        f"  - 具体的な改善点の指摘（実行可能なアクション）\n"
        f"  - 優先度の高い改善領域\n"
        f"  - 実装可能な具体的施策\n"
        f"- key_recommendations: 3-5件の推奨事項（実行可能で具体的）\n"
        f"  - 各推奨事項は1文で明確に記述\n"
        f"  - 優先度順（最重要から順に）\n"
        f"  - 具体的な数値目標を含める（可能な場合）\n"
        f"- expected_impact: 期待される効果（200-300字）\n"
        f"  - 定量的効果の推定（数値目標を含む）\n"
        f"  - 定性的効果の説明\n"
        f"  - 実装タイムラインの目安"
    )
    
    try:
        print(f"DEBUG: Generating {perspective_type} perspective...")
        
        # LLM呼び出し（GPT-4.1-mini用: effort/verbosity不要、temperature=0.1で一貫性重視）
        result = await _LLM.generate_commentary(
            system_prompt,
            user_content,
            PerspectiveResult,
            max_tokens=2000,  # 単一視点なので2000トークンで十分（推論オーバーヘッドなし）
            temperature=0.1,  # GPT-4.1-mini用: 一貫性重視（ベストプラクティス）
        )
        
        # 【持続性（Persistence）】不完全な出力を検出して自動補完を試みる
        if _is_incomplete_output(result, min_analysis_length=100):
            print(f"WARNING: {perspective_type}視点の出力が不完全です。自動補完を試みます...")
            result = await _retry_with_completion(
                _LLM,
                system_prompt,
                user_content,
                PerspectiveResult,
                max_tokens=2000,
                temperature=0.1,
                max_retries=3,
                min_analysis_length=100,
            )
            
            # 補完が失敗した場合
            if result is None or _is_incomplete_output(result, min_analysis_length=100):
                print(f"ERROR: {perspective_type}視点の補完に失敗しました。デフォルト値を返します。")
                raise ValueError(f"{perspective_type}視点の出力が不完全で、補完にも失敗しました。")
        
        print(f"DEBUG: {perspective_type} perspective generated successfully")
        
        # テキストのプロフェッショナル化
        raw_analysis = result.analysis if result.analysis else ""
        raw_impact = result.expected_impact if result.expected_impact else ""
        
        # ルールベース前処理
        preprocessed_analysis = preprocess_text_rule_based(raw_analysis, survey_type)
        preprocessed_impact = preprocess_text_rule_based(raw_impact, survey_type)
        
        # LLM整形（非同期処理、preprocessed_textをフォールバック用に渡す）
        professionalized_analysis = await professionalize_text_with_llm(
            preprocessed_analysis,
            perspective_type,
            survey_type,
            preprocessed_text=preprocessed_analysis
        )
        professionalized_impact = await professionalize_text_with_llm(
            preprocessed_impact,
            perspective_type,
            survey_type,
            preprocessed_text=preprocessed_impact
        )
        
        # PDF直前のサニタイズ
        final_analysis = sanitize_text_for_pdf(professionalized_analysis, perspective_type, survey_type)
        final_impact = sanitize_text_for_pdf(professionalized_impact, perspective_type, survey_type)
        
        # 返却値の構築（None安全）
        return {
            f"{perspective_type}_perspective": final_analysis,
            f"{perspective_type}_recommendations": result.key_recommendations if result.key_recommendations else [],
            f"{perspective_type}_impact": final_impact,
        }
        
    except Exception as e:
        print(f"ERROR in generate_{perspective_type}_perspective: {type(e).__name__}: {e}")
        
        # エラー時のデフォルト値
        return {
            f"{perspective_type}_perspective": (
                f"{perspective_type}視点の分析生成中にエラーが発生しました。\n"
                "データの再確認をお願いします。"
            ),
            f"{perspective_type}_recommendations": [
                "データの再確認",
                "分析の再実行",
                "エラーログの確認"
            ],
            f"{perspective_type}_impact": "詳細は利用できません。",
        }


async def generate_summary_commentary(
    evidence: Dict[str, Any],
    survey_type: str,
) -> SummaryResult:
    """サマリー解説文を生成する。
    
    Args:
        evidence: Evidence Pack（集計データ）
        survey_type: アンケート形態
        
    Returns:
        SummaryResult: サマリー生成結果
    """
    _LLM = get_llm_client()
    
    system_prompt = (
        "あなたはデータアナリストです。提供されたEvidenceを要約し、"
        "重要なインサイトを簡潔に伝えます。\n\n"
        "重要な原則:\n"
        "1. 3つのポイントで要約する\n"
        "2. データに基づく客観的な分析\n"
        "3. 実行可能なアクションを提案\n"
        "4. ビジネス価値を明確にする"
    )
    
    user_content = (
        f"以下のEvidence Packを要約してください。\n\n"
        f"### Evidence Pack\n"
        f"{json.dumps(evidence, ensure_ascii=False, indent=2)}\n\n"
        f"### アンケート形態\n"
        f"{survey_type}\n\n"
        f"### 出力要件\n"
        f"- summary_text: 分析結果全体の要約（400-600字）\n"
        f"  - 3つのポイントで構成\n"
        f"  - 最重要インサイトを強調\n"
        f"- action_items: 推奨アクション（最大{settings.MAX_ACTION_ITEMS}件、優先度順）\n"
        f"  - 優先度順\n"
        f"  - 具体的で実行可能\n"
        f"- sentiment_commentary: 感情分析の解説（400-600字）\n"
        f"  - 感情分布のパターン分析\n"
        f"  - 注目すべきインサイト\n"
        f"- topics_commentary: トピック分析の解説（400-600字）\n"
        f"  - 主要トピックの傾向分析\n"
        f"  - 注目すべきインサイト"
    )
    
    try:
        print("DEBUG: Generating summary commentary...")
        
        result = await _LLM.generate_commentary(
            system_prompt,
            user_content,
            SummaryResult,
            max_tokens=settings.PDF_SUMMARY_MAX_TOKENS,  # 設定ファイルから取得（デフォルト2000）
            temperature=0.1,  # GPT-4.1-mini用: 一貫性重視（ベストプラクティス）
        )
        
        print("DEBUG: Summary commentary generated successfully")
        
        # テキストのプロフェッショナル化
        raw_summary_text = result.summary_text if result.summary_text else ""
        raw_sentiment_commentary = result.sentiment_commentary if result.sentiment_commentary else ""
        raw_topics_commentary = result.topics_commentary if result.topics_commentary else ""
        
        # ルールベース前処理
        preprocessed_summary = preprocess_text_rule_based(raw_summary_text, survey_type)
        preprocessed_sentiment = preprocess_text_rule_based(raw_sentiment_commentary, survey_type)
        preprocessed_topics = preprocess_text_rule_based(raw_topics_commentary, survey_type)
        
        # LLM整形（非同期処理）- サマリーは"consultant"ペルソナを使用
        # preprocessed_textをフォールバック用に渡す
        professionalized_summary = await professionalize_text_with_llm(
            preprocessed_summary,
            "consultant",
            survey_type,
            preprocessed_text=preprocessed_summary
        )
        professionalized_sentiment = await professionalize_text_with_llm(
            preprocessed_sentiment,
            "consultant",
            survey_type,
            preprocessed_text=preprocessed_sentiment
        )
        professionalized_topics = await professionalize_text_with_llm(
            preprocessed_topics,
            "consultant",
            survey_type,
            preprocessed_text=preprocessed_topics
        )
        
        # PDF直前のサニタイズ
        final_summary = sanitize_text_for_pdf(professionalized_summary, "consultant", survey_type)
        final_sentiment = sanitize_text_for_pdf(professionalized_sentiment, "consultant", survey_type)
        final_topics = sanitize_text_for_pdf(professionalized_topics, "consultant", survey_type)
        
        # 結果を更新
        result.summary_text = final_summary
        result.sentiment_commentary = final_sentiment
        result.topics_commentary = final_topics
        
        # action_itemsの検証とフォールバック
        if not result.action_items or (isinstance(result.action_items, list) and len(result.action_items) == 0):
            print(f"警告: LLMが空のaction_itemsを返しました。フォールバックを生成します。", flush=True)
            # フォールバック: トピックからアクションを生成
            topic_counts = evidence.get("topic_counts", {})
            if topic_counts and isinstance(topic_counts, dict):
                ranked_topics = sorted(topic_counts.items(), key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0, reverse=True)
                fallback_actions = []
                for topic, _ in ranked_topics[:3]:
                    fallback_actions.append(f"「{topic}」に関する改善策を設計し、担当部署と共有する")
                if not fallback_actions:
                    fallback_actions.append("顧客の回答内容を再確認し、優先改善テーマを特定する")
                fallback_actions.append("改善施策ごとにKPIと担当者を設定し、四半期ごとに進捗レビューを行う")
                result.action_items = fallback_actions[:settings.MAX_ACTION_ITEMS]
            else:
                result.action_items = ["データの再確認", "分析の再実行", "エラーログの確認"]
        
        return result
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in generate_summary_commentary: {type(e).__name__}: {e}")
        print(f"ERROR traceback:\n{error_details}")
        
        # エラーログファイルに記録
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"generate_summary_commentary error: {type(e).__name__}: {e}")
            logger.error(f"Traceback:\n{error_details}")
        except Exception:
            pass
        
        # エラー時のデフォルト値
        return SummaryResult(
            summary_text=f"分析結果の生成中にエラーが発生しました。データの再確認をお願いします。\n（エラー詳細: {type(e).__name__}: {str(e)[:100]}）",
            action_items=["データの再確認", "分析の再実行", "エラーログの確認"],
            sentiment_commentary="感情分析の詳細は利用できません。",
            topics_commentary="トピック分析の詳細は利用できません。",
        )


# ============================================================================
# メイン関数（既存のgenerate_report_commentaryを置き換え）
# ============================================================================

async def generate_report_commentary_v2(
    summary_data: Dict[str, Any],
    personas: Dict[str, Dict[str, str]],
    survey_type: str = "customer_satisfaction",
) -> ReportCommentary:
    """改良版: 三視点を並列生成してReportCommentaryを構築する。
    
    この関数は既存のgenerate_report_commentary()を置き換えます。
    
    主な改善点:
    1. サマリーと各視点を分離して生成（トークン制限回避）
    2. 三視点を並列実行（高速化）
    3. エラーハンドリングの強化（部分的失敗でも継続）
    4. max_completion_tokensの最適化（各2000-2500トークン）
    
    Args:
        summary_data: 集計データ
            - sample_size: サンプル数
            - sentiment_counts: 感情分布
            - emotion_averages: 感情スコア平均
            - topic_counts: トピック頻度
            - actionable_insights_ratio: アクショナブルインサイト比率
            - key_insights: キーインサイト
            - data_quality: データ品質警告
        personas: ペルソナ情報
            - marketing: マーケティング専門家
            - user: ユーザーエクスペリエンス専門家
            - consultant: コンサルタント
        survey_type: アンケート形態
        
    Returns:
        ReportCommentary: 完全なレポート解説文
    """
    print(f"DEBUG: generate_report_commentary_v2 開始 - survey_type: {survey_type}")
    
    # Evidence Pack作成（共通）
    # NumPy型をPython標準型に変換（JSONシリアライズ対応）
    raw_topic_counts = summary_data.get("topic_counts", {})
    topic_counts_dict = dict(list(raw_topic_counts.items())[:15]) if raw_topic_counts else {}
    
    evidence = {
        "sample_size": int(summary_data.get("sample_size", 0)),
        "sentiment_counts": _convert_numpy_types(summary_data.get("sentiment_counts", {})),
        "emotion_averages": _convert_numpy_types(summary_data.get("emotion_averages", {})),
        "topic_counts": _convert_numpy_types(topic_counts_dict),
        "actionable_ratio": float(summary_data.get("actionable_insights_ratio", 0)),
        "key_insights": _convert_numpy_types(summary_data.get("key_insights", [])),
        "data_quality": _convert_numpy_types(summary_data.get("data_quality", {})),
    }
    
    print(f"DEBUG: Evidence Pack created - sample_size: {evidence['sample_size']}")
    
    # Step 1: サマリー生成（最優先、小規模）
    summary_result = await generate_summary_commentary(evidence, survey_type)
    
    # Step 2: 三視点を並列生成
    print("DEBUG: Starting parallel perspective generation...")
    
    marketing_task = generate_perspective_commentary(
        evidence, 
        personas.get("marketing", {}), 
        "marketing", 
        survey_type
    )
    user_task = generate_perspective_commentary(
        evidence, 
        personas.get("user", {}), 
        "user", 
        survey_type
    )
    consultant_task = generate_perspective_commentary(
        evidence, 
        personas.get("consultant", {}), 
        "consultant", 
        survey_type
    )
    
    try:
        # 並列実行（高速化）
        marketing_result, user_result, consultant_result = await asyncio.gather(
            marketing_task, 
            user_task, 
            consultant_task,
            return_exceptions=True  # 一部失敗でも継続
        )
        
        # エラーチェック（各視点が例外を返していないか）
        if isinstance(marketing_result, Exception):
            print(f"ERROR in marketing perspective: {marketing_result}")
            marketing_result = {
                "marketing_perspective": "マーケティング分析の生成中にエラーが発生しました。"
            }
        elif not isinstance(marketing_result, dict):
            print(f"WARNING: marketing_result is not a dict: {type(marketing_result)}")
            marketing_result = {
                "marketing_perspective": "マーケティング分析の生成中にエラーが発生しました。"
            }
        elif not marketing_result.get("marketing_perspective"):
            print(f"WARNING: marketing_perspective is empty or missing")
            marketing_result["marketing_perspective"] = "マーケティング分析の生成中にエラーが発生しました。"
        
        if isinstance(user_result, Exception):
            print(f"ERROR in user perspective: {user_result}")
            user_result = {
                "user_perspective": "ユーザー分析の生成中にエラーが発生しました。"
            }
        elif not isinstance(user_result, dict):
            print(f"WARNING: user_result is not a dict: {type(user_result)}")
            user_result = {
                "user_perspective": "ユーザー分析の生成中にエラーが発生しました。"
            }
        elif not user_result.get("user_perspective"):
            print(f"WARNING: user_perspective is empty or missing")
            user_result["user_perspective"] = "ユーザー分析の生成中にエラーが発生しました。"
        
        if isinstance(consultant_result, Exception):
            print(f"ERROR in consultant perspective: {consultant_result}")
            consultant_result = {
                "consultant_perspective": "コンサルタント分析の生成中にエラーが発生しました。"
            }
        elif not isinstance(consultant_result, dict):
            print(f"WARNING: consultant_result is not a dict: {type(consultant_result)}")
            consultant_result = {
                "consultant_perspective": "コンサルタント分析の生成中にエラーが発生しました。"
            }
        elif not consultant_result.get("consultant_perspective"):
            print(f"WARNING: consultant_perspective is empty or missing")
            consultant_result["consultant_perspective"] = "コンサルタント分析の生成中にエラーが発生しました。"
        
        print("DEBUG: Parallel perspective generation completed")
        
    except Exception as e:
        print(f"ERROR in parallel perspective generation: {type(e).__name__}: {e}")
        import traceback
        print(f"ERROR traceback:\n{traceback.format_exc()}")
        
        # 全て失敗した場合のフォールバック
        marketing_result = {"marketing_perspective": "マーケティング分析の生成中にエラーが発生しました。"}
        user_result = {"user_perspective": "ユーザー分析の生成中にエラーが発生しました。"}
        consultant_result = {"consultant_perspective": "コンサルタント分析の生成中にエラーが発生しました。"}
    
    # ReportCommentary統合
    print("DEBUG: Building ReportCommentary...")
    
    # デバッグ: 各視点の値を確認
    marketing_text = marketing_result.get("marketing_perspective", "") if isinstance(marketing_result, dict) else ""
    user_text = user_result.get("user_perspective", "") if isinstance(user_result, dict) else ""
    consultant_text = consultant_result.get("consultant_perspective", "") if isinstance(consultant_result, dict) else ""
    
    print(f"DEBUG: marketing_perspective length: {len(marketing_text)}")
    print(f"DEBUG: user_perspective length: {len(user_text)}")
    print(f"DEBUG: consultant_perspective length: {len(consultant_text)}")
    
    # action_itemsの検証とフォールバック
    action_items = summary_result.action_items if summary_result.action_items else []
    if not action_items or (isinstance(action_items, list) and len(action_items) == 0):
        print(f"警告: generate_summary_commentaryが空のaction_itemsを返しました。フォールバックを生成します。", flush=True)
        # フォールバック: トピックからアクションを生成
        topic_counts = evidence.get("topic_counts", {})
        if topic_counts and isinstance(topic_counts, dict):
            ranked_topics = sorted(topic_counts.items(), key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0, reverse=True)
            action_items = []
            for topic, _ in ranked_topics[:3]:
                action_items.append(f"「{topic}」に関する改善策を設計し、担当部署と共有する")
            if not action_items:
                action_items.append("顧客の回答内容を再確認し、優先改善テーマを特定する")
            action_items.append("改善施策ごとにKPIと担当者を設定し、四半期ごとに進捗レビューを行う")
            action_items = action_items[:settings.MAX_ACTION_ITEMS]
        else:
            action_items = ["データの再確認", "分析の再実行", "エラーログの確認"]
    
    commentary = ReportCommentary(
        summary_text=summary_result.summary_text or "分析結果の要約を準備中です。",
        action_items=action_items,
        sentiment_commentary=summary_result.sentiment_commentary or "感情分析の詳細は利用できません。",
        topics_commentary=summary_result.topics_commentary or "トピック分析の詳細は利用できません。",
        marketing_perspective=marketing_text or "マーケティング分析の詳細は利用できません。",
        user_perspective=user_text or "ユーザー分析の詳細は利用できません。",
        consultant_perspective=consultant_text or "コンサルタント分析の詳細は利用できません。",
        comprehensive_advice=None,  # Optionalなので省略（トークン節約）
    )
    
    print("DEBUG: ReportCommentary built successfully")
    return commentary


# ============================================================================
# 段階的生成版（代替案2）
# ============================================================================

async def generate_report_commentary_staged(
    summary_data: Dict[str, Any],
    personas: Dict[str, Dict[str, str]],
    survey_type: str = "customer_satisfaction",
) -> ReportCommentary:
    """段階的生成版: サマリー → 三視点（逐次）
    
    並列処理が困難な環境向けの代替実装。
    実装が簡単で、リスクが低い。
    
    Args:
        summary_data: 集計データ
        personas: ペルソナ情報
        survey_type: アンケート形態
        
    Returns:
        ReportCommentary: 完全なレポート解説文
    """
    print(f"DEBUG: generate_report_commentary_staged 開始 - survey_type: {survey_type}")
    
    # Evidence Pack作成
    evidence = {
        "sample_size": summary_data.get("sample_size", 0),
        "sentiment_counts": summary_data.get("sentiment_counts", {}),
        "emotion_averages": summary_data.get("emotion_averages", {}),
        "topic_counts": dict(list(summary_data.get("topic_counts", {}).items())[:15]),
        "actionable_ratio": summary_data.get("actionable_insights_ratio", 0),
        "key_insights": summary_data.get("key_insights", []),
        "data_quality": summary_data.get("data_quality", {}),
    }
    
    # Stage 1: サマリー生成
    summary_result = await generate_summary_commentary(evidence, survey_type)
    
    # Stage 2: 三視点を逐次生成
    perspectives = {}
    
    for ptype in ["marketing", "user", "consultant"]:
        print(f"DEBUG: Generating {ptype} perspective...")
        try:
            result = await generate_perspective_commentary(
                evidence, 
                personas.get(ptype, {}), 
                ptype, 
                survey_type
            )
            perspectives.update(result)
            print(f"DEBUG: {ptype} perspective completed")
        except Exception as e:
            print(f"ERROR in {ptype} perspective: {e}")
            perspectives[f"{ptype}_perspective"] = f"{ptype}分析の生成中にエラーが発生しました。"
    
    # ReportCommentary統合
    return ReportCommentary(
        summary_text=summary_result.summary_text,
        action_items=summary_result.action_items,
        sentiment_commentary=summary_result.sentiment_commentary,
        topics_commentary=summary_result.topics_commentary,
        marketing_perspective=perspectives.get("marketing_perspective", ""),
        user_perspective=perspectives.get("user_perspective", ""),
        consultant_perspective=perspectives.get("consultant_perspective", ""),
        comprehensive_advice=None,
    )


# ============================================================================
# エクスポート
# ============================================================================

__all__ = [
    "generate_report_commentary_v2",
    "generate_report_commentary_staged",
    "generate_perspective_commentary",
    "generate_summary_commentary",
    "PerspectiveResult",
    "SummaryResult",
]


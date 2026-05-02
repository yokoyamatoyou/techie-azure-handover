"""
テキストのプロフェッショナル化モジュール
頻出語の抑制とペルソナ別の文体調整
"""

from typing import List, Optional
import re
import asyncio
import traceback
from pathlib import Path
from pydantic import BaseModel, Field

# SudachiPyのインポート（オプション）
try:
    from sudachipy import Dictionary, Tokenizer
    SUDACHI_AVAILABLE = True
except ImportError:
    SUDACHI_AVAILABLE = False

# 頻出語リスト
FREQUENT_WORDS = [
    "こと", "もの", "です", "ます", "いる", "ている", "ある",
    "的", "的な", "ような", "という", "というもの", "ということ"
]


class ProfessionalizedText(BaseModel):
    """プロフェッショナル化されたテキスト"""
    text: str = Field(description="プロフェッショナル化されたテキスト")


def preprocess_text_rule_based(text: str, survey_type: str = "customer_satisfaction") -> str:
    """
    ルールベース前処理（頻出語の抑制）
    SudachiPyを使用した形態素解析による高精度な処理を実装
    
    Args:
        text: 入力テキスト
        survey_type: 調査タイプ
    
    Returns:
        前処理済みテキスト
    """
    if not text:
        return ""
    
    result = text
    
    # SudachiPyが利用可能な場合、形態素解析を使用
    if SUDACHI_AVAILABLE:
        try:
            # SudachiPy辞書の初期化（シングルトンパターン）
            if not hasattr(preprocess_text_rule_based, '_tokenizer'):
                preprocess_text_rule_based._tokenizer = Dictionary().create()
            
            tokenizer_obj = preprocess_text_rule_based._tokenizer
            
            # SplitModeの取得（Tokenizer.SplitMode.Bを使用）
            from sudachipy import tokenizer as sudachi_tokenizer
            mode = sudachi_tokenizer.Tokenizer.SplitMode.B  # モードB（推奨）
            
            # 形態素解析を実行（text, modeの順序）
            tokens = tokenizer_obj.tokenize(text, mode)
            
            # 頻出語を除外しつつ、テキストを再構築
            filtered_tokens = []
            for token in tokens:
                surface = token.surface()
                pos = token.part_of_speech()
                
                # 頻出語を除外（ただし、文脈を考慮）
                # 「こと」「もの」が名詞として独立している場合のみ削除
                if surface in FREQUENT_WORDS:
                    # 品詞が名詞で、独立した語として使われている場合のみ削除
                    if pos[0] == "名詞" and len(surface) <= 2:
                        continue  # 頻出語をスキップ
                
                filtered_tokens.append(surface)
            
            # トークンを結合してテキストを再構築
            result = ''.join(filtered_tokens)
            
        except Exception as e:
            print(f"警告: SudachiPy処理エラー、フォールバックを使用: {e}")
            # エラー時は正規表現ベースの処理にフォールバック
            result = text
    
    # 正規表現ベースの処理（SudachiPyが利用不可の場合、またはフォールバック時）
    # 「こと」「もの」などの削除（文脈を考慮）
    # 「〜すること」→「〜する」、「〜もの」→削除
    patterns = [
        (r'([する為])\s*こと', r'\1'),  # 「すること」→「する」
        (r'([する為])\s*もの', r'\1'),  # 「するもの」→「する」
        (r'という\s*こと', ''),  # 「ということ」→削除
        (r'という\s*もの', ''),  # 「というもの」→削除
        (r'的な\s*', ''),  # 「的な」→削除
        (r'のような\s*', ''),  # 「のような」→削除
    ]
    
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result)
    
    # 連続する空白を1つに
    result = re.sub(r'\s+', ' ', result)
    result = result.strip()
    
    return result


async def professionalize_text_with_llm(
    text: str,
    persona: str,
    survey_type: str = "customer_satisfaction",
    preprocessed_text: Optional[str] = None
) -> str:
    """
    LLMを使用したテキストのプロフェッショナル化
    エラーハンドリングとリトライロジックを強化
    
    Args:
        text: 入力テキスト
        persona: ペルソナ（marketing/user/consultant）
        survey_type: 調査タイプ
        preprocessed_text: 前処理済みテキスト（エラー時のフォールバック用）
    
    Returns:
        プロフェッショナル化されたテキスト
    """
    from PDFreport.llm_client import get_llm_client
    from PDFreport.config.pdf_config import settings
    
    if not text or not text.strip():
        return text
    
    # LLMクライアントを取得
    client = get_llm_client()
    
    # ペルソナ別のプロンプト設定（より詳細に）
    persona_prompts = {
        "marketing": """マーケティング専門家として、以下の点を重視してください：
- データドリブンで戦略的な視点
- ビジネスインパクトを明確に示す
- 数値や指標を活用した説得力のある表現
- 顧客価値とROIを強調""",
        "user": """ユーザー視点の専門家として、以下の点を重視してください：
- 実際の利用者の声を反映
- 具体的で実用的な提案
- ユーザーの課題とニーズを明確に
- 体験に基づいた説得力のある表現""",
        "consultant": """コンサルタントとして、以下の点を重視してください：
- 客観的で論理的な分析
- 実行可能な改善提案を明確に示す
- 構造化された思考プロセス
- 戦略的視点と具体的アクションのバランス"""
    }
    
    persona_instruction = persona_prompts.get(persona, "プロフェッショナルな文体で記述してください。")
    
    # プロンプトの構築（最適化版）
    system_prompt = f"""あなたはプロフェッショナルなレポート作成の専門家です。
以下のテキストを、{persona}ペルソナに相応しい文体に変換してください。

【要件】
1. 「こと」「もの」「です」「ます」などの意味が薄い語を抑制
2. 冗長な語尾（「ということ」「というもの」など）を削減
3. 専門語彙を選好し、簡潔で明確な表現に
4. 元のテキストの意味と文脈を完全に保持
5. {persona_instruction}

【出力例】
入力: 「改善することは重要なことです。」
出力（marketing）: 「改善は重要な戦略的課題である。」
出力（user）: 「改善は利用者にとって重要な課題である。」
出力（consultant）: 「改善は優先度の高い施策として位置づけられる。」

【出力形式】
- 元のテキストの意味を保持しつつ、よりプロフェッショナルな表現に変換
- 過度に簡略化せず、必要な情報は保持
- 日本語で出力
- 自然で読みやすい文章を心がける"""
    
    user_content = f"以下のテキストをプロフェッショナル化してください:\n\n{text}"
    
    # リトライ設定
    max_retries = getattr(settings, 'API_MAX_RETRIES', 3)
    retry_base_ms = getattr(settings, 'LLM_RETRY_BASE_MS', 500)
    
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            # LLM呼び出し（Instructor + Pydanticを使用）
            result = await client._client.chat.completions.create(
                model=settings.PDF_LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_model=ProfessionalizedText,
                max_tokens=settings.PDF_PERSPECTIVE_MAX_TOKENS,
                temperature=0.2,
            )
            
            # 成功時は結果を返す
            if hasattr(result, 'text') and result.text:
                return result.text
            else:
                # テキストが空の場合は元のテキストを返す
                print(f"警告: LLM出力が空です。元のテキストを返します。")
                return preprocessed_text if preprocessed_text else text
            
        except Exception as e:
            last_exception = e
            error_type = type(e).__name__
            
            # 詳細なエラーログ
            print(f"警告: テキストプロフェッショナル化エラー (試行 {attempt + 1}/{max_retries}): {error_type}: {e}")
            
            # デバッグモードの場合はトレースバックを出力
            if getattr(settings, 'DEBUG', False):
                traceback.print_exc()
            
            # リトライ可能なエラーの場合のみリトライ
            # 429 (Rate Limit), 500 (Server Error), 503 (Service Unavailable) など
            if attempt < max_retries - 1:
                if hasattr(e, 'status_code'):
                    status_code = e.status_code
                    if status_code in [429, 500, 503]:
                        # 指数バックオフ
                        wait_time_ms = retry_base_ms * (2 ** attempt)
                        print(f"リトライまで {wait_time_ms}ms 待機します...")
                        await asyncio.sleep(wait_time_ms / 1000.0)
                        continue
                elif "timeout" in str(e).lower() or "timed out" in str(e).lower():
                    # タイムアウトエラーの場合もリトライ
                    wait_time_ms = retry_base_ms * (2 ** attempt)
                    print(f"タイムアウトエラー。リトライまで {wait_time_ms}ms 待機します...")
                    await asyncio.sleep(wait_time_ms / 1000.0)
                    continue
            
            # リトライ不可、または最後の試行の場合はフォールバック
            break
    
    # すべてのリトライが失敗した場合
    print(f"エラー: テキストプロフェッショナル化に失敗しました（{max_retries}回試行）。")
    if last_exception:
        print(f"最終エラー: {type(last_exception).__name__}: {last_exception}")
    
    # エラー時は前処理済みテキストを返す（フォールバック）
    return preprocessed_text if preprocessed_text else text


def sanitize_text_for_pdf(text: str, persona: str, survey_type: str = "customer_satisfaction") -> str:
    """
    PDF直前のサニタイズ
    禁則処理と文字種の正規化を実装
    
    Args:
        text: 入力テキスト
        persona: ペルソナ
        survey_type: 調査タイプ
    
    Returns:
        サニタイズ済みテキスト
    """
    if not text:
        return ""
    
    import unicodedata
    
    # 文字種の正規化
    result = text
    
    # 改行の正規化（\r\n → \n, \r → \n）
    result = re.sub(r'\r\n', '\n', result)
    result = re.sub(r'\r', '\n', result)
    
    # 連続する改行を2つまでに制限
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    # 禁則処理: 行頭禁則文字の処理
    # 行頭に来てはいけない文字: 「、」「。」「，」「．」「）」「」」「』」など
    PROHIBITED_START_CHARS = ['、', '。', '，', '．', '）', '」', '』', '）', '】', '〕', '］', '｝', '〉', '》', '』', '」', '）']
    
    lines = result.split('\n')
    processed_lines = []
    
    for i, line in enumerate(lines):
        if i > 0 and line and line[0] in PROHIBITED_START_CHARS:
            # 前の行の末尾に移動
            if processed_lines:
                processed_lines[-1] += line[0]
                line = line[1:] if len(line) > 1 else ""
        processed_lines.append(line)
    
    result = '\n'.join(processed_lines)
    
    # 連続する空白を1つに（タブも含む）
    result = re.sub(r'[ \t]+', ' ', result)
    
    # 行頭・行末の空白を削除
    lines = result.split('\n')
    lines = [line.strip() for line in lines]
    result = '\n'.join(lines)
    
    # 文字種の正規化（全角・半角の統一）
    # 全角空白を半角空白に
    result = result.replace('　', ' ')
    # 全角カンマを半角カンマに
    result = result.replace('，', ',')
    # 全角ピリオドを半角ピリオドに
    result = result.replace('．', '.')
    # 全角括弧を半角括弧に（オプション、必要に応じて）
    # result = result.replace('（', '(').replace('）', ')')
    
    # Unicode正規化（NFKC形式）
    try:
        result = unicodedata.normalize('NFKC', result)
    except Exception as e:
        print(f"警告: Unicode正規化エラー: {e}")
        # エラー時はそのまま返す
    
    # 特殊文字の処理（制御文字の除去）
    result = ''.join(char for char in result if unicodedata.category(char)[0] != 'C' or char in ['\n', '\t'])
    
    return result.strip()



from __future__ import annotations

from dataclasses import dataclass
import asyncio
from typing import Any, Dict, List, Protocol, Optional
import json
import re
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from enum import Enum

from PDFreport.config.pdf_config import settings

try:
    from PDFreport.prompt_optimizer import PromptOptimizer
except ModuleNotFoundError:
    class PromptOptimizer:  # type: ignore[override]
        def optimize_prompt(self, text: str, context: dict[str, Any] | None = None) -> str:
            return text

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """セキュリティレベル定義"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PromptSecurityValidator:
    """プロンプトインジェクション対策クラス"""
    
    # 危険なパターンの定義
    DANGEROUS_PATTERNS = [
        # システムプロンプト操作
        r'ignore\s+previous\s+instructions',
        r'forget\s+everything',
        r'system\s+prompt',
        r'role\s*:\s*system',
        r'you\s+are\s+now',
        r'pretend\s+to\s+be',
        r'act\s+as\s+if',
        
        # 特殊トークン（括弧全体の除去は誤検知を招くため除外）
        r'<\|.*?\|>',
        
        # プロンプトエスケープ
        r'\\n.*?system',
        r'\\r.*?system',
        r'\\t.*?system',
        
        # 日本語の危険パターン
        r'前の指示を無視',
        r'システムプロンプト',
        r'役割を変更',
        r'あなたは今',
        
        # コードインジェクション
        r'<script.*?>',
        r'javascript:',
        r'data:text/html',
        r'vbscript:',
        
        # ファイルシステムアクセス
        r'file://',
        r'ftp://',
        r'\\\\.*?\\',
        r'/.*?/',
    ]
    
    def __init__(self, security_level: SecurityLevel = SecurityLevel.HIGH):
        self.security_level = security_level
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE | re.MULTILINE) 
                                for pattern in self.DANGEROUS_PATTERNS]
    
    def validate_input(self, text: str) -> tuple[bool, str, List[str]]:
        """入力テキストの検証
        
        Returns:
            tuple: (is_safe, sanitized_text, detected_threats)
        """
        if not text or not isinstance(text, str):
            return True, "", []
        
        detected_threats = []
        sanitized_text = text
        
        # パターンマッチングによる検出
        for pattern in self.compiled_patterns:
            matches = pattern.findall(text)
            if matches:
                detected_threats.extend(matches)
                # 危険な部分を置換
                sanitized_text = pattern.sub('[FILTERED]', sanitized_text)
        
        # 長さ制限（セキュリティレベルに応じて）
        max_length = {
            SecurityLevel.LOW: 16000,
            SecurityLevel.MEDIUM: 12000,
            SecurityLevel.HIGH: 8000,
            SecurityLevel.CRITICAL: 4000
        }[self.security_level]
        
        if len(sanitized_text) > max_length:
            sanitized_text = sanitized_text[:max_length] + "...[TRUNCATED]"
            detected_threats.append("LENGTH_EXCEEDED")
        
        # セキュリティレベルに応じた判定
        is_safe = len(detected_threats) == 0 or self.security_level == SecurityLevel.LOW
        
        return is_safe, sanitized_text, detected_threats
    
    def log_security_event(self, text: str, threats: List[str], user_id: Optional[str] = None):
        """セキュリティイベントのログ記録"""
        timestamp = datetime.now().isoformat()
        event = {
            "timestamp": timestamp,
            "user_id": user_id,
            "threats": threats,
            "text_length": len(text),
            "security_level": self.security_level.value
        }
        
        # セキュリティログファイルに記録
        try:
            log_path = Path(__file__).resolve().parent / "security.log"
            with log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception:
            pass


class LLMClient(Protocol):
    async def analyze_survey(self, tokenized_text: str, response_model: Any) -> Any: ...
    async def analyze_emotions(self, prompt: str, response_model: Any) -> Any: ...
    async def moderate(self, text: str) -> Any: ...
    # 後方互換のため effort / verbosity は任意引数に変更
    async def generate_commentary(self, system_prompt: str, user_content: str, response_model: Any, max_tokens: int, effort: str | None = None, verbosity: str | None = None, temperature: float = 0.2) -> Any: ...


# OpenAI Adapter（Instructor を使用した構造化出力）
from openai import AsyncOpenAI
import instructor
from instructor.exceptions import IncompleteOutputException


class PromptCache:
    """プロンプトキャッシング管理クラス"""
    
    def __init__(self, cache_size: int = 100):
        self.cache_size = cache_size
        self.cache: Dict[str, str] = {}
        self.cache_hits = 0
        self.cache_misses = 0
    
    def _generate_cache_key(self, system_prompt: str, model: str) -> str:
        """キャッシュキーの生成"""
        content = f"{system_prompt}:{model}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
    
    def get_cached_prompt_id(self, system_prompt: str, model: str) -> Optional[str]:
        """キャッシュされたプロンプトIDを取得"""
        key = self._generate_cache_key(system_prompt, model)
        if key in self.cache:
            self.cache_hits += 1
            return self.cache[key]
        self.cache_misses += 1
        return None
    
    def store_prompt_id(self, system_prompt: str, model: str, prompt_id: str):
        """プロンプトIDをキャッシュに保存"""
        key = self._generate_cache_key(system_prompt, model)
        self.cache[key] = prompt_id
        
        # キャッシュサイズ制限
        if len(self.cache) > self.cache_size:
            # LRU方式で古いエントリを削除
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
    
    def get_cache_stats(self) -> Dict[str, int]:
        """キャッシュ統計を取得"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": round(hit_rate, 2),
            "cache_size": len(self.cache)
        }


class TokenUsageTracker:
    """トークン使用量追跡クラス"""
    
    def __init__(self):
        self.daily_usage = 0
        self.monthly_usage = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        # コスト計算（GPT-4.1-miniの正確なコスト）
        self.input_cost_per_1k = 0.0004   # $0.40/1M tokens
        self.output_cost_per_1k = 0.0016  # $1.60/1M tokens
    
    def add_usage(self, prompt_tokens: int, completion_tokens: int):
        """使用量を追加（実際のトークン数を使用）"""
        total_tokens = prompt_tokens + completion_tokens
        self.daily_usage += total_tokens
        self.monthly_usage += total_tokens
        self.total_tokens += total_tokens
        
        # 正確なコスト計算（入力・出力別）
        input_cost = prompt_tokens * self.input_cost_per_1k / 1000
        output_cost = completion_tokens * self.output_cost_per_1k / 1000
        cost = input_cost + output_cost
        self.total_cost += cost
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """使用量統計を取得（実際のトークン数ベース）"""
        return {
            "daily_tokens": self.daily_usage,
            "monthly_tokens": self.monthly_usage,
            "total_tokens": self.total_tokens,
            "total_cost": round(self.total_cost, 6),
            "input_cost_per_1k": self.input_cost_per_1k,
            "output_cost_per_1k": self.output_cost_per_1k,
            "model": "gpt-4.1-mini",
            "data_source": "actual_api_response"
        }


class OpenAIAdapter:
    def __init__(self) -> None:
        # APIキー未設定時は早期に明示エラー（無通信で即時ニュートラルになる事象を防止）
        api_key = settings.require_openai_api_key()
        self._raw = AsyncOpenAI(api_key=api_key)
        
        # Instructor でクライアントをパッチ（構造化出力を有効化）
        self._client = instructor.patch(self._raw)
        
        # セキュリティとキャッシュ機能の初期化
        self.security_validator = PromptSecurityValidator(SecurityLevel.HIGH)
        self.prompt_cache = PromptCache(cache_size=50)
        self.token_tracker = TokenUsageTracker()
        self.prompt_optimizer = PromptOptimizer()

    def _get_debug_log_path(self) -> Path:
        return Path(__file__).resolve().parent / "llm_debug.log"

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]

    def _summarize_exception(self, exc: Exception) -> str:
        status_code = getattr(exc, "status_code", None)
        response = getattr(exc, "response", None)
        if status_code is None and response is not None:
            status_code = getattr(response, "status_code", None)
        summary = type(exc).__name__
        if status_code:
            summary += f" status={status_code}"
        return summary

    async def _create_with_retry(self, kwargs: Dict[str, Any], label: str = "chat.completions"):
        """OpenAI API呼び出しを指数バックオフ付きでリトライ実行する。
        ネットワークエラー/一時的エラー/429を対象。
        """
        max_retries = max(1, int(getattr(settings, "API_MAX_RETRIES", 3)))
        base_ms = max(100, int(getattr(settings, "LLM_RETRY_BASE_MS", 500)))
        last_err: Exception | None = None
        for attempt in range(1, max_retries + 1):
            try:
                return await self._raw.chat.completions.create(**kwargs)
            except Exception as e:
                last_err = e
                msg = str(e).lower()
                # 429 / 一時的障害 / タイムアウト系を判定
                should_retry = (
                    "rate limit" in msg or "429" in msg or
                    "timeout" in msg or "timed out" in msg or
                    "service unavailable" in msg or "temporarily" in msg or
                    "connection" in msg or "reset" in msg
                )
                if not should_retry or attempt >= max_retries:
                    self._log(f"API_RETRY_GIVEUP label={label} attempt={attempt} err={self._summarize_exception(e)}")
                    raise
                # wait (exponential backoff with jitter)
                wait_ms = base_ms * (2 ** (attempt - 1))
                # 0-200msのジッター
                try:
                    import random
                    wait_ms += random.randint(0, 200)
                except Exception:
                    pass
                self._log(f"API_RETRY_WAIT label={label} attempt={attempt} wait_ms={wait_ms}")
                try:
                    await asyncio.sleep(wait_ms / 1000)
                except Exception:
                    pass
        # 最終失敗
        if last_err:
            raise last_err

    def _log(self, message: str) -> None:
        if not settings.DEBUG_API_LOG:
            return
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {message}"
        try:
            logger.debug(line)
        except Exception:
            pass
        try:
            with self._get_debug_log_path().open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

    async def _chat_json_call_with_caching(
        self,
        messages: List[Dict[str, str]],
        *,
        max_tokens: int,
        temperature: float | None = None,
        response_format: Dict[str, Any] | None = None,
        use_caching: bool = True,
    ) -> Dict[str, Any]:
        """プロンプトキャッシングを活用したAPI呼び出し"""
        
        # セキュリティ検証
        for message in messages:
            if message.get("role") == "user":
                is_safe, sanitized_text, threats = self.security_validator.validate_input(message["content"])
                if not is_safe:
                    self.security_validator.log_security_event(message["content"], threats)
                    message["content"] = sanitized_text
                    self._log(f"SECURITY_FILTER applied: {threats}")
        
        # プロンプトキャッシングの適用
        system_prompt = ""
        user_content = ""
        for msg in messages:
            if msg.get("role") == "system":
                system_prompt = msg["content"]
            elif msg.get("role") == "user":
                user_content = msg["content"]
        
        # プロンプトキャッシングを完全無効化（安定性重視）
        cached_prompt_id = None

        # 追加: プロンプト最適化（安全な範囲でのトークン削減）
        try:
            for msg in messages:
                if msg.get("role") == "user" and isinstance(msg.get("content"), str):
                    msg["content"] = self.prompt_optimizer.optimize_prompt(
                        msg["content"],
                        context={"max_chars": 8000},
                    )
        except Exception:
            # 最適化はベストエフォート。失敗しても処理継続
            pass
        
        # API呼び出し（最新のAPI仕様に完全対応）
        if cached_prompt_id:
            # キャッシュされたプロンプトを使用
            self._log(f"Using cached prompt: {cached_prompt_id}")
            # OpenAI API仕様: response_format=json_object使用時は「json」を含める必要がある
            if "json" not in user_content.lower():
                user_content = f"{user_content}\n\n出力はJSON形式でお願いします。"
            kwargs = {
                # モデル名は設定から取得して一貫性を保つ
                "model": getattr(settings, "OPENAI_MODEL", settings.PDF_LLM_MODEL),
                "messages": [{"role": "user", "content": user_content}],
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
                "extra_headers": {"OpenAI-Beta": "caching-v1"},
                "extra_body": {"prompt_id": cached_prompt_id}  # extra_bodyに含める
            }
        else:
            # 通常のAPI呼び出し
            # OpenAI API仕様: response_format=json_object使用時は「json」を含める必要がある
            for msg in messages:
                if msg.get("role") == "user" and "json" not in msg.get("content", "").lower():
                    msg["content"] = f"{msg['content']}\n\n出力はJSON形式でお願いします。"
            kwargs = {
                "model": getattr(settings, "OPENAI_MODEL", settings.PDF_LLM_MODEL),
                "messages": messages,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
            }
        
        if temperature is not None:
            kwargs["temperature"] = temperature
        
        try:
            resp = await self._create_with_retry(kwargs, label="chat.completions")
            
            # トークン使用量を追跡
            if hasattr(resp, 'usage') and resp.usage:
                self.token_tracker.add_usage(
                    resp.usage.prompt_tokens,
                    resp.usage.completion_tokens
                )
                self._log(f"Token usage: {resp.usage.prompt_tokens} prompt + {resp.usage.completion_tokens} completion")
            
            # プロンプトIDをキャッシュに保存
            if use_caching and system_prompt and hasattr(resp, 'system_fingerprint'):
                self.prompt_cache.store_prompt_id(system_prompt, getattr(settings, "OPENAI_MODEL", settings.PDF_LLM_MODEL), resp.system_fingerprint)
                self._log(f"Cached prompt ID: {resp.system_fingerprint}")
            
        except Exception as e:
            msg = str(e)
            self._log(f"API_HTTP_ERR label=chat.completions err={self._summarize_exception(e)}")
            
            # フォールバック処理
            if "Invalid schema for response_format" in msg or "response_format" in msg:
                try:
                    kwargs_fallback = dict(kwargs)
                    kwargs_fallback["response_format"] = {"type": "json_object"}
                    self._log("API_HTTP_FALLBACK response_format=json_object")
                    resp = await self._create_with_retry(kwargs_fallback, label="chat.completions_fallback_schema")
                except Exception as e2:
                    self._log(f"API_HTTP_ERR_FALLBACK err={self._summarize_exception(e2)}")
                    raise
            elif "prompt_id" in msg or "caching" in msg.lower():
                # プロンプトキャッシングエラーの場合、キャッシュなしで再試行
                try:
                    self._log("API_HTTP_FALLBACK disabling prompt caching")
                    kwargs_fallback = dict(kwargs)
                    # キャッシュ関連のパラメータを削除
                    kwargs_fallback.pop("extra_headers", None)
                    kwargs_fallback.pop("extra_body", None)
                    # 通常のメッセージ形式に戻す
                    kwargs_fallback["messages"] = messages
                    resp = await self._create_with_retry(kwargs_fallback, label="chat.completions_no_cache")
                except Exception as e2:
                    self._log(f"API_HTTP_ERR_FALLBACK_NO_CACHE err={self._summarize_exception(e2)}")
                    raise
            else:
                raise
        
        content = (resp.choices[0].message.content or "").strip()
        self._log(f"API_HTTP_OK content_len={len(content)} content_sha256={self._hash_text(content) if content else 'empty'}")

        # 段階的リトライ（受信が空/JSONでない場合）
        def _try_parse(text: str) -> Dict[str, Any]:
            try:
                return json.loads(text)
            except Exception:
                import re
                m = re.search(r"\{[\s\S]*\}", text)
                if m:
                    return json.loads(m.group(0))
                raise

        if content:
            try:
                return _try_parse(content)
            except Exception as e:
                self._log(f"API_PARSE_ERR first_pass err={type(e).__name__}")
        else:
            self._log("API_EMPTY_CONTENT first pass")

        # 2nd: schemaを外してjson_objectのみで再試行
        try:
            kwargs2 = dict(kwargs)
            kwargs2["response_format"] = {"type": "json_object"}
            resp2 = await self._create_with_retry(kwargs2, label="chat.completions_retry2")
            c2 = (resp2.choices[0].message.content or "").strip()
            self._log(f"API_HTTP_OK retry2 content_len={len(c2)} content_sha256={self._hash_text(c2) if c2 else 'empty'}")
            if c2:
                return _try_parse(c2)
        except Exception as e2:
            self._log(f"API_RETRY2_ERR err={self._summarize_exception(e2)}")

        # 3rd: 最小プロンプトで再試行（system極小 + temperature=0.2）
        try:
            min_messages = []
            for msg in messages:
                if msg.get("role") == "user":
                    min_messages.append({"role": "user", "content": msg["content"] + "\n\n出力はJSON形式でお願いします。"})
            kwargs3 = {
                "model": getattr(settings, "OPENAI_MODEL", settings.PDF_LLM_MODEL),
                "messages": min_messages or messages,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
                "temperature": 0.2,
            }
            resp3 = await self._create_with_retry(kwargs3, label="chat.completions_retry3")
            c3 = (resp3.choices[0].message.content or "").strip()
            self._log(f"API_HTTP_OK retry3 content_len={len(c3)} content_sha256={self._hash_text(c3) if c3 else 'empty'}")
            if c3:
                return _try_parse(c3)
        except Exception as e3:
            self._log(f"API_RETRY3_ERR err={self._summarize_exception(e3)}")

        # 全て失敗
        raise ValueError("LLM empty or non-JSON after retries")

    async def _chat_json_call(
        self,
        messages: List[Dict[str, str]],
        *,
        max_tokens: int,
        temperature: float | None = None,
        response_format: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        self._log(
            f"API_HTTP chat.completions.create model=gpt-4.1-mini-2025-04-14 max_tokens={max_tokens} temp={temperature} msgs={len(messages)}"
        )
        kwargs: Dict[str, Any] = {
            "model": "gpt-4.1-mini-2025-04-14",
            "messages": messages,
            "max_tokens": max_tokens,
            "response_format": response_format or {"type": "json_object"},
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
        try:
            resp = await self._create_with_retry(kwargs, label="chat.completions_simple")
        except Exception as e:
            msg = str(e)
            self._log(f"API_HTTP_ERR label=chat.completions_simple err={self._summarize_exception(e)}")
            # schemaエラーなどで400のときは json_object でフォールバック
            if "Invalid schema for response_format" in msg or "response_format" in msg:
                try:
                    kwargs_fallback = dict(kwargs)
                    kwargs_fallback["response_format"] = {"type": "json_object"}
                    self._log("API_HTTP_FALLBACK response_format=json_object")
                    resp = await self._create_with_retry(kwargs_fallback, label="chat.completions_simple_fallback")
                except Exception as e2:
                    self._log(f"API_HTTP_ERR_FALLBACK err={self._summarize_exception(e2)}")
                    raise
            else:
                raise
        content = (resp.choices[0].message.content or "").strip()
        self._log(f"API_HTTP_OK content_len={len(content)} content_sha256={self._hash_text(content) if content else 'empty'}")
        try:
            return json.loads(content)
        except Exception:
            import re
            match = re.search(r"\{[\s\S]*\}", content)
            if match:
                return json.loads(match.group(0))
            self._log("API_PARSE_ERR non-JSON content returned")
            raise ValueError("LLM did not return JSON content")

    def _json_schema_format(self, model_cls: Any, name: str) -> Dict[str, Any]:
        """Build strict JSON Schema response_format for Chat Completions."""
        try:
            schema = model_cls.model_json_schema()
        except Exception:
            schema = {}
        # Chat Completions 側の期待に合わせて top-level object を明示し、追加プロパティを禁止
        obj_schema: Dict[str, Any] = {
            "type": "object",
            "properties": schema.get("properties", {}),
            "required": schema.get("required", []),
            "additionalProperties": False,
        }
        return {
            "type": "json_schema",
            "json_schema": {
                "name": name,
                "schema": obj_schema,
                "strict": True,
            },
        }

    # --- Normalizers to coerce slightly-off JSON into our schema ----------------
    def _normalize_sentiment(self, value: Any) -> str:
        if isinstance(value, str):
            v = value.strip().lower()
            if any(k in v for k in ["positive", "ポジティブ", "良い", "+"]):
                return "positive"
            if any(k in v for k in ["negative", "ネガティブ", "悪い", "-", "不満", "やや不満", "ややネガ"]):
                return "negative"
            if "mixed" in v or "ミックス" in v or "混" in v:
                return "mixed"
            if "neutral" in v or "ニュートラル" in v or "どちらでもない" in v:
                return "neutral"
        return "neutral"

    def _normalize_bool(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            s = value.strip().lower()
            if s in ("true", "1", "yes", "y", "t", "はい", "あり", "可", "有"):
                return True
            if s in ("false", "0", "no", "n", "f", "いいえ", "なし", "不可", "無"):
                return False
        # 保守的に False
        return False

    def _normalize_survey_payload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "sentiment": self._normalize_sentiment(data.get("sentiment")),
            "key_topics": data.get("key_topics") or [],
            "verbatim_quote": data.get("verbatim_quote") or "",
            "actionable_insight": self._normalize_bool(data.get("actionable_insight")),
        }
        # key_topics が文字列のときは単一要素配列にする
        if isinstance(result["key_topics"], str):
            result["key_topics"] = [result["key_topics"].strip()] if result["key_topics"].strip() else []
        # 文字列要素に限定
        if isinstance(result["key_topics"], list):
            result["key_topics"] = [str(x).strip() for x in result["key_topics"] if str(x).strip()]
        return result

    def _normalize_emotions_payload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # 日本語キーのラップを剥がす
        if "感情スコア" in data and isinstance(data["感情スコア"], dict):
            jp = data["感情スコア"]
            data = {
                "joy": jp.get("喜び"),
                "sadness": jp.get("悲しみ"),
                "fear": jp.get("恐れ"),
                "surprise": jp.get("驚き"),
                "anger": jp.get("怒り"),
                "disgust": jp.get("嫌悪"),
                "reason": data.get("理由") or data.get("reason"),
            }
        # 数値化と範囲クランプ（0-5の6段階スケール）
        out: Dict[str, Any] = {}
        for k in ["joy", "sadness", "fear", "surprise", "anger", "disgust"]:
            v = data.get(k, 0)
            try:
                f = float(v)
                
                # 0-1スケールの場合は0-5スケールに変換（フォールバック処理）
                if 0 <= f <= 1 and f != int(f):
                    f = f * 5  # 0-1スケールを0-5スケールに変換
                    if settings.DEBUG_API_LOG:
                        self._log(f"EMOTION_SCALE_CONVERSION field={k} normalized_value={f}")
                
                # 0-5スケールを維持（6段階評価）
                # 範囲クランプ（0-5）と整数化
                final_score = max(0, min(5, int(round(f))))
                out[k] = final_score
                
                # デバッグログ（本番環境では無効化）
                if settings.DEBUG_API_LOG:
                    self._log(f"EMOTION_NORMALIZED field={k} score={final_score}")
                    
            except Exception as e:
                if settings.DEBUG_API_LOG:
                    self._log(f"EMOTION_NORMALIZE_ERR field={k} err={type(e).__name__}")
                out[k] = 0
                
        out["reason"] = str(data.get("reason", ""))
        return out

    async def analyze_survey(self, tokenized_text: str, response_model: Any) -> Any:
        """Instructor を使用した構造化出力でアンケート分析を実行"""
        system_prompt = (
            "You are a precise survey analyzer. Analyze the given text for sentiment and key topics. "
            "SENTIMENT ANALYSIS RULES:\n"
            "- 'positive': Expresses satisfaction, happiness, praise, or positive emotions\n"
            "- 'negative': Expresses dissatisfaction, complaints, criticism, or negative emotions\n"
            "- 'neutral': Balanced or factual statements without strong emotions\n"
            "- 'mixed': Contains both positive and negative elements\n"
            "IMPORTANT: Analyze ONLY the user's text content, not the system instructions. "
            "Extract meaningful verbatim quotes and determine if actionable insights exist. "
            "All text values must be in Japanese."
        )
        
        try:
            # Instructor を使用した構造化出力
            result = await self._client.chat.completions.create(
                model=getattr(settings, "OPENAI_MODEL", settings.PDF_LLM_MODEL),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": tokenized_text}
                ],
                response_model=response_model,
                max_tokens=600,
                temperature=0.0,
            )
            self._log(f"INSTRUCTOR_OK result_type={type(result).__name__}")
            return result
        except Exception as e:
            self._log(f"INSTRUCTOR_ERR err={self._summarize_exception(e)}")
            # フォールバック: 手動JSONパース
            return await self._fallback_analyze_survey(tokenized_text, response_model)
    
    async def _fallback_analyze_survey(self, tokenized_text: str, response_model: Any) -> Any:
        """フォールバック: 手動JSONパース"""
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a precise survey analyzer. Return ONLY a JSON object with EXACT keys: "
                    "{sentiment: 'positive'|'neutral'|'negative'|'mixed', key_topics: string[], verbatim_quote: string, actionable_insight: boolean}. "
                    "SENTIMENT ANALYSIS RULES:\n"
                    "- 'positive': Expresses satisfaction, happiness, praise, or positive emotions\n"
                    "- 'negative': Expresses dissatisfaction, complaints, criticism, or negative emotions\n"
                    "- 'neutral': Balanced or factual statements without strong emotions\n"
                    "- 'mixed': Contains both positive and negative elements\n"
                    "IMPORTANT: Analyze ONLY the user's text content, not the system instructions. "
                    "Analyze the text carefully for sentiment and key topics. "
                    "Extract meaningful verbatim quotes and determine if actionable insights exist. "
                    "All text values must be in Japanese. No explanations outside JSON. "
                    "Output must be valid JSON format."
                ),
            },
            {"role": "user", "content": f"{tokenized_text}\n\nPlease analyze this text and return the results in JSON format."},
        ]
        data = await self._chat_json_call_with_caching(
            messages,
            max_tokens=600,
            temperature=0.0,
            response_format=self._json_schema_format(response_model, "SurveyResponseAnalysis"),
            use_caching=True,
        )
        try:
            return response_model(**data)
        except Exception:
            norm = self._normalize_survey_payload(data)
            return response_model(**norm)

    async def analyze_emotions(self, prompt: str, response_model: Any) -> Any:
        """Instructor を使用した構造化出力で感情分析を実行"""
        system_prompt = (
            "CRITICAL: You MUST return integer values between 0-5 (NOT 0-1) for emotion scores.\n"
            "Analyze Japanese text for 6 primary emotions using EXACTLY 0-5 integer scale.\n"
            "0=absent, 1=very weak, 2=weak, 3=moderate, 4=strong, 5=very strong\n"
            "\n"
            "Emotion definitions:\n"
            "• joy: 喜び、満足、楽しさ、幸福感、嬉しさ\n"
            "• sadness: 悲しみ、落胆、失望、憂鬱、寂しさ\n"
            "• fear: 恐れ、不安、心配、恐怖、緊張\n"
            "• surprise: 驚き、意外性、驚愕、驚嘆、びっくり\n"
            "• anger: 怒り、憤り、不満、イライラ、腹立ち\n"
            "• disgust: 嫌悪、軽蔑、拒絶、嫌悪感、うんざり"
        )
        
        try:
            # Instructor を使用した構造化出力
            result = await self._client.chat.completions.create(
                model=getattr(settings, "OPENAI_MODEL", settings.PDF_LLM_MODEL),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_model=response_model,
                max_tokens=400,
                temperature=0.0,
            )
            return result
        except Exception as e:
            self._log(f"INSTRUCTOR_EMOTION_ERR err={self._summarize_exception(e)}")
            # フォールバック: 手動JSONパース
            return await self._fallback_analyze_emotions(prompt, response_model)
    
    async def _fallback_analyze_emotions(self, prompt: str, response_model: Any) -> Any:
        """フォールバック: 手動JSONパース"""
        messages = [
            {"role": "system", "content": (
                "CRITICAL: You MUST return integer values between 0-5 (NOT 0-1) for emotion scores.\n"
                "Analyze Japanese text for 6 primary emotions using EXACTLY 0-5 integer scale.\n"
                "Return JSON: {joy:0-5, sadness:0-5, fear:0-5, surprise:0-5, anger:0-5, disgust:0-5, reason:string}\n"
                "\n"
                "MANDATORY SCORING RULES:\n"
                "• ONLY integer values: 0, 1, 2, 3, 4, 5\n"
                "• NEVER use decimal values (0.0, 0.5, 1.0, etc.)\n"
                "• NEVER use 0-1 scale\n"
                "• 0=absent, 1=very weak, 2=weak, 3=moderate, 4=strong, 5=very strong\n"
                "\n"
                "Emotion definitions:\n"
                "• joy: 喜び、満足、楽しさ、幸福感、嬉しさ\n"
                "• sadness: 悲しみ、落胆、失望、憂鬱、寂しさ\n"
                "• fear: 恐れ、不安、心配、恐怖、緊張\n"
                "• surprise: 驚き、意外性、驚愕、驚嘆、びっくり\n"
                "• anger: 怒り、憤り、不満、イライラ、腹立ち\n"
                "• disgust: 嫌悪、軽蔑、拒絶、嫌悪感、うんざり\n"
                "\n"
                "Japanese context analysis:\n"
                "• Honorifics: です/ます (formal), でございます (very formal)\n"
                "• Intensity modifiers: とても/すごく (strong), かなり (quite), まあまあ (moderate), 少し (slight)\n"
                "• Onomatopoeia: わくわく (excitement), どきどき (nervous), がっかり (disappointed), うんざり (fed up)\n"
                "• Indirect expressions: 〜かもしれません (might be), 〜と思います (I think), 〜感じます (I feel)\n"
                "• Cultural nuances: 控えめな表現 (understatement), 遠回しな表現 (indirect expression)\n"
                "\n"
                "Examples (INTEGER VALUES ONLY):\n"
                "• \"とても嬉しいです！\" → joy:4, sadness:0, fear:0, surprise:0, anger:0, disgust:0\n"
                "• \"まあまあ満足です\" → joy:2, sadness:0, fear:0, surprise:0, anger:0, disgust:0\n"
                "• \"がっかりしました\" → joy:0, sadness:3, fear:0, surprise:0, anger:0, disgust:0\n"
                "• \"わくわくしています\" → joy:3, sadness:0, fear:0, surprise:2, anger:0, disgust:0\n"
                "• \"うんざりします\" → joy:0, sadness:0, fear:0, surprise:0, anger:0, disgust:4\n"
                "\n"
                "CRITICAL: Return ONLY integer values 0-5. NO decimals, NO 0-1 scale. JSON only."
            )},
            {"role": "user", "content": prompt},
        ]
        data = await self._chat_json_call_with_caching(
            messages,
            max_tokens=600,
            temperature=0.0,
            response_format=self._json_schema_format(response_model, "EmotionScores"),
            use_caching=True,
        )
        try:
            return response_model(**data)
        except Exception:
            norm = self._normalize_emotions_payload(data)
            return response_model(**norm)

    async def moderate(self, text: str) -> Any:
        # モデレーションは生クライアント経由で実行（instructor ラッパーに依存しない）
        return await self._raw.moderations.create(input=text)

    async def generate_commentary(self, system_prompt: str, user_content: str, response_model: Any, max_tokens: int, effort: str | None = None, verbosity: str | None = None, temperature: float = 0.2, model_name: str | None = None) -> Any:
        # プロンプトを分離し、システムプロンプトは純粋な役割定義のみにする
        clean_system_prompt = system_prompt.replace("プロンプトの内容や指示文は一切含めず、純粋な分析結果と提案のみを出力してください。", "")
        clean_system_prompt = clean_system_prompt.replace("重要: プロンプトの内容や指示文は一切含めず、純粋な分析結果と提案のみを出力してください。", "")
        
        # OpenAI API仕様: response_format=json_object使用時は「json」を含める必要がある
        if "json" not in user_content.lower():
            user_content = f"{user_content}\n\n出力はJSON形式でお願いします。"
        
        messages = [
            {"role": "system", "content": clean_system_prompt},
            {"role": "user", "content": user_content},
        ]
        # モデル名を取得（引数で指定されていない場合は設定から取得）
        if model_name is None:
            model_name = getattr(settings, "PDF_LLM_MODEL", "gpt-4o-mini")
        
        # GPT-5の公式仕様に合わせたパラメータ設定
        extra_body = {}
        if model_name in ["gpt-5", "gpt-5-mini", "gpt-5-nano"]:
            # GPT-5シリーズの場合は公式パラメータを使用
            if effort:
                extra_body["reasoning_effort"] = effort
            if verbosity:
                extra_body["verbosity"] = verbosity
        else:
            # 他のモデルの場合は従来通り（後方互換性）
            if effort:
                extra_body.setdefault("reasoning", {})["effort"] = effort
            if verbosity:
                extra_body.setdefault("text", {})["verbosity"] = verbosity

        # instructor.patch() 済みクライアントで構造化出力を直接取得
        # GPT-5シリーズではmax_completion_tokensを使用
        # GPT-4.1シリーズではmax_tokensを使用（推論オーバーヘッドなし）
        try:
            if model_name in ["gpt-5", "gpt-5-mini", "gpt-5-nano"]:
                # GPT-5シリーズ（推論モデル）
                result = await self._client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    response_model=response_model,
                    max_completion_tokens=max_tokens,  # 推論+出力の合計
                    extra_body=extra_body if extra_body else None,
                )
            elif model_name in ["gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano"]:
                # GPT-4.1シリーズ（従来型モデル、推論オーバーヘッドなし）
                result = await self._client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    response_model=response_model,
                    max_tokens=max_tokens,  # 出力のみ（予測可能）
                    temperature=0.1,  # 一貫性重視
                )
            else:
                # その他のモデル（GPT-4oシリーズなど）
                result = await self._client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    response_model=response_model,
                    max_tokens=max_tokens,
                    temperature=0.1,  # 一貫性重視
                )
        except IncompleteOutputException as e:
            # 不完全な出力を検出（Claudeの分析で指摘された問題）
            self._log(f"INCOMPLETE_OUTPUT err={self._summarize_exception(e)} model={model_name} max_tokens={max_tokens}")
            # デフォルト値を返す（response_modelの型に応じて）
            # Pydanticモデルのデフォルトインスタンスを作成
            try:
                # response_modelがPydanticモデルの場合、デフォルト値を設定
                if hasattr(response_model, 'model_validate'):
                    # 空のdictからデフォルトインスタンスを作成
                    result = response_model.model_validate({})
                else:
                    # その他の場合はNoneを返す
                    raise ValueError(f"IncompleteOutputException: 不完全な出力が検出されました。モデル: {model_name}, トークン制限: {max_tokens}")
            except Exception as fallback_error:
                self._log(f"INCOMPLETE_OUTPUT_FALLBACK_ERR err={type(fallback_error).__name__}")
                raise ValueError(f"IncompleteOutputException: 不完全な出力が検出されました。モデル: {model_name}, トークン制限: {max_tokens}")
        
        # action_items が dict の配列で返る事例に対応
        if hasattr(result, 'action_items') and isinstance(result.action_items, list):
            ai = []
            for it in result.action_items:
                if isinstance(it, str):
                    ai.append(it)
                elif isinstance(it, dict):
                    # 最初の値を文字列化
                    try:
                        ai.append(next((str(v) for v in it.values() if v), ""))
                    except Exception:
                        pass
            result.action_items = [s for s in ai if isinstance(s, str) and s.strip()]
        
        return result
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """使用量統計とキャッシュ統計を取得"""
        token_stats = self.token_tracker.get_usage_stats()
        cache_stats = self.prompt_cache.get_cache_stats()
        
        return {
            "token_usage": token_stats,
            "cache_performance": cache_stats,
            "security_level": self.security_validator.security_level.value,
            "estimated_savings": self._calculate_estimated_savings()
        }
    
    def _calculate_estimated_savings(self) -> Dict[str, float]:
        """プロンプトキャッシングによる推定コスト削減を計算"""
        cache_stats = self.prompt_cache.get_cache_stats()
        token_stats = self.token_tracker.get_usage_stats()
        
        if cache_stats["hit_rate"] > 0:
            # キャッシュヒット率に基づく推定削減
            estimated_savings = token_stats["total_cost"] * (cache_stats["hit_rate"] / 100) * 0.5  # 50%削減と仮定
            return {
                "estimated_cost_savings": round(estimated_savings, 4),
                "hit_rate_percentage": cache_stats["hit_rate"],
                "cache_efficiency": "high" if cache_stats["hit_rate"] > 70 else "medium" if cache_stats["hit_rate"] > 40 else "low"
            }
        else:
            return {
                "estimated_cost_savings": 0.0,
                "hit_rate_percentage": 0.0,
                "cache_efficiency": "none"
            }


def get_llm_client() -> LLMClient:
    # 将来: settings.LLM_PROVIDER == "vertex" で VertexAdapter を返す
    return OpenAIAdapter()
